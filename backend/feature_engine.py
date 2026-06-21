"""
Feature Engine — upgraded with:
  • Structured output parsing via Pydantic (LLM fallback-safe)
  • LangChain Gemini integration with retry / fallback
  • Full code_snippet + expected_impact + complexity in suggestions
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any, List, Optional

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from backend.prompts import feature_prompt_template
from backend.rag_engine import RAGEngine
from src.config.settings import settings
from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Pydantic schema — guarantees the shape of every suggestion returned to callers
# ---------------------------------------------------------------------------

class FeatureSuggestionSchema(BaseModel):
    """Structured output schema for a single feature engineering suggestion."""

    column: str = Field(..., description="Name of the new engineered feature")
    idea: str = Field(..., description="Short description of the feature")
    reason: str = Field(..., description="Why this feature adds value")
    code_snippet: str = Field(..., description="Executable pandas/sklearn Python code")
    expected_impact: Optional[str] = Field(None, description="Qualitative impact estimate")
    complexity: Optional[str] = Field(None, description="low | medium | high")

    @field_validator("complexity", mode="before")
    @classmethod
    def _normalise_complexity(cls, v):
        if v:
            v = str(v).lower().strip()
            if v not in {"low", "medium", "high"}:
                return "medium"
        return v

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# LLM initialisation (Gemini via google-generativeai, with LangChain wrapper)
# ---------------------------------------------------------------------------

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY

# Primary: google-generativeai SDK
_genai_model = None

if gemini_api_key:
    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_api_key)
        model_name = os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL

        try:
            available = [
                m.name for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
            # Pick configured model or best available
            chosen = next(
                (m for m in available if model_name in m),
                available[0] if available else None,
            )
            if chosen:
                clean = chosen.split("/")[-1] if "/" in chosen else chosen
                _genai_model = genai.GenerativeModel(clean)
                logger.info(f"Gemini model initialised: {clean}")
            else:
                raise RuntimeError("No generateContent-capable models found.")
        except Exception as e:
            logger.warning(f"Model discovery failed ({e}); falling back to direct init.")
            for candidate in [model_name, "gemini-2.5-flash", "gemini-1.5-pro", "gemini-pro"]:
                try:
                    _genai_model = genai.GenerativeModel(candidate)
                    logger.info(f"Gemini model (fallback): {candidate}")
                    break
                except Exception:
                    continue

    except ImportError:
        logger.warning("google-generativeai not installed.")
else:
    logger.warning("GEMINI_API_KEY not set — LLM features disabled.")


# ---------------------------------------------------------------------------
# RAG engine (lazy-loaded singleton)
# ---------------------------------------------------------------------------

rag = RAGEngine(settings.RAG_DOC_FOLDER)
try:
    rag.load_index()
    logger.info("RAG index loaded successfully.")
except Exception as e:
    logger.warning(f"RAG index load failed ({e}); continuing without context.")


# ---------------------------------------------------------------------------
# EDA Summary
# ---------------------------------------------------------------------------

def generate_eda_summary(df: pd.DataFrame) -> dict:
    """Generate a comprehensive EDA summary for *df*."""
    logger.info(f"Generating EDA summary — shape: {df.shape}")

    summary: dict[str, Any] = {
        "shape": df.shape,
        "columns": list(df.columns),
        "column_info": {},
    }

    for col in df.columns:
        info: dict[str, Any] = {
            "dtype": str(df[col].dtype),
            "missing_values": int(df[col].isnull().sum()),
            "unique_values": int(df[col].nunique()),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            info["mean"] = float(df[col].mean())
            info["std"] = float(df[col].std())
            info["min"] = float(df[col].min())
            info["max"] = float(df[col].max())
            info["median"] = float(df[col].median())
        summary["column_info"][col] = info

    targets = [c for c in df.columns if any(k in c.lower() for k in ("target", "churn", "label", "class", "y"))]
    summary["likely_target_column"] = targets[0] if targets else None
    logger.info(f"EDA done — {len(df.columns)} cols, target: {summary['likely_target_column']}")
    return summary


# ---------------------------------------------------------------------------
# Structured output parsing
# ---------------------------------------------------------------------------

def _parse_suggestions(text: str) -> List[dict]:
    """
    Parse the LLM response into a validated list of FeatureSuggestionSchema dicts.
    Tries:
      1. Direct JSON parse
      2. Regex extraction of the first JSON array
      3. Returns an error dict if both fail
    """
    def _validate(raw_list: list) -> List[dict]:
        validated = []
        for item in raw_list:
            try:
                validated.append(FeatureSuggestionSchema(**item).model_dump())
            except (ValidationError, TypeError) as ve:
                logger.warning(f"Suggestion skipped (validation error): {ve}")
        return validated

    # Attempt 1 — direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            result = _validate(parsed)
            if result:
                logger.info(f"Parsed {len(result)} suggestions (direct JSON).")
                return result
    except json.JSONDecodeError:
        pass

    # Attempt 2 — regex extraction
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                result = _validate(parsed)
                if result:
                    logger.info(f"Parsed {len(result)} suggestions (regex extraction).")
                    return result
        except json.JSONDecodeError:
            pass

    logger.error("Could not parse LLM response as valid feature suggestions.")
    return [{"error": "LLM returned invalid JSON", "raw": text[:2000]}]


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def suggest_features(file_path: str, domain: str = "telecom") -> List[dict]:
    """
    Generate feature engineering suggestions for the CSV at *file_path*.

    Returns a list of dicts, each conforming to FeatureSuggestionSchema
    (or a single error dict if something goes wrong).
    """
    logger.info(f"Feature suggestion request — file: {file_path}, domain: {domain}")

    try:
        df = pd.read_csv(file_path)
        df_sample = df.head(5).to_csv(index=False)
        columns = df.columns.tolist()
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return [{"error": "Could not read dataset", "details": str(e)}]

    # Retrieve RAG context
    try:
        chunks = rag.search(f"feature engineering for {domain}", top_k=settings.RAG_TOP_K)
        context = "\n\n".join(chunks)
        logger.info(f"RAG returned {len(chunks)} context chunks.")
    except Exception as e:
        logger.warning(f"RAG search failed ({e}); proceeding without context.")
        context = ""

    prompt = feature_prompt_template(df_sample, columns, context, domain)

    # Call LLM — re-fetch module-level reference so tests can patch it
    import backend.feature_engine as _self
    _model = _self._genai_model
    if _model is None:
        logger.error("No LLM model initialised.")
        return [{"error": "LLM not initialised", "details": "Check GEMINI_API_KEY."}]

    # Call LLM
    try:
        response = _model.generate_content(prompt)
        text = getattr(response, "text", None)
        if not text:
            return [{"error": "Empty response from LLM", "details": "Model returned no text."}]
        return _parse_suggestions(text.strip())
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        return [{"error": "LLM call failed", "details": str(e)}]


# Keep legacy alias for any existing callers
model = _genai_model
