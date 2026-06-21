"""Unit tests for evaluation_service (Auto-Validator)"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from src.services.evaluation_service import (
    evaluate_feature,
    _detect_task,
    _prepare_features,
)


class TestDetectTask:
    def test_classification_binary(self):
        df = pd.DataFrame({"target": [0, 1, 0, 1, 0, 1]})
        assert _detect_task(df, "target") == "classification"

    def test_classification_categorical(self):
        df = pd.DataFrame({"label": ["A", "B", "A", "C"]})
        assert _detect_task(df, "label") == "classification"

    def test_regression_continuous(self):
        df = pd.DataFrame({"price": list(range(100))})
        assert _detect_task(df, "price") == "regression"


class TestPrepareFeatures:
    def test_numeric_passthrough(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "target": [0, 1, 0]})
        X, y = _prepare_features(df, "target")
        assert "target" not in X.columns
        assert len(X) == 3

    def test_categorical_encoding(self):
        df = pd.DataFrame({"cat": ["A", "B", "A"], "target": [0, 1, 0]})
        X, y = _prepare_features(df, "target")
        assert X["cat"].dtype in [np.int32, np.int64, np.float64]

    def test_missing_filled(self):
        df = pd.DataFrame({"a": [1, None, 3], "target": [0, 1, 0]})
        X, y = _prepare_features(df, "target")
        assert not X["a"].isnull().any()


class TestEvaluateFeature:
    def _make_csv(self, df: pd.DataFrame) -> str:
        """Write df to a temp CSV and return the path."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        df.to_csv(f.name, index=False)
        f.close()
        return f.name

    def test_successful_classification(self):
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "feature_a": np.random.randn(80),
                "feature_b": np.random.randn(80),
                "target": np.random.randint(0, 2, 80),
            }
        )
        path = self._make_csv(df)
        try:
            code = "df['feature_sum'] = df['feature_a'] + df['feature_b']"
            result = evaluate_feature(path, "target", code, cv_folds=2)
            assert result["status"] == "success"
            assert "baseline_score" in result
            assert "augmented_score" in result
            assert "improvement" in result
            assert result["task"] == "classification"
        finally:
            os.unlink(path)

    def test_successful_regression(self):
        np.random.seed(0)
        df = pd.DataFrame(
            {
                "x1": np.random.randn(80),
                "x2": np.random.randn(80),
                "price": np.random.uniform(10, 1000, 80),
            }
        )
        path = self._make_csv(df)
        try:
            code = "df['x_ratio'] = df['x1'] / (df['x2'].abs() + 1e-9)"
            result = evaluate_feature(path, "price", code, cv_folds=2)
            assert result["status"] == "success"
            assert result["task"] == "regression"
        finally:
            os.unlink(path)

    def test_invalid_target_column(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        path = self._make_csv(df)
        try:
            result = evaluate_feature(path, "nonexistent", "df['x'] = 1", cv_folds=2)
            assert result["status"] == "error"
            assert "not found" in result["error"]
        finally:
            os.unlink(path)

    def test_broken_code_snippet(self):
        np.random.seed(1)
        df = pd.DataFrame(
            {
                "a": np.random.randn(60),
                "target": np.random.randint(0, 2, 60),
            }
        )
        path = self._make_csv(df)
        try:
            bad_code = "df['bad'] = 1 / 0"  # will raise ZeroDivisionError
            result = evaluate_feature(path, "target", bad_code, cv_folds=2)
            assert result["status"] == "error"
        finally:
            os.unlink(path)
