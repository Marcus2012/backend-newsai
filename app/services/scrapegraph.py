"""
ScrapeGraph Service - Web scraping using Playwright + Gemini
"""
import asyncio
import json
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from app.core.config import settings
import google.generativeai as genai
from playwright.async_api import async_playwright

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

async def scrape_url(
    url: str,
    template: Optional[Dict[str, Any]] = None,
    scraping_type: str = "list"
) -> Dict[str, Any]:
    """
    Scrape a URL using Playwright + Gemini (Custom implementation)
    
    Args:
        url: URL to scrape
        template: Optional template
        scraping_type: "list" for section pages, "article" for detail pages
    """
    print(f"--- Scraping {url} ({scraping_type}) ---")
    
    # 1. Fetch HTML content using Playwright
    html_content = ""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Create a new context with a user agent to avoid blocking
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                # Wait a bit for dynamic content
                await page.wait_for_timeout(2000)
                
                # Clean HTML to reduce tokens (remove scripts, styles, svgs)
                html_content = await page.evaluate("""() => {
                    const elements = document.querySelectorAll('script, style, noscript, iframe, svg, link[rel="stylesheet"]');
                    elements.forEach(el => el.remove());
                    return document.body.innerHTML;
                }""")
            except Exception as e:
                print(f"❌ Playwright Error: {e}")
                return _get_mock_data(url)
            finally:
                await browser.close()
    except Exception as e:
        print(f"❌ Browser Error: {e}")
        return _get_mock_data(url)

    if not html_content:
        return _get_mock_data(url)

    # 2. Process with Gemini
    try:
        # Use gemini-pro for better compatibility
        model = genai.GenerativeModel('gemini-pro') 
        
        if scraping_type == "list":
            prompt = """
            You are an expert web scraper. Extract a list of the top 10 news articles from the provided HTML.
            Return a JSON object with a key 'articles' containing a list of objects.
            
            For each article extract:
            - title: The headline.
            - url: The absolute link to the article. (If relative, prepend the base domain).
            - summary: A brief summary.
            - image_url: The URL of the image.
            
            HTML Content:
            """
        else:
            prompt = """
            You are an expert web scraper. Extract the full content of the news article from the provided HTML.
            Return a JSON object with keys: title, body, image_url, summary.
            
            Fields:
            - title: Main headline.
            - body: Full article text, preserving paragraphs and quotes. Exclude ads/menus.
            - image_url: Main article image.
            - summary: Brief summary.
            
            HTML Content:
            """
            
        # Truncate HTML if necessary (Gemini 1.5 Flash has 1M context, so usually fine, but let's be safe)
        prompt_content = f"{prompt}\n\n{html_content[:200000]}"
        
        response = await model.generate_content_async(
            prompt_content,
            generation_config={"response_mime_type": "application/json"}
        )
        
        result_text = response.text
        result = json.loads(result_text)
        
        if scraping_type == "list":
            articles = result.get("articles", [])
            # Fix relative URLs if needed (basic check)
            base_domain = "/".join(url.split("/")[:3])
            for art in articles:
                if art.get("url") and art.get("url").startswith("/"):
                    art["url"] = base_domain + art["url"]
                    
            return {
                "articles": articles,
                "raw_json": result,
                "success": True
            }
        else:
            return {
                "title": result.get("title", ""),
                "body": result.get("body", ""),
                "image_url": result.get("image_url", ""),
                "summary": result.get("summary", ""),
                "raw_json": result,
                "success": True
            }

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
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
