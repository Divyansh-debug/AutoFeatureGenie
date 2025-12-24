"""Quick test script - Run this to test the improved project"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work"""
    print("[TEST] Testing imports...")
    try:
        from src.config.settings import settings
        print("[OK] Settings imported successfully")
        
        from src.models.schemas import UploadResponse, FeatureSuggestionsResponse
        print("[OK] Models imported successfully")
        
        from src.utils.logger import logger
        print("[OK] Logger imported successfully")
        
        from src.utils.exceptions import raise_file_too_large
        print("[OK] Exceptions imported successfully")
        
        from backend.feature_engine import generate_eda_summary
        print("[OK] Feature engine imported successfully")
        
        from backend.main import app
        print("[OK] Main app imported successfully")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {str(e)}")
        return False

def test_eda_summary():
    """Test EDA summary generation"""
    print("\n[TEST] Testing EDA summary generation...")
    try:
        import pandas as pd
        from backend.feature_engine import generate_eda_summary
        
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e'],
            'target': [0, 1, 0, 1, 0]
        })
        
        summary = generate_eda_summary(df)
        
        assert summary['shape'] == (5, 3)
        assert len(summary['columns']) == 3
        assert 'col1' in summary['column_info']
        assert summary['likely_target_column'] == 'target'
        
        print("[OK] EDA summary test passed")
        return True
    except Exception as e:
        print(f"[FAIL] EDA summary test failed: {str(e)}")
        return False

def test_settings():
    """Test settings configuration"""
    print("\n[TEST] Testing settings...")
    try:
        from src.config.settings import settings
        
        assert hasattr(settings, 'API_TITLE')
        assert hasattr(settings, 'MAX_FILE_SIZE')
        assert hasattr(settings, 'UPLOAD_DIR')
        
        print(f"[OK] Settings loaded: API_TITLE={settings.API_TITLE}")
        print(f"[OK] MAX_FILE_SIZE={settings.MAX_FILE_SIZE / (1024*1024):.0f}MB")
        print(f"[OK] UPLOAD_DIR={settings.UPLOAD_DIR}")
        return True
    except Exception as e:
        print(f"[FAIL] Settings test failed: {str(e)}")
        return False

def test_api_app():
    """Test API app creation"""
    print("\n[TEST] Testing API app...")
    try:
        from backend.main import app
        
        assert app is not None
        assert hasattr(app, 'routes')
        
        # Check if routes exist
        route_paths = [route.path for route in app.routes]
        assert "/health" in route_paths
        assert "/upload/" in route_paths
        assert "/feature-suggestions/" in route_paths
        
        print("[OK] API app test passed")
        print(f"[OK] Found {len(route_paths)} routes")
        return True
    except Exception as e:
        print(f"[FAIL] API app test failed: {str(e)}")
        return False

def main():
    """Run all quick tests"""
    print("=" * 60)
    print("Quick Test Suite - AutoFeatureGenie")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Settings", test_settings()))
    results.append(("EDA Summary", test_eda_summary()))
    results.append(("API App", test_api_app()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{test_name:20} {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Your project is ready.")
        print("\nNext steps:")
        print("1. Install pytest: pip install pytest pytest-cov httpx")
        print("2. Run full test suite: pytest")
        print("3. Start backend: uvicorn backend.main:app --reload")
        print("4. Start frontend: streamlit run frontend/app.py")
    else:
        print("\n[WARNING] Some tests failed. Please check the errors above.")
        print("Make sure you've installed all dependencies:")
        print("   pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

