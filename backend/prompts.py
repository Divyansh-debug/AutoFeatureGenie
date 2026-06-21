"""Prompt templates for AutoFeatureGenie feature engineering suggestions."""


def feature_prompt_template(
    df_sample: str,
    columns: list,
    domain_knowledge: str,
    domain: str = "general",
) -> str:
    """
    Build the LLM prompt for feature engineering suggestions.

    The prompt asks the model to return a *strict* JSON array where every
    element has the following guaranteed fields:
        - column        : name of the new engineered feature
        - idea          : short plain-English explanation
        - reason        : business / ML justification
        - code_snippet  : executable pandas / sklearn Python code
        - expected_impact : qualitative impact estimate
        - complexity    : one of  low | medium | high
    """
    return f"""
You are a senior Data Scientist specialising in feature engineering for {domain} ML models.
Your task: generate 5–7 creative, high-value engineered features based on the dataset below.

─────────────────────────────────────────────────────────────
DATASET SAMPLE (first few rows)
─────────────────────────────────────────────────────────────
{df_sample}

COLUMN LIST
{columns}

DOMAIN
{domain}

DOMAIN KNOWLEDGE (from RAG retrieval)
{domain_knowledge if domain_knowledge else "No additional domain knowledge available."}

─────────────────────────────────────────────────────────────
INSTRUCTIONS
─────────────────────────────────────────────────────────────
1. Do NOT suggest features that already exist in the column list above.
2. Suggest transformations, interactions, aggregations, or encoding ideas.
3. For each feature write a complete, runnable Python snippet using pandas or
   scikit-learn.  Assume the dataframe variable is called `df`.
4. Estimate the expected_impact qualitatively (e.g., "Likely to reduce RMSE
   by 5–10%").
5. Rate complexity as: low | medium | high.

─────────────────────────────────────────────────────────────
OUTPUT FORMAT — respond ONLY with a valid JSON array, no other text.
─────────────────────────────────────────────────────────────
[
  {{
    "column": "feature_name",
    "idea": "Short plain-English description of the new feature",
    "reason": "Why this feature adds predictive value for a {domain} model",
    "code_snippet": "df['feature_name'] = ...",
    "expected_impact": "Expected effect on model performance",
    "complexity": "low | medium | high"
  }},
  ...
]
"""
