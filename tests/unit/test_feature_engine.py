"""Unit tests for feature_engine module"""
import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from backend.feature_engine import generate_eda_summary, suggest_features


class TestGenerateEDASummary:
    """Test cases for EDA summary generation"""
    
    def test_basic_eda_summary(self):
        """Test basic EDA summary generation"""
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
    
    def test_numeric_column_stats(self):
        """Test numeric column statistics"""
        df = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5]
        })
        
        summary = generate_eda_summary(df)
        col_info = summary['column_info']['numeric_col']
        
        assert 'mean' in col_info
        assert 'std' in col_info
        assert 'min' in col_info
        assert 'max' in col_info
        assert col_info['mean'] == 3.0
    
    def test_missing_values(self):
        """Test handling of missing values"""
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5]
        })
        
        summary = generate_eda_summary(df)
        assert summary['column_info']['col1']['missing_values'] == 1
    
    def test_no_target_column(self):
        """Test when no target column is detected"""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        summary = generate_eda_summary(df)
        assert summary['likely_target_column'] is None


class TestSuggestFeatures:
    """Test cases for feature suggestion"""
    
    @patch('backend.feature_engine.model')
    @patch('backend.feature_engine.rag')
    def test_successful_feature_suggestion(self, mock_rag, mock_model):
        """Test successful feature suggestion"""
        # Setup mocks
        mock_rag.search.return_value = ["domain context"]
        mock_response = MagicMock()
        mock_response.text = '[{"column": "test_feature", "idea": "test", "reason": "test", "code_snippet": "df[\'test\'] = 1"}]'
        mock_model.generate_content.return_value = mock_response
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({'col1': [1, 2, 3]})
            df.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            suggestions = suggest_features(test_file, domain="test")
            assert len(suggestions) > 0
            assert suggestions[0]['column'] == 'test_feature'
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    @patch('backend.feature_engine.model')
    @patch('backend.feature_engine.rag')
    def test_api_error_handling(self, mock_rag, mock_model):
        """Test error handling when API fails"""
        mock_rag.search.return_value = []
        mock_model.generate_content.side_effect = Exception("API Error")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({'col1': [1, 2, 3]})
            df.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            suggestions = suggest_features(test_file)
            assert len(suggestions) == 1
            assert 'error' in suggestions[0]
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    @patch('backend.feature_engine.model')
    @patch('backend.feature_engine.rag')
    def test_invalid_json_response(self, mock_rag, mock_model):
        """Test handling of invalid JSON response"""
        mock_rag.search.return_value = []
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"
        mock_model.generate_content.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({'col1': [1, 2, 3]})
            df.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            suggestions = suggest_features(test_file)
            assert len(suggestions) == 1
            assert 'error' in suggestions[0]
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

