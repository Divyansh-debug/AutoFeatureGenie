import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Import the new routers
from src.api.routes import features, health, upload
from src.config.settings import settings
from src.database.database import Base, engine
from src.middleware.rate_limit import RateLimitMiddleware
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(
        "Starting AutoFeatureGenie API",
        extra={
            "version": settings.API_VERSION,
            "host": settings.HOST,
            "port": settings.PORT,
        },
    )

    # Initialize Database Tables
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    logger.info("Shutting down AutoFeatureGenie API")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)


# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Include Routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(features.router, tags=["Features"])
app.include_router(health.router, tags=["System"])

# Serve the static frontend (CSS, JS)
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")


@app.get("/app", include_in_schema=False)
async def serve_frontend():
    """Serve the professional web frontend."""
    idx = os.path.join(_frontend_dir, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx, media_type="text/html")
    return JSONResponse({"error": "Frontend not found"}, status_code=404)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to the web app or return API info."""
    idx = os.path.join(_frontend_dir, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx, media_type="text/html")
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "app": "/app",
        "docs": "/docs",
        "health": "/health",
    }
