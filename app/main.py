"""
News AI Generator - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import init_db
from app.core.config import settings
from app.routers import auth, articles, templates, health
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    await init_db()
    start_scheduler()
    print("✅ Sistema iniciado")
    yield
    # Shutdown
    print("🛑 Sistema apagado")


app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de scraping y generación de noticias con IA",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(articles.router, prefix="/admin/articles", tags=["Articles"])
app.include_router(templates.router, prefix="/admin/templates", tags=["Templates"])
app.include_router(health.router, tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
