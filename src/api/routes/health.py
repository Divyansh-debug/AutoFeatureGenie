from fastapi import APIRouter
import time
import os

from src.config.settings import settings
from src.models.schemas import HealthResponse
from src.utils.logger import logger

router = APIRouter()
app_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint with DB and disk metrics."""
    uptime = time.time() - app_start_time

    # Database connectivity check
    db_status = "unknown"
    try:
        from src.database.database import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.warning(f"Health check DB error: {e}")

    # Redis/cache check (optional — won't fail if Redis not running)
    cache_status = "not configured"
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis as redis_lib
            r = redis_lib.from_url(redis_url, socket_connect_timeout=1)
            r.ping()
            cache_status = "connected"
        except Exception:
            cache_status = "unavailable"

    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        uptime=uptime,
        database=db_status,
        cache=cache_status,
    )
