"""
Scheduler - Automated scraping jobs using APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse, urlunparse
import re
from sqlalchemy import select
import asyncio

from app.core.config import settings
from app.core.database import async_session
from app.core.models import RawArticle, GeneratedArticle, ScraperTemplate, StatusEnum
from app.services.scrapegraph import scrape_url
from app.services.gemini import generate_article


scheduler = AsyncIOScheduler()


def _format_category(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "General"
    value = value.replace("-", " ").replace("_", " ").strip()
    return value.title()


def _derive_category_from_list_url(list_url: str) -> str:
    try:
        normalized = (list_url or "").strip().rstrip("/")
    except Exception:
        normalized = ""

    explicit_map = {
        "https://rpp.pe/futbol/descentralizado": "Liga 1",
        "https://rpp.pe/futbol/champions-league": "Champions League",
        "https://www.espn.com.pe/futbol/liga/_/nombre/ita.1": "Serie A - Italia",
    }
    if normalized in explicit_map:
        return explicit_map[normalized]

    try:
        parsed = urlparse(normalized)
        segments = [s for s in parsed.path.split("/") if s]
    except Exception:
        segments = []

    if not segments:
        return "General"

    # Prioridad explícita si se detecta fútbol/deportes
    if "futbol" in segments:
        return "Fútbol"
    if "deportes" in segments or "sports" in segments:
        return "Deportes"

    ignore = {"news", "noticias", "liga", "nombre"}
    for seg in reversed(segments):
        if seg in ignore:
            continue
        if seg.startswith("_"):
            continue
        if "." in seg:
            continue
        return _format_category(seg)

    return _format_category(segments[-1])


async def scraping_job():
    """
    Scheduled job that runs scraping and AI generation
    
    This job:
    1. Gets active templates from database
    2. Scrapes configured URLs using matching templates
    3. Saves raw articles to database
    4. Generates AI content using Gemini
    5. Saves generated articles to database
    """
    print(f"[{datetime.now()}] Iniciando scraping automático...")
    
    async with async_session() as db:
        try:
            # Get active templates
            result = await db.execute(
                select(ScraperTemplate).where(ScraperTemplate.active == "true")
            )
            templates = result.scalars().all()
            
            for url in settings.scrape_urls_list:
                try:
                    list_category = _derive_category_from_list_url(url)
                    # Find template for this domain
                    template = next(
                        (t for t in templates if t.domain in url),
                        None
                    )
                    
                    template_dict = None
                    if template:
                        template_dict = {
                            "selectors": template.selectors,
                            "rules": template.rules
                        }
                    
                    # Scrape URL (List Mode)
                    print(f"  Scrapeando lista: {url}")
                    scraped_data = await scrape_url(url, template_dict, scraping_type="list")
                    
                    articles = scraped_data.get("articles", [])
                    if not articles:
                        print(f"  ⚠️ No se encontraron artículos en {url}")
                        continue

                    # Limit to 5 articles (reduce LLM calls / quota usage)
                    count = 0
                    for article in articles[:5]:
                        article_url = article.get("url")
                        if not article_url:
                            continue

                        # Normalize relative URLs and remove duplicated slashes in path
                        try:
                            # Resolve relative URLs against the list page
                            article_url = urljoin(url, article_url)
                            parsed = urlparse(article_url)
                            # Collapse multiple slashes in path (but preserve leading slash)
                            normalized_path = re.sub(r'/+', '/', parsed.path)
                            parsed = parsed._replace(path=normalized_path)
                            article_url = urlunparse(parsed)
                        except Exception:
                            # keep original if normalization fails
                            pass
                            
                        # Scrape Detail (Article Mode)
                        print(f"    Scrapeando detalle: {article.get('title')[:30]}...")
                        try:
                            # Small delay to avoid rate limits but keep flow fast
                            await asyncio.sleep(3)

                            local_now = datetime.now(timezone(timedelta(hours=-5)))
                            
                            detail_data = await scrape_url(article_url, scraping_type="article")
                            
                            img_url = detail_data.get("image_url") or article.get("image_url")
                            
                            # Save to raw_articles
                            raw_article = RawArticle(
                                source=url.split('/')[2],
                                source_url=article_url,
                                scraped_title=detail_data.get("title") or article.get("title"),
                                scraped_body=detail_data.get("body"),  # Full body from detail
                                image_url=img_url,
                                context=detail_data.get("summary") or article.get("summary"),
                                raw_json=detail_data.get("raw_json"),
                                scraper_template=str(template.id) if template else None,
                                scraper_version=template.version if template else "default",
                                scraped_at=datetime.utcnow(),
                                created_at=local_now
                            )
                            
                            db.add(raw_article)
                            # Flush to assign primary key before creating generated article
                            try:
                                await db.flush()
                            except Exception as flush_error:
                                await db.rollback()
                                print(f"      ❌ Error preparando RawArticle: {flush_error}")
                                continue

                            # Generate AI article linked to the raw scrape so the UI can display it
                            try:
                                generation_context = (
                                    detail_data.get("summary")
                                    or detail_data.get("body")
                                    or article.get("summary")
                                    or ""
                                )
                                ai_article = await generate_article(
                                    generation_context,
                                    raw_title=detail_data.get("title") or article.get("title")
                                )
                                generated_article = GeneratedArticle(
                                    raw_article_id=raw_article.id,
                                    title=ai_article.get("title") or raw_article.scraped_title or "Sin título",
                                    description=ai_article.get("description") or generation_context,
                                    scraped_body=detail_data.get("body") or raw_article.scraped_body,
                                    seo_meta=ai_article.get("seo"),
                                    categories=list_category,
                                    image_url=img_url,
                                    status=StatusEnum.draft,
                                    created_at=local_now
                                )
                            except Exception as e:
                                print(f"      ⚠️ Error generando artículo IA: {e}")
                                # Fallback: create a minimal generated article so UI still shows the item
                                fallback_description = (
                                    (detail_data.get("summary") or "")
                                    or (detail_data.get("body") or "")[:280]
                                    or (article.get("summary") or "")
                                )
                                generated_article = GeneratedArticle(
                                    raw_article_id=raw_article.id,
                                    title=raw_article.scraped_title or article.get("title") or "Sin título",
                                    description=fallback_description,
                                    scraped_body=detail_data.get("body") or raw_article.scraped_body,
                                    seo_meta=None,
                                    categories=list_category,
                                    image_url=img_url,
                                    status=StatusEnum.draft,
                                    created_at=local_now
                                )
                            db.add(generated_article)

                            # Persist each article immediately so UI sees results even if job stops later
                            try:
                                await db.commit()
                            except Exception as commit_error:
                                await db.rollback()
                                print(f"      ❌ Error guardando en BD: {commit_error}")
                                continue

                            count += 1
                            print(f"      ✅ Guardado [Img: {'✅' if img_url else '❌'}]")
                        
                        except Exception as e:
                            print(f"      ❌ Error scrapeando detalle {article_url}: {e}")
                    
                    print(f"  ✅ Procesados {count} artículos de {url}")
                    
                    # AI Generation disabled as per request
                    # await db.flush()
                    # ... generation logic removed ...
                
                except Exception as e:
                    print(f"  ❌ Error en {url}: {str(e)}")
            
            # Final commit not strictly needed (per-article commits above), but keep for safety
            try:
                await db.commit()
            except Exception:
                await db.rollback()
            print(f"[{datetime.now()}] Scraping completado")
        
        except Exception as e:
            print(f"[{datetime.now()}] Error en scheduler: {str(e)}")
            await db.rollback()


def start_scheduler():
    """
    Initialize and start the scheduler
    
    Configures:
    - Hourly scraping (10 news per hour)
    """
    
    # Hourly job
    scheduler.add_job(
        scraping_job,
        CronTrigger(minute=0), # Run at the start of every hour
        id="hourly_scrape",
        name="Scraping por hora",
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Scheduler iniciado")
    print("   - Scraping programado: Cada hora (minuto 0)")
