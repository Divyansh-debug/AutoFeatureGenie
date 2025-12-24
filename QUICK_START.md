# 🚀 Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <your-repo-url>
   cd AutoFeatureGenie
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Build RAG index** (if not already built):
   ```bash
   cd backend
   python build_rag_index.py
   cd ..
   ```

## Running the Application

### Option 1: Run Backend and Frontend Separately

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py --server.port 8501
```

### Option 2: Using Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up --build
```

## Accessing the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

Run all tests with coverage:
```bash
pytest
```

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify GEMINI_API_KEY is set in .env
- Check logs for errors

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Use the "Test Backend Connection" button in the sidebar
- Check CORS settings in backend/main.py

### File upload fails
- Check file size (max 100MB)
- Ensure file is valid CSV
- Check backend logs for errors

## Next Steps

- Read `IMPROVEMENTS.md` for detailed improvement guide
- Check `PROJECT_ANALYSIS_SUMMARY.md` for project overview
- Review `IMPLEMENTATION_EXAMPLES.md` for code examples

