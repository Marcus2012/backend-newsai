from app.core.config import settings
"""
News AI Generator - Main Application Entry Point
"""
import importlib
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Compat shim for Python 3.9: add packages_distributions if missing
try:  # pragma: no cover
    if not hasattr(importlib.metadata, "packages_distributions"):
        import importlib_metadata  # type: ignore
        importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
except Exception:
    pass

from app.core.database import get_db, init_db
from app.core.config import settings
from app.routers import auth, articles, templates, health
from app.routers import football
from app.routers import api as api_router
from app.routers import scheduler as scheduler_router
from app.routers import sportmonks
from typing import Dict, Any
from app.routers import api as api_module
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup - Initialize database asynchronously
    try:
        await init_db()
        print("✅ Base de datos inicializada")
    except Exception as e:
        print(f"⚠️ Error inicializando DB (continuando): {e}")
    
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
# Define allowed origins for different environments
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4200",
    "https://newsai-predictorfutbol.vercel.app", # Production Vercel
    "https://www.asieselfutbol.com",
    "https://asieselfutbol.com",
    "https://asieselfutbol-e5004.web.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|https://(www\.)?asieselfutbol\.com|https://.*\.web\.app",
    allow_credentials=True,
    allow_methods=["*"],                         # Include OPTIONS
    allow_headers=["*"],                         # Include Authorization, Content-Type
)

# Register Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(articles.router, prefix="/admin/articles", tags=["Articles"])
app.include_router(templates.router, prefix="/admin/templates", tags=["Templates"])
app.include_router(health.router, tags=["Health"])
app.include_router(football.router, prefix="/football", tags=["Football"])
app.include_router(api_router.router, prefix="/api", tags=["API"])
app.include_router(sportmonks.router, tags=["Sportmonks"])
app.include_router(scheduler_router.router, prefix="/scheduler", tags=["Scheduler"])


# Compatibilidad: ruta raíz `/predict` usada por algunos frontends
@app.post("/predict")
async def predict_root(fixture: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    return await api_module.predict_from_frontend(fixture, db)



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
