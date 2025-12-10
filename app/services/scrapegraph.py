"""
ScrapeGraph Service - Web scraping using ScrapeGraphAI (Local Library)
"""
import asyncio
import json
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from app.core.config import settings

try:
    from scrapegraphai.graphs import SmartScraperGraph
    HAS_SCRAPEGRAPH = True
except ImportError:
    HAS_SCRAPEGRAPH = False
    print("⚠️ ScrapeGraphAI library not found. Please install it: pip install scrapegraphai playwright && playwright install")

async def scrape_url(
    url: str,
    template: Optional[Dict[str, Any]] = None,
    scraping_type: str = "list"
) -> Dict[str, Any]:
    """
    Scrape a URL using ScrapeGraphAI library locally
    
    Args:
        url: URL to scrape
        template: Optional template
        scraping_type: "list" for section pages, "article" for detail pages
    """
    if not HAS_SCRAPEGRAPH:
        print("⚠️ Using MOCK data because ScrapeGraphAI is not installed.")
        return _get_mock_data(url)

    # Configuración para ScrapeGraphAI
    graph_config = {
        "llm": {
            "api_key": settings.GROQ_API_KEY,
            "model": f"groq/{settings.GROQ_MODEL}",
        },
        "verbose": True,
        "headless": True,
    }

    if scraping_type == "list":
        prompt = """
        Extract a list of the top 10 news articles from the page.
        For each article, extract:
        - title: The headline.
        - url: The absolute link to the article.
        - summary: A brief summary or context.
        - image_url: The URL of the image displayed with the article. Look for 'src', 'data-src', or 'srcset' attributes. Ensure it is the direct link to the image file.

        Return the result as a JSON object with a key 'articles' which is a list of these objects.
        """
    else:
        # Prompt detallado para artículos individuales
        prompt = """
        Extract the full content of the news article.
        Fields to extract:
        - title: The main headline.
        - body: The full article text. IMPORTANT: Preserve all content including:
            - Standard paragraphs.
            - Quotes and statements (e.g., "Yo soy de Alianza...").
            - Data tables or statistics (format them as readable text or markdown tables).
            - Exclude ads, "Read also" links, and navigation menus.
        - image_url: The main featured image URL (high quality). Look for 'src', 'data-src', or 'srcset'.
        - summary: A brief summary (2-3 sentences).
        
        Return the result as a JSON object with keys: title, body, image_url, summary.
        """

    loop = asyncio.get_event_loop()
    
    def run_scraper():
        try:
            smart_scraper_graph = SmartScraperGraph(
                prompt=prompt,
                source=url,
                config=graph_config
            )
            return smart_scraper_graph.run()
        except Exception as e:
            print(f"❌ ScrapeGraphAI Error: {e}")
            raise e

    try:
        # Ejecutar en un thread aparte para no bloquear
        result = await loop.run_in_executor(None, run_scraper)
        
        # Si el resultado es un string JSON, parsearlo
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except:
                pass
        
        if scraping_type == "list":
            # Normalizar resultado lista
            articles = result.get("articles", [])
            if not articles and "title" in result:
                articles = [result]
            return {
                "articles": articles,
                "raw_json": result,
                "success": True
            }
        else:
            # Normalizar resultado artículo
            return {
                "title": result.get("title", ""),
                "body": result.get("body", ""),
                "image_url": result.get("image_url", ""),
                "summary": result.get("summary", ""),
                "raw_json": result,
                "success": True
            }
    
    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")
        print("⚠️ Using MOCK data for testing purposes.")
        return _get_mock_data(url)

def _get_mock_data(url: str) -> Dict[str, Any]:
    return {
        "articles": [
            {
                "title": f"Mock Article {i}: {url}",
                "url": f"{url}/article-{i}",
                "summary": "Mock summary for testing.",
                "image_url": "https://via.placeholder.com/800x400"
            } for i in range(1, 11)
        ],
        "raw_json": {},
        "success": True
    }

async def test_template(template: Any, url: str) -> Dict[str, Any]:
    return await scrape_url(url)


def extract_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: Full URL string
    
    Returns:
        Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split('/')[0]
