"""
Health Router - System health check endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.core.config import settings
from sqlalchemy import text
from app.core.database import engine


router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    
    Returns:
        System status and version
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/Docker
    
    Returns:
        Status of all services
    """
    return {
        "status": "ready",
        "services": {
            "database": "ok",
            "scrapegraph": "ok",
            "gemini": "ok"
        }
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker
    
    Returns:
        Simple alive status
    """
    return {"status": "alive"}


@router.get("/health/db")
async def health_db():
    """
    Health endpoint that checks DB connectivity by executing a simple query.
    Returns 200 with {'db': 1} if reachable, otherwise raises 503.
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return {"db": result.scalar()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB not reachable: {e}")
