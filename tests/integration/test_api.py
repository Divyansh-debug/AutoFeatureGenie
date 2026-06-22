"""Integration tests for AutoFeatureGenie API endpoints"""

import io
import os
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from src.database.database import Base, engine


@pytest.fixture(autouse=True, scope="module")
def create_test_tables():
    """Create DB tables before the test module runs and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    """Shared TestClient that runs the app lifespan once per module."""
    with TestClient(app) as c:
        yield c


def _make_csv_bytes(df: pd.DataFrame) -> bytes:
    """Helper: dataframe → CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Health & Root
# ─────────────────────────────────────────────────────────────────────────────


def test_health_check(client):
    """Health endpoint returns 200 with expected fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime" in data


def test_root_endpoint(client):
    """Root endpoint returns API info or frontend HTML."""
    response = client.get("/")
    assert response.status_code == 200
    
    if "text/html" in response.headers.get("content-type", ""):
        assert b"<html" in response.content.lower()
    else:
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


# ─────────────────────────────────────────────────────────────────────────────
# Upload
# ─────────────────────────────────────────────────────────────────────────────


def test_upload_csv_success(client):
    """Valid CSV upload returns 200 with EDA summary."""
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"], "target": [0, 1, 0]})
    csv_bytes = _make_csv_bytes(df)

    response = client.post(
        "/upload/",
        files={"file": ("test_upload.csv", io.BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_upload.csv"
    assert data["rows"] == 3
    assert "eda_summary" in data
    assert data["eda_summary"]["likely_target_column"] == "target"


def test_upload_empty_file(client):
    """Empty CSV returns 400."""
    response = client.post(
        "/upload/",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == 400


def test_upload_non_csv(client):
    """Non-CSV extension returns 400."""
    response = client.post(
        "/upload/",
        files={"file": ("data.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Feature Suggestions
# ─────────────────────────────────────────────────────────────────────────────


def test_feature_suggestions_file_not_found(client):
    """Non-existent file returns 404."""
    response = client.get(
        "/feature-suggestions/",
        params={"filename": "definitely_does_not_exist_xyz.csv"},
    )
    assert response.status_code == 404


@patch("src.api.routes.features.suggest_features")
def test_feature_suggestions_success(mock_suggest, client):
    """Successful feature suggestion response is correctly shaped."""
    mock_suggest.return_value = [
        {
            "column": "new_feature",
            "idea": "Sum of col1 and col2",
            "reason": "Captures interaction",
            "code_snippet": "df['new_feature'] = df['col1'] + df['col2']",
            "expected_impact": "+3% F1",
            "complexity": "low",
        }
    ]

    # Write a test CSV so the endpoint finds it on disk
    fname = "test_feat_sugg.csv"
    fpath = os.path.join("data", fname)
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    df.to_csv(fpath, index=False)

    try:
        response = client.get(
            "/feature-suggestions/",
            params={"filename": fname, "domain": "telecom"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["column"] == "new_feature"
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)


# ─────────────────────────────────────────────────────────────────────────────
# History
# ─────────────────────────────────────────────────────────────────────────────


def test_history_endpoint(client):
    """History endpoint returns 200 with expected structure."""
    response = client.get("/history/", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "count" in data
    assert isinstance(data["history"], list)


# ─────────────────────────────────────────────────────────────────────────────
# Validate-Feature
# ─────────────────────────────────────────────────────────────────────────────


@patch("src.services.evaluation_service.evaluate_feature")
def test_validate_feature_success(mock_eval, client):
    """Validate-feature endpoint returns evaluation result."""
    mock_eval.return_value = {
        "status": "success",
        "baseline_score": 0.72,
        "augmented_score": 0.75,
        "improvement": 0.03,
        "task": "classification",
        "metric": "f1_macro",
    }

    fname = "test_validate.csv"
    fpath = os.path.join("data", fname)
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame({"a": [1, 2, 3], "target": [0, 1, 0]})
    df.to_csv(fpath, index=False)

    try:
        response = client.post(
            "/validate-feature/",
            params={"filename": fname, "target_col": "target"},
            content="df['new'] = df['a'] * 2",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["improvement"] == pytest.approx(0.03)
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)
