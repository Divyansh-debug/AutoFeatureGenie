"""Pydantic models for API request/response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


class EDASummary(BaseModel):
    """EDA Summary model"""
    shape: Tuple[int, int] = Field(..., description="Dataset shape (rows, columns)")
    columns: List[str] = Field(..., description="List of column names")
    column_info: Dict[str, Dict[str, Any]] = Field(..., description="Column-wise statistics")
    likely_target_column: Optional[str] = Field(None, description="Detected target column")


class FeatureSuggestion(BaseModel):
    """Feature suggestion model - supports both success and error responses"""
    # Success fields (optional to support error cases)
    column: Optional[str] = Field(None, description="Name of the feature")
    idea: Optional[str] = Field(None, description="Description of the feature idea")
    reason: Optional[str] = Field(None, description="Why this feature is valuable")
    code_snippet: Optional[str] = Field(None, description="Python code to create the feature")
    expected_impact: Optional[str] = Field(None, description="Expected impact on model performance")
    complexity: Optional[str] = Field(None, description="Implementation complexity (low/medium/high)")
    # Error fields
    error: Optional[str] = Field(None, description="Error message if suggestion generation failed")
    details: Optional[str] = Field(None, description="Error details")
    raw_output: Optional[str] = Field(None, description="Raw output from AI if parsing failed")
    raw: Optional[str] = Field(None, description="Raw response if JSON parsing failed")
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class UploadResponse(BaseModel):
    """Response model for file upload"""
    filename: str = Field(..., description="Name of the uploaded file")
    rows: int = Field(..., description="Number of rows in the dataset")
    eda_summary: EDASummary = Field(..., description="EDA summary of the dataset")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Upload timestamp")


class FeatureSuggestionsResponse(BaseModel):
    """Response model for feature suggestions"""
    suggestions: List[FeatureSuggestion] = Field(..., description="List of feature suggestions")
    domain: str = Field(..., description="Domain context used")
    generated_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    database: Optional[str] = Field(None, description="Database connection status")
    cache: Optional[str] = Field(None, description="Cache connection status")

