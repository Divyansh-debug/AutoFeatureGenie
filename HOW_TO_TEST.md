# 🧪 How to Test Your Improved Project

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run Quick Test

```bash
python test_quick.py
```

This will test:
- ✅ All imports work
- ✅ Settings configuration
- ✅ EDA summary generation
- ✅ API app creation

---

## Full Testing Guide

### Option 1: Quick Manual Test (No pytest needed)

#### 1. Test Backend API

**Terminal 1 - Start Backend:**
```bash
uvicorn backend.main:app --reload
```

**Terminal 2 - Test Endpoints:**

```bash
# Test health check
curl http://localhost:8000/health

# Test root endpoint
curl http://localhost:8000/

# Test API docs (open in browser)
# http://localhost:8000/docs
```

#### 2. Test File Upload

Create a test CSV file `test_data.csv`:
```csv
col1,col2,target
1,a,0
2,b,1
3,c,0
```

Then test upload:
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@test_data.csv"
```

#### 3. Test Frontend

**Terminal 3 - Start Frontend:**
```bash
streamlit run frontend/app.py
```

Open browser: http://localhost:8501

Test:
- ✅ Upload a CSV file
- ✅ View EDA summary
- ✅ Get feature suggestions
- ✅ Test error handling

---

### Option 2: Automated Tests (with pytest)

#### Install pytest

```bash
pip install pytest pytest-cov httpx
```

#### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=backend --cov=src --cov-report=html
```

#### Run Specific Tests

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_feature_engine.py -v

# Specific test function
pytest tests/unit/test_feature_engine.py::TestGenerateEDASummary::test_basic_eda_summary -v
```

---

## Testing Checklist

### ✅ Backend Tests

- [ ] **Health Check**
  ```bash
  curl http://localhost:8000/health
  ```
  Expected: `{"status": "healthy", "version": "1.0.0", ...}`

- [ ] **File Upload (Valid CSV)**
  ```bash
  curl -X POST "http://localhost:8000/upload/" -F "file=@test.csv"
  ```
  Expected: Status 200, returns filename and EDA summary

- [ ] **File Upload (Invalid File)**
  ```bash
  curl -X POST "http://localhost:8000/upload/" -F "file=@test.txt"
  ```
  Expected: Status 400, error message

- [ ] **File Upload (Too Large)**
  Create a file > 100MB and try to upload
  Expected: Status 413, error message

- [ ] **Feature Suggestions**
  ```bash
  curl "http://localhost:8000/feature-suggestions/?filename=test.csv&domain=telecom"
  ```
  Expected: Status 200, returns feature suggestions

- [ ] **Feature Suggestions (File Not Found)**
  ```bash
  curl "http://localhost:8000/feature-suggestions/?filename=nonexistent.csv"
  ```
  Expected: Status 404, error message

- [ ] **Rate Limiting**
  Make 61 requests in 1 minute
  Expected: 61st request returns Status 429

### ✅ Frontend Tests

- [ ] **Connection Test**
  - Click "Test Backend Connection" in sidebar
  - Expected: Shows backend status

- [ ] **File Upload**
  - Upload valid CSV
  - Expected: Shows EDA summary

- [ ] **File Validation**
  - Try uploading non-CSV file
  - Expected: Shows error message

- [ ] **Feature Suggestions**
  - Click "Get Feature Suggestions"
  - Expected: Shows feature suggestions

- [ ] **Error Handling**
  - Stop backend, try uploading
  - Expected: Shows connection error

---

## Using Swagger UI (Easiest Way)

1. **Start Backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Open Browser:**
   Navigate to: http://localhost:8000/docs

3. **Test Each Endpoint:**
   - Click on endpoint
   - Click "Try it out"
   - Fill parameters
   - Click "Execute"
   - View response

---

## Test Coverage Report

After running pytest with coverage:

```bash
pytest --cov=backend --cov=src --cov-report=html
```

Open `htmlcov/index.html` in your browser to see:
- Which lines are covered
- Which functions are tested
- Coverage percentage

---

## Common Test Scenarios

### Scenario 1: Happy Path
1. Upload valid CSV ✅
2. View EDA summary ✅
3. Get feature suggestions ✅
4. All working ✅

### Scenario 2: Error Handling
1. Upload invalid file → Error shown ✅
2. Upload empty file → Error shown ✅
3. Upload too large file → Error shown ✅
4. Backend down → Connection error ✅

### Scenario 3: Edge Cases
1. CSV with only headers → Handled ✅
2. CSV with missing values → Handled ✅
3. CSV with special characters → Handled ✅
4. Very large dataset → Handled ✅

---

## Troubleshooting

### Issue: Import errors in tests

**Solution:**
```bash
# Make sure you're in project root
cd AutoFeatureGenie

# Install dependencies
pip install -r requirements.txt
```

### Issue: Tests can't find modules

**Solution:**
```bash
# Add to PYTHONPATH (Linux/Mac)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or (Windows PowerShell)
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
```

### Issue: RAG index not found

**Solution:**
```bash
cd backend
python build_rag_index.py
cd ..
```

---

## Next Steps

1. ✅ Run `python test_quick.py` - Quick validation
2. ✅ Start backend and test with Swagger UI
3. ✅ Install pytest and run full test suite
4. ✅ Test frontend manually
5. ✅ Check test coverage

---

**Start with `python test_quick.py` for immediate results! 🚀**

