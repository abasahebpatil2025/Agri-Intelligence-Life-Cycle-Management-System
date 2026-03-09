"""
Central Configuration Module

Provides application-wide constants and configuration settings.
Interfaces with SecretsManager for AWS credentials but does not store secrets.

This module serves as the single source of truth for:
- AWS service configuration
- DynamoDB table names
- IoT sensor thresholds
- Language settings
- Model identifiers
"""

from typing import Dict, Any


# ============================================================================
# AWS CONFIGURATION
# ============================================================================

class AWSConfig:
    """AWS service configuration constants."""
    
    # Default AWS region (can be overridden by secrets.toml)
    DEFAULT_REGION = "us-east-1"
    
    # Bedrock Model IDs
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    
    # Default model for chatbot
    DEFAULT_MODEL = CLAUDE_3_SONNET
    
    # S3 Configuration
    S3_BUCKET_PREFIX = "agri-intelligence"
    
    # CloudWatch Log Group
    LOG_GROUP_NAME = "/aws/agri-intelligence"


# ============================================================================
# DYNAMODB TABLE NAMES
# ============================================================================

class DynamoDBTables:
    """DynamoDB table name constants."""
    
    FARMER_PROFILES = "FarmerProfiles"
    PRICE_TRENDS = "PriceTrends"
    WEATHER_DATA = "WeatherData"
    SENSOR_READINGS = "SensorReadings"
    CHAT_HISTORY = "ChatHistory"
    
    @classmethod
    def get_all_tables(cls) -> list:
        """Return list of all table names."""
        return [
            cls.FARMER_PROFILES,
            cls.PRICE_TRENDS,
            cls.WEATHER_DATA,
            cls.SENSOR_READINGS,
            cls.CHAT_HISTORY
        ]


# ============================================================================
# IOT SENSOR SETTINGS
# ============================================================================

class IoTConfig:
    """IoT sensor threshold and configuration constants."""
    
    # Temperature thresholds (Celsius)
    TEMP_MIN = 15.0
    TEMP_MAX = 35.0
    TEMP_OPTIMAL_MIN = 20.0
    TEMP_OPTIMAL_MAX = 30.0
    
    # Humidity thresholds (percentage)
    HUMIDITY_MIN = 40.0
    HUMIDITY_MAX = 90.0
    HUMIDITY_OPTIMAL_MIN = 50.0
    HUMIDITY_OPTIMAL_MAX = 70.0
    
    # Sensor reading intervals (seconds)
    READING_INTERVAL = 300  # 5 minutes
    ALERT_CHECK_INTERVAL = 60  # 1 minute
    
    @classmethod
    def is_temperature_optimal(cls, temp: float) -> bool:
        """Check if temperature is in optimal range."""
        return cls.TEMP_OPTIMAL_MIN <= temp <= cls.TEMP_OPTIMAL_MAX
    
    @classmethod
    def is_humidity_optimal(cls, humidity: float) -> bool:
        """Check if humidity is in optimal range."""
        return cls.HUMIDITY_OPTIMAL_MIN <= humidity <= cls.HUMIDITY_OPTIMAL_MAX
    
    @classmethod
    def get_temperature_status(cls, temp: float) -> str:
        """Get temperature status message."""
        if temp < cls.TEMP_MIN:
            return "too_cold"
        elif temp > cls.TEMP_MAX:
            return "too_hot"
        elif cls.is_temperature_optimal(temp):
            return "optimal"
        else:
            return "acceptable"
    
    @classmethod
    def get_humidity_status(cls, humidity: float) -> str:
        """Get humidity status message."""
        if humidity < cls.HUMIDITY_MIN:
            return "too_dry"
        elif humidity > cls.HUMIDITY_MAX:
            return "too_humid"
        elif cls.is_humidity_optimal(humidity):
            return "optimal"
        else:
            return "acceptable"


# ============================================================================
# LANGUAGE SETTINGS
# ============================================================================

class LanguageConfig:
    """Language and localization constants."""
    
    DEFAULT_LANGUAGE = "mr"  # Marathi
    SUPPORTED_LANGUAGES = ["mr", "en", "hi"]  # Marathi, English, Hindi
    
    LANGUAGE_NAMES = {
        "mr": "मराठी",
        "en": "English",
        "hi": "हिन्दी"
    }


# ============================================================================
# API ENDPOINTS
# ============================================================================

class APIConfig:
    """External API endpoint constants."""
    
    # OpenWeatherMap
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_FORECAST_ENDPOINT = f"{OPENWEATHER_BASE_URL}/forecast"
    OPENWEATHER_CURRENT_ENDPOINT = f"{OPENWEATHER_BASE_URL}/weather"
    
    # Agmarknet
    AGMARKNET_BASE_URL = "https://api.data.gov.in/resource"
    AGMARKNET_PRICE_ENDPOINT = f"{AGMARKNET_BASE_URL}/9ef84268-d588-465a-a308-a864a43d0070"


# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

class AppConfig:
    """General application configuration."""
    
    APP_NAME = "Agri-Intelligence System"
    APP_NAME_MARATHI = "कृषी-बुद्धिमत्ता प्रणाली"
    VERSION = "1.0.0"
    
    # Cache settings
    CACHE_TTL = 3600  # 1 hour in seconds
    PRICE_CACHE_TTL = 1800  # 30 minutes
    WEATHER_CACHE_TTL = 1800  # 30 minutes
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # QR Code settings
    QR_CODE_SIZE = 10
    QR_CODE_BORDER = 4


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of all configuration settings.
    
    Returns:
        Dict containing all configuration values (excluding secrets)
    """
    return {
        "aws": {
            "default_region": AWSConfig.DEFAULT_REGION,
            "default_model": AWSConfig.DEFAULT_MODEL,
            "log_group": AWSConfig.LOG_GROUP_NAME
        },
        "dynamodb_tables": DynamoDBTables.get_all_tables(),
        "iot": {
            "temp_range": f"{IoTConfig.TEMP_MIN}-{IoTConfig.TEMP_MAX}°C",
            "humidity_range": f"{IoTConfig.HUMIDITY_MIN}-{IoTConfig.HUMIDITY_MAX}%",
            "reading_interval": f"{IoTConfig.READING_INTERVAL}s"
        },
        "language": {
            "default": LanguageConfig.DEFAULT_LANGUAGE,
            "supported": LanguageConfig.SUPPORTED_LANGUAGES
        },
        "app": {
            "name": AppConfig.APP_NAME,
            "version": AppConfig.VERSION,
            "cache_ttl": AppConfig.CACHE_TTL
        }
    }


if __name__ == "__main__":
    # Print configuration summary when run directly
    import json
    print("Configuration Summary:")
    print(json.dumps(get_config_summary(), indent=2))
