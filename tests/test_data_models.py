"""
Unit tests for data models.

Tests WeatherData, MarketPriceData, and SmartInsight models.
Requirements: 1.1, 3.1, 5.1
"""

import pytest
from datetime import datetime
from src.models import (
    WeatherData,
    MarketPriceData,
    SmartInsight,
    APIError,
    WEATHER_TRANSLATIONS,
    translate_weather_description
)


class TestWeatherData:
    """Test WeatherData model."""
    
    def test_weather_data_creation(self):
        """Test creating a WeatherData instance."""
        now = datetime.now()
        weather = WeatherData(
            temperature=28.5,
            humidity=65,
            description="scattered clouds",
            description_marathi="विखुरलेले ढग",
            rain_probability=45.0,
            timestamp=now,
            location="Nashik"
        )
        
        assert weather.temperature == 28.5
        assert weather.humidity == 65
        assert weather.description == "scattered clouds"
        assert weather.description_marathi == "विखुरलेले ढग"
        assert weather.rain_probability == 45.0
        assert weather.timestamp == now
        assert weather.location == "Nashik"
    
    def test_weather_data_to_dict(self):
        """Test converting WeatherData to dictionary."""
        now = datetime.now()
        weather = WeatherData(
            temperature=28.5,
            humidity=65,
            description="scattered clouds",
            description_marathi="विखुरलेले ढग",
            rain_probability=45.0,
            timestamp=now,
            location="Nashik"
        )
        
        data = weather.to_dict()
        
        assert data['temperature'] == 28.5
        assert data['humidity'] == 65
        assert data['description'] == "scattered clouds"
        assert data['description_marathi'] == "विखुरलेले ढग"
        assert data['rain_probability'] == 45.0
        assert data['timestamp'] == now.isoformat()
        assert data['location'] == "Nashik"
    
    def test_weather_data_from_dict(self):
        """Test creating WeatherData from dictionary."""
        now = datetime.now()
        data = {
            'temperature': 28.5,
            'humidity': 65,
            'description': "scattered clouds",
            'description_marathi': "विखुरलेले ढग",
            'rain_probability': 45.0,
            'timestamp': now.isoformat(),
            'location': "Nashik"
        }
        
        weather = WeatherData.from_dict(data)
        
        assert weather.temperature == 28.5
        assert weather.humidity == 65
        assert weather.description == "scattered clouds"
        assert weather.description_marathi == "विखुरलेले ढग"
        assert weather.rain_probability == 45.0
        assert weather.timestamp == now
        assert weather.location == "Nashik"
    
    def test_weather_data_round_trip(self):
        """Test round-trip conversion: object -> dict -> object."""
        now = datetime.now()
        original = WeatherData(
            temperature=28.5,
            humidity=65,
            description="scattered clouds",
            description_marathi="विखुरलेले ढग",
            rain_probability=45.0,
            timestamp=now,
            location="Nashik"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = WeatherData.from_dict(data)
        
        # Verify all fields are preserved
        assert restored.temperature == original.temperature
        assert restored.humidity == original.humidity
        assert restored.description == original.description
        assert restored.description_marathi == original.description_marathi
        assert restored.rain_probability == original.rain_probability
        assert restored.timestamp == original.timestamp
        assert restored.location == original.location


class TestMarketPriceData:
    """Test MarketPriceData model."""
    
    def test_market_price_data_creation(self):
        """Test creating a MarketPriceData instance."""
        now = datetime.now()
        market_price = MarketPriceData(
            crop="Onion",
            price=2500.0,
            market_name="Nashik APMC",
            location="Nashik",
            timestamp=now
        )
        
        assert market_price.crop == "Onion"
        assert market_price.price == 2500.0
        assert market_price.market_name == "Nashik APMC"
        assert market_price.location == "Nashik"
        assert market_price.timestamp == now
    
    def test_market_price_data_to_dict(self):
        """Test converting MarketPriceData to dictionary."""
        now = datetime.now()
        market_price = MarketPriceData(
            crop="Onion",
            price=2500.0,
            market_name="Nashik APMC",
            location="Nashik",
            timestamp=now
        )
        
        data = market_price.to_dict()
        
        assert data['crop'] == "Onion"
        assert data['price'] == 2500.0
        assert data['market_name'] == "Nashik APMC"
        assert data['location'] == "Nashik"
        assert data['timestamp'] == now.isoformat()
    
    def test_market_price_data_from_dict(self):
        """Test creating MarketPriceData from dictionary."""
        now = datetime.now()
        data = {
            'crop': "Onion",
            'price': 2500.0,
            'market_name': "Nashik APMC",
            'location': "Nashik",
            'timestamp': now.isoformat()
        }
        
        market_price = MarketPriceData.from_dict(data)
        
        assert market_price.crop == "Onion"
        assert market_price.price == 2500.0
        assert market_price.market_name == "Nashik APMC"
        assert market_price.location == "Nashik"
        assert market_price.timestamp == now
    
    def test_market_price_data_round_trip(self):
        """Test round-trip conversion: object -> dict -> object."""
        now = datetime.now()
        original = MarketPriceData(
            crop="Onion",
            price=2500.0,
            market_name="Nashik APMC",
            location="Nashik",
            timestamp=now
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = MarketPriceData.from_dict(data)
        
        # Verify all fields are preserved
        assert restored.crop == original.crop
        assert restored.price == original.price
        assert restored.market_name == original.market_name
        assert restored.location == original.location
        assert restored.timestamp == original.timestamp


class TestSmartInsight:
    """Test SmartInsight model."""
    
    def test_smart_insight_creation(self):
        """Test creating a SmartInsight instance."""
        now = datetime.now()
        insight = SmartInsight(
            recommendation="लवकरच विक्री करा",
            recommendation_en="Sell soon",
            prophet_change=5.2,
            rain_probability=45.0,
            confidence="high",
            timestamp=now
        )
        
        assert insight.recommendation == "लवकरच विक्री करा"
        assert insight.recommendation_en == "Sell soon"
        assert insight.prophet_change == 5.2
        assert insight.rain_probability == 45.0
        assert insight.confidence == "high"
        assert insight.timestamp == now
    
    def test_smart_insight_to_dict(self):
        """Test converting SmartInsight to dictionary."""
        now = datetime.now()
        insight = SmartInsight(
            recommendation="लवकरच विक्री करा",
            recommendation_en="Sell soon",
            prophet_change=5.2,
            rain_probability=45.0,
            confidence="high",
            timestamp=now
        )
        
        data = insight.to_dict()
        
        assert data['recommendation'] == "लवकरच विक्री करा"
        assert data['recommendation_en'] == "Sell soon"
        assert data['prophet_change'] == 5.2
        assert data['rain_probability'] == 45.0
        assert data['confidence'] == "high"
        assert data['timestamp'] == now.isoformat()
    
    def test_smart_insight_from_dict(self):
        """Test creating SmartInsight from dictionary."""
        now = datetime.now()
        data = {
            'recommendation': "लवकरच विक्री करा",
            'recommendation_en': "Sell soon",
            'prophet_change': 5.2,
            'rain_probability': 45.0,
            'confidence': "high",
            'timestamp': now.isoformat()
        }
        
        insight = SmartInsight.from_dict(data)
        
        assert insight.recommendation == "लवकरच विक्री करा"
        assert insight.recommendation_en == "Sell soon"
        assert insight.prophet_change == 5.2
        assert insight.rain_probability == 45.0
        assert insight.confidence == "high"
        assert insight.timestamp == now
    
    def test_smart_insight_round_trip(self):
        """Test round-trip conversion: object -> dict -> object."""
        now = datetime.now()
        original = SmartInsight(
            recommendation="लवकरच विक्री करा",
            recommendation_en="Sell soon",
            prophet_change=5.2,
            rain_probability=45.0,
            confidence="high",
            timestamp=now
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = SmartInsight.from_dict(data)
        
        # Verify all fields are preserved
        assert restored.recommendation == original.recommendation
        assert restored.recommendation_en == original.recommendation_en
        assert restored.prophet_change == original.prophet_change
        assert restored.rain_probability == original.rain_probability
        assert restored.confidence == original.confidence
        assert restored.timestamp == original.timestamp


class TestAPIError:
    """Test APIError exception class."""
    
    def test_api_error_basic(self):
        """Test creating a basic APIError."""
        error = APIError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.api_name is None
        assert error.status_code is None
        assert str(error) == "API Error: Connection failed"
    
    def test_api_error_with_api_name(self):
        """Test APIError with API name."""
        error = APIError("Connection failed", api_name="Weather")
        
        assert error.message == "Connection failed"
        assert error.api_name == "Weather"
        assert error.status_code is None
        assert str(error) == "Weather API Error: Connection failed"
    
    def test_api_error_with_status_code(self):
        """Test APIError with status code."""
        error = APIError("Unauthorized", api_name="Agmarknet", status_code=401)
        
        assert error.message == "Unauthorized"
        assert error.api_name == "Agmarknet"
        assert error.status_code == 401
        assert str(error) == "Agmarknet API Error (401): Unauthorized"
    
    def test_api_error_can_be_raised(self):
        """Test that APIError can be raised and caught."""
        with pytest.raises(APIError) as exc_info:
            raise APIError("Test error", api_name="Weather", status_code=500)
        
        assert exc_info.value.message == "Test error"
        assert exc_info.value.api_name == "Weather"
        assert exc_info.value.status_code == 500


class TestWeatherTranslations:
    """Test weather translation functionality."""
    
    def test_weather_translations_dict_exists(self):
        """Test that WEATHER_TRANSLATIONS dictionary exists."""
        assert isinstance(WEATHER_TRANSLATIONS, dict)
        assert len(WEATHER_TRANSLATIONS) > 0
    
    def test_common_translations(self):
        """Test common weather translations."""
        assert WEATHER_TRANSLATIONS["clear sky"] == "स्वच्छ आकाश"
        assert WEATHER_TRANSLATIONS["rain"] == "पाऊस"
        assert WEATHER_TRANSLATIONS["scattered clouds"] == "विखुरलेले ढग"
        assert WEATHER_TRANSLATIONS["thunderstorm"] == "वादळ"
    
    def test_translate_weather_description_found(self):
        """Test translating a known weather description."""
        result = translate_weather_description("clear sky")
        assert result == "स्वच्छ आकाश"
    
    def test_translate_weather_description_case_insensitive(self):
        """Test that translation is case-insensitive."""
        result = translate_weather_description("Clear Sky")
        assert result == "स्वच्छ आकाश"
    
    def test_translate_weather_description_not_found(self):
        """Test translating an unknown weather description."""
        result = translate_weather_description("unknown weather")
        assert result == "unknown weather"  # Returns original if not found
