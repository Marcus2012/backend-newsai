from app.core.config import settings
"""
News AI Generator - Main Application Entry Point
"""
import importlib
from fastapi import FastAPI, Query
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
from app.routers import api as api_router
from typing import Dict, Any, Optional
from app.routers import api as api_module
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
# Define allowed origins for different environments
cors_origins = [
    "http://localhost:3000",
    "http://localhost:4200",
    "https://newsai-predictorfutbol.vercel.app", # Production Vercel
    "https://www.asieselfutbol.com",
    "https://asieselfutbol.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|https://(www\.)?asieselfutbol\.com",
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


# Compatibilidad: ruta raíz `/predict` usada por algunos frontends
@app.post("/predict")
async def predict_root(fixture: Dict[str, Any]):
    return await api_module.predict_from_frontend(fixture)



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
        "docs": "/docs",
        "health": "/health"
    }


# --- Legacy frontend routes (compatibility) ---------------------------------
@app.get("/peru/summary", summary="Legacy: Resumen Liga Perú")
async def peru_summary_legacy():
    return await football.peru_summary()


@app.get("/peru/table", summary="Legacy: Tabla Liga Perú")
async def peru_table_legacy(phase: str = Query("Apertura", description="Fase: Apertura o Clausura")):
    return await football.peru_table(phase=phase)


# --- Legacy public wrappers for frontend compatibility (no /football prefix) ---
@app.get("/public/premier/info", summary="Legacy wrapper: Premier League info")
async def public_premier_info():
    return await football.premier_info()


@app.get("/public/premier/standings", summary="Legacy wrapper: Premier League standings")
async def public_premier_standings(season: Optional[int] = None):
    return await football.premier_standings(season=season)


@app.get("/public/premier/fixtures", summary="Legacy wrapper: Premier League fixtures")
async def public_premier_fixtures(next: int = Query(10, ge=1, le=100)):
    return await football.premier_fixtures(next=next)


@app.get("/public/seriea/info", summary="Legacy wrapper: Serie A info")
async def public_seriea_info():
    return await football.seriea_info()


@app.get("/public/seriea/standings", summary="Legacy wrapper: Serie A standings")
async def public_seriea_standings(season: Optional[int] = None):
    return await football.seriea_standings(season=season)


@app.get("/public/seriea/fixtures", summary="Legacy wrapper: Serie A fixtures")
async def public_seriea_fixtures(next: int = Query(10, ge=1, le=100)):
    return await football.seriea_fixtures(next=next)


@app.get("/public/premier/top-scorers", summary="Legacy wrapper: Premier League top scorers")
async def public_premier_top_scorers(season: Optional[int] = None):
    return await football.premier_top_scorers(season=season)


@app.get("/public/seriea/top-scorers", summary="Legacy wrapper: Serie A top scorers")
async def public_seriea_top_scorers(season: Optional[int] = None):
    return await football.seriea_top_scorers(season=season)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
