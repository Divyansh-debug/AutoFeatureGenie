"""
Auto-Validator / Evaluation Service
====================================
Empirically validates a generated feature by:
  1. Running a baseline ML model on the original dataset.
  2. Applying the generated feature code snippet.
  3. Re-running the model on the augmented dataset.
  4. Returning the metric delta so callers can store an improvement_score in the DB.

Supports both classification (F1) and regression (RMSE) tasks.
"""
from __future__ import annotations

import traceback
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import f1_score, mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder

from src.utils.logger import logger


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_task(df: pd.DataFrame, target_col: str) -> str:
    """Return 'classification' or 'regression' based on the target column."""
    n_unique = df[target_col].nunique()
    if n_unique <= 20 or df[target_col].dtype == object:
        return "classification"
    return "regression"


def _prepare_features(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series]:
    """Drop non-numeric columns, encode categoricals, split X / y."""
    df = df.copy()
    y = df.pop(target_col)

    # Encode categorical target if needed
    if y.dtype == object:
        le = LabelEncoder()
        y = pd.Series(le.fit_transform(y), name=target_col)

    # Encode object columns in X
    for col in df.select_dtypes(include=["object", "string"]).columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))

    # Fill NaNs
    df = df.fillna(df.median(numeric_only=True))
    return df, y


def _score_model(X: pd.DataFrame, y: pd.Series, task: str, cv: int = 3) -> float:
    """
    Cross-validate a Gradient Boosting model.
    Returns mean F1 (macro) for classification, or negative RMSE for regression
    (so that higher = better in both cases).
    """
    if task == "classification":
        model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")
        return float(np.mean(scores))
    else:
        model = GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv, scoring="neg_root_mean_squared_error")
        return float(np.mean(scores))  # already negative RMSE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_feature(
    file_path: str,
    target_col: str,
    code_snippet: str,
    cv_folds: int = 3,
) -> dict:
    """
    Evaluate the uplift a *code_snippet* provides over a baseline model.

    Parameters
    ----------
    file_path   : path to the original CSV dataset
    target_col  : name of the target / label column
    code_snippet: Python code that creates a new column in `df`
    cv_folds    : number of cross-validation folds

    Returns
    -------
    A dict with keys:
        baseline_score   (float)
        augmented_score  (float)
        improvement      (float, positive = better)
        task             ('classification' | 'regression')
        metric           ('f1_macro' | 'neg_rmse')
        status           ('success' | 'error')
        error            (str, only present on failure)
    """
    try:
        df_original = pd.read_csv(file_path)

        if target_col not in df_original.columns:
            return {
                "status": "error",
                "error": f"Target column '{target_col}' not found in dataset.",
            }

        task = _detect_task(df_original, target_col)
        metric = "f1_macro" if task == "classification" else "neg_rmse"
        logger.info(f"Evaluating feature — task: {task}, target: {target_col}")

        # ── Baseline score ──────────────────────────────────────────────────
        X_base, y = _prepare_features(df_original, target_col)
        baseline_score = _score_model(X_base, y, task, cv=cv_folds)
        logger.info(f"Baseline {metric}: {baseline_score:.4f}")

        # ── Apply feature snippet ───────────────────────────────────────────
        df_augmented = df_original.copy()
        try:
            exec(code_snippet, {"df": df_augmented, "pd": pd, "np": np})  # noqa: S102
        except Exception as exec_err:
            logger.warning(f"code_snippet execution failed: {exec_err}")
            return {
                "status": "error",
                "error": f"Feature code execution failed: {exec_err}",
                "baseline_score": baseline_score,
                "augmented_score": None,
                "improvement": None,
                "task": task,
                "metric": metric,
            }

        # ── Augmented score ─────────────────────────────────────────────────
        X_aug, y_aug = _prepare_features(df_augmented, target_col)
        augmented_score = _score_model(X_aug, y_aug, task, cv=cv_folds)
        logger.info(f"Augmented {metric}: {augmented_score:.4f}")

        improvement = round(augmented_score - baseline_score, 6)
        logger.info(f"Improvement: {improvement:+.4f}")

        return {
            "status": "success",
            "baseline_score": round(baseline_score, 6),
            "augmented_score": round(augmented_score, 6),
            "improvement": improvement,
            "task": task,
            "metric": metric,
        }

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
