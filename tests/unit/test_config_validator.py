"""
Unit Tests for ConfigValidator

Tests the configuration validation functionality including:
- Validation of required secrets
- Safe retrieval of API keys
- Error handling for missing secrets
"""

import pytest
from unittest.mock import Mock, patch
from config.config_validator import ConfigValidator


class TestConfigValidator:
    """Test suite for ConfigValidator class."""
    
    def test_required_secrets_list(self):
        """Verify REQUIRED_SECRETS contains the expected API keys."""
        expected_secrets = ["openweather_api_key", "agmarknet_api_key"]
        assert ConfigValidator.REQUIRED_SECRETS == expected_secrets
    
    @patch('config.config_validator.st')
    def test_validate_secrets_all_present(self, mock_st):
        """Test validate_secrets returns True when all secrets are present."""
        # Mock st.secrets to contain all required keys
        mock_st.secrets = {
            "openweather_api_key": "test_weather_key",
            "agmarknet_api_key": "test_agmarknet_key"
        }
        
        result = ConfigValidator.validate_secrets()
        
        assert result is True
    
    @patch('config.config_validator.st')
    def test_validate_secrets_missing_one(self, mock_st):
        """Test validate_secrets returns False when one secret is missing."""
        # Mock st.secrets with only one key
        mock_st.secrets = {
            "openweather_api_key": "test_weather_key"
        }
        
        result = ConfigValidator.validate_secrets()
        
        assert result is False
    
    @patch('config.config_validator.st')
    def test_validate_secrets_all_missing(self, mock_st):
        """Test validate_secrets returns False when all secrets are missing."""
        # Mock st.secrets as empty
        mock_st.secrets = {}
        
        result = ConfigValidator.validate_secrets()
        
        assert result is False
    
    @patch('config.config_validator.st')
    def test_validate_secrets_extra_keys_present(self, mock_st):
        """Test validate_secrets returns True when extra keys are present."""
        # Mock st.secrets with required keys plus extras
        mock_st.secrets = {
            "openweather_api_key": "test_weather_key",
            "agmarknet_api_key": "test_agmarknet_key",
            "extra_key": "extra_value"
        }
        
        result = ConfigValidator.validate_secrets()
        
        assert result is True
    
    @patch('config.config_validator.st')
    def test_get_api_key_success(self, mock_st):
        """Test get_api_key successfully retrieves an existing key."""
        expected_key = "test_api_key_12345"
        mock_st.secrets = {
            "openweather_api_key": expected_key
        }
        
        result = ConfigValidator.get_api_key("openweather_api_key")
        
        assert result == expected_key
    
    @patch('config.config_validator.st')
    def test_get_api_key_missing(self, mock_st):
        """Test get_api_key raises KeyError for missing key."""
        mock_st.secrets = {}
        
        with pytest.raises(KeyError) as exc_info:
            ConfigValidator.get_api_key("nonexistent_key")
        
        assert "nonexistent_key" in str(exc_info.value)
        assert "not found in st.secrets" in str(exc_info.value)
    
    @patch('config.config_validator.st')
    def test_get_api_key_retrieves_correct_value(self, mock_st):
        """Test get_api_key retrieves the correct value when multiple keys exist."""
        mock_st.secrets = {
            "openweather_api_key": "weather_key_123",
            "agmarknet_api_key": "agmarknet_key_456"
        }
        
        weather_key = ConfigValidator.get_api_key("openweather_api_key")
        agmarknet_key = ConfigValidator.get_api_key("agmarknet_api_key")
        
        assert weather_key == "weather_key_123"
        assert agmarknet_key == "agmarknet_key_456"
    
    @patch('config.config_validator.st')
    def test_validate_secrets_case_sensitive(self, mock_st):
        """Test validate_secrets is case-sensitive for key names."""
        # Mock st.secrets with wrong case
        mock_st.secrets = {
            "OpenWeather_API_Key": "test_key",  # Wrong case
            "agmarknet_api_key": "test_key"
        }
        
        result = ConfigValidator.validate_secrets()
        
        # Should fail because exact key name doesn't match
        assert result is False
    
    @patch('config.config_validator.st')
    def test_get_api_key_empty_string_value(self, mock_st):
        """Test get_api_key returns empty string if that's the value."""
        mock_st.secrets = {
            "openweather_api_key": ""
        }
        
        result = ConfigValidator.get_api_key("openweather_api_key")
        
        # Should return the empty string (validation of non-empty is separate concern)
        assert result == ""
    
    @patch('config.config_validator.st')
    def test_validate_secrets_with_none_values(self, mock_st):
        """Test validate_secrets considers keys with None values as present."""
        mock_st.secrets = {
            "openweather_api_key": None,
            "agmarknet_api_key": "test_key"
        }
        
        result = ConfigValidator.validate_secrets()
        
        # Keys exist even if value is None
        assert result is True
