import pandas as pd
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from backend.prompts import feature_prompt_template

# Load Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_eda_summary(df: pd.DataFrame) -> dict:
    summary = {}
    summary["shape"] = df.shape
    summary["columns"] = list(df.columns)

    column_info = {}
    for col in df.columns:
        column_info[col] = {
            "dtype": str(df[col].dtype),
            "missing_values": int(df[col].isnull().sum()),
            "unique_values": int(df[col].nunique()),
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            column_info[col]["mean"] = float(df[col].mean())
            column_info[col]["std"] = float(df[col].std())
            column_info[col]["min"] = float(df[col].min())
            column_info[col]["max"] = float(df[col].max())

    summary["column_info"] = column_info

    likely_targets = [col for col in df.columns if 'target' in col.lower() or 'churn' in col.lower()]
    summary["likely_target_column"] = likely_targets[0] if likely_targets else None

    return summary


def suggest_features(file_path, domain="telecom"):
    df = pd.read_csv(file_path)
    df_sample = df.head(5).to_csv(index=False)

    # Prepare prompt using sample + columns + domain
    prompt = feature_prompt_template(df_sample, df.columns.tolist(), domain=domain)

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text
        
        # Debug: Print the response for troubleshooting
        print(f"Gemini Response: {text[:500]}...")  # Print first 500 chars

        try:
            # Try to parse Gemini's response directly
            suggestions = json.loads(text)
            return suggestions
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            # Try to extract JSON from the response if it's wrapped in text
            import re
            # Look for JSON array pattern
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                try:
                    suggestions = json.loads(json_match.group())
                    return suggestions
                except json.JSONDecodeError:
                    pass
            
            # If all parsing attempts fail, return the raw text
            return [{
                "error": "Invalid JSON format in Gemini response",
                "raw_output": text
            }]
    except Exception as e:
        return [{"error": "Gemini API call failed", "details": str(e)}]
