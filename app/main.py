"""
News AI Generator - Main Application Entry Point
"""
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Compat shim for Python 3.9: add packages_distributions if missing
try:  # pragma: no cover
    if not hasattr(importlib.metadata, "packages_distributions"):
        import importlib_metadata  # type: ignore
        importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
except Exception:
    pass

from app.core.database import init_db
from app.core.config import settings
from app.routers import auth, articles, templates, health
from app.routers import football
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup - Initialize database asynchronously
    try:
        await init_db()
        print("✅ Base de datos inicializada")
    except Exception as e:
        print(f"⚠️ Error inicializando DB (continuando): {e}")
    
    # Start scheduler without blocking
    try:
        start_scheduler()
        print("✅ Scheduler iniciado")
    except Exception as e:
        print(f"⚠️ Error iniciando scheduler: {e}")
    
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
    # Restrict to known frontends; add more origins here if needed
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(articles.router, prefix="/admin/articles", tags=["Articles"])
app.include_router(templates.router, prefix="/admin/templates", tags=["Templates"])
app.include_router(health.router, tags=["Health"])
app.include_router(football.router, prefix="/football", tags=["Football"])


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
