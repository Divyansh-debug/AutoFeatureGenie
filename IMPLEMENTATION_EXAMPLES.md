# 🛠️ Implementation Examples - Critical Improvements

This document provides concrete code examples for the most important improvements.

---

## 1. Configuration Management (`src/config/settings.py`)

```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "AutoFeatureGenie API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["http://localhost:8501", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: list[str] = ["csv", "parquet"]
    UPLOAD_DIR: str = "data"
    
    # AI/ML Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # RAG Settings
    RAG_INDEX_PATH: str = "vectorstore.pkl"
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 3
    
    # Database Settings (if adding DB)
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings (for caching)
    REDIS_URL: Optional[str] = None
    
    # Security Settings
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
```

---

## 2. Pydantic Models for API (`src/models/schemas.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class EDASummary(BaseModel):
    shape: tuple[int, int]
    columns: List[str]
    column_info: Dict[str, Dict[str, Any]]
    likely_target_column: Optional[str] = None

class FeatureSuggestion(BaseModel):
    column: str = Field(..., description="Name of the feature")
    idea: str = Field(..., description="Description of the feature idea")
    reason: str = Field(..., description="Why this feature is valuable")
    code_snippet: str = Field(..., description="Python code to create the feature")
    expected_impact: Optional[str] = Field(None, description="Expected impact on model performance")
    complexity: Optional[str] = Field(None, description="Implementation complexity (low/medium/high)")

class UploadResponse(BaseModel):
    filename: str
    rows: int
    eda_summary: EDASummary
    uploaded_at: datetime = Field(default_factory=datetime.now)

class FeatureSuggestionsResponse(BaseModel):
    suggestions: List[FeatureSuggestion]
    domain: str
    generated_at: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    database: Optional[str] = None
    cache: Optional[str] = None
```

---

## 3. Improved Error Handling (`src/utils/exceptions.py`)

```python
from fastapi import HTTPException, status
from typing import Optional

class AutoFeatureGenieException(Exception):
    """Base exception for the application"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class FileUploadException(AutoFeatureGenieException):
    """Exception raised during file upload"""
    pass

class FileProcessingException(AutoFeatureGenieException):
    """Exception raised during file processing"""
    pass

class FeatureGenerationException(AutoFeatureGenieException):
    """Exception raised during feature generation"""
    pass

class RAGException(AutoFeatureGenieException):
    """Exception raised during RAG operations"""
    pass

class APIException(AutoFeatureGenieException):
    """Exception raised during external API calls"""
    pass

# HTTP Exception handlers
def raise_file_too_large(max_size: int):
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File size exceeds maximum allowed size of {max_size / (1024*1024):.1f}MB"
    )

def raise_invalid_file_type(allowed_types: list[str]):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
    )

def raise_file_not_found(filename: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"File '{filename}' not found"
    )
```

---

## 4. Structured Logging (`src/utils/logger.py`)

```python
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from src.config.settings import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def setup_logger(name: str = "autofeaturegenie") -> logging.Logger:
    """Setup and configure logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on config
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Create default logger
logger = setup_logger()
```

---

## 5. Improved Main API (`backend/main_improved.py`)

```python
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import pandas as pd
import os
from typing import Optional
import time

from src.config.settings import settings
from src.models.schemas import (
    UploadResponse, FeatureSuggestionsResponse, 
    ErrorResponse, HealthResponse
)
from src.utils.exceptions import (
    raise_file_too_large, raise_invalid_file_type, 
    raise_file_not_found
)
from src.utils.logger import logger
from backend.feature_engine import generate_eda_summary, suggest_features

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AutoFeatureGenie API")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown
    logger.info("Shutting down AutoFeatureGenie API")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code}",
        extra={"process_time": process_time}
    )
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc) if settings.DEBUG else None
        ).dict()
    )

@app.post(f"{settings.API_PREFIX}/upload/", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload and analyze a CSV file"""
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise_file_too_large(settings.MAX_FILE_SIZE)
        
        # Validate file type
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            raise_invalid_file_type(settings.ALLOWED_FILE_TYPES)
        
        # Process file
        import io
        df = pd.read_csv(io.BytesIO(file_content))
        
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        df.to_csv(file_path, index=False)
        
        eda_summary = generate_eda_summary(df)
        
        logger.info(f"File uploaded successfully: {file.filename}")
        
        return UploadResponse(
            filename=file.filename,
            rows=len(df),
            eda_summary=eda_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_PREFIX}/feature-suggestions/", response_model=FeatureSuggestionsResponse)
async def feature_suggestions(
    filename: str = Query(..., description="Name of the uploaded file"),
    domain: str = Query("telecom", description="Domain context for feature suggestions")
):
    """Get AI-powered feature suggestions"""
    start_time = time.time()
    
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise_file_not_found(filename)
        
        suggestions = suggest_features(file_path, domain=domain)
        processing_time = time.time() - start_time
        
        logger.info(f"Feature suggestions generated for {filename}")
        
        return FeatureSuggestionsResponse(
            suggestions=suggestions,
            domain=domain,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        uptime=0.0  # Calculate actual uptime
    )
```

---

## 6. Unit Test Example (`tests/unit/test_feature_engine.py`)

```python
import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch, MagicMock
from backend.feature_engine import generate_eda_summary, suggest_features

class TestGenerateEDASummary:
    """Test cases for EDA summary generation"""
    
    def test_basic_eda_summary(self):
        """Test basic EDA summary generation"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e'],
            'target': [0, 1, 0, 1, 0]
        })
        
        summary = generate_eda_summary(df)
        
        assert summary['shape'] == (5, 3)
        assert len(summary['columns']) == 3
        assert 'col1' in summary['column_info']
        assert summary['likely_target_column'] == 'target'
    
    def test_numeric_column_stats(self):
        """Test numeric column statistics"""
        df = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5]
        })
        
        summary = generate_eda_summary(df)
        col_info = summary['column_info']['numeric_col']
        
        assert 'mean' in col_info
        assert 'std' in col_info
        assert 'min' in col_info
        assert 'max' in col_info
        assert col_info['mean'] == 3.0
    
    def test_missing_values(self):
        """Test handling of missing values"""
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5]
        })
        
        summary = generate_eda_summary(df)
        assert summary['column_info']['col1']['missing_values'] == 1

class TestSuggestFeatures:
    """Test cases for feature suggestion"""
    
    @patch('backend.feature_engine.model')
    @patch('backend.feature_engine.rag')
    def test_successful_feature_suggestion(self, mock_rag, mock_model):
        """Test successful feature suggestion"""
        # Setup mocks
        mock_rag.search.return_value = ["domain context"]
        mock_response = MagicMock()
        mock_response.text = '[{"column": "test_feature", "idea": "test", "reason": "test", "code_snippet": "df[\'test\'] = 1"}]'
        mock_model.generate_content.return_value = mock_response
        
        # Create test file
        test_file = "test_data.csv"
        df = pd.DataFrame({'col1': [1, 2, 3]})
        df.to_csv(test_file, index=False)
        
        try:
            suggestions = suggest_features(test_file, domain="test")
            assert len(suggestions) > 0
            assert suggestions[0]['column'] == 'test_feature'
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    @patch('backend.feature_engine.model')
    def test_api_error_handling(self, mock_model):
        """Test error handling when API fails"""
        mock_model.generate_content.side_effect = Exception("API Error")
        
        test_file = "test_data.csv"
        df = pd.DataFrame({'col1': [1, 2, 3]})
        df.to_csv(test_file, index=False)
        
        try:
            suggestions = suggest_features(test_file)
            assert len(suggestions) == 1
            assert 'error' in suggestions[0]
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
```

---

## 7. Docker Configuration (`docker/Dockerfile.backend`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ../data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

---

## 9. GitHub Actions CI (`github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov black flake8 mypy
    
    - name: Lint with flake8
      run: |
        flake8 backend/ frontend/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 backend/ frontend/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Check formatting with black
      run: black --check backend/ frontend/
    
    - name: Type check with mypy
      run: mypy backend/ --ignore-missing-imports
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=backend --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 10. Rate Limiting Middleware (`src/middleware/rate_limit.py`)

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
from src.config.settings import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.clients = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        
        # Clean old entries
        current_time = time.time()
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if current_time - timestamp < 60
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record this request
        self.clients[client_ip].append(current_time)
        
        response = await call_next(request)
        return response
```

---

These examples provide a solid foundation for making your project industry-ready. Start implementing them in order of priority!

