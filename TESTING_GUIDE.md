# 🧪 Testing Guide - AutoFeatureGenie

Complete guide for testing the improved project.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Running Unit Tests](#running-unit-tests)
3. [Running Integration Tests](#running-integration-tests)
4. [Running All Tests](#running-all-tests)
5. [Test Coverage](#test-coverage)
6. [Manual API Testing](#manual-api-testing)
7. [Frontend Testing](#frontend-testing)
8. [Testing with Docker](#testing-with-docker)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Testing Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `httpx` - For API testing

### 2. Verify Installation

```bash
pytest --version
```

---

## Running Unit Tests

Unit tests test individual functions and modules in isolation.

### Run All Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_feature_engine.py -v
```

### Run Specific Test Function

```bash
pytest tests/unit/test_feature_engine.py::TestGenerateEDASummary::test_basic_eda_summary -v
```

### Expected Output

```
tests/unit/test_feature_engine.py::TestGenerateEDASummary::test_basic_eda_summary PASSED
tests/unit/test_feature_engine.py::TestGenerateEDASummary::test_numeric_column_stats PASSED
tests/unit/test_feature_engine.py::TestGenerateEDASummary::test_missing_values PASSED
...
```

---

## Running Integration Tests

Integration tests test the API endpoints end-to-end.

### Run All Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Specific Integration Test

```bash
pytest tests/integration/test_api.py::test_health_check -v
```

### Note

Integration tests use `TestClient` which doesn't require the backend to be running. However, for tests that interact with external services (like Gemini API), you may need to mock them.

---

## Running All Tests

### Run Everything

```bash
pytest
```

This runs:
- All unit tests
- All integration tests
- Generates coverage report

### Run with Verbose Output

```bash
pytest -v
```

### Run and Stop on First Failure

```bash
pytest -x
```

### Run with More Details

```bash
pytest -vv
```

---

## Test Coverage

### Generate Coverage Report

```bash
pytest --cov=backend --cov=src --cov-report=term-missing
```

### Generate HTML Coverage Report

```bash
pytest --cov=backend --cov=src --cov-report=html
```

This creates an `htmlcov/` directory. Open `htmlcov/index.html` in your browser to see the coverage report.

### Coverage Report Options

```bash
# Terminal report
pytest --cov=backend --cov=src --cov-report=term

# HTML report
pytest --cov=backend --cov=src --cov-report=html

# XML report (for CI/CD)
pytest --cov=backend --cov=src --cov-report=xml

# All formats
pytest --cov=backend --cov=src --cov-report=term --cov-report=html --cov-report=xml
```

---

## Manual API Testing

### Option 1: Using Swagger UI (Recommended)

1. **Start the backend**:
   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Open Swagger UI**:
   Navigate to: http://localhost:8000/docs

3. **Test endpoints**:
   - Click on any endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - View response

### Option 2: Using curl

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Root Endpoint
```bash
curl http://localhost:8000/
```

#### Upload File
```bash
curl -X POST "http://localhost:8000/upload/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/file.csv"
```

#### Get Feature Suggestions
```bash
curl "http://localhost:8000/feature-suggestions/?filename=your_file.csv&domain=telecom"
```

### Option 3: Using Python requests

Create a test script `test_api_manual.py`:

```python
import requests
import pandas as pd
import io

# Health check
response = requests.get("http://localhost:8000/health")
print("Health:", response.json())

# Upload file
df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
csv_content = df.to_csv(index=False)

files = {'file': ('test.csv', csv_content, 'text/csv')}
response = requests.post("http://localhost:8000/upload/", files=files)
print("Upload:", response.json())

# Get suggestions
filename = response.json()['filename']
response = requests.get(
    "http://localhost:8000/feature-suggestions/",
    params={"filename": filename, "domain": "telecom"}
)
print("Suggestions:", response.json())
```

Run it:
```bash
python test_api_manual.py
```

### Option 4: Using Postman

1. Import the OpenAPI schema from http://localhost:8000/openapi.json
2. Create requests for each endpoint
3. Test with different parameters

---

## Frontend Testing

### Manual Testing Steps

1. **Start Backend**:
   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   streamlit run frontend/app.py
   ```

3. **Test Scenarios**:

   #### ✅ Test File Upload
   - Upload a valid CSV file
   - Verify EDA summary appears
   - Check column information

   #### ✅ Test File Validation
   - Try uploading a non-CSV file (should fail)
   - Try uploading a file > 100MB (should fail)
   - Try uploading an empty file (should fail)

   #### ✅ Test Feature Suggestions
   - Click "Get Feature Suggestions"
   - Verify suggestions appear
   - Check different domains

   #### ✅ Test Error Handling
   - Stop backend, try uploading (should show error)
   - Upload invalid file (should show error)
   - Test with missing file (should show error)

   #### ✅ Test Connection Status
   - Use sidebar "Test Backend Connection" button
   - Verify status updates correctly

---

## Testing with Docker

### Build and Test

```bash
# Build containers
docker-compose -f docker/docker-compose.yml build

# Start containers
docker-compose -f docker/docker-compose.yml up -d

# Test health endpoint
curl http://localhost:8000/health

# Run tests inside container
docker-compose -f docker/docker-compose.yml exec backend pytest

# View logs
docker-compose -f docker/docker-compose.yml logs backend
docker-compose -f docker/docker-compose.yml logs frontend

# Stop containers
docker-compose -f docker/docker-compose.yml down
```

---

## Test Scenarios Checklist

### ✅ Unit Tests
- [ ] EDA summary generation
- [ ] Numeric column statistics
- [ ] Missing value handling
- [ ] Target column detection
- [ ] Feature suggestion generation
- [ ] Error handling

### ✅ Integration Tests
- [ ] Health check endpoint
- [ ] Root endpoint
- [ ] File upload (success)
- [ ] File upload (empty file)
- [ ] File upload (invalid file)
- [ ] Feature suggestions (file not found)
- [ ] Feature suggestions (success)

### ✅ Manual Testing
- [ ] Backend starts successfully
- [ ] Frontend connects to backend
- [ ] File upload works
- [ ] File validation works
- [ ] EDA summary displays correctly
- [ ] Feature suggestions generate
- [ ] Error messages are clear
- [ ] Rate limiting works
- [ ] Logging works

---

## Troubleshooting

### Issue: Tests fail with import errors

**Solution**:
```bash
# Make sure you're in the project root
cd AutoFeatureGenie

# Install in development mode
pip install -e .

# Or add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Tests fail because RAG index not found

**Solution**:
```bash
# Build RAG index first
cd backend
python build_rag_index.py
cd ..
```

### Issue: Integration tests fail because backend not running

**Solution**: Integration tests use `TestClient` and don't need the backend running. If you're testing actual API calls, start the backend first.

### Issue: Coverage report shows 0%

**Solution**: Make sure you're running tests from the project root and using correct paths:
```bash
pytest --cov=backend --cov=src
```

### Issue: Tests timeout

**Solution**: Some tests mock external APIs. If tests are slow, check if mocks are working correctly.

---

## Continuous Integration (CI) Testing

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=backend --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Performance Testing

### Load Testing with Locust

Install Locust:
```bash
pip install locust
```

Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task(3)
    def upload_file(self):
        files = {'file': ('test.csv', 'col1,col2\n1,a\n2,b', 'text/csv')}
        self.client.post("/upload/", files=files)
```

Run:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 and start testing.

---

## Next Steps

1. **Add More Tests**: Expand test coverage for edge cases
2. **Add E2E Tests**: Use Selenium/Playwright for browser testing
3. **Add Performance Tests**: Use Locust or similar tools
4. **Set Up CI/CD**: Automate testing on every commit
5. **Add Mutation Testing**: Use tools like mutmut

---

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_feature_engine.py::test_basic_eda_summary

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "test_eda"

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

---

**Happy Testing! 🧪**

