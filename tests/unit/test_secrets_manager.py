"""
Unit tests for Secrets Manager Component

Tests credential retrieval and validation logic.
Property-based tests for missing credential error handling.
"""

import pytest
from unittest.mock import patch
from hypothesis import given, strategies as st

# Import the component
import sys
sys.path.insert(0, 'src/components')
from secrets_manager import SecretsManager, MissingCredentialError


class TestSecretsManager:
    """Test suite for SecretsManager component"""
    
    @patch('secrets_manager.st')
    def test_get_aws_credentials_success(self, mock_st):
        """Test successful AWS credentials retrieval"""
        mock_st.secrets = {
            "aws": {
                "AWS_ACCESS_KEY": "test-access-key",
                "AWS_SECRET_KEY": "test-secret-key",
                "AWS_REGION": "us-east-1"
            },
            "api_keys": {
                "OPENWEATHER_API_KEY": "test-weather-key",
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        manager = SecretsManager()
        access_key, secret_key = manager.get_aws_credentials()
        
        assert access_key == "test-access-key"
        assert secret_key == "test-secret-key"
    
    @patch('secrets_manager.st')
    def test_get_openweather_key_success(self, mock_st):
        """Test successful OpenWeatherMap API key retrieval"""
        mock_st.secrets = {
            "aws": {
                "AWS_ACCESS_KEY": "test-access-key",
                "AWS_SECRET_KEY": "test-secret-key"
            },
            "api_keys": {
                "OPENWEATHER_API_KEY": "test-weather-key",
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        manager = SecretsManager()
        api_key = manager.get_openweather_key()
        
        assert api_key == "test-weather-key"
    
    @patch('secrets_manager.st')
    def test_get_agmarknet_key_success(self, mock_st):
        """Test successful Agmarknet API key retrieval"""
        mock_st.secrets = {
            "aws": {
                "AWS_ACCESS_KEY": "test-access-key",
                "AWS_SECRET_KEY": "test-secret-key"
            },
            "api_keys": {
                "OPENWEATHER_API_KEY": "test-weather-key",
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        manager = SecretsManager()
        api_key = manager.get_agmarknet_key()
        
        assert api_key == "test-agmark-key"
    
    @patch('secrets_manager.st')
    def test_missing_aws_credentials(self, mock_st):
        """Test error when AWS credentials are missing"""
        mock_st.secrets = {
            "api_keys": {
                "OPENWEATHER_API_KEY": "test-weather-key",
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        with pytest.raises(MissingCredentialError) as exc_info:
            SecretsManager()
        
        assert "AWS credentials not found" in str(exc_info.value)
    
    @patch('secrets_manager.st')
    def test_missing_openweather_key(self, mock_st):
        """Test error when OpenWeatherMap API key is missing"""
        mock_st.secrets = {
            "aws": {
                "AWS_ACCESS_KEY": "test-access-key",
                "AWS_SECRET_KEY": "test-secret-key"
            },
            "api_keys": {
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        with pytest.raises(MissingCredentialError) as exc_info:
            SecretsManager()
        
        assert "OpenWeatherMap API key not found" in str(exc_info.value)
    
    @patch('secrets_manager.st')
    def test_validate_credentials_all_present(self, mock_st):
        """Test validation passes when all credentials are present"""
        mock_st.secrets = {
            "aws": {
                "AWS_ACCESS_KEY": "test-access-key",
                "AWS_SECRET_KEY": "test-secret-key"
            },
            "api_keys": {
                "OPENWEATHER_API_KEY": "test-weather-key",
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        manager = SecretsManager()
        result = manager.validate_credentials()
        
        assert result["aws_credentials"] is True
        assert result["openweather_key"] is True
        assert result["agmarknet_key"] is True


# Property-Based Tests
class TestSecretsManagerProperties:
    """Property-based tests for Secrets Manager"""
    
    @given(
        access_key=st.text(min_size=1, max_size=100),
        secret_key=st.text(min_size=1, max_size=100)
    )
    @patch('secrets_manager.st')
    def test_property_aws_credentials_roundtrip(self, mock_st, access_key, secret_key):
        """
        Property 1: Missing Credential Error Handling
        
        GIVEN any non-empty AWS credentials
        WHEN stored in secrets and retrieved
        THEN the retrieved values match the stored values
        
        Validates: Requirement 1.5
        """
        mock_st.secrets = {
            "aws": {
                "AWS_ACCESS_KEY": access_key,
                "AWS_SECRET_KEY": secret_key
            },
            "api_keys": {
                "OPENWEATHER_API_KEY": "test-weather-key",
                "AGMARKNET_API_KEY": "test-agmark-key"
            }
        }
        
        manager = SecretsManager()
        retrieved_access, retrieved_secret = manager.get_aws_credentials()
        
        assert retrieved_access == access_key
        assert retrieved_secret == secret_key
    
    @patch('secrets_manager.st')
    def test_property_missing_credential_raises_error(self, mock_st):
        """
        Property 1: Missing Credential Error Handling
        
        GIVEN missing credentials in any combination
        WHEN SecretsManager is initialized
        THEN MissingCredentialError is raised with descriptive message
        
        Validates: Requirement 1.5
        """
        mock_st.secrets = {}
        
        with pytest.raises(MissingCredentialError) as exc_info:
            SecretsManager()
        
        error_message = str(exc_info.value)
        assert "Missing required credentials" in error_message
        assert len(error_message) > 50
