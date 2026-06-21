from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import os
import io

from src.config.settings import settings
from src.models.schemas import UploadResponse
from src.utils.logger import logger
from src.utils.exceptions import raise_file_too_large, raise_invalid_file_type
from src.database.database import get_db
from src.database.models import Dataset
from backend.feature_engine import generate_eda_summary

router = APIRouter()

@router.post("/upload/", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and analyze a CSV file, then log to the database."""
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise_file_too_large(settings.MAX_FILE_SIZE)
            
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            raise_invalid_file_type(settings.ALLOWED_FILE_TYPES)
            
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            if df.empty:
                raise HTTPException(status_code=400, detail="File is empty")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
            
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        df.to_csv(file_path, index=False)
        
        # Save metadata to database
        db_dataset = Dataset(
            filename=file.filename,
            row_count=df.shape[0],
            column_count=df.shape[1]
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        
        eda_summary = generate_eda_summary(df)
        
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
