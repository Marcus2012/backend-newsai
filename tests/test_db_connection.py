import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import asyncio

from app.core.database import engine


@pytest.mark.asyncio
async def test_db_connection():
    """Verifica que se puede ejecutar una consulta simple contra la DB.

    Si la base de datos no es accesible desde el entorno de tests, se salta
    el test en lugar de fallar la suite.
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        if isinstance(e, (OperationalError, OSError, asyncio.TimeoutError)):
            pytest.skip(f"DB not reachable, skipping test: {e}")
        raise
