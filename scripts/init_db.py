"""
Database Initialization Script
Run: python -m scripts.init_db
"""
import asyncio
from datetime import datetime

from app.core.database import async_session, init_db
from app.core.models import RawArticle, GeneratedArticle, ScraperTemplate, StatusEnum


async def seed_data():
    """Initialize database with sample data"""
    async with async_session() as db:
        try:
            # Create sample scraper templates
            templates = [
                ScraperTemplate(
                    domain="bbc.com",
                    selectors={
                        "title": "h1, h2[data-testid='internal-headline']",
                        "body": "[data-testid='article-body'] p",
                        "image": "img[data-src]",
                        "context": "[data-testid='article-headline'], [data-testid='article-headline-description']"
                    },
                    rules={
                        "image_attr": "data-src",
                        "remove_ads": True
                    },
                    version="1.0",
                    active="true"
                ),
                ScraperTemplate(
                    domain="elcomercio.pe",
                    selectors={
                        "title": "h1.titular, h1.story-header",
                        "body": ".story-content p, article p",
                        "image": "figure img, .featured-image img",
                        "context": ".titular, .story-header, .story-summary"
                    },
                    rules={
                        "image_attr": "src",
                        "remove_ads": True
                    },
                    version="1.0",
                    active="true"
                ),
                ScraperTemplate(
                    domain="rpp.pe",
                    selectors={
                        "title": "h1.title, h1",
                        "body": ".article-body p, article p",
                        "image": ".article-image img, .featured img",
                        "context": ".article-summary, .lead"
                    },
                    rules={
                        "image_attr": "src",
                        "remove_ads": True
                    },
                    version="1.0",
                    active="true"
                )
            ]
            
            for template in templates:
                db.add(template)
            
            # Create sample raw articles
            raw_articles = [
                RawArticle(
                    source="bbc.com",
                    source_url="https://www.bbc.com/news/example1",
                    scraped_title="Nuevos avances en tecnología IA",
                    scraped_body="Las últimas investigaciones muestran avances significativos...",
                    image_url="https://example.com/image1.jpg",
                    context="Las empresas de tecnología están invirtiendo masivamente en inteligencia artificial...",
                    raw_json={
                        "title": "Nuevos avances en tecnología IA",
                        "url": "https://www.bbc.com/news/example1"
                    },
                    scraped_at=datetime.utcnow()
                ),
                RawArticle(
                    source="elcomercio.pe",
                    source_url="https://www.elcomercio.pe/economia/noticia",
                    scraped_title="Economía peruana muestra recuperación",
                    scraped_body="El PBI creció más de lo esperado en el último trimestre...",
                    image_url="https://example.com/image2.jpg",
                    context="Los indicadores económicos de Perú muestran señales positivas...",
                    raw_json={
                        "title": "Economía peruana muestra recuperación",
                        "url": "https://www.elcomercio.pe/economia/noticia"
                    },
                    scraped_at=datetime.utcnow()
                )
            ]
            
            for raw in raw_articles:
                db.add(raw)
            
            await db.flush()
            
            # Create sample generated articles
            generated_articles = [
                GeneratedArticle(
                    raw_article_id=raw_articles[0].id,
                    title="Inteligencia Artificial: El futuro del desarrollo tecnológico",
                    description="Las empresas tecnológicas impulsan inversión masiva en IA, revolucionando industrias. Expertos advierten sobre la necesidad de regulación responsable.",
                    seo_meta={
                        "meta_title": "IA y tecnología: Tendencias 2024",
                        "meta_description": "Descubre los últimos avances en inteligencia artificial y su impacto en la industria tecnológica.",
                        "keywords": ["inteligencia artificial", "tecnología", "IA 2024", "machine learning", "innovación"]
                    },
                    image_url="https://example.com/image1.jpg",
                    status=StatusEnum.draft
                ),
                GeneratedArticle(
                    raw_article_id=raw_articles[1].id,
                    title="Perú registra crecimiento económico superior a proyecciones",
                    description="El PBI peruano creció más de lo estimado, impulsado por sectores de minería y servicios. Analistas pronostican recuperación sostenida.",
                    seo_meta={
                        "meta_title": "Economía Perú 2024 - Crecimiento PBI",
                        "meta_description": "El crecimiento económico de Perú supera expectativas. Conoce los datos y análisis del PBI peruano.",
                        "keywords": ["economía Perú", "PBI", "crecimiento económico", "minería", "desarrollo"]
                    },
                    image_url="https://example.com/image2.jpg",
                    status=StatusEnum.draft
                )
            ]
            
            for article in generated_articles:
                db.add(article)
            
            await db.commit()
            
            print("✅ Base de datos inicializada con éxito")
            print(f"   - {len(templates)} plantillas de scraping creadas")
            print(f"   - {len(raw_articles)} artículos crudos creados")
            print(f"   - {len(generated_articles)} artículos generados creados (estado: draft)")
        
        except Exception as e:
            await db.rollback()
            print(f"❌ Error inicializando BD: {str(e)}")
            raise


async def main():
    """Main function"""
    print("🚀 Inicializando base de datos...")
    
    # Create tables
    await init_db()
    
    # Insert sample data
    await seed_data()


if __name__ == "__main__":
    asyncio.run(main())
