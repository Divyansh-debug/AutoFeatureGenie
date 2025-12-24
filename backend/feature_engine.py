import pandas as pd
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

from backend.prompts import feature_prompt_template
from backend.rag_engine import RAGEngine
from src.config.settings import settings
from src.utils.logger import logger

# Load Gemini API key
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
if not gemini_api_key:
    logger.warning("GEMINI_API_KEY not found in environment or settings")
    model = None
else:
    genai.configure(api_key=gemini_api_key)
    
    # List available models and use the first available one
    model = None
    model_name = os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL
    
    try:
        # Try to list available models
        available_models = genai.list_models()
        model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
        
        if model_names:
            logger.info(f"Available models: {model_names}")
            
            # Try the configured model first
            if model_name in model_names or any(model_name in m for m in model_names):
                # Find matching model
                matching_model = next((m for m in model_names if model_name in m), None)
                if matching_model:
                    # Extract just the model name part (remove 'models/' prefix if present)
                    clean_name = matching_model.split('/')[-1] if '/' in matching_model else matching_model
                    model = genai.GenerativeModel(clean_name)
                    logger.info(f"Initialized Gemini model: {clean_name}")
                else:
                    # Use first available model
                    first_model = model_names[0].split('/')[-1] if '/' in model_names[0] else model_names[0]
                    model = genai.GenerativeModel(first_model)
                    logger.info(f"Using first available model: {first_model}")
            else:
                # Use first available model as fallback
                first_model = model_names[0].split('/')[-1] if '/' in model_names[0] else model_names[0]
                model = genai.GenerativeModel(first_model)
                logger.info(f"Configured model '{model_name}' not found. Using: {first_model}")
        else:
            logger.warning("No models with generateContent method found")
            # Try direct initialization as fallback
            try:
                model = genai.GenerativeModel(model_name)
                logger.info(f"Initialized model directly: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize model {model_name}: {str(e)}")
                model = None
                
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        # Fallback: try common model names
        fallback_models = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash", "models/gemini-pro"]
        for fallback in fallback_models:
            try:
                model = genai.GenerativeModel(fallback)
                logger.info(f"Using fallback model: {fallback}")
                break
            except Exception as e2:
                logger.debug(f"Fallback model {fallback} failed: {str(e2)}")
                continue
        
        if model is None:
            logger.error("All model initialization attempts failed")

# Initialize RAG engine (assumes vectorstore.pkl already exists)
rag = RAGEngine(settings.RAG_DOC_FOLDER)
try:
    rag.load_index()
    logger.info("RAG index loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load RAG index: {str(e)}")

def generate_eda_summary(df: pd.DataFrame) -> dict:
    """Generate EDA summary for a DataFrame"""
    logger.info(f"Generating EDA summary for DataFrame with shape {df.shape}")
    
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
    
    logger.info(f"EDA summary generated: {len(df.columns)} columns, target: {summary['likely_target_column']}")
    return summary


def suggest_features(file_path, domain="telecom"):
    """Generate feature engineering suggestions using AI"""
    logger.info(f"Generating feature suggestions for {file_path}, domain: {domain}")
    
    try:
        df = pd.read_csv(file_path)
        df_sample = df.head(5).to_csv(index=False)
        columns = df.columns.tolist()

        # 🔥 Inject domain knowledge via RAG
        try:
            context_chunks = rag.search(f"feature engineering for {domain}", top_k=settings.RAG_TOP_K)
            context = "\n\n".join(context_chunks)
            logger.info(f"Retrieved {len(context_chunks)} RAG context chunks")
        except Exception as e:
            logger.warning(f"RAG search failed: {str(e)}, continuing without context")
            context = ""

        # ✅ Prepare prompt with domain context
        prompt = feature_prompt_template(df_sample, columns, context, domain)

        # Check if model is initialized
        if model is None:
            logger.error("Gemini model is not initialized. Please check your API key and model name.")
            return [{"error": "Model not initialized", "details": "Gemini model failed to initialize. Please check your API key and model configuration."}]

        try:
            response = model.generate_content(prompt)
            
            # Check if response has text
            if not hasattr(response, 'text'):
                logger.error("Gemini API response missing 'text' attribute")
                return [{"error": "Invalid response from Gemini API", "details": "Response object does not have 'text' attribute."}]
            
            if response.text is None:
                logger.error("Gemini API returned None for text")
                return [{"error": "Empty response from Gemini API", "details": "The API call succeeded but returned None for text content."}]
            
            text = response.text.strip()
            
            # Check if text is empty
            if not text:
                logger.error("Gemini API returned empty text after stripping")
                return [{"error": "Empty response from Gemini API", "details": "The API returned an empty response after processing."}]

            logger.debug(f"Gemini response preview: {text[:500]}")

            # Try parsing full text
            try:
                suggestions = json.loads(text)
                logger.info(f"Successfully parsed {len(suggestions)} feature suggestions")
                return suggestions
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {str(e)}, attempting extraction")
                # Try to extract only the JSON array part
                import re
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group())
                    logger.info(f"Extracted {len(suggestions)} feature suggestions from text")
                    return suggestions
                else:
                    logger.error("Could not extract JSON from Gemini response")
                    return [{"error": "Gemini returned invalid JSON", "raw": text[:1000]}]
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}", exc_info=True)
            return [{"error": "Gemini API call failed", "details": str(e)}]
    except Exception as e:
        logger.error(f"Feature suggestion generation failed: {str(e)}", exc_info=True)
        return [{"error": "Feature generation failed", "details": str(e)}]
