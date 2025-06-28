def feature_prompt_template(df_sample: str, columns: list, domain: str = "general") -> str:
    return f"""
You are an expert data scientist. Based on the sample dataset and the domain, suggest useful and creative feature engineering ideas.

Sample Data (first few rows):
{df_sample}

Columns: {columns}
Domain: {domain}

Respond ONLY in JSON format:
[
  {{
    "column": "feature_name",
    "idea": "What transformation or feature to create",
    "reason": "Why this feature is useful",
    "code_snippet": "Python code (Pandas or Sklearn) to create the feature"
  }},
  ...
]
"""
