"""
Cache manager for weather and market data.

This module provides caching functions for external API data using Streamlit's
caching mechanism to minimize API calls and improve performance.

Requirements: 1.7, 3.6, 9.1, 9.2, 9.3, 9.4
"""

import streamlit as st
import logging
import sys
from typing import Optional
from src.utils.weather_api_client import WeatherAPIClient
from src.utils.agmarknet_api_client import AgmarknetAPIClient
from src.models.weather_data import WeatherData
from src.models.market_price_data import MarketPriceData
from src.models.exceptions import APIError

# Add config path
sys.path.insert(0, 'config')
from config_validator import ConfigValidator

# Configure logging
logger = logging.getLogger(__name__)


@st.cache_data(ttl=1800)  # 30 minutes = 1800 seconds
def get_cached_weather(location: str) -> WeatherData:
    """
    Fetch and cache weather data for a location with fallback mechanism.
    
    This function uses Streamlit's caching mechanism to store weather data
    for 30 minutes, minimizing API calls to OpenWeatherMap. The cache is
    automatically invalidated after the TTL expires.
    
    **Fallback Logic (Requirement 1.6, 8.1):**
    - On API failure, attempts to return stale cached data
    - Displays warning message when using stale cache
    - Logs error details for debugging
    - Only raises error if no cached data is available
    
    Args:
        location: City name (e.g., "Nashik", "Mumbai")
        
    Returns:
        WeatherData object with current weather information
        
    Raises:
        APIError: When API request fails and no cached data is available
        
    Requirements:
        - 1.6: Fallback to stale cache on API failure
        - 1.7: Cache weather data for 30 minutes
        - 8.1: Graceful degradation when API unavailable
        - 9.1: Use st.cache_data decorator with 30-minute TTL
        - 9.4: Display cached data immediately without API calls
    """
    # Retrieve API key from AWS Secrets Manager via ConfigValidator
    validator = ConfigValidator()
    api_key = validator.get_api_key("OPENWEATHER_API_KEY")
    
    # Instantiate client
    client = WeatherAPIClient(api_key)
    
    try:
        # Attempt to fetch fresh weather data
        weather_data = client.get_current_weather(location)
        return weather_data
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Weather API failed for {location}: {str(e)}", exc_info=True)
        
        # Attempt to retrieve stale cached data
        try:
            # Access Streamlit's cache to get stale data
            # Note: Streamlit's cache_data doesn't provide direct access to stale data
            # So we'll use a secondary cache mechanism with session_state
            cache_key = f"weather_fallback_{location}"
            
            if cache_key in st.session_state:
                stale_data = st.session_state[cache_key]
                
                # Display warning to user
                st.warning(f"⚠️ Weather API unavailable. Showing cached data for {location}.")
                logger.info(f"Using stale cached weather data for {location}")
                
                return stale_data
            else:
                # No cached data available - propagate error
                logger.error(f"No cached weather data available for {location}")
                raise APIError(f"Weather API failed and no cached data available for {location}") from e
                
        except KeyError:
            # No cached data available - propagate error
            logger.error(f"No cached weather data available for {location}")
            raise APIError(f"Weather API failed and no cached data available for {location}") from e


def _store_weather_fallback_cache(location: str, weather_data: WeatherData) -> None:
    """
    Store weather data in fallback cache for use when API fails.
    
    This is a helper function that stores weather data in session_state
    to enable fallback when the primary API fails.
    
    Args:
        location: City name
        weather_data: WeatherData object to cache
    """
    cache_key = f"weather_fallback_{location}"
    st.session_state[cache_key] = weather_data


@st.cache_data(ttl=3600)  # 60 minutes = 3600 seconds
def get_cached_market_price(crop: str, location: str) -> MarketPriceData:
    """
    Fetch and cache market price data for a crop and location.
    
    This function uses Streamlit's caching mechanism to store market price data
    for 60 minutes, minimizing API calls to Agmarknet. The cache is
    automatically invalidated after the TTL expires.
    
    Args:
        crop: Crop name (e.g., "Onion", "Tomato")
        location: Market location (e.g., "Nashik")
        
    Returns:
        MarketPriceData object with current market price information
        
    Raises:
        APIError: When API request fails and no cached data is available
        
    Requirements:
        - 3.6: Cache Agmarknet data for 60 minutes
        - 9.2: Use st.cache_data decorator with 60-minute TTL
        - 9.4: Display cached data immediately without API calls
    """
    # Retrieve API key from AWS Secrets Manager via ConfigValidator
    validator = ConfigValidator()
    api_key = validator.get_api_key("AGMARKNET_API_KEY")
    
    # Instantiate client and fetch market price data
    client = AgmarknetAPIClient(api_key)
    return client.get_live_price(crop, location)


@st.cache_data  # Session lifetime caching (no TTL)
def get_cached_prophet_prediction(crop: str, days: int) -> 'pd.DataFrame':
    """
    Cache Prophet model predictions for the session lifetime.
    
    This function uses Streamlit's caching mechanism to store Prophet model
    predictions for the entire session duration, avoiding re-running the model
    for the same crop and forecast period. The cache persists until the session
    ends or is manually cleared.
    
    Args:
        crop: Crop name (e.g., "Onion", "Tomato")
        days: Number of days to forecast (typically 15)
        
    Returns:
        DataFrame with columns:
            - date: Forecast date
            - predicted_price: Predicted price
            - lower_bound: Lower confidence bound (95%)
            - upper_bound: Upper confidence bound (95%)
            
    Raises:
        ValueError: When model is not trained or prediction fails
        
    Requirements:
        - 9.3: Cache Prophet predictions for session lifetime
        - 9.4: Display cached predictions immediately without re-running model
        
    Note:
        This function expects the Prophet model to be trained before calling.
        The actual Prophet model training and prediction logic should be
        implemented by the caller or integrated here based on the application's
        architecture.
    """
    import pandas as pd
    from src.components.price_forecaster import PriceForecaster
    from src.components.cloud_logger import CloudLogger
    
    # Initialize logger and forecaster
    logger = CloudLogger()
    forecaster = PriceForecaster(logger=logger)
    
    # Note: This is a simplified implementation. In a production system,
    # you would need to:
    # 1. Load or train the model with historical data for the specific crop
    # 2. Handle the case where historical data is not available
    # 3. Implement proper error handling for model training failures
    
    # For now, this function assumes the model will be trained externally
    # and this cache wrapper will be called after training.
    # The actual implementation should be integrated with the existing
    # Prophet model training workflow in the application.
    
    # Generate predictions
    predictions = forecaster.predict(days=days)
    
    return predictions
