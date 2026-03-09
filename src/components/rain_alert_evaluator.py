"""
RainAlertEvaluator for weather-market-api-integration feature.

This module evaluates weather data and determines if rain alerts should be shown
to farmers, generating bilingual alert messages with actionable advice.

Requirements: 2.1, 2.2, 2.4, 2.5
"""

from typing import Tuple
from src.models.weather_data import WeatherData


class RainAlertEvaluator:
    """
    Evaluates weather data and determines if rain alert should be shown.
    
    This class checks if rain probability exceeds the threshold and generates
    appropriate bilingual alert messages for farmers.
    """
    
    RAIN_THRESHOLD = 60.0  # Percentage threshold for rain alerts
    
    def should_show_alert(self, weather_data: WeatherData) -> bool:
        """
        Determine if rain alert should be displayed.
        
        Args:
            weather_data: WeatherData object containing rain probability
            
        Returns:
            True if rain probability exceeds threshold, False otherwise
            
        Requirements: 2.1, 2.5
        """
        return weather_data.rain_probability > self.RAIN_THRESHOLD
    
    def generate_alert_message(self, weather_data: WeatherData) -> Tuple[str, str]:
        """
        Generate bilingual rain alert message.
        
        Creates alert messages in both Marathi (primary) and English (secondary)
        with specific probability percentage and actionable advice for farmers.
        
        Args:
            weather_data: WeatherData object containing rain probability
            
        Returns:
            Tuple of (marathi_message, english_message)
            
        Requirements: 2.2, 2.4
        """
        probability = weather_data.rain_probability
        
        # Marathi message with actionable advice
        marathi_message = (
            f"🌧️ पाऊस चा इशारा: {probability:.1f}% शक्यता\n\n"
            f"पीक संरक्षणासाठी आवश्यक उपाययोजना करा:\n"
            f"• कापणी केलेले धान्य सुरक्षित ठिकाणी ठेवा\n"
            f"• खते आणि कीटकनाशके झाकून ठेवा\n"
            f"• पाण्याचा निचरा व्यवस्थित असल्याची खात्री करा"
        )
        
        # English message
        english_message = (
            f"🌧️ Rain Alert: {probability:.1f}% probability\n\n"
            f"Take necessary precautions to protect your crops:\n"
            f"• Store harvested produce in safe locations\n"
            f"• Cover fertilizers and pesticides\n"
            f"• Ensure proper water drainage"
        )
        
        return (marathi_message, english_message)
