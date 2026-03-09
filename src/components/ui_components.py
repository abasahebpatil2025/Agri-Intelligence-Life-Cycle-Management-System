"""
UI Components for Weather Market API Integration

This module contains Streamlit UI rendering functions for displaying
weather data, market prices, smart insights, and location selection.
"""

import streamlit as st
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add models directory to path
sys.path.insert(0, 'src/models')
sys.path.insert(0, 'src/components')

from src.models.weather_data import WeatherData
from src.models.market_price_data import MarketPriceData
from src.models.smart_insight import SmartInsight


def render_weather_display(weather_data: WeatherData) -> None:
    """
    Display weather information using Streamlit components
    
    Args:
        weather_data: WeatherData object with temperature, humidity, description, rain probability
        
    Displays:
        - Temperature and humidity metrics in two columns
        - Weather description in both English and Marathi
        - Rain alert if probability > 60%
    """
    # Create two-column layout for metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="🌡️ Temperature / तापमान",
            value=f"{weather_data.temperature:.1f}°C"
        )
    
    with col2:
        st.metric(
            label="💧 Humidity / आर्द्रता",
            value=f"{weather_data.humidity}%"
        )
    
    # Display weather description in both languages
    st.write(f"**Weather / हवामान**: {weather_data.description} / {weather_data.description_marathi}")
    
    # Check for rain alert using RainAlertEvaluator
    from src.components.rain_alert_evaluator import RainAlertEvaluator
    
    evaluator = RainAlertEvaluator()
    if evaluator.should_show_alert(weather_data):
        marathi_msg, english_msg = evaluator.generate_alert_message(weather_data)
        st.error(f"🌧️ {marathi_msg}\n\n_{english_msg}_")


def render_market_comparison(
    predicted_price: float,
    market_data: MarketPriceData,
    comparison: Dict[str, Any]
) -> None:
    """
    Display market price comparison between Prophet prediction and live market price
    
    Args:
        predicted_price: Prophet predicted price
        market_data: MarketPriceData object with live market price
        comparison: Dictionary with comparison metrics (difference, percentage_diff, direction)
        
    Displays:
        - Prophet prediction metric
        - Live market price metric with delta
        - Market name and timestamp
    """
    # Create two-column layout for price comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="📈 Prophet Prediction / भविष्यवाणी",
            value=f"₹{predicted_price:.2f}"
        )
    
    with col2:
        # Calculate delta for display
        delta_value = comparison.get('percentage_diff', 0)
        st.metric(
            label="💹 Live Market Price / बाजार भाव",
            value=f"₹{market_data.price:.2f}",
            delta=f"{delta_value:+.1f}%"
        )
    
    # Display market name and timestamp
    st.caption(f"📍 Market / बाजार: {market_data.market_name}")
    st.caption(f"🕐 Last Updated / शेवटचे अपडेट: {market_data.timestamp.strftime('%d/%m/%Y %I:%M %p')}")


def render_smart_insight(insight: SmartInsight) -> None:
    """
    Display Smart AI Insight recommendation
    
    Args:
        insight: SmartInsight object with recommendation and metadata
        
    Displays:
        - Marathi recommendation prominently
        - English recommendation as secondary text
        - Confidence level
    """
    st.info(f"""
🤖 **Smart AI Insight / स्मार्ट एआय सल्ला**

{insight.recommendation}

_{insight.recommendation_en}_

**Confidence / विश्वास**: {insight.confidence.upper()}
    """)


def render_location_selector() -> str:
    """
    Render location selector for weather and market data
    
    Returns:
        Selected location string
        
    Displays:
        - Dropdown with Maharashtra cities
        - Default location: Nashik
        - Stores selection in session_state
    """
    # Define list of Maharashtra cities
    locations = [
        "Nashik",
        "Mumbai",
        "Pune",
        "Aurangabad",
        "Nagpur",
        "Solapur",
        "Kolhapur"
    ]
    
    # Initialize session state with default location
    if "selected_location" not in st.session_state:
        st.session_state.selected_location = "Nashik"
    
    # Create location selector
    location = st.selectbox(
        "📍 Select Location / स्थान निवडा",
        locations,
        index=locations.index(st.session_state.selected_location)
    )
    
    # Store selected location in session state
    st.session_state.selected_location = location
    
    return location
