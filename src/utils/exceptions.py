"""Custom exception classes and HTTP exception helpers"""
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


# HTTP Exception helpers
def raise_file_too_large(max_size: int):
    """Raise HTTP exception for file too large"""
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File size exceeds maximum allowed size of {max_size / (1024*1024):.1f}MB"
    )


def raise_invalid_file_type(allowed_types: list[str]):
    """Raise HTTP exception for invalid file type"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
    )


def raise_file_not_found(filename: str):
    """Raise HTTP exception for file not found"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"File '{filename}' not found"
    )

