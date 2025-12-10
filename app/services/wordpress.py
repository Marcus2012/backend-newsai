"""
WordPress Service - Publishing articles via WPGraphQL
"""
import aiohttp
from typing import Optional

from app.core.config import settings


CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    post {
      id
      databaseId
      title
      excerpt
      status
      featuredImage {
        node {
          sourceUrl
        }
      }
    }
  }
}
"""

PUBLISH_POST_MUTATION = """
mutation PublishPost($input: UpdatePostInput!) {
  updatePost(input: $input) {
    post {
      id
      databaseId
      status
    }
  }
}
"""


async def publish_to_wordpress(article) -> str:
    """
    Publish a generated article to WordPress via WPGraphQL
    
    Args:
        article: GeneratedArticle object
    
    Returns:
        WordPress post ID
    
    Raises:
        Exception: On publishing errors
    """
    
    # Variables to create post as DRAFT
    create_variables = {
        "input": {
            "clientMutationId": str(article.id),
            "title": article.title,
            "excerpt": article.description,
            "status": "DRAFT",
            "content": f"<p>{article.description}</p>",
        }
    }
    
    # Add featured image if available
    if article.image_url:
        create_variables["input"]["featuredImage"] = {
            "node": {
                "sourceUrl": article.image_url
            }
        }
    
    # Add SEO meta if available
    if article.seo_meta:
        create_variables["input"]["seo"] = {
            "title": article.seo_meta.get("meta_title", ""),
            "metaDesc": article.seo_meta.get("meta_description", ""),
            "focuskw": ",".join(article.seo_meta.get("keywords", []))
        }
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
            }
            
            if settings.WP_AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {settings.WP_AUTH_TOKEN}"
            
            # Create post
            payload = {
                "query": CREATE_POST_MUTATION,
                "variables": create_variables
            }
            
            async with session.post(
                settings.WP_GRAPHQL_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise Exception(f"WordPress error: {response.status}")
                
                data = await response.json()
                
                if "errors" in data:
                    raise Exception(f"GraphQL error: {data['errors']}")
                
                post_id = data["data"]["createPost"]["post"]["databaseId"]
                return str(post_id)
    
    except Exception as e:
        raise Exception(f"Error publicando a WordPress: {str(e)}")


async def update_post_status(post_id: str, status: str = "PUBLISH") -> bool:
    """
    Update post status in WordPress
    
    Args:
        post_id: WordPress post ID
        status: New status (DRAFT, PUBLISH, PENDING)
    
    Returns:
        True if successful
    """
    
    variables = {
        "input": {
            "clientMutationId": post_id,
            "id": f"cG9zdDp7cG9zdF9pZH0={post_id}",  # GraphQL ID encoding
            "status": status
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
            }
            
            if settings.WP_AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {settings.WP_AUTH_TOKEN}"
            
            payload = {
                "query": PUBLISH_POST_MUTATION,
                "variables": variables
            }
            
            async with session.post(
                settings.WP_GRAPHQL_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    return False
                
                data = await response.json()
                return "errors" not in data
    
    except Exception as e:
        print(f"Error updating post: {str(e)}")
        return False
