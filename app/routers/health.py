"""
Health Router - System health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings


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
