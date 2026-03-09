"""
Weather Market API Integration Module

This module provides the main integration logic for combining weather data,
market prices, and Prophet predictions to generate Smart AI Insights.

Requirements: All requirements (1-10)
"""

import streamlit as st
import sys
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Add paths
sys.path.insert(0, 'src/components')
sys.path.insert(0, 'src/models')
sys.path.insert(0, 'src/utils')
sys.path.insert(0, 'config')

from src.models.weather_data import WeatherData
from src.models.market_price_data import MarketPriceData
from src.models.smart_insight import SmartInsight
from src.components.rain_alert_evaluator import RainAlertEvaluator
from src.components.price_comparison_calculator import PriceComparisonCalculator
from src.components.smart_insight_generator import SmartInsightGenerator
from src.components.ui_components import (
    render_weather_display,
    render_market_comparison,
    render_smart_insight,
    render_location_selector
)
from src.utils.cache_manager import get_cached_weather, get_cached_market_price
from config.config_validator import ConfigValidator
from config.error_handler import ErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherMarketIntegration:
    """
    Main integration class for weather and market data features.
    
    This class orchestrates the integration of:
    - Weather data from OpenWeatherMap API
    - Market prices from Agmarknet API
    - Prophet ML predictions
    - Smart AI Insight generation
    """
    
    def __init__(self):
        """Initialize integration components"""
        self.rain_evaluator = RainAlertEvaluator()
        self.price_calculator = PriceComparisonCalculator()
        self.insight_generator = SmartInsightGenerator()
        self.error_handler = ErrorHandler()
    
    def render_weather_section(self, location: str) -> Optional[WeatherData]:
        """
        Render weather section with data fetching and error handling.
        
        Args:
            location: City name for weather data
            
        Returns:
            WeatherData object if successful, None otherwise
        """
        st.subheader("🌤️ Current Weather / सध्याचे हवामान")
        
        try:
            # Fetch weather data with caching (includes fallback logic)
            weather_data = get_cached_weather(location)
            
            # Store in fallback cache for future use if API fails
            from src.utils.cache_manager import _store_weather_fallback_cache
            _store_weather_fallback_cache(location, weather_data)
            
            # Render weather display
            render_weather_display(weather_data)
            
            # Log successful fetch
            logger.info(f"Weather data fetched successfully for {location}")
            
            return weather_data
            
        except Exception as e:
            # Handle error with user-friendly message
            self.error_handler.handle_api_error(e, "Weather")
            logger.error(f"Weather API error for {location}: {str(e)}", exc_info=True)
            return None
    
    def render_market_section(
        self,
        crop: str,
        location: str,
        predicted_price: Optional[float] = None
    ) -> Optional[MarketPriceData]:
        """
        Render market price section with comparison to Prophet prediction.
        
        Args:
            crop: Crop name
            location: Market location
            predicted_price: Prophet predicted price (optional)
            
        Returns:
            MarketPriceData object if successful, None otherwise
        """
        st.subheader("💹 Market Price / बाजार भाव")
        
        try:
            # Fetch market price data with caching
            market_data = get_cached_market_price(crop, location)
            
            # Store in session_state for fallback
            cache_key = f"market_fallback_{crop}_{location}"
            st.session_state[cache_key] = market_data
            
            # If predicted price available, show comparison
            if predicted_price is not None:
                comparison = self.price_calculator.calculate_comparison(
                    predicted_price,
                    market_data.price
                )
                render_market_comparison(predicted_price, market_data, comparison)
            else:
                # Show market price only
                st.metric(
                    label="💹 Live Market Price / बाजार भाव",
                    value=f"₹{market_data.price:.2f}"
                )
                st.caption(f"📍 Market: {market_data.market_name}")
                st.caption(f"🕐 Updated: {market_data.timestamp.strftime('%d/%m/%Y %I:%M %p')}")
            
            # Log successful fetch
            logger.info(f"Market price fetched successfully for {crop} in {location}")
            
            return market_data
            
        except Exception as e:
            # Handle timeout and API errors with cached data fallback
            cache_key = f"market_fallback_{crop}_{location}"
            if cache_key in st.session_state:
                cached_data = st.session_state[cache_key]
                st.warning("⚠️ Agmarknet server slow, showing last available prices.")
                
                # Show cached market price
                if predicted_price is not None:
                    comparison = self.price_calculator.calculate_comparison(
                        predicted_price,
                        cached_data.price
                    )
                    render_market_comparison(predicted_price, cached_data, comparison)
                else:
                    st.metric(
                        label="💹 Market Price (Cached) / बाजार भाव (संचित)",
                        value=f"₹{cached_data.price:.2f}"
                    )
                    st.caption(f"📍 Market: {cached_data.market_name}")
                    st.caption(f"🕐 Cached from: {cached_data.timestamp.strftime('%d/%m/%Y %I:%M %p')}")
                
                logger.info(f"Using cached market data for {crop} in {location} due to API error")
                return cached_data
            else:
                st.warning("⚠️ Market prices updating...")
                logger.error(f"API error and no cached data for {crop} in {location}: {str(e)}")
                return None
    
    def render_smart_insight_section(
        self,
        prophet_prediction: float,
        current_price: float,
        weather_data: Optional[WeatherData]
    ) -> Optional[SmartInsight]:
        """
        Render Smart AI Insight section combining Prophet and weather data.
        
        Args:
            prophet_prediction: Predicted future price
            current_price: Current market price
            weather_data: WeatherData object (optional)
            
        Returns:
            SmartInsight object if successful, None otherwise
        """
        st.subheader("🤖 Smart AI Insight / स्मार्ट एआय सल्ला")
        
        try:
            if weather_data is None:
                # Graceful degradation: Generate insight without weather data
                st.warning("⚠️ Weather data unavailable. Showing prediction-only insight.")
                
                # Create mock weather data with neutral values
                from datetime import datetime
                weather_data = WeatherData(
                    temperature=25.0,
                    humidity=60,
                    description="Unknown",
                    description_marathi="अज्ञात",
                    rain_probability=30.0,  # Neutral value
                    timestamp=datetime.utcnow(),
                    location="Unknown"
                )
            
            # Generate Smart AI Insight
            insight = self.insight_generator.generate_insight(
                prophet_prediction,
                current_price,
                weather_data
            )
            
            # Render insight
            render_smart_insight(insight)
            
            # Log successful generation
            logger.info(f"Smart insight generated successfully")
            
            return insight
            
        except Exception as e:
            # Handle error
            st.error(f"❌ Error generating Smart AI Insight: {str(e)}")
            logger.error(f"Smart insight generation error: {str(e)}", exc_info=True)
            return None
    
    def render_location_selector_section(self) -> str:
        """
        Render location selector and handle location changes.
        
        Returns:
            Selected location string
        """
        # Render location selector
        location = render_location_selector()
        
        # Check if location changed
        if "previous_location" in st.session_state:
            if st.session_state.previous_location != location:
                # Location changed - clear caches
                logger.info(f"Location changed from {st.session_state.previous_location} to {location}")
                st.cache_data.clear()
                st.info(f"📍 Location changed to {location}. Refreshing data...")
        
        # Store current location
        st.session_state.previous_location = location
        
        return location
    
    def render_manual_refresh_button(self) -> None:
        """
        Render manual refresh button and handle cache clearing.
        """
        if st.button("🔄 Refresh Data / डेटा रिफ्रेश करा", width='stretch'):
            # Clear all caches
            st.cache_data.clear()
            st.success("✅ Data refreshed successfully!")
            logger.info("Manual refresh triggered - all caches cleared")
            st.rerun()
    
    def render_data_timestamp(self, data_type: str, timestamp: datetime) -> None:
        """
        Render data timestamp showing when data was last updated.
        
        Args:
            data_type: Type of data (e.g., "Weather", "Market Price")
            timestamp: Timestamp of last update
        """
        # Calculate time difference - handle both naive and aware datetimes
        try:
            # Check if timestamp is timezone-aware
            if timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None:
                # Timestamp is aware - make now aware too
                from datetime import timezone
                now = datetime.now(timezone.utc)
            else:
                # Timestamp is naive - use naive now
                now = datetime.utcnow()
            
            diff_seconds = (now - timestamp).total_seconds()
            
            if diff_seconds < 60:
                time_str = f"{int(diff_seconds)} seconds ago"
            elif diff_seconds < 3600:
                time_str = f"{int(diff_seconds / 60)} minutes ago"
            else:
                time_str = f"{int(diff_seconds / 3600)} hours ago"
            
            st.caption(f"🕐 {data_type} last updated: {time_str}")
        except Exception as e:
            # Fallback if datetime comparison fails
            st.caption(f"🕐 {data_type} last updated: {timestamp.strftime('%d/%m/%Y %I:%M %p')}")


def initialize_integration() -> bool:
    """
    Initialize integration by validating configuration using AWS Secrets Manager exclusively.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    # Validate secrets from AWS Secrets Manager only (bypass environment variables)
    validator = ConfigValidator()
    
    try:
        # Try to fetch API keys from AWS Secrets Manager directly
        for secret_key in validator.REQUIRED_SECRETS:
            validator.get_api_key_from_aws_only(secret_key)
        
        logger.info("Configuration validated successfully - API keys loaded from AWS Secrets Manager")
        return True
        
    except Exception as e:
        # Configuration error - return False to let caller handle display
        logger.warning(f"Configuration validation failed: {str(e)}")
        return False
