import pandas as pd
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

from backend.prompts import feature_prompt_template
from backend.rag_engine import RAGEngine

# Load Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize RAG engine (assumes vectorstore.pkl already exists)
rag = RAGEngine("domain_docs")
rag.load_index()

def generate_eda_summary(df: pd.DataFrame) -> dict:
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "column_info": {}
    }

    for col in df.columns:
        info = {
            "dtype": str(df[col].dtype),
            "missing_values": int(df[col].isnull().sum()),
            "unique_values": int(df[col].nunique()),
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            info["mean"] = float(df[col].mean())
            info["std"] = float(df[col].std())
            info["min"] = float(df[col].min())
            info["max"] = float(df[col].max())

        summary["column_info"][col] = info

    likely_targets = [col for col in df.columns if 'target' in col.lower() or 'churn' in col.lower()]
    summary["likely_target_column"] = likely_targets[0] if likely_targets else None

    return summary


def suggest_features(file_path, domain="telecom"):
    df = pd.read_csv(file_path)
    df_sample = df.head(5).to_csv(index=False)
    columns = df.columns.tolist()

    # 🔥 Inject domain knowledge via RAG
    context_chunks = rag.search(f"feature engineering for {domain}")
    context = "\n\n".join(context_chunks)

    # ✅ Prepare prompt with domain context
    prompt = feature_prompt_template(df_sample, columns, context, domain)

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Debug print
        print("Gemini response preview:\n", text[:500])

        # Try parsing full text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract only the JSON array part
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return [{"error": "Gemini returned invalid JSON", "raw": text}]
    except Exception as e:
        return [{"error": "Gemini API call failed", "details": str(e)}]
