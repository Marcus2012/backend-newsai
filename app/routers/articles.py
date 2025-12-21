
import os
import httpx
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

    # 2. Configuración de Strapi
    strapi_url = os.getenv("STRAPI_URL", "http://72.62.83.18:1338/api/articles")
    strapi_token = os.getenv("STRAPI_TOKEN", "fe81e548eae6af5a3a7157d9bb7ef83dc756396951a865c7c3a8e820ca0afd0766d8c0665db87520cbccf8486415ed0feca20a345372825990a8b4265ceaaf1b6a6810fc24972842e850d7eab0f5938e33bd73bef7d2266d68fd9256eefa4203283b00b83a6e5924695f48492fdfd1e17fce6ef1ddb7aa4152a34fd9616c2bd6")

    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json",
    }

    results = []
    async with httpx.AsyncClient() as client:
        for article in articles:
            payload = {
                "data": {
                    "title": article.title,
                    "description": article.description,
                    "seo_meta": article.seo_meta,
                    "image_url": article.image_url,
                    "created_at": article.created_at.isoformat() if article.created_at else None,
                }
            }
            resp = await client.post(strapi_url, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                results.append({"title": article.title, "status": "ok"})
            else:
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
