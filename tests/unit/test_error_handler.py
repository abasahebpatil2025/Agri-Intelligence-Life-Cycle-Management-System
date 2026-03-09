"""
Unit tests for ErrorHandler class.

Tests the centralized error handling functionality including API error handling,
configuration error handling, and ensuring API keys are never exposed in error messages.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from config.error_handler import ErrorHandler


class TestErrorHandler:
    """Test suite for ErrorHandler class."""
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_timeout(self, mock_logging, mock_st):
        """Test handling of API timeout errors."""
        # Arrange
        error = requests.Timeout("Connection timed out")
        api_name = "Weather"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.warning.assert_called_once()
        warning_message = mock_st.warning.call_args[0][0]
        assert "⏱️" in warning_message
        assert api_name in warning_message
        assert "cached data" in warning_message.lower()
        mock_logging.warning.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_connection_error(self, mock_logging, mock_st):
        """Test handling of API connection errors."""
        # Arrange
        error = requests.ConnectionError("Failed to establish connection")
        api_name = "Agmarknet"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.warning.assert_called_once()
        warning_message = mock_st.warning.call_args[0][0]
        assert "🔌" in warning_message
        assert api_name in warning_message
        assert "internet connection" in warning_message.lower()
        mock_logging.error.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_authentication_401(self, mock_logging, mock_st):
        """Test handling of API authentication errors (401)."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 401
        error = requests.HTTPError()
        error.response = mock_response
        api_name = "Weather"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.error.assert_called_once()
        error_message = mock_st.error.call_args[0][0]
        assert "🔑" in error_message
        assert api_name in error_message
        assert "authentication" in error_message.lower()
        mock_logging.error.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_rate_limit_429(self, mock_logging, mock_st):
        """Test handling of API rate limit errors (429)."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 429
        error = requests.HTTPError()
        error.response = mock_response
        api_name = "Agmarknet"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.warning.assert_called_once()
        warning_message = mock_st.warning.call_args[0][0]
        assert "⏳" in warning_message
        assert api_name in warning_message
        assert "rate limit" in warning_message.lower()
        mock_logging.warning.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_other_http_error(self, mock_logging, mock_st):
        """Test handling of other HTTP errors (e.g., 500, 503)."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        error = requests.HTTPError()
        error.response = mock_response
        api_name = "Weather"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.warning.assert_called_once()
        warning_message = mock_st.warning.call_args[0][0]
        assert "⚠️" in warning_message
        assert api_name in warning_message
        assert "500" in warning_message
        mock_logging.error.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_http_error_no_response(self, mock_logging, mock_st):
        """Test handling of HTTP errors without response object."""
        # Arrange
        error = requests.HTTPError()
        error.response = None
        api_name = "Weather"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.warning.assert_called_once()
        warning_message = mock_st.warning.call_args[0][0]
        assert "⚠️" in warning_message
        assert api_name in warning_message
        mock_logging.error.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_unexpected_error(self, mock_logging, mock_st):
        """Test handling of unexpected errors."""
        # Arrange
        error = ValueError("Unexpected error occurred")
        api_name = "Agmarknet"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert
        mock_st.warning.assert_called_once()
        warning_message = mock_st.warning.call_args[0][0]
        assert "❌" in warning_message
        assert "Unexpected error" in warning_message
        assert api_name in warning_message
        mock_logging.error.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_no_api_key_exposure(self, mock_logging, mock_st):
        """Test that API keys are never exposed in error messages."""
        # Arrange
        fake_api_key = "secret_api_key_12345"
        error = requests.HTTPError(f"Authentication failed with key {fake_api_key}")
        api_name = "Weather"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert - Check that API key is not in any displayed message
        if mock_st.error.called:
            error_message = mock_st.error.call_args[0][0]
            assert fake_api_key not in error_message
        if mock_st.warning.called:
            warning_message = mock_st.warning.call_args[0][0]
            assert fake_api_key not in warning_message
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_missing_secrets(self, mock_logging, mock_st):
        """Test handling of missing API keys configuration."""
        # Act
        ErrorHandler.handle_missing_secrets()
        
        # Assert
        mock_st.error.assert_called_once()
        error_message = mock_st.error.call_args[0][0]
        
        # Verify error message contains key information
        assert "🔑" in error_message
        assert "Configuration Error" in error_message
        assert "openweather_api_key" in error_message
        assert "agmarknet_api_key" in error_message
        assert ".streamlit/secrets.toml" in error_message
        
        # Verify application is stopped
        mock_st.stop.assert_called_once()
        
        # Verify error is logged
        mock_logging.error.assert_called_once()
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_missing_secrets_no_key_exposure(self, mock_logging, mock_st):
        """Test that handle_missing_secrets doesn't expose actual API keys."""
        # Act
        ErrorHandler.handle_missing_secrets()
        
        # Assert - Check that message only contains placeholder text
        error_message = mock_st.error.call_args[0][0]
        assert "your_openweather_api_key_here" in error_message
        assert "your_agmarknet_api_key_here" in error_message
        # Ensure no actual keys are present (this is a sanity check)
        assert "sk-" not in error_message  # Common API key prefix
        assert "Bearer" not in error_message  # Common auth header
    
    @patch('config.error_handler.st')
    @patch('config.error_handler.logging')
    def test_handle_api_error_logs_without_sensitive_data(self, mock_logging, mock_st):
        """Test that logging doesn't include sensitive information."""
        # Arrange
        error = requests.Timeout("Connection timed out")
        api_name = "Weather"
        
        # Act
        ErrorHandler.handle_api_error(error, api_name)
        
        # Assert - Verify logging was called
        assert mock_logging.warning.called or mock_logging.error.called
        
        # Check that log messages don't contain common API key patterns
        for call in mock_logging.warning.call_args_list + mock_logging.error.call_args_list:
            if call and len(call[0]) > 0:
                log_message = str(call[0][0])
                # Ensure no API key patterns in logs
                assert "api_key=" not in log_message.lower()
                assert "appid=" not in log_message.lower()
                assert "token=" not in log_message.lower()
