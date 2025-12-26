"""
Scheduler - Automated scraping jobs using APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
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
                                scraped_at=datetime.utcnow()
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
                                    image_url=img_url,
                                    status=StatusEnum.draft
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
                                    image_url=img_url,
                                    status=StatusEnum.draft
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
