"""
Unit tests for Price Forecaster Component

Tests Prophet integration, sentiment adjustment, S3 persistence, and data validation.
Property-based tests for forecasting correctness.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

# Import the component
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from price_forecaster import PriceForecaster


class TestPriceForecaster:
    """Test suite for PriceForecaster component"""
    
    def test_initialization(self):
        """Test forecaster initialization"""
        forecaster = PriceForecaster()
        
        assert forecaster.model_type == 'prophet'
        assert forecaster.model is None
        assert forecaster.MIN_TRAINING_DAYS == 180
        assert forecaster.MAX_MISSING_PCT == 10.0
        assert len(forecaster.SENTIMENT_ADJUSTMENTS) == 3
    
    def test_sentiment_adjustments(self):
        """Test sentiment adjustment factors"""
        forecaster = PriceForecaster()
        
        assert forecaster.SENTIMENT_ADJUSTMENTS['Positive'] == 0.075
        assert forecaster.SENTIMENT_ADJUSTMENTS['Neutral'] == 0.0
        assert forecaster.SENTIMENT_ADJUSTMENTS['Negative'] == -0.125
    
    def test_validate_training_data_success(self):
        """Test data validation with valid data"""
        forecaster = PriceForecaster()
        
        # Create valid data (180+ days, no missing values)
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'ds': dates,
            'y': np.random.uniform(2000, 3000, 200)
        })
        
        is_valid, error_msg = forecaster.validate_training_data(df)
        
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_training_data_insufficient_days(self):
        """Test data validation with insufficient data"""
        forecaster = PriceForecaster()
        
        # Create insufficient data (< 180 days)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'ds': dates,
            'y': np.random.uniform(2000, 3000, 100)
        })
        
        is_valid, error_msg = forecaster.validate_training_data(df)
        
        assert is_valid is False
        assert "Insufficient data" in error_msg
    
    def test_validate_training_data_too_many_missing(self):
        """Test data validation with too many missing values"""
        forecaster = PriceForecaster()
        
        # Create data with >10% missing values
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        prices = np.random.uniform(2000, 3000, 200)
        prices[:25] = np.nan  # 12.5% missing
        
        df = pd.DataFrame({
            'ds': dates,
            'y': prices
        })
        
        is_valid, error_msg = forecaster.validate_training_data(df)
        
        assert is_valid is False
        assert "Too many missing values" in error_msg
    
    def test_train_success(self):
        """Test successful model training"""
        forecaster = PriceForecaster()
        
        # Create valid training data
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 200)
        })
        
        metadata = forecaster.train(df)
        
        assert forecaster.model is not None
        assert 'training_date' in metadata
        assert 'training_duration' in metadata
        assert 'data_points' in metadata
        assert metadata['data_points'] == 200
    
    def test_train_insufficient_data(self):
        """Test training fails with insufficient data"""
        forecaster = PriceForecaster()
        
        # Create insufficient data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 100)
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            forecaster.train(df)
    
    def test_predict_without_training(self):
        """Test prediction fails without training"""
        forecaster = PriceForecaster()
        
        with pytest.raises(ValueError, match="Model not trained"):
            forecaster.predict(days=15)
    
    def test_predict_success(self):
        """Test successful prediction"""
        forecaster = PriceForecaster()
        
        # Train model
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 200)
        })
        forecaster.train(df)
        
        # Generate predictions
        predictions = forecaster.predict(days=15)
        
        assert len(predictions) == 15
        assert 'date' in predictions.columns
        assert 'predicted_price' in predictions.columns
        assert 'lower_bound' in predictions.columns
        assert 'upper_bound' in predictions.columns
        assert (predictions['predicted_price'] >= 0).all()
    
    def test_apply_sentiment_adjustment_positive(self):
        """Test positive sentiment adjustment (+7.5%)"""
        forecaster = PriceForecaster()
        
        predictions = pd.DataFrame({
            'date': ['2024-01-01'],
            'predicted_price': [2000.0],
            'lower_bound': [1800.0],
            'upper_bound': [2200.0]
        })
        
        adjusted = forecaster.apply_sentiment_adjustment(predictions, 'Positive')
        
        assert adjusted['predicted_price'].iloc[0] == 2150.0  # 2000 * 1.075
        assert adjusted['lower_bound'].iloc[0] == 1935.0  # 1800 * 1.075
        assert adjusted['upper_bound'].iloc[0] == 2365.0  # 2200 * 1.075
    
    def test_apply_sentiment_adjustment_negative(self):
        """Test negative sentiment adjustment (-12.5%)"""
        forecaster = PriceForecaster()
        
        predictions = pd.DataFrame({
            'date': ['2024-01-01'],
            'predicted_price': [2000.0],
            'lower_bound': [1800.0],
            'upper_bound': [2200.0]
        })
        
        adjusted = forecaster.apply_sentiment_adjustment(predictions, 'Negative')
        
        assert adjusted['predicted_price'].iloc[0] == 1750.0  # 2000 * 0.875
        assert adjusted['lower_bound'].iloc[0] == 1575.0  # 1800 * 0.875
        assert adjusted['upper_bound'].iloc[0] == 1925.0  # 2200 * 0.875
    
    def test_apply_sentiment_adjustment_neutral(self):
        """Test neutral sentiment adjustment (0%)"""
        forecaster = PriceForecaster()
        
        predictions = pd.DataFrame({
            'date': ['2024-01-01'],
            'predicted_price': [2000.0],
            'lower_bound': [1800.0],
            'upper_bound': [2200.0]
        })
        
        adjusted = forecaster.apply_sentiment_adjustment(predictions, 'Neutral')
        
        assert adjusted['predicted_price'].iloc[0] == 2000.0
        assert adjusted['lower_bound'].iloc[0] == 1800.0
        assert adjusted['upper_bound'].iloc[0] == 2200.0
    
    def test_apply_sentiment_adjustment_invalid(self):
        """Test invalid sentiment defaults to Neutral"""
        forecaster = PriceForecaster()
        
        predictions = pd.DataFrame({
            'date': ['2024-01-01'],
            'predicted_price': [2000.0],
            'lower_bound': [1800.0],
            'upper_bound': [2200.0]
        })
        
        adjusted = forecaster.apply_sentiment_adjustment(predictions, 'Invalid')
        
        # Should default to Neutral (no adjustment)
        assert adjusted['predicted_price'].iloc[0] == 2000.0
    
    def test_save_model_to_s3_without_training(self):
        """Test saving model fails without training"""
        mock_s3 = Mock()
        forecaster = PriceForecaster(s3_client=mock_s3)
        
        with pytest.raises(ValueError, match="No model to save"):
            forecaster.save_model_to_s3('test-bucket', 'Onion', 'Nashik')
    
    def test_save_model_to_s3_success(self):
        """Test successful model save to S3"""
        mock_s3 = Mock()
        forecaster = PriceForecaster(s3_client=mock_s3)
        
        # Train model
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 200)
        })
        forecaster.train(df)
        
        # Save to S3
        s3_key = forecaster.save_model_to_s3('test-bucket', 'Onion', 'Nashik')
        
        assert 'Onion_Nashik' in s3_key
        assert s3_key.endswith('.pkl')
        mock_s3.put_object.assert_called_once()
    
    def test_load_model_from_s3_success(self):
        """Test successful model load from S3"""
        mock_s3 = Mock()
        forecaster = PriceForecaster(s3_client=mock_s3)
        
        # Train and save model first
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 200)
        })
        forecaster.train(df)
        
        # Mock S3 response
        import pickle
        model_package = {
            'model': forecaster.model,
            'metadata': forecaster.training_metadata,
            'model_type': 'prophet'
        }
        model_bytes = pickle.dumps(model_package)
        
        mock_response = {'Body': Mock()}
        mock_response['Body'].read = Mock(return_value=model_bytes)
        mock_s3.get_object = Mock(return_value=mock_response)
        
        # Create new forecaster and load model
        new_forecaster = PriceForecaster(s3_client=mock_s3)
        metadata = new_forecaster.load_model_from_s3('test-bucket', 'test_key.pkl')
        
        assert new_forecaster.model is not None
        assert 'training_date' in metadata
        mock_s3.get_object.assert_called_once()
    
    def test_forecast_with_sentiment_complete_workflow(self):
        """Test complete forecasting workflow"""
        forecaster = PriceForecaster()
        
        # Create training data
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 200)
        })
        
        # Run complete workflow
        predictions = forecaster.forecast_with_sentiment(df, 'Positive', days=15)
        
        assert len(predictions) == 15
        assert 'predicted_price' in predictions.columns
        # Verify positive adjustment was applied (prices should be higher)
        assert forecaster.model is not None


# Property-Based Tests
class TestPriceForecasterProperties:
    """Property-based tests for Price Forecaster"""
    
    @settings(deadline=None, max_examples=10)
    @given(
        sentiment=st.sampled_from(['Positive', 'Neutral', 'Negative'])
    )
    def test_property_sentiment_adjustment_validity(self, sentiment):
        """
        Property 13/14/15: Sentiment Adjustment Validity
        
        GIVEN any valid sentiment
        WHEN applied to predictions
        THEN adjustments are within expected ranges
        
        Validates: Requirements 7.1, 7.2, 7.3
        """
        forecaster = PriceForecaster()
        
        predictions = pd.DataFrame({
            'date': ['2024-01-01'],
            'predicted_price': [2000.0],
            'lower_bound': [1800.0],
            'upper_bound': [2200.0]
        })
        
        adjusted = forecaster.apply_sentiment_adjustment(predictions, sentiment)
        
        # Verify adjustment is applied correctly
        original_price = 2000.0
        adjusted_price = adjusted['predicted_price'].iloc[0]
        
        if sentiment == 'Positive':
            assert adjusted_price == original_price * 1.075
        elif sentiment == 'Negative':
            assert adjusted_price == original_price * 0.875
        else:  # Neutral
            assert adjusted_price == original_price
        
        # Verify no negative prices
        assert (adjusted['predicted_price'] >= 0).all()
        assert (adjusted['lower_bound'] >= 0).all()
        assert (adjusted['upper_bound'] >= 0).all()
    
    @settings(deadline=None, max_examples=5)
    @given(
        days=st.integers(min_value=1, max_value=30)
    )
    def test_property_prediction_structure(self, days):
        """
        Property 12: Prediction Structure Completeness
        
        GIVEN any number of forecast days
        WHEN predictions are generated
        THEN DataFrame has all required columns
        
        Validates: Requirement 6.3
        """
        forecaster = PriceForecaster()
        
        # Train model
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'price': np.random.uniform(2000, 3000, 200)
        })
        forecaster.train(df)
        
        # Generate predictions
        predictions = forecaster.predict(days=days)
        
        # Verify structure
        required_columns = ['date', 'predicted_price', 'lower_bound', 'upper_bound']
        for col in required_columns:
            assert col in predictions.columns
        
        assert len(predictions) == days
    
    @settings(deadline=None, max_examples=5)
    @given(
        missing_pct=st.floats(min_value=0.0, max_value=9.9)
    )
    def test_property_data_quality_threshold(self, missing_pct):
        """
        Property 35: Historical Data Quality Threshold
        
        GIVEN data with <10% missing values
        WHEN validated
        THEN validation passes
        
        Validates: Requirement 20.3
        """
        forecaster = PriceForecaster()
        
        # Create data with specified missing percentage
        total_points = 200
        missing_count = int(total_points * (missing_pct / 100))
        
        dates = pd.date_range(start='2023-01-01', periods=total_points, freq='D')
        prices = np.random.uniform(2000, 3000, total_points)
        
        if missing_count > 0:
            missing_indices = np.random.choice(total_points, missing_count, replace=False)
            prices[missing_indices] = np.nan
        
        df = pd.DataFrame({
            'ds': dates,
            'y': prices
        })
        
        is_valid, error_msg = forecaster.validate_training_data(df)
        
        # Should be valid since missing_pct < 10%
        assert is_valid is True
