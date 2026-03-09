"""
Bug Condition Exploration Test for Secrets Case Sensitivity Fix

This test demonstrates the bug where ConfigValidator fails to find secrets
when they exist with different casing (uppercase vs lowercase).

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
The test encodes the EXPECTED behavior (case-insensitive lookup).
When the fix is implemented, this test will pass, confirming the bug is fixed.

**Validates: Requirements 2.1, 2.2, 2.3**
"""

import pytest
from unittest.mock import patch
from hypothesis import given, strategies as st, settings
from config.config_validator import ConfigValidator


class TestBugConditionExploration:
    """
    Bug Condition Exploration Tests
    
    These tests demonstrate the bug by mocking st.secrets with UPPERCASE keys
    while the code expects lowercase keys. The tests encode the EXPECTED behavior
    (case-insensitive lookup should work), so they will FAIL on unfixed code.
    """
    
    @patch('config.config_validator.st')
    def test_validate_secrets_with_uppercase_keys(self, mock_st):
        """
        Property 1: Bug Condition - Case-Insensitive Secret Lookup
        
        Test that validate_secrets() returns True when secrets exist with
        uppercase keys but lowercase keys are expected.
        
        EXPECTED ON UNFIXED CODE: This test will FAIL because validate_secrets()
        performs case-sensitive lookup and won't find OPENWEATHER_API_KEY when
        looking for openweather_api_key.
        
        EXPECTED AFTER FIX: This test will PASS because validate_secrets() will
        use case-insensitive fallback logic.
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Mock st.secrets with UPPERCASE keys (as they appear in secrets.toml)
        mock_st.secrets = {
            "OPENWEATHER_API_KEY": "test_weather_key_123",
            "AGMARKNET_API_KEY": "test_agmarknet_key_456"
        }
        
        # Call validate_secrets() which expects lowercase keys
        result = ConfigValidator.validate_secrets()
        
        # EXPECTED BEHAVIOR: Should return True (secrets exist, just different case)
        # UNFIXED CODE: Returns False (case-sensitive lookup fails)
        assert result is True, (
            "validate_secrets() should return True when secrets exist with "
            "uppercase keys, even though REQUIRED_SECRETS has lowercase keys. "
            "This test FAILS on unfixed code (confirming the bug) and PASSES "
            "after implementing case-insensitive lookup."
        )
    
    @patch('config.config_validator.st')
    def test_get_api_key_with_uppercase_variant(self, mock_st):
        """
        Property 1: Bug Condition - Case-Insensitive Secret Lookup
        
        Test that get_api_key() successfully retrieves a secret when the
        uppercase variant exists but lowercase key is requested.
        
        EXPECTED ON UNFIXED CODE: This test will FAIL with KeyError because
        get_api_key() performs direct dictionary access without case fallback.
        
        EXPECTED AFTER FIX: This test will PASS because get_api_key() will
        try uppercase variant as fallback.
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Mock st.secrets with UPPERCASE keys
        mock_st.secrets = {
            "OPENWEATHER_API_KEY": "weather_secret_xyz",
            "AGMARKNET_API_KEY": "agmarknet_secret_abc"
        }
        
        # Try to retrieve with lowercase key name (as code expects)
        # EXPECTED BEHAVIOR: Should return the value from uppercase key
        # UNFIXED CODE: Raises KeyError
        weather_key = ConfigValidator.get_api_key("openweather_api_key")
        agmarknet_key = ConfigValidator.get_api_key("agmarknet_api_key")
        
        assert weather_key == "weather_secret_xyz", (
            "get_api_key() should retrieve value from OPENWEATHER_API_KEY "
            "when called with lowercase 'openweather_api_key'. "
            "This test FAILS on unfixed code (KeyError) and PASSES after fix."
        )
        assert agmarknet_key == "agmarknet_secret_abc", (
            "get_api_key() should retrieve value from AGMARKNET_API_KEY "
            "when called with lowercase 'agmarknet_api_key'. "
            "This test FAILS on unfixed code (KeyError) and PASSES after fix."
        )
    
    @patch('config.config_validator.st')
    def test_mixed_case_scenario(self, mock_st):
        """
        Property 1: Bug Condition - Case-Insensitive Secret Lookup
        
        Test a mixed scenario where one secret has exact case match and
        another has uppercase variant.
        
        EXPECTED ON UNFIXED CODE: Partial failure - exact match works but
        uppercase variant fails.
        
        EXPECTED AFTER FIX: Both should work.
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Mock st.secrets with mixed casing
        mock_st.secrets = {
            "openweather_api_key": "exact_match_key",  # Exact match
            "AGMARKNET_API_KEY": "uppercase_key"       # Uppercase variant
        }
        
        # validate_secrets() should return True (both secrets exist in some form)
        result = ConfigValidator.validate_secrets()
        assert result is True, (
            "validate_secrets() should return True when secrets exist with "
            "mixed casing (one exact match, one uppercase variant)."
        )
        
        # Both get_api_key() calls should succeed
        weather_key = ConfigValidator.get_api_key("openweather_api_key")
        agmarknet_key = ConfigValidator.get_api_key("agmarknet_api_key")
        
        assert weather_key == "exact_match_key"
        assert agmarknet_key == "uppercase_key"


class TestBugConditionPropertyBased:
    """
    Property-Based Bug Condition Exploration
    
    Uses Hypothesis to generate various case combinations and verify
    the expected behavior (case-insensitive lookup).
    """
    
    @given(
        weather_key_value=st.text(min_size=1, max_size=50),
        agmarknet_key_value=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50)
    @patch('config.config_validator.st')
    def test_property_uppercase_secrets_should_validate(
        self, mock_st, weather_key_value, agmarknet_key_value
    ):
        """
        Property 1: Bug Condition - Case-Insensitive Secret Lookup
        
        Property-based test: For ANY secret values, when secrets exist with
        uppercase keys, validate_secrets() should return True.
        
        This test generates many random secret values and verifies the
        expected behavior across all of them.
        
        EXPECTED ON UNFIXED CODE: All test cases FAIL (validate_secrets returns False)
        EXPECTED AFTER FIX: All test cases PASS (validate_secrets returns True)
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Mock st.secrets with UPPERCASE keys and generated values
        mock_st.secrets = {
            "OPENWEATHER_API_KEY": weather_key_value,
            "AGMARKNET_API_KEY": agmarknet_key_value
        }
        
        # validate_secrets() should return True regardless of the actual values
        result = ConfigValidator.validate_secrets()
        
        assert result is True, (
            f"validate_secrets() should return True when secrets exist with "
            f"uppercase keys. Failed with values: weather={weather_key_value!r}, "
            f"agmarknet={agmarknet_key_value!r}"
        )
    
    @given(
        key_value=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50)
    @patch('config.config_validator.st')
    def test_property_get_api_key_uppercase_variant(self, mock_st, key_value):
        """
        Property 1: Bug Condition - Case-Insensitive Secret Lookup
        
        Property-based test: For ANY secret value, when a secret exists with
        uppercase key, get_api_key() with lowercase key should retrieve it.
        
        EXPECTED ON UNFIXED CODE: All test cases FAIL (KeyError raised)
        EXPECTED AFTER FIX: All test cases PASS (value retrieved successfully)
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        # Mock st.secrets with UPPERCASE key
        mock_st.secrets = {
            "OPENWEATHER_API_KEY": key_value
        }
        
        # get_api_key() with lowercase should retrieve the value
        result = ConfigValidator.get_api_key("openweather_api_key")
        
        assert result == key_value, (
            f"get_api_key('openweather_api_key') should retrieve value from "
            f"OPENWEATHER_API_KEY. Expected {key_value!r}, got {result!r}"
        )
