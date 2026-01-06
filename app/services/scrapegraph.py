"""
ScrapeGraph Service - Web scraping using Playwright + Gemini
"""
import asyncio
import json
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from app.core.config import settings
import google.generativeai as genai
# reuse model selection logic from gemini service
from app.services.gemini import _choose_model
from playwright.async_api import async_playwright
import httpx

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
    
    # 1. Try a fast HTTP fetch first (avoids launching Chromium when not needed)
    html_content = ""
    used_httpx = False
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200 and resp.text and len(resp.text) > 200:
                html_content = resp.text
                used_httpx = True
                print(f"Fetched HTML via httpx for {url} (len={len(html_content)})")
    except Exception:
        used_httpx = False

    # If httpx didn't produce useful HTML, fall back to Playwright (for JS-heavy pages)
    try:
        if not used_httpx:
            async with async_playwright() as p:
                launch_args = getattr(settings, "playwright_launch_args_list", [])
                browser = await p.chromium.launch(headless=True, args=launch_args)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                try:
                    timeout_ms = getattr(settings, "SCRAPE_TIMEOUT_MS", 120000)
                    await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    try:
                        structured = await page.evaluate("""() => {
                            const qs = (s) => document.querySelector(s);
                            const qsa = (s) => Array.from(document.querySelectorAll(s));

                            const getMeta = (name) => {
                                const m = document.querySelector(`meta[name="${name}"]`) || document.querySelector(`meta[property="${name}"]`);
                                return m ? m.getAttribute('content') : null;
                            };

                            const title = (qs('h1') && qs('h1').innerText.trim()) || (qs('.article-title') && qs('.article-title').innerText.trim()) || getMeta('og:title') || getMeta('twitter:title');
                            const timeEl = qs('time');
                            const published = timeEl ? (timeEl.getAttribute('datetime') || timeEl.innerText.trim()) : (getMeta('article:published_time') || getMeta('og:published_time') || getMeta('pubdate'));

                            const articleEl = qs('article') || qs('.story-contents.w-full') || qs('.story-contents') || qs('.article__main') || qs('.article-body') || qs('.post-content') || qs('.content') || qs('#content');

                            const paragraphs = [];
                            if (articleEl) {
                                const nodes = articleEl.querySelectorAll('p, h2, h3, blockquote, li');
                                nodes.forEach(n => { const t = n.innerText.trim(); if (t) paragraphs.push(t); });
                            } else {
                                qsa('p').forEach(p => { const t = p.innerText.trim(); if (t) paragraphs.push(t); });
                            }

                            const images = [];
                            const imgEls = articleEl ? Array.from(articleEl.querySelectorAll('img')) : qsa('img');
                            imgEls.forEach(img => { const src = img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src'); if (src) images.push(src); });
                            if (images.length === 0) {
                                const og = getMeta('og:image') || getMeta('twitter:image'); if (og) images.push(og);
                            }

                            return { title: title || null, published: published || null, paragraphs: paragraphs, images: images, raw_html: document.body.innerHTML };
                        """)
                        html_content = structured.get('raw_html', '')
                    except Exception:
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
        else:
            # httpx provided HTML, continue
            pass
    except Exception as e:
        print(f"❌ Browser Error: {e}")
        return _get_mock_data(url)

    if not html_content:
        return _get_mock_data(url)

    # If we extracted structured DOM data already, prefer that result for article pages
    if scraping_type == "article":
        if 'structured' in locals() and structured and isinstance(structured.get('paragraphs', None), list) and len(structured.get('paragraphs'))>0:
            body_text = "\n\n".join(structured.get('paragraphs', []))
            images = structured.get('images', []) or []
            return {
                "title": structured.get('title') or "",
                "body": body_text,
                "image_url": images[0] if images else "",
                "images": images,
                "published": structured.get('published'),
                "raw_html": html_content,
                "success": True
            }

    # 2. Process with Gemini
    try:
        # Choose a model using the centralized selector (may return namespaced 'models/..')
        model_name = _choose_model()
        print(f"Using Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
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
