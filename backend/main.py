from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

from backend.feature_engine import generate_eda_summary, suggest_features

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    df.to_csv(file_path, index=False)
    eda_summary = generate_eda_summary(df)

    return {
        "filename": file.filename,
        "rows": len(df),
        "eda_summary": eda_summary
    }

@app.get("/feature-suggestions/")
def feature_suggestions(filename: str = Query(...)):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    df = pd.read_csv(file_path)
    suggestions = suggest_features(file_path)
    return {"suggestions": suggestions}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
