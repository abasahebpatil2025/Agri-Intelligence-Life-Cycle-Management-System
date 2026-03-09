"""
Unit tests for AgmarknetAPIClient.

Requirements: 3.1, 3.2, 3.5
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.utils.agmarknet_api_client import AgmarknetAPIClient
from src.models.market_price_data import MarketPriceData
from src.models.exceptions import APIError
import requests


class TestAgmarknetAPIClientInit:
    """Tests for AgmarknetAPIClient initialization."""
    
    def test_init_with_valid_api_key(self):
        """Test initialization with valid API key."""
        client = AgmarknetAPIClient("test_api_key_123")
        assert client.api_key == "test_api_key_123"
        assert client.BASE_URL == "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        assert client.TIMEOUT == 15
    
    def test_init_with_empty_api_key(self):
        """Test initialization with empty API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AgmarknetAPIClient("")
    
    def test_init_with_none_api_key(self):
        """Test initialization with None API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AgmarknetAPIClient(None)


class TestAgmarknetAPIClientBuildRequestParams:
    """Tests for _build_request_params method."""
    
    def test_build_request_params_basic(self):
        """Test parameter construction with basic crop and location."""
        client = AgmarknetAPIClient("test_key")
        params = client._build_request_params("Onion", "Nashik")
        
        assert params["api-key"] == "test_key"
        assert params["format"] == "json"
        assert params["filters[commodity]"] == "Onion"
        assert params["filters[market]"] == "Nashik"
        assert params["limit"] == "100"
    
    def test_build_request_params_different_crops(self):
        """Test parameter construction with different crops."""
        client = AgmarknetAPIClient("test_key")
        
        crops = ["Tomato", "Potato", "Wheat"]
        for crop in crops:
            params = client._build_request_params(crop, "Mumbai")
            assert params["filters[commodity]"] == crop


class TestAgmarknetAPIClientParseResponse:
    """Tests for _parse_response method."""
    
    def test_parse_response_with_modal_price(self):
        """Test parsing response with modal_price."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2500",
                    "arrival_date": "2024-01-15"
                }
            ]
        }
        
        market_data = client._parse_response(response, "Onion", "Nashik")
        
        assert market_data.crop == "Onion"
        assert market_data.price == 2500.0
        assert market_data.market_name == "Nashik APMC"
        assert market_data.location == "Nashik"
        assert isinstance(market_data.timestamp, datetime)
    
    def test_parse_response_with_max_price_fallback(self):
        """Test parsing response using max_price when modal_price unavailable."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Tomato",
                    "market": "Mumbai APMC",
                    "max_price": "3000",
                    "arrival_date": "2024-01-15"
                }
            ]
        }
        
        market_data = client._parse_response(response, "Tomato", "Mumbai")
        
        assert market_data.crop == "Tomato"
        assert market_data.price == 3000.0
        assert market_data.market_name == "Mumbai APMC"
    
    def test_parse_response_most_recent_price(self):
        """Test that most recent price is selected from multiple records."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2000",
                    "arrival_date": "2024-01-10"
                },
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2500",
                    "arrival_date": "2024-01-15"
                },
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2200",
                    "arrival_date": "2024-01-12"
                }
            ]
        }
        
        market_data = client._parse_response(response, "Onion", "Nashik")
        
        # Should select the most recent (2024-01-15)
        assert market_data.price == 2500.0
        assert market_data.timestamp.day == 15
    
    def test_parse_response_alternative_date_format(self):
        """Test parsing response with alternative date format (DD/MM/YYYY)."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2500",
                    "arrival_date": "15/01/2024"
                }
            ]
        }
        
        market_data = client._parse_response(response, "Onion", "Nashik")
        
        assert market_data.price == 2500.0
        assert market_data.timestamp.day == 15
        assert market_data.timestamp.month == 1
    
    def test_parse_response_no_records(self):
        """Test parsing response with no records raises APIError."""
        client = AgmarknetAPIClient("test_key")
        
        response = {"records": []}
        
        with pytest.raises(APIError) as exc_info:
            client._parse_response(response, "Onion", "Nashik")
        
        assert "No market data available" in str(exc_info.value)
        assert exc_info.value.api_name == "Agmarknet"
    
    def test_parse_response_missing_records_field(self):
        """Test parsing response without records field raises APIError."""
        client = AgmarknetAPIClient("test_key")
        
        response = {"status": "success"}
        
        with pytest.raises(APIError) as exc_info:
            client._parse_response(response, "Onion", "Nashik")
        
        assert "No market data available" in str(exc_info.value)
    
    def test_parse_response_no_valid_dates(self):
        """Test parsing response with no valid dates raises APIError."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2500",
                    "arrival_date": "invalid-date"
                }
            ]
        }
        
        with pytest.raises(APIError) as exc_info:
            client._parse_response(response, "Onion", "Nashik")
        
        assert "No valid date records found" in str(exc_info.value)
    
    def test_parse_response_no_valid_price(self):
        """Test parsing response with no valid price raises APIError."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "",
                    "max_price": "",
                    "arrival_date": "2024-01-15"
                }
            ]
        }
        
        with pytest.raises(APIError) as exc_info:
            client._parse_response(response, "Onion", "Nashik")
        
        assert "No valid price data found" in str(exc_info.value)
    
    def test_parse_response_market_name_fallback(self):
        """Test that location is used as fallback when market name missing."""
        client = AgmarknetAPIClient("test_key")
        
        response = {
            "records": [
                {
                    "commodity": "Onion",
                    "modal_price": "2500",
                    "arrival_date": "2024-01-15"
                }
            ]
        }
        
        market_data = client._parse_response(response, "Onion", "Nashik")
        
        assert market_data.market_name == "Nashik"


class TestAgmarknetAPIClientGetLivePrice:
    """Tests for get_live_price method."""
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_success(self, mock_get):
        """Test successful market price fetch."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "commodity": "Onion",
                    "market": "Nashik APMC",
                    "modal_price": "2500",
                    "arrival_date": "2024-01-15"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = AgmarknetAPIClient("test_key")
        market_data = client.get_live_price("Onion", "Nashik")
        
        assert isinstance(market_data, MarketPriceData)
        assert market_data.crop == "Onion"
        assert market_data.price == 2500.0
        assert market_data.location == "Nashik"
        
        # Verify request was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 15
        assert "params" in call_args[1]
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.Timeout()
        
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_live_price("Onion", "Nashik")
        
        assert "timeout" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Agmarknet"
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_connection_error(self, mock_get):
        """Test handling of connection error."""
        mock_get.side_effect = requests.ConnectionError()
        
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_live_price("Onion", "Nashik")
        
        assert "connection" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Agmarknet"
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_401_unauthorized(self, mock_get):
        """Test handling of 401 unauthorized error (invalid API key)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_live_price("Onion", "Nashik")
        
        assert exc_info.value.status_code == 401
        assert "invalid api key" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Agmarknet"
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_429_rate_limit(self, mock_get):
        """Test handling of 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_live_price("Onion", "Nashik")
        
        assert exc_info.value.status_code == 429
        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Agmarknet"
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_500_server_error(self, mock_get):
        """Test handling of 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_live_price("Onion", "Nashik")
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.api_name == "Agmarknet"
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_no_data_available(self, mock_get):
        """Test handling when no data available for crop/location."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"records": []}
        mock_get.return_value = mock_response
        
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_live_price("Onion", "Nashik")
        
        assert "No market data available" in str(exc_info.value)
        assert exc_info.value.api_name == "Agmarknet"
    
    def test_get_live_price_empty_crop(self):
        """Test get_live_price with empty crop raises ValueError."""
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(ValueError, match="Crop cannot be empty"):
            client.get_live_price("", "Nashik")
    
    def test_get_live_price_empty_location(self):
        """Test get_live_price with empty location raises ValueError."""
        client = AgmarknetAPIClient("test_key")
        
        with pytest.raises(ValueError, match="Location cannot be empty"):
            client.get_live_price("Onion", "")
    
    @patch('src.utils.agmarknet_api_client.requests.get')
    def test_get_live_price_with_different_crops(self, mock_get):
        """Test price fetch for different crops."""
        def mock_response_factory(crop):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "records": [
                    {
                        "commodity": crop,
                        "market": "Test Market",
                        "modal_price": "1000",
                        "arrival_date": "2024-01-15"
                    }
                ]
            }
            return mock_response
        
        client = AgmarknetAPIClient("test_key")
        
        # Test multiple crops
        crops = ["Onion", "Tomato", "Potato"]
        for crop in crops:
            mock_get.return_value = mock_response_factory(crop)
            market_data = client.get_live_price(crop, "Nashik")
            assert market_data.crop == crop
