"""Integration tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
import pandas as pd
import io

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_upload_csv_success():
    """Test successful CSV upload"""
    # Create a test CSV
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    csv_content = df.to_csv(index=False)
    
    response = client.post(
        "/upload/",
        files={"file": ("test.csv", io.StringIO(csv_content), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.csv"
    assert data["rows"] == 3
    assert "eda_summary" in data


def test_upload_empty_file():
    """Test upload of empty file"""
    response = client.post(
        "/upload/",
        files={"file": ("empty.csv", io.StringIO(""), "text/csv")}
    )
    
    assert response.status_code == 400


def test_feature_suggestions_file_not_found():
    """Test feature suggestions with non-existent file"""
    response = client.get(
        "/feature-suggestions/",
        params={"filename": "nonexistent.csv"}
    )
    
    assert response.status_code == 404

