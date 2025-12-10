"""
Templates Router - CRUD operations for scraper templates
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.models import ScraperTemplate
from app.services.scrapegraph import test_template
from app.utils.auth import get_current_user


router = APIRouter()


class TemplateCreate(BaseModel):
    """Schema for creating a template"""
    domain: str
    selectors: dict
    rules: Optional[dict] = None
    version: str = "1.0"


class TemplateUpdate(BaseModel):
    """Schema for updating a template"""
    selectors: Optional[dict] = None
    rules: Optional[dict] = None
    version: Optional[str] = None
    active: Optional[str] = None


class TemplateResponse(BaseModel):
    """Schema for template responses"""
    id: str
    domain: str
    selectors: dict
    rules: Optional[dict]
    version: str
    active: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.post("", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new scraper template
    
    Args:
        template: Template data
    
    Returns:
        Created template
    """
    # Check if domain already exists
    existing = await db.execute(
        select(ScraperTemplate).where(ScraperTemplate.domain == template.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Dominio ya existe")
    
    new_template = ScraperTemplate(
        domain=template.domain,
        selectors=template.selectors,
        rules=template.rules,
        version=template.version
    )
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)
    
    return new_template


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List all scraper templates"""
    result = await db.execute(select(ScraperTemplate))
    templates = result.scalars().all()
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get a specific template by ID"""
    result = await db.execute(
        select(ScraperTemplate).where(ScraperTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    update: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update a scraper template
    
    Args:
        template_id: Template UUID
        update: Updated template data
    
    Returns:
        Updated template
    """
    result = await db.execute(
        select(ScraperTemplate).where(ScraperTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    if update.selectors:
        template.selectors = update.selectors
    if update.rules:
        template.rules = update.rules
    if update.version:
        template.version = update.version
    if update.active:
        template.active = update.active
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete a scraper template"""
    result = await db.execute(
        select(ScraperTemplate).where(ScraperTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    await db.delete(template)
    await db.commit()
    
    return {"status": "deleted", "id": template_id}


@router.post("/{template_id}/test")
async def test_scraper_template(
    template_id: str,
    url: str = Query(..., description="URL to test the template against"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Test a template against a specific URL
    
    Args:
        template_id: Template UUID
        url: URL to scrape for testing
    
    Returns:
        Scraped data using the template
    """
    result = await db.execute(
        select(ScraperTemplate).where(ScraperTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    try:
        result = await test_template(template, url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en test: {str(e)}")
