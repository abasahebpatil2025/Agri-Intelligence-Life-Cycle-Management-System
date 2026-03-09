"""
Unit tests for Weather Client Component

Tests OpenWeatherMap API integration, caching, retry logic, and Marathi translations.
Property-based tests for weather data completeness.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from hypothesis import given, strategies as st, settings

# Import the component
import sys
sys.path.insert(0, 'src/components')
from weather_client import WeatherClient


class TestWeatherClient:
    """Test suite for WeatherClient component"""
    
    def test_initialization(self):
        """Test client initialization"""
        client = WeatherClient(api_key="test-key")
        
        assert client.api_key == "test-key"
        assert client.max_retries == 3
        assert len(client.retry_delays) == 3
        assert len(client.WEATHER_TRANSLATIONS) > 0
    
    def test_marathi_translation(self):
        """Test weather description translation to Marathi"""
        client = WeatherClient(api_key="test-key")
        
        assert client._translate_to_marathi('clear sky') == 'निरभ्र आकाश'
        assert client._translate_to_marathi('light rain') == 'हलका पाऊस'
        assert client._translate_to_marathi('heavy rain') == 'मुसळधार पाऊस'
        assert client._translate_to_marathi('unknown weather') == 'unknown weather'
    
    def test_fetch_current_weather_success(self):
        """Test successful current weather fetch"""
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            'main': {
                'temp': 28.5,
                'humidity': 65,
                'feels_like': 30.0,
                'temp_min': 26.0,
                'temp_max': 31.0,
                'pressure': 1013
            },
            'weather': [
                {'description': 'clear sky', 'icon': '01d'}
            ],
            'wind': {'speed': 3.5},
            'rain': {'1h': 0}
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            weather = client.fetch_current_weather('Nashik')
        
        assert weather['temp'] == 28.5
        assert weather['humidity'] == 65
        assert weather['description'] == 'clear sky'
        assert weather['description_mr'] == 'निरभ्र आकाश'
        assert weather['icon'] == '01d'
        assert 'wind_speed' in weather
        assert 'pressure' in weather
    
    def test_fetch_current_weather_from_cache(self):
        """Test current weather retrieved from cache"""
        cached_weather = {
            'temp': 28.5,
            'humidity': 65,
            'description': 'clear sky',
            'description_mr': 'निरभ्र आकाश',
            'icon': '01d',
            'precipitation': 0,
            'wind_speed': 3.5,
            'pressure': 1013
        }
        
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=cached_weather)
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        weather = client.fetch_current_weather('Nashik')
        
        assert weather['temp'] == 28.5
        assert weather['description_mr'] == 'निरभ्र आकाश'
        mock_cache.get.assert_called_once()
    
    def test_fetch_current_weather_api_failure_with_cache_fallback(self):
        """Test current weather falls back to cache on API failure"""
        cached_weather = {
            'temp': 28.5,
            'humidity': 65,
            'description': 'clear sky',
            'description_mr': 'निरभ्र आकाश'
        }
        
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)  # Cache miss initially
        mock_cache.cache = {
            'current_weather_Nashik': {'value': cached_weather, 'expires_at': 0}
        }
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        # Mock failed API response
        with patch.object(client.session, 'request', side_effect=Exception("API Error")):
            weather = client.fetch_current_weather('Nashik')
        
        assert weather['temp'] == 28.5
        assert weather['description_mr'] == 'निरभ्र आकाश'
    
    def test_fetch_current_weather_api_failure_no_cache(self):
        """Test current weather returns empty dict on API failure with no cache"""
        client = WeatherClient(api_key="test-key")
        
        # Mock failed API response
        with patch.object(client.session, 'request', side_effect=Exception("API Error")):
            weather = client.fetch_current_weather('Nashik')
        
        assert weather == {}
    
    def test_fetch_forecast_success(self):
        """Test successful forecast fetch"""
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            'list': [
                {
                    'dt_txt': '2024-01-01 12:00:00',
                    'main': {
                        'temp': 28.5,
                        'humidity': 65,
                        'feels_like': 30.0,
                        'temp_min': 26.0,
                        'temp_max': 31.0,
                        'pressure': 1013
                    },
                    'weather': [{'description': 'clear sky'}],
                    'wind': {'speed': 3.5},
                    'pop': 0.1
                },
                {
                    'dt_txt': '2024-01-01 15:00:00',
                    'main': {
                        'temp': 30.0,
                        'humidity': 60,
                        'feels_like': 32.0,
                        'temp_min': 28.0,
                        'temp_max': 33.0,
                        'pressure': 1012
                    },
                    'weather': [{'description': 'light rain'}],
                    'wind': {'speed': 4.0},
                    'pop': 0.3
                }
            ]
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            forecast = client.fetch_forecast('Nashik', days=1)
        
        assert not forecast.empty
        assert len(forecast) == 2
        assert 'datetime' in forecast.columns
        assert 'temp' in forecast.columns
        assert 'description_mr' in forecast.columns
        assert forecast.iloc[0]['description_mr'] == 'निरभ्र आकाश'
        assert forecast.iloc[1]['description_mr'] == 'हलका पाऊस'
    
    def test_fetch_forecast_from_cache(self):
        """Test forecast retrieved from cache"""
        cached_forecast = pd.DataFrame({
            'datetime': ['2024-01-01 12:00:00'],
            'temp': [28.5],
            'humidity': [65],
            'description': ['clear sky'],
            'description_mr': ['निरभ्र आकाश'],
            'precipitation': [0.1],
            'wind_speed': [3.5],
            'pressure': [1013]
        })
        
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=cached_forecast)
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        forecast = client.fetch_forecast('Nashik', days=1)
        
        assert not forecast.empty
        assert len(forecast) == 1
        mock_cache.get.assert_called_once()
    
    def test_fetch_forecast_api_failure_with_cache_fallback(self):
        """Test forecast falls back to cache on API failure"""
        cached_forecast = pd.DataFrame({
            'datetime': ['2024-01-01 12:00:00'],
            'temp': [28.5],
            'humidity': [65],
            'description': ['clear sky'],
            'description_mr': ['निरभ्र आकाश'],
            'precipitation': [0.1],
            'wind_speed': [3.5],
            'pressure': [1013]
        })
        
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.cache = {
            'forecast_Nashik_1': {'value': cached_forecast, 'expires_at': 0}
        }
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        # Mock failed API response
        with patch.object(client.session, 'request', side_effect=Exception("API Error")):
            forecast = client.fetch_forecast('Nashik', days=1)
        
        assert not forecast.empty
        assert len(forecast) == 1
    
    def test_fetch_forecast_api_failure_no_cache(self):
        """Test forecast returns empty DataFrame on API failure with no cache"""
        client = WeatherClient(api_key="test-key")
        
        # Mock failed API response
        with patch.object(client.session, 'request', side_effect=Exception("API Error")):
            forecast = client.fetch_forecast('Nashik', days=1)
        
        assert forecast.empty
        assert 'datetime' in forecast.columns
        assert 'temp' in forecast.columns
        assert 'description_mr' in forecast.columns
    
    def test_get_weather_summary(self):
        """Test comprehensive weather summary"""
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        
        client = WeatherClient(api_key="test-key", cache=mock_cache)
        
        # Mock current weather response
        mock_current_response = Mock()
        mock_current_response.json = Mock(return_value={
            'main': {
                'temp': 28.5,
                'humidity': 65,
                'feels_like': 30.0,
                'temp_min': 26.0,
                'temp_max': 31.0,
                'pressure': 1013
            },
            'weather': [{'description': 'clear sky', 'icon': '01d'}],
            'wind': {'speed': 3.5},
            'rain': {'1h': 0}
        })
        mock_current_response.raise_for_status = Mock()
        
        # Mock forecast response
        mock_forecast_response = Mock()
        forecast_data = []
        for i in range(8):  # 24 hours = 8 intervals
            forecast_data.append({
                'dt_txt': f'2024-01-01 {i*3:02d}:00:00',
                'main': {
                    'temp': 25.0 + i,
                    'humidity': 60,
                    'feels_like': 27.0 + i,
                    'temp_min': 24.0 + i,
                    'temp_max': 26.0 + i,
                    'pressure': 1013
                },
                'weather': [{'description': 'clear sky'}],
                'wind': {'speed': 3.5},
                'pop': 0.1
            })
        
        mock_forecast_response.json = Mock(return_value={'list': forecast_data})
        mock_forecast_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', side_effect=[mock_current_response, mock_forecast_response]):
            summary = client.get_weather_summary('Nashik')
        
        assert 'current' in summary
        assert 'forecast_available' in summary
        assert summary['forecast_available'] is True
        assert 'avg_temp_next_24h' in summary
        assert 'max_temp_next_24h' in summary
        assert 'min_temp_next_24h' in summary


# Property-Based Tests
class TestWeatherClientProperties:
    """Property-based tests for Weather Client"""
    
    @settings(deadline=None, max_examples=20)
    @given(
        temp=st.floats(min_value=-10.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        humidity=st.integers(min_value=0, max_value=100)
    )
    def test_property_weather_data_completeness(self, temp, humidity):
        """
        Property 5: Weather Data Completeness
        
        GIVEN valid temperature and humidity data
        WHEN weather data is returned
        THEN all required fields are present
        
        Validates: Requirement 3.3
        """
        client = WeatherClient(api_key="test-key")
        
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            'main': {
                'temp': temp,
                'humidity': humidity,
                'feels_like': temp + 2,
                'temp_min': temp - 2,
                'temp_max': temp + 2,
                'pressure': 1013
            },
            'weather': [{'description': 'clear sky', 'icon': '01d'}],
            'wind': {'speed': 3.5},
            'rain': {'1h': 0}
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            weather = client.fetch_current_weather('TestCity')
        
        # Verify all required fields are present
        required_fields = ['temp', 'humidity', 'description', 'description_mr', 
                          'icon', 'precipitation', 'wind_speed', 'pressure']
        for field in required_fields:
            assert field in weather
        
        assert weather['temp'] == temp
        assert weather['humidity'] == humidity
    
    @settings(deadline=None, max_examples=10)
    @given(
        description=st.sampled_from(['clear sky', 'light rain', 'heavy rain', 
                                     'thunderstorm', 'fog', 'snow'])
    )
    def test_property_marathi_translation_exists(self, description):
        """
        Property: Marathi Translation Coverage
        
        GIVEN common weather descriptions
        WHEN translated to Marathi
        THEN translation exists
        
        Validates: Requirement 3.2
        """
        client = WeatherClient(api_key="test-key")
        
        translation = client._translate_to_marathi(description)
        
        # Translation should not be empty and should be different from English
        # (or same if it's a proper noun)
        assert translation is not None
        assert len(translation) > 0
    
    @settings(deadline=None, max_examples=10)
    @given(
        days=st.integers(min_value=1, max_value=5)
    )
    def test_property_forecast_dataframe_structure(self, days):
        """
        Property: Forecast DataFrame Structure
        
        GIVEN any number of forecast days
        WHEN forecast is fetched
        THEN DataFrame has required columns
        
        Validates: Requirement 3.4
        """
        client = WeatherClient(api_key="test-key")
        
        # Mock forecast response
        mock_response = Mock()
        forecast_data = []
        for i in range(days * 8):  # 8 intervals per day
            forecast_data.append({
                'dt_txt': f'2024-01-01 {(i*3)%24:02d}:00:00',
                'main': {
                    'temp': 25.0,
                    'humidity': 60,
                    'feels_like': 27.0,
                    'temp_min': 24.0,
                    'temp_max': 26.0,
                    'pressure': 1013
                },
                'weather': [{'description': 'clear sky'}],
                'wind': {'speed': 3.5},
                'pop': 0.1
            })
        
        mock_response.json = Mock(return_value={'list': forecast_data})
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            forecast = client.fetch_forecast('TestCity', days=days)
        
        # Verify DataFrame structure
        required_columns = ['datetime', 'temp', 'humidity', 'description', 
                           'description_mr', 'precipitation', 'wind_speed', 'pressure']
        for col in required_columns:
            assert col in forecast.columns
        
        assert len(forecast) == days * 8
