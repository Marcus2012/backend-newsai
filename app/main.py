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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deployments
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
