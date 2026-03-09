"""
SmartInsightGenerator Component

This module combines Prophet ML model predictions with weather data to generate
actionable Smart AI Insights for farmers. It provides bilingual recommendations
(Marathi primary, English secondary) based on price trends and weather conditions.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7, 5.8, 5.9
"""

import logging
from datetime import datetime
from src.models.smart_insight import SmartInsight
from src.models.weather_data import WeatherData

# Configure logging
logger = logging.getLogger(__name__)


class SmartInsightGenerator:
    """
    Generates Smart AI Insights by combining Prophet predictions with weather data.
    
    This class implements the core business logic for generating actionable
    recommendations to farmers based on:
    - Prophet price prediction trends (increasing/decreasing)
    - Weather conditions (rain probability)
    
    Decision Logic:
    - Price increasing + Low rain (≤60%) → "Sell soon"
    - Price increasing + High rain (>60%) → "Wait for better weather"
    - Price decreasing + Low rain (≤60%) → "Sell immediately"
    - Price decreasing + High rain (>60%) → "Urgent sale before rain"
    """
    
    RAIN_THRESHOLD = 60.0  # Percentage threshold for high rain probability
    
    def generate_insight(
        self,
        prophet_prediction: float,
        current_price: float,
        weather_data: WeatherData
    ) -> SmartInsight:
        """
        Generate Smart AI Insight combining price and weather data.
        
        Args:
            prophet_prediction: Predicted future price from Prophet model
            current_price: Current market price
            weather_data: WeatherData object with current weather conditions
            
        Returns:
            SmartInsight object with bilingual recommendation and metadata
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7, 5.8, 5.9
        """
        # Calculate price change percentage
        prophet_change = ((prophet_prediction - current_price) / current_price) * 100
        
        # Determine price trend
        price_trend = "increasing" if prophet_change > 0 else "decreasing"
        
        # Generate recommendation based on price trend and rain probability
        recommendation_mr, recommendation_en = self._determine_recommendation(
            price_trend,
            weather_data.rain_probability
        )
        
        # Calculate confidence level
        confidence = self._calculate_confidence(prophet_change, weather_data)
        
        return SmartInsight(
            recommendation=recommendation_mr,
            recommendation_en=recommendation_en,
            prophet_change=prophet_change,
            rain_probability=weather_data.rain_probability,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
    
    def _determine_recommendation(
        self,
        price_trend: str,
        rain_probability: float
    ) -> tuple[str, str]:
        """
        Determine recommendation based on price trend and rain conditions.
        
        Implements the decision logic matrix:
        - Price increasing + Low rain → "Sell soon"
        - Price increasing + High rain → "Wait for better weather"
        - Price decreasing + Low rain → "Sell immediately"
        - Price decreasing + High rain → "Urgent sale before rain"
        
        Args:
            price_trend: "increasing" or "decreasing"
            rain_probability: Rain probability percentage (0-100)
            
        Returns:
            Tuple of (marathi_recommendation, english_recommendation)
            
        Requirements: 5.2, 5.3, 5.4, 5.5, 5.7
        """
        high_rain = rain_probability > self.RAIN_THRESHOLD
        
        if price_trend == "increasing":
            if high_rain:
                # Price increasing + High rain → Wait for better weather
                marathi = (
                    f"🤖 किंमत वाढण्याची शक्यता आहे, परंतु पाऊस ({rain_probability:.1f}%) येण्याची शक्यता जास्त आहे.\n\n"
                    f"शिफारस: चांगल्या हवामानाची प्रतीक्षा करा. पाऊस थांबल्यानंतर विक्री करणे अधिक फायदेशीर ठरेल."
                )
                english = (
                    f"🤖 Price is likely to increase, but high rain probability ({rain_probability:.1f}%).\n\n"
                    f"Recommendation: Wait for better weather. Selling after rain stops will be more profitable."
                )
            else:
                # Price increasing + Low rain → Sell soon
                marathi = (
                    f"🤖 किंमत वाढण्याची शक्यता आहे आणि हवामान अनुकूल आहे (पाऊस: {rain_probability:.1f}%).\n\n"
                    f"शिफारस: लवकरच विक्री करा. चांगल्या किंमती मिळण्याची शक्यता आहे."
                )
                english = (
                    f"🤖 Price is likely to increase and weather is favorable (rain: {rain_probability:.1f}%).\n\n"
                    f"Recommendation: Sell soon. Good prices are expected."
                )
        else:  # price_trend == "decreasing"
            if high_rain:
                # Price decreasing + High rain → Urgent sale before rain
                marathi = (
                    f"🤖 किंमत कमी होण्याची शक्यता आहे आणि पाऊस ({rain_probability:.1f}%) येण्याची शक्यता जास्त आहे.\n\n"
                    f"शिफारस: तातडीने विक्री करा! पाऊस येण्यापूर्वी विक्री करणे अत्यंत आवश्यक आहे."
                )
                english = (
                    f"🤖 Price is likely to decrease and high rain probability ({rain_probability:.1f}%).\n\n"
                    f"Recommendation: Urgent sale before rain! Selling before rain is critical."
                )
            else:
                # Price decreasing + Low rain → Sell immediately
                marathi = (
                    f"🤖 किंमत कमी होण्याची शक्यता आहे, परंतु हवामान अनुकूल आहे (पाऊस: {rain_probability:.1f}%).\n\n"
                    f"शिफारस: ताबडतोब विक्री करा. किंमत आणखी कमी होण्यापूर्वी विक्री करा."
                )
                english = (
                    f"🤖 Price is likely to decrease, but weather is favorable (rain: {rain_probability:.1f}%).\n\n"
                    f"Recommendation: Sell immediately. Sell before prices drop further."
                )
        
        return (marathi, english)
    
    def _calculate_confidence(
        self,
        prophet_change: float,
        weather_data: WeatherData
    ) -> str:
        """
        Calculate confidence level based on data quality.
        
        Confidence levels:
        - High: Strong price signal (|change| > 5%) AND fresh weather data (<15 min)
        - Medium: Moderate price signal (2% < |change| ≤ 5%) OR cached weather data (15-30 min)
        - Low: Weak price signal (|change| ≤ 2%) OR stale weather data (>30 min)
        
        Args:
            prophet_change: Predicted price change percentage
            weather_data: WeatherData object with timestamp
            
        Returns:
            Confidence level: "high", "medium", or "low"
            
        Requirements: 5.1
        """
        # Calculate weather data age in minutes - handle both naive and aware datetimes
        try:
            # Get current time
            now = datetime.utcnow()
            
            # Convert both to naive UTC for comparison
            weather_timestamp = weather_data.timestamp
            if weather_timestamp.tzinfo is not None and weather_timestamp.tzinfo.utcoffset(weather_timestamp) is not None:
                # Timestamp is aware - convert to naive UTC
                weather_timestamp = weather_timestamp.replace(tzinfo=None)
            
            weather_age_minutes = (now - weather_timestamp).total_seconds() / 60
        except Exception as e:
            # Fallback: assume data is fresh if comparison fails
            logger.warning(f"Failed to calculate weather data age: {str(e)}")
            weather_age_minutes = 0
        
        # Determine confidence based on price signal strength and data freshness
        abs_change = abs(prophet_change)
        
        if abs_change > 5.0 and weather_age_minutes < 15:
            return "high"
        elif abs_change > 2.0 or (abs_change > 5.0 and weather_age_minutes < 30):
            return "medium"
        else:
            return "low"
