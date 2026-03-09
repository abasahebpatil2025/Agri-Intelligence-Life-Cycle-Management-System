"""
Unit tests for WeatherAPIClient.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.utils.weather_api_client import WeatherAPIClient
from src.models.weather_data import WeatherData
from src.models.exceptions import APIError
import requests


class TestWeatherAPIClientInit:
    """Tests for WeatherAPIClient initialization."""
    
    def test_init_with_valid_api_key(self):
        """Test initialization with valid API key."""
        client = WeatherAPIClient("test_api_key_123")
        assert client.api_key == "test_api_key_123"
        assert client.BASE_URL == "https://api.openweathermap.org/data/2.5/weather"
        assert client.TIMEOUT == 10
    
    def test_init_with_empty_api_key(self):
        """Test initialization with empty API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            WeatherAPIClient("")
    
    def test_init_with_none_api_key(self):
        """Test initialization with None API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            WeatherAPIClient(None)


class TestWeatherAPIClientBuildRequestUrl:
    """Tests for _build_request_url method."""
    
    def test_build_request_url_basic(self):
        """Test URL construction with basic location."""
        client = WeatherAPIClient("test_key")
        url = client._build_request_url("Nashik")
        
        assert "https://api.openweathermap.org/data/2.5/weather?" in url
        assert "q=Nashik" in url
        assert "appid=test_key" in url
        assert "units=metric" in url
    
    def test_build_request_url_with_spaces(self):
        """Test URL construction with location containing spaces."""
        client = WeatherAPIClient("test_key")
        url = client._build_request_url("New York")
        
        assert "q=New York" in url


class TestWeatherAPIClientCalculateRainProbability:
    """Tests for _calculate_rain_probability method."""
    
    def test_rain_probability_with_rain_data(self):
        """Test rain probability calculation when rain data is present."""
        client = WeatherAPIClient("test_key")
        
        # 1mm of rain = 20% probability
        response = {"rain": {"1h": 1.0}}
        assert client._calculate_rain_probability(response) == 20.0
        
        # 2.5mm of rain = 50% probability
        response = {"rain": {"1h": 2.5}}
        assert client._calculate_rain_probability(response) == 50.0
        
        # 5mm of rain = 100% probability (capped)
        response = {"rain": {"1h": 5.0}}
        assert client._calculate_rain_probability(response) == 100.0
        
        # 10mm of rain = 100% probability (capped)
        response = {"rain": {"1h": 10.0}}
        assert client._calculate_rain_probability(response) == 100.0
    
    def test_rain_probability_with_high_clouds(self):
        """Test rain probability with high cloud coverage (>80%)."""
        client = WeatherAPIClient("test_key")
        
        response = {"clouds": {"all": 85}}
        assert client._calculate_rain_probability(response) == 70.0
        
        response = {"clouds": {"all": 95}}
        assert client._calculate_rain_probability(response) == 70.0
    
    def test_rain_probability_with_medium_clouds(self):
        """Test rain probability with medium cloud coverage (60-80%)."""
        client = WeatherAPIClient("test_key")
        
        response = {"clouds": {"all": 65}}
        assert client._calculate_rain_probability(response) == 50.0
        
        response = {"clouds": {"all": 75}}
        assert client._calculate_rain_probability(response) == 50.0
    
    def test_rain_probability_with_low_clouds(self):
        """Test rain probability with low cloud coverage (<60%)."""
        client = WeatherAPIClient("test_key")
        
        response = {"clouds": {"all": 30}}
        assert client._calculate_rain_probability(response) == 20.0
        
        response = {"clouds": {"all": 50}}
        assert client._calculate_rain_probability(response) == 20.0
    
    def test_rain_probability_no_data(self):
        """Test rain probability with no rain or cloud data."""
        client = WeatherAPIClient("test_key")
        
        response = {}
        assert client._calculate_rain_probability(response) == 20.0


class TestWeatherAPIClientParseResponse:
    """Tests for _parse_response method."""
    
    def test_parse_response_complete_data(self):
        """Test parsing complete API response."""
        client = WeatherAPIClient("test_key")
        
        response = {
            "main": {
                "temp": 28.5,
                "humidity": 65
            },
            "weather": [
                {"description": "scattered clouds"}
            ],
            "clouds": {"all": 40}
        }
        
        weather_data = client._parse_response(response, "Nashik")
        
        assert weather_data.temperature == 28.5
        assert weather_data.humidity == 65
        assert weather_data.description == "scattered clouds"
        assert weather_data.description_marathi == "विखुरलेले ढग"
        assert weather_data.rain_probability == 20.0
        assert weather_data.location == "Nashik"
        assert isinstance(weather_data.timestamp, datetime)
    
    def test_parse_response_with_rain_data(self):
        """Test parsing response with rain data."""
        client = WeatherAPIClient("test_key")
        
        response = {
            "main": {
                "temp": 22.0,
                "humidity": 80
            },
            "weather": [
                {"description": "light rain"}
            ],
            "rain": {"1h": 1.5},
            "clouds": {"all": 90}
        }
        
        weather_data = client._parse_response(response, "Mumbai")
        
        assert weather_data.temperature == 22.0
        assert weather_data.humidity == 80
        assert weather_data.description == "light rain"
        assert weather_data.description_marathi == "हलका पाऊस"
        assert weather_data.rain_probability == 30.0  # 1.5mm * 20 = 30%
        assert weather_data.location == "Mumbai"
    
    def test_parse_response_missing_main_field(self):
        """Test parsing response with missing main field raises KeyError."""
        client = WeatherAPIClient("test_key")
        
        response = {
            "weather": [{"description": "clear sky"}]
        }
        
        with pytest.raises(KeyError):
            client._parse_response(response, "Nashik")
    
    def test_parse_response_missing_weather_field(self):
        """Test parsing response with missing weather field raises KeyError."""
        client = WeatherAPIClient("test_key")
        
        response = {
            "main": {
                "temp": 28.5,
                "humidity": 65
            }
        }
        
        with pytest.raises(KeyError):
            client._parse_response(response, "Nashik")
    
    def test_parse_response_invalid_temperature_type(self):
        """Test parsing response with invalid temperature type."""
        client = WeatherAPIClient("test_key")
        
        response = {
            "main": {
                "temp": "not_a_number",
                "humidity": 65
            },
            "weather": [{"description": "clear sky"}],
            "clouds": {"all": 20}
        }
        
        with pytest.raises(ValueError):
            client._parse_response(response, "Nashik")


class TestWeatherAPIClientGetCurrentWeather:
    """Tests for get_current_weather method."""
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_success(self, mock_get):
        """Test successful weather data fetch."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {
                "temp": 28.5,
                "humidity": 65
            },
            "weather": [
                {"description": "clear sky"}
            ],
            "clouds": {"all": 10}
        }
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        weather_data = client.get_current_weather("Nashik")
        
        assert isinstance(weather_data, WeatherData)
        assert weather_data.temperature == 28.5
        assert weather_data.humidity == 65
        assert weather_data.description == "clear sky"
        assert weather_data.location == "Nashik"
        
        # Verify request was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "Nashik" in call_args[0][0]
        assert call_args[1]["timeout"] == 10
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.Timeout()
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("Nashik")
        
        assert "timeout" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Weather"
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_connection_error(self, mock_get):
        """Test handling of connection error."""
        mock_get.side_effect = requests.ConnectionError()
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("Nashik")
        
        assert "connection" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Weather"
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_401_unauthorized(self, mock_get):
        """Test handling of 401 unauthorized error (invalid API key)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("Nashik")
        
        assert exc_info.value.status_code == 401
        assert "invalid api key" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Weather"
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_404_not_found(self, mock_get):
        """Test handling of 404 not found error (invalid location)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("InvalidCity123")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Weather"
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_429_rate_limit(self, mock_get):
        """Test handling of 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("Nashik")
        
        assert exc_info.value.status_code == 429
        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Weather"
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_500_server_error(self, mock_get):
        """Test handling of 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("Nashik")
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.api_name == "Weather"
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_malformed_response(self, mock_get):
        """Test handling of malformed API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invalid": "data"
        }
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(APIError) as exc_info:
            client.get_current_weather("Nashik")
        
        assert "parse" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Weather"
    
    def test_get_current_weather_empty_location(self):
        """Test get_current_weather with empty location raises ValueError."""
        client = WeatherAPIClient("test_key")
        
        with pytest.raises(ValueError, match="Location cannot be empty"):
            client.get_current_weather("")
    
    @patch('src.utils.weather_api_client.requests.get')
    def test_get_current_weather_with_different_locations(self, mock_get):
        """Test weather fetch for different locations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 30.0, "humidity": 70},
            "weather": [{"description": "rain"}],
            "rain": {"1h": 2.0}
        }
        mock_get.return_value = mock_response
        
        client = WeatherAPIClient("test_key")
        
        # Test multiple locations
        locations = ["Nashik", "Mumbai", "Pune"]
        for location in locations:
            weather_data = client.get_current_weather(location)
            assert weather_data.location == location
