def feature_prompt_template(df_sample: str, columns: list, domain_knowledge: str, domain: str = "general") -> str:
    return f"""
You are a top-tier data scientist skilled in feature engineering. Based on the provided data sample and domain knowledge, suggest smart and practical feature engineering ideas to improve ML model performance.

### Sample Data (First Few Rows)
{df_sample}

### Columns
{columns}

### Domain
{domain}

### Domain Knowledge
{domain_knowledge}

Your task:
- Suggest 5–7 relevant and unique features.
- Use the domain knowledge to guide your creativity.
- Avoid suggesting features already present.
- Include transformations, combinations, or encoding ideas.

Respond ONLY in strict JSON format:
[
  {{
    "column": "feature_name",
    "idea": "Short explanation of the new feature",
    "reason": "Why this is a valuable feature",
    "code_snippet": "Python code using pandas or sklearn"
  }},
  ...
]
"""
