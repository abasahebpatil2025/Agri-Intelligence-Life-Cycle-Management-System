"""
Unit tests for Prophet prediction caching functionality.

Tests the get_cached_prophet_prediction function to ensure it properly
caches Prophet model predictions for the session lifetime.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta


class TestGetCachedProphetPrediction:
    """Tests for get_cached_prophet_prediction function."""
    
    @patch('src.utils.cache_manager.st')
    @patch('src.components.cloud_logger.CloudLogger')
    @patch('src.components.price_forecaster.PriceForecaster')
    def test_successful_prediction_generation(self, mock_forecaster_class, mock_logger_class, mock_st):
        """
        Test that predictions are successfully generated and cached.
        
        Verifies that the function:
        1. Initializes the PriceForecaster with a logger
        2. Calls the predict method with the correct days parameter
        3. Returns a DataFrame with the expected structure
        """
        # Mock the cache_data decorator to be a pass-through
        mock_st.cache_data = lambda **kwargs: lambda func: func
        
        # Create mock prediction data
        mock_predictions = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'predicted_price': [100.0, 105.0, 110.0],
            'lower_bound': [90.0, 95.0, 100.0],
            'upper_bound': [110.0, 115.0, 120.0]
        })
        
        # Mock the forecaster instance and its predict method
        mock_forecaster_instance = Mock()
        mock_forecaster_instance.predict = Mock(return_value=mock_predictions)
        mock_forecaster_class.return_value = mock_forecaster_instance
        
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger_class.return_value = mock_logger_instance
        
        # Import after mocking to avoid decorator issues
        from src.utils.cache_manager import get_cached_prophet_prediction
        
        # Call function
        result = get_cached_prophet_prediction("Onion", 3)
        
        # Verify logger was initialized
        mock_logger_class.assert_called_once()
        
        # Verify forecaster was initialized with logger
        mock_forecaster_class.assert_called_once_with(logger=mock_logger_instance)
        
        # Verify predict was called with correct days parameter
        mock_forecaster_instance.predict.assert_called_once_with(days=3)
        
        # Verify result structure
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'date' in result.columns
        assert 'predicted_price' in result.columns
        assert 'lower_bound' in result.columns
        assert 'upper_bound' in result.columns
        assert result['predicted_price'].iloc[0] == 100.0
    
    @patch('src.utils.cache_manager.st')
    @patch('src.components.cloud_logger.CloudLogger')
    @patch('src.components.price_forecaster.PriceForecaster')
    def test_prediction_with_different_days(self, mock_forecaster_class, mock_logger_class, mock_st):
        """
        Test that different forecast periods are handled correctly.
        
        Verifies that the function can generate predictions for different
        numbers of days (e.g., 7, 15, 30).
        """
        # Mock the cache_data decorator
        mock_st.cache_data = lambda **kwargs: lambda func: func
        
        # Create mock prediction data for 15 days
        dates = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15)]
        mock_predictions = pd.DataFrame({
            'date': dates,
            'predicted_price': [100.0 + i * 2 for i in range(15)],
            'lower_bound': [90.0 + i * 2 for i in range(15)],
            'upper_bound': [110.0 + i * 2 for i in range(15)]
        })
        
        # Mock the forecaster
        mock_forecaster_instance = Mock()
        mock_forecaster_instance.predict = Mock(return_value=mock_predictions)
        mock_forecaster_class.return_value = mock_forecaster_instance
        
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger_class.return_value = mock_logger_instance
        
        # Import after mocking
        from src.utils.cache_manager import get_cached_prophet_prediction
        
        # Call function with 15 days
        result = get_cached_prophet_prediction("Tomato", 15)
        
        # Verify predict was called with correct days parameter
        mock_forecaster_instance.predict.assert_called_once_with(days=15)
        
        # Verify result has correct length
        assert len(result) == 15
        assert result['predicted_price'].iloc[0] == 100.0
        assert result['predicted_price'].iloc[14] == 128.0
    
    @patch('src.utils.cache_manager.st')
    @patch('src.components.cloud_logger.CloudLogger')
    @patch('src.components.price_forecaster.PriceForecaster')
    def test_prediction_error_propagation(self, mock_forecaster_class, mock_logger_class, mock_st):
        """
        Test that errors from the forecaster are properly propagated.
        
        Verifies that when the PriceForecaster.predict() method raises
        an exception, it is propagated to the caller.
        """
        # Mock the cache_data decorator
        mock_st.cache_data = lambda **kwargs: lambda func: func
        
        # Mock the forecaster to raise an error
        mock_forecaster_instance = Mock()
        mock_forecaster_instance.predict = Mock(side_effect=ValueError("Model not trained"))
        mock_forecaster_class.return_value = mock_forecaster_instance
        
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger_class.return_value = mock_logger_instance
        
        # Import after mocking
        from src.utils.cache_manager import get_cached_prophet_prediction
        
        # Verify error is raised
        with pytest.raises(ValueError) as exc_info:
            get_cached_prophet_prediction("Potato", 15)
        
        assert "Model not trained" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
