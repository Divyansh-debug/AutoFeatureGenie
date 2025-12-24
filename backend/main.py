"""Main FastAPI application with improved error handling, validation, and logging"""
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import pandas as pd
import os
import io
import time
from typing import Optional

from src.config.settings import settings
from src.models.schemas import UploadResponse, ErrorResponse, HealthResponse
from src.utils.exceptions import (
    raise_file_too_large,
    raise_invalid_file_type,
    raise_file_not_found
)
from src.utils.logger import logger
from src.middleware.rate_limit import RateLimitMiddleware
from backend.feature_engine import generate_eda_summary, suggest_features

# Track application start time for uptime calculation
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AutoFeatureGenie API", extra={
        "version": settings.API_VERSION,
        "host": settings.HOST,
        "port": settings.PORT
    })
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory ready: {settings.UPLOAD_DIR}")
    yield
    # Shutdown
    logger.info("Shutting down AutoFeatureGenie API")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests with timing information"""
    start_time = time.time()
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {str(e)}",
            extra={"process_time": process_time},
            exc_info=True
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc) if settings.DEBUG else None,
            error_code="INTERNAL_ERROR"
        ).dict()
    )


@app.post("/upload/", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload and analyze a CSV file
    
    - Validates file size, type, and structure
    - Generates EDA summary
    - Returns file metadata and analysis
    """
    try:
        logger.info(f"File upload request: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise_file_too_large(settings.MAX_FILE_SIZE)
        
        # Validate file type
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            logger.warning(f"Invalid file type: {file_ext}")
            raise_invalid_file_type(settings.ALLOWED_FILE_TYPES)
        
        # Validate CSV structure
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            if df.empty:
                logger.warning("Uploaded file is empty")
                raise HTTPException(status_code=400, detail="File is empty")
        except pd.errors.EmptyDataError:
            logger.warning("Uploaded file has no data")
            raise HTTPException(status_code=400, detail="File has no data")
        except Exception as e:
            logger.error(f"CSV parsing error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        df.to_csv(file_path, index=False)
        
        logger.info(f"File saved: {file_path}, rows: {len(df)}")
        
        # Generate EDA summary
        eda_summary = generate_eda_summary(df)
        
        logger.info(f"EDA summary generated for {file.filename}")
        
        return UploadResponse(
            filename=file.filename,
            rows=len(df),
            eda_summary=eda_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/feature-suggestions/")
async def feature_suggestions(
    filename: str = Query(..., description="Name of the uploaded file"),
    domain: str = Query("telecom", description="Domain context for feature suggestions")
):
    """
    Get AI-powered feature engineering suggestions
    
    - Uses RAG for domain-specific knowledge
    - Generates feature suggestions using Gemini AI
    - Returns structured feature recommendations
    """
    start_time = time.time()
    
    try:
        logger.info(f"Feature suggestion request: {filename}, domain: {domain}")
        
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            raise_file_not_found(filename)
        
        # Generate feature suggestions (raw list of dicts from Gemini/RAG pipeline)
        suggestions = suggest_features(file_path, domain=domain)
        processing_time = time.time() - start_time

        # Basic logging
        if suggestions and isinstance(suggestions, list):
            first = suggestions[0]
            if isinstance(first, dict) and first.get("error"):
                logger.warning(
                    f"Feature generation returned error: {first.get('error')}",
                    extra={"processing_time": processing_time},
                )
            else:
                logger.info(
                    f"Feature suggestions generated: {len(suggestions)} suggestions",
                    extra={"processing_time": processing_time},
                )
        else:
            logger.warning("No suggestions generated or invalid suggestions format")

        # Return raw suggestions so the frontend can display everything without Pydantic interfering
        return {
            "suggestions": suggestions,
            "domain": domain,
            "processing_time": processing_time,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Feature generation failed: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service status and basic information
    """
    uptime = time.time() - app_start_time
    
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        uptime=uptime
    )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }
