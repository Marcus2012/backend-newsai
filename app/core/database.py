"""
Database Configuration and Session Management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import ssl


from app.core.config import settings
from app.core.models import Base

# Mostrar el valor real de DATABASE_URL al arrancar
print(f"[INFO] DATABASE_URL en runtime: {settings.DATABASE_URL}")


# Configurar connect_args según el tipo de base de datos
connect_args = {}
if "mysql" in settings.DATABASE_URL:
    # Si se usa socket Unix, localhost, o la proxy de Railway (rlwy.net), no requerir SSL personalizado de Cloud SQL
    if any(k in settings.DATABASE_URL for k in ["unix_socket=", "127.0.0.1", "localhost", "rlwy.net"]):
        connect_args = {"charset": "utf8mb4"}
    else:
        # Configurar SSL para conexiones TCP directas a Cloud SQL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args = {
            "charset": "utf8mb4",
            "ssl": ssl_context
        }

elif "postgresql" in settings.DATABASE_URL:
    connect_args = {"server_settings": {"application_name": "news_ai_app"}}

# Crear el motor de base de datos
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,
    connect_args=connect_args
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Base de datos inicializada")


async def get_db():
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Close database connection"""
    await engine.dispose()
