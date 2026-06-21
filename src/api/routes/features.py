from fastapi import APIRouter, Query, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import os
import time
from typing import Optional

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import raise_file_not_found
from src.database.database import get_db
from src.database.models import Dataset, FeatureSuggestion
from backend.feature_engine import suggest_features

router = APIRouter()


@router.get("/feature-suggestions/")
async def feature_suggestions(
    filename: str = Query(..., description="Name of the uploaded file"),
    domain: str = Query(
        "telecom", description="Domain context for feature suggestions"
    ),
    db: Session = Depends(get_db),
):
    """
    Get AI-powered feature engineering suggestions.
    Results are persisted to the DB for the history tab.
    """
    start_time = time.time()

    try:
        logger.info(f"Feature suggestion request: {filename}, domain: {domain}")
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise_file_not_found(filename)

        # Get dataset record from DB
        dataset = (
            db.query(Dataset)
            .filter(Dataset.filename == filename)
            .order_by(Dataset.created_at.desc())
            .first()
        )

        suggestions = suggest_features(file_path, domain=domain)
        processing_time = time.time() - start_time

        # Persist valid suggestions to DB
        if (
            dataset
            and isinstance(suggestions, list)
            and len(suggestions) > 0
            and "error" not in suggestions[0]
        ):
            for sg in suggestions:
                db_sg = FeatureSuggestion(
                    dataset_id=dataset.id,
                    column_name=sg.get("column", "unknown"),
                    idea=sg.get("idea", ""),
                    reason=sg.get("reason", ""),
                    code_snippet=sg.get("code_snippet", ""),
                )
                db.add(db_sg)
            db.commit()

        return {
            "suggestions": suggestions,
            "domain": domain,
            "processing_time": processing_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Feature generation failed: {str(e)}"
        )


@router.post("/validate-feature/")
async def validate_feature(
    filename: str = Query(..., description="Name of the uploaded CSV file"),
    target_col: str = Query(..., description="Target column in the dataset"),
    code_snippet: str = Body(
        ..., media_type="text/plain", description="Python code snippet to evaluate"
    ),
    suggestion_id: Optional[int] = Query(
        None, description="DB id of FeatureSuggestion to update"
    ),
    db: Session = Depends(get_db),
):
    """
    Auto-Validator endpoint.
    Runs a baseline model on the dataset, applies the feature code_snippet, and
    returns the metric improvement.  Optionally persists improvement_score to DB.
    """
    from src.services.evaluation_service import evaluate_feature

    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise_file_not_found(filename)

    logger.info(f"Validate-feature: {filename}, target: {target_col}")
    result = evaluate_feature(file_path, target_col, code_snippet)

    # Persist improvement score if we have a suggestion_id
    if suggestion_id and result.get("status") == "success":
        sg = (
            db.query(FeatureSuggestion)
            .filter(FeatureSuggestion.id == suggestion_id)
            .first()
        )
        if sg:
            sg.improvement_score = result["improvement"]
            db.commit()

    return result


@router.get("/history/")
async def get_history(
    limit: int = Query(20, description="Number of recent suggestions to return"),
    db: Session = Depends(get_db),
):
    """
    Return the most recent feature suggestions stored in the DB,
    including their parent dataset name — used by the frontend History tab.
    """
    rows = (
        db.query(FeatureSuggestion)
        .order_by(FeatureSuggestion.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for row in rows:
        dataset_name = row.dataset.filename if row.dataset else "unknown"
        results.append(
            {
                "id": row.id,
                "dataset": dataset_name,
                "column_name": row.column_name,
                "idea": row.idea,
                "reason": row.reason,
                "code_snippet": row.code_snippet,
                "improvement_score": row.improvement_score,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return {"history": results, "count": len(results)}
