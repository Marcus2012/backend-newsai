
import os
import re
import httpx
import asyncio
import time
from urllib.parse import urlparse
import httpx as _httpx_exceptions  # alias to reference exceptions in typing
"""
Articles Router - CRUD operations for generated articles
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.models import GeneratedArticle, RawArticle, StatusEnum
from app.services.wordpress import publish_to_wordpress
from app.utils.auth import get_current_user

router = APIRouter()

# logger removido para evitar exposición de credenciales en logs
# Endpoint para sincronizar artículos a Strapi
@router.post("/sync-strapi", summary="Sincroniza artículos a Strapi")
async def sync_strapi_articles(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Sincroniza los artículos generados a Strapi CMS usando la API REST de Strapi.
    """
    # 1. Obtener los artículos desde la base de datos
    result = await db.execute(select(GeneratedArticle))
    articles = result.scalars().all()

    # 2. Configuración de Strapi (obligatorio en entorno de producción)
    # STRAPI_URL debe apuntar al endpoint público de Strapi (ej: https://mi-strapi.example.com/api/articles)
    # STRAPI_TOKEN debe guardarse en secreto (Secret Manager / env var) y no versionarse.
    strapi_url = os.getenv("STRAPI_URL")
    strapi_token = os.getenv("STRAPI_TOKEN")
    # Sanitizar token de posibles saltos de línea o espacios
    if strapi_token:
        strapi_token = strapi_token.strip()

    # Forzar que estén presentes en el entorno; evita usar defaults inseguros en producción
    if not strapi_url or not strapi_token:
        raise HTTPException(status_code=500, detail="STRAPI_URL o STRAPI_TOKEN no configurados en el entorno")

    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json",
    }

    # No registrar headers ni token en producción

    results = []
    # Configurar timeouts y reintentos
    timeout = httpx.Timeout(10.0, connect=5.0)
    max_retries = 3

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Procesar y enviar artículos a Strapi
        async def upload_image_from_url(img_url: str) -> Optional[int]:
            """Download image from a remote URL and upload to Strapi via /api/upload.

            Returns media id on success or None on failure.
            """
            if not img_url:
                return None
            try:
                # fetch image bytes
                r = await client.get(img_url, timeout=10.0)
                r.raise_for_status()
                content = r.content
                content_type = r.headers.get("content-type", "application/octet-stream")
                # derive filename from URL path
                parsed = urlparse(img_url)
                filename = os.path.basename(parsed.path) or f"image_{int(time.time())}.jpg"

                upload_url = strapi_url.rsplit("/api", 1)[0] + "/api/upload"
                # For multipart upload remove JSON content-type so httpx sets it correctly
                upload_headers = dict(headers)
                upload_headers.pop("Content-Type", None)

                files = [("files", (filename, content, content_type))]
                resp = await client.post(upload_url, files=files, headers=upload_headers)
                if resp.status_code in (200, 201):
                    j = resp.json()
                    # Strapi returns a list of uploaded files
                    if isinstance(j, list) and len(j) > 0:
                        return j[0].get("id")
                    # older/alternate formats
                    if isinstance(j, dict) and j.get("data"):
                        data_obj = j.get("data")
                        if isinstance(data_obj, list) and len(data_obj) > 0:
                            return data_obj[0].get("id")
                # Image upload failed: continuar sin media
            except Exception as e:
                # Ignorar errores de subida de imagen
                pass
            return None
        for idx, article in enumerate(articles, start=1):
            # generar slug seguro a partir del title
            def slugify(text: str) -> Optional[str]:
                if not text:
                    return None
                s = text.lower()
                s = re.sub(r"[^\w\s-]", "", s)
                s = re.sub(r"[\s_-]+", "-", s).strip("-")
                return s[:200]

            slug_val = slugify(article.title) or (getattr(article, "id", None) or datetime.utcnow().strftime("%Y%m%d%H%M%S"))

            # Construir payload con campos permitidos por Strapi
            # Enviar solamente: title, slug, content, excerpt (evitar campos rechazados como documentId/createdAt/seo_meta/image_url)
            data = {
                "title": article.title or "",
                "slug": slug_val,
                "content": article.description or "",
            }

            # excerpt: usar meta_description si existe
            try:
                seo = getattr(article, "seo_meta", None)
                if seo and isinstance(seo, dict):
                    excerpt = seo.get("meta_description") or seo.get("meta_description") or seo.get("metaTitle") or None
                    if excerpt:
                        data["excerpt"] = excerpt
            except Exception:
                pass

            payload = {"data": data}

            # Preparado para enviar artículo

            # Si existe image_url, intentar subirla a Strapi y enlazarla como media
            try:
                image_url = getattr(article, "image_url", None)
                if image_url:
                    # Intento de subir imagen desde URL
                    media_id = await upload_image_from_url(image_url)
                    if media_id:
                        # Asignar el id del media al campo 'image' (campo Media en Strapi)
                        data["image"] = media_id
                        payload = {"data": data}
                        # Imagen subida con éxito
                    else:
                        # No se pudo subir la imagen; continuar sin imagen
                        pass
            except Exception:
                # Ignorar errores al manejar image_url
                pass

            # Intentar reintentos en caso de timeout/connection errors
            resp = None
            for attempt in range(1, max_retries + 1):
                try:
                    resp = await client.post(strapi_url, json=payload, headers=headers)
                    break
                except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RequestError) as e:
                    if attempt < max_retries:
                        backoff = 2 ** (attempt - 1)
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        results.append({"title": article.title, "status": "error", "detail": str(e)})
                        resp = None
                        break

            if resp is None:
                continue

            body_snippet = resp.text
            if len(body_snippet) > 1000:
                body_snippet = body_snippet[:1000] + "..."
            # Response body (recortado si es largo)

            if resp.status_code in (200, 201):
                results.append({"title": article.title, "status": "ok"})
                continue

            # para 400, parsear y devolver detalle útil
            if resp.status_code == 400:
                try:
                    j = resp.json()
                except Exception:
                    j = None
                results.append({"title": article.title, "status": "error", "detail": j or body_snippet})
                continue

            # otros códigos
            results.append({"title": article.title, "status": "error", "detail": resp.text})

    return {"synced": results}


class ArticleUpdate(BaseModel):
    """Schema for article updates"""
    title: str
    description: str
    seo_meta: Optional[dict] = None


class ArticleResponse(BaseModel):
    """Schema for article responses"""
    id: str
    title: str
    description: str
    status: str
    image_url: Optional[str]
    seo_meta: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/run")
async def run_scraping(
    db: AsyncSession = Depends(get_db),
    # current_user: str = Depends(get_current_user)
):
    """Trigger manual scraping job"""
    from app.scheduler import scraping_job
    import asyncio
    
    # Run scraping in background
    asyncio.create_task(scraping_job())
    
    return {
        "status": "started",
        "message": "Scraping iniciado en segundo plano"
    }


@router.get("", response_model=List[ArticleResponse])
async def get_articles(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Records limit")
):
    """
    List generated articles with filters and pagination
    
    Args:
        status_filter: Filter by article status (draft, pending_review, published)
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of articles
    """
    query = select(GeneratedArticle).options(
        selectinload(GeneratedArticle.raw_article)
    ).order_by(desc(GeneratedArticle.created_at))
    
    if status_filter:
        try:
            status_enum = StatusEnum[status_filter]
            query = query.where(GeneratedArticle.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Estado inválido")
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return articles


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get a specific article by ID"""
    result = await db.execute(
        select(GeneratedArticle).where(GeneratedArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    
    return article


@router.put("/{article_id}")
async def update_article(
    article_id: str,
    update: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an article (draft only)
    
    Args:
        article_id: Article UUID
        update: Updated article data
    
    Returns:
        Updated article
    """
    result = await db.execute(
        select(GeneratedArticle).where(GeneratedArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    
    if article.status == StatusEnum.published:
        raise HTTPException(status_code=400, detail="No se puede editar un artículo publicado")
    
    article.title = update.title
    article.description = update.description
    if update.seo_meta:
        article.seo_meta = update.seo_meta
    
    db.add(article)
    await db.commit()
    await db.refresh(article)
    
    return article


@router.post("/{article_id}/publish")
async def publish_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Publish an article to WordPress
    
    Args:
        article_id: Article UUID
    
    Returns:
        WordPress post ID and status
    """
    result = await db.execute(
        select(GeneratedArticle).where(GeneratedArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    
    try:
        wp_post_id = await publish_to_wordpress(article)
        article.wp_post_id = wp_post_id
        article.status = StatusEnum.published
        db.add(article)
        await db.commit()
        
        return {
            "status": "success",
            "wp_post_id": wp_post_id,
            "message": "Artículo publicado en WordPress"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al publicar: {str(e)}")
