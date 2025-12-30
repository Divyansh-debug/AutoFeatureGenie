# 🧠 AutoFeatureGenie

> **Intelligent, AI-powered feature engineering automation for tabular datasets**

AutoFeatureGenie leverages Large Language Models and semantic search to generate domain-aware feature suggestions, reducing the manual effort in feature engineering workflows while improving model performance.

---

## 🎯 Problem Statement

Feature engineering is a critical but time-consuming step in machine learning pipelines. Data scientists spend **countless hours** exploring datasets, identifying patterns, and manually creating new features. This process requires deep domain expertise and is difficult to scale.

**AutoFeatureGenie solves this by**:
- 🔍 Automating exploratory data analysis (EDA) at scale
- 🤖 Generating contextually relevant feature suggestions using AI
- 📚 Reducing domain knowledge dependency through intelligent recommendations
- ⚙️ Integrating seamlessly into existing ML workflows

---

## 🏗️ Architecture & Workflow

```
📤 User Input (CSV)
    ↓
🎨 [Frontend - Streamlit]
    ↓
⚡ [FastAPI Backend]
    ├── 📊 EDA Engine (Data Analysis & Profiling)
    ├── 🔧 Feature Engine (Initial Feature Generation)
    └── 🧠 RAG Engine (Semantic Similarity + LLM)
    ↓
🗂️ [Vector Store (FAISS) + Embeddings (Sentence Transformers)]
    ↓
✨ [Google Gemini LLM]
    ↓
📋 Feature Suggestions (JSON)
    ↓
🎯 [Frontend - Results Display]
```

### 🔑 Key Components

| Component | Purpose |
|-----------|---------|
| **📊 EDA Pipeline** | Analyzes dataset structure, computes statistics, identifies targets, detects missing values |
| **🔧 Feature Engine** | Extracts initial feature candidates and prepares context for LLM |
| **🧠 RAG System** | Uses FAISS + Sentence Transformers to retrieve similar historical features |
| **✨ LLM Integration** | Google Gemini generates context-aware, domain-specific suggestions |
| **⚡ API Layer** | FastAPI exposes endpoints for seamless integration |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|--------------|
| **🎨 Frontend** | Streamlit · Pandas · Requests |
| **⚙️ Backend** | FastAPI · Pandas · Feature Engine |
| **🤖 AI/ML** | Google Generative AI (Gemini) · Sentence Transformers · FAISS · LangChain |
| **🐳 Infrastructure** | Docker · Python 3.8+ |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Automated EDA** | Comprehensive dataset summaries with statistics, distributions, metadata |
| 🤖 **AI-Powered Suggestions** | Intelligent, context-aware feature recommendations via Gemini |
| 🧠 **RAG Integration** | Semantic search over feature history for relevant suggestions |
| 🎯 **Domain-Specific Prompts** | Customizable prompting for industry-specific engineering |
| 📋 **JSON Output** | Structured, machine-readable feature suggestions |
| 📈 **Scalable Design** | Batch processing & ML pipeline integration |
| 🔌 **API-First** | RESTful endpoints for programmatic access |

---

## 📦 Installation

### 📋 Prerequisites
- Python 3.8+
- pip
- 🔑 Google Cloud API key for Gemini → [Get it here](https://makersuite.google.com/app/apikey)

### 🚀 Setup

```bash
# 1️⃣ Clone repository
git clone https://github.com/Divyansh-debug/AutoFeatureGenie.git
cd AutoFeatureGenie

# 2️⃣ Install dependencies
pip install -r requirements.txt

# 3️⃣ Configure environment
echo "GOOGLE_API_KEY=your-api-key-here" > .env

# 4️⃣ Verify setup
python -c "import fastapi, streamlit, google.generativeai; print('✅ All dependencies installed')"
```

---

## 🎯 Quick Start

### ⚡ Running Backend Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- 🌐 Backend: `http://localhost:8000`
- 📚 API Docs: `http://localhost:8000/docs`

### 🎨 Running Frontend

```bash
streamlit run frontend/app.py
```

- 🌐 Frontend: `http://localhost:8501`

### 🐳 Docker Deployment

```bash
docker-compose -f docker/docker-compose.yml up
```

---

## 📡 API Usage

### 1️⃣ Generate EDA Summary

```http
POST /api/eda
```

**Request**:
```json
{
  "file_name": "customer_data.csv",
  "data": "base64_encoded_csv_content"
}
```

**Response** ✅:
```json
{
  "summary": "Dataset contains 10,000 customer records with 15 features...",
  "columns": [
    {
      "name": "age",
      "type": "numeric",
      "missing_percent": 0.5,
      "stats": {
        "mean": 42.3,
        "std": 15.2,
        "min": 18,
        "max": 85
      }
    }
  ],
  "target": "conversion",
  "record_count": 10000
}
```

### 2️⃣ Get Feature Suggestions

```http
POST /api/suggest-features
```

**Request**:
```json
{
  "eda_summary": "Dataset with customer data...",
  "columns": ["age", "income", "purchase_history"],
  "target": "conversion",
  "domain": "e-commerce",
  "custom_prompt": "Focus on interaction features and temporal patterns"
}
```

**Response** ✅:
```json
{
  "features": [
    {
      "name": "age_income_ratio",
      "formula": "age / income",
      "description": "Normalized age-to-income proportion for demographic segmentation",
      "rationale": "Captures purchasing power relative to demographic age group"
    },
    {
      "name": "recency_frequency_interaction",
      "formula": "log(purchase_recency + 1) * purchase_frequency",
      "description": "Interaction between purchase recency and frequency",
      "rationale": "Identifies highly engaged recent customers"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🔄 Example Workflow

```
1️⃣ Upload CSV via Streamlit interface
   ↓
2️⃣ View EDA Summary (statistics, missing values, distributions)
   ↓
3️⃣ Click "Get Feature Suggestions"
   ↓
4️⃣ Review AI-generated features with explanations
   ↓
5️⃣ Export features for model training
```

---

## 📂 Folder Structure

```
AutoFeatureGenie/
├── 📁 backend/
│   ├── main.py                 # ⚡ FastAPI entry point
│   ├── rag_engine.py           # 🧠 FAISS + retrieval logic
│   ├── feature_engine.py       # 🔧 Feature generation & EDA
│   └── prompts.py              # 📝 LLM prompt templates
│
├── 📁 frontend/
│   └── app.py                  # 🎨 Streamlit UI
│
├── 📁 data/
│   └── sample_datasets/        # 📊 Example CSVs
│
├── 📁 docker/
│   ├── Dockerfile              # 🐳 Container config
│   └── docker-compose.yml      # 🔗 Multi-container setup
│
├── 📁 domain_docs/
│   └── feature_patterns.md     # 📚 Domain templates
│
├── 📁 src/
│   └── utils.py                # 🛠️ Shared utilities
│
├── 📁 tests/
│   ├── test_eda.py             # ✅ EDA tests
│   ├── test_api.py             # ✅ API tests
│   └── test_rag.py             # ✅ RAG tests
│
├── requirements.txt            # 📦 Dependencies
├── .env.example                # 🔑 Environment template
└── README.md                   # 📖 This file
```

---

## ⚙️ Configuration

### 🔑 Environment Variables

```bash
GOOGLE_API_KEY=                 # 🔴 Required: API key
FASTAPI_HOST=0.0.0.0           # API host
FASTAPI_PORT=8000              # API port
LOG_LEVEL=INFO                  # Logging level
VECTORSTORE_PATH=./vectorstore  # FAISS location
```

### 🎯 Domain-Specific Customization

Edit `backend/prompts.py`:

```python
FINANCE_PROMPT = """
You are a feature engineer for financial risk modeling.
Generate features for predicting loan defaults...
"""

ECOMMERCE_PROMPT = """
You are a feature engineer for e-commerce recommendation systems.
Generate features for predicting customer churn...
"""
```

---

## 🚀 Future Roadmap

- 🎬 **Multi-Modal Features**: Text, images, time-series support
- ⚡ **Distributed Processing**: Spark integration (100GB+ datasets)
- 📊 **Feature Ranking**: Automated importance scoring
- 🔄 **Feedback Loop**: Self-improving suggestions
- 📈 **Version Control**: Feature evolution tracking
- 🔌 **Integrations**: Databricks, Snowflake, BigQuery connectors
- 👁️ **Monitoring**: Drift detection & analytics
- 🔍 **Explainability**: SHAP/LIME integration
- ⏳ **Async Jobs**: Batch processing queue
- 🎓 **Fine-Tuned Models**: Enterprise LLM training

---

## ✅ Testing

```bash
# 🧪 Run all tests
pytest tests/ -v

# 🎯 Run specific suite
pytest tests/test_api.py

# 📊 With coverage report
pytest tests/ --cov=backend --cov-report=html
```

---

## ⚡ Performance Metrics

| Operation | Time | Details |
|-----------|------|---------|
| 📊 EDA Generation | 2-5s | For 100K rows |
| 🤖 Feature Suggestions | 5-10s | Includes LLM latency |
| 🔍 Vector Search | <100ms | Similarity retrieval |
| 💾 Memory Usage | ~500MB + 2GB | Baseline + large datasets |

---

## 🤝 Contributing

We ❤️ contributions! Here's how:

```bash
# 1. Fork the repo
# 2. Create feature branch
git checkout -b feature/your-awesome-feature

# 3. Commit with clear messages
git commit -m "Add awesome feature"

# 4. Push & submit PR
git push origin feature/your-awesome-feature
```

---

## 📧 Contact & Links

| | |
|--|--|
| 👨‍💻 **Author** | Divyansh Agarwal |
| 📧 **Email** | agarwaldivyansh4002@gmail.com |
| 🔗 **Repository** | [AutoFeatureGenie on GitHub](https://github.com/Divyansh-debug/AutoFeatureGenie) |

---

<div align="center">

### 🚀 Built for data scientists and ML engineers who want to ship models faster

**⭐ If you find this useful, please star the repo!**

[Give Feedback](https://github.com/Divyansh-debug/AutoFeatureGenie/issues) · [Report Bug](https://github.com/Divyansh-debug/AutoFeatureGenie/issues) · [Request Feature](https://github.com/Divyansh-debug/AutoFeatureGenie/issues)

</div>
