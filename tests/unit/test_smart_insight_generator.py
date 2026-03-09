"""
Unit tests for SmartInsightGenerator component.

Tests the core business logic for generating Smart AI Insights by combining
Prophet predictions with weather data.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7, 5.8, 5.9
"""

import pytest
from datetime import datetime, timedelta
from src.components.smart_insight_generator import SmartInsightGenerator
from src.models.weather_data import WeatherData
from src.models.smart_insight import SmartInsight


@pytest.fixture
def generator():
    """Create SmartInsightGenerator instance for testing."""
    return SmartInsightGenerator()


@pytest.fixture
def sample_weather_low_rain():
    """Create sample WeatherData with low rain probability."""
    return WeatherData(
        temperature=28.5,
        humidity=65,
        description="Clear sky",
        description_marathi="स्वच्छ आकाश",
        rain_probability=30.0,
        timestamp=datetime.utcnow(),
        location="Nashik"
    )


@pytest.fixture
def sample_weather_high_rain():
    """Create sample WeatherData with high rain probability."""
    return WeatherData(
        temperature=26.0,
        humidity=85,
        description="Rain",
        description_marathi="पाऊस",
        rain_probability=75.0,
        timestamp=datetime.utcnow(),
        location="Nashik"
    )


class TestSmartInsightGenerator:
    """Test suite for SmartInsightGenerator class."""
    
    def test_generate_insight_returns_smart_insight_object(
        self, generator, sample_weather_low_rain
    ):
        """Test that generate_insight returns a SmartInsight object."""
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        assert isinstance(result, SmartInsight)
        assert result.recommendation is not None
        assert result.recommendation_en is not None
        assert result.prophet_change is not None
        assert result.rain_probability is not None
        assert result.confidence is not None
        assert result.timestamp is not None
    
    def test_insight_price_increasing_low_rain_sell_soon(
        self, generator, sample_weather_low_rain
    ):
        """
        Test recommendation: Price increasing + Low rain → "Sell soon"
        
        Requirements: 5.2, 5.3
        """
        result = generator.generate_insight(
            prophet_prediction=2100.0,  # 5% increase
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        # Verify price change calculation
        assert result.prophet_change == pytest.approx(5.0, rel=0.01)
        
        # Verify rain probability is captured
        assert result.rain_probability == 30.0
        
        # Verify Marathi recommendation contains "sell soon" concept
        assert "लवकरच विक्री करा" in result.recommendation or "विक्री करा" in result.recommendation
        
        # Verify English recommendation contains "sell soon"
        assert "sell soon" in result.recommendation_en.lower()
    
    def test_insight_price_increasing_high_rain_wait_for_weather(
        self, generator, sample_weather_high_rain
    ):
        """
        Test recommendation: Price increasing + High rain → "Wait for better weather"
        
        Requirements: 5.2, 5.4
        """
        result = generator.generate_insight(
            prophet_prediction=2150.0,  # 7.5% increase
            current_price=2000.0,
            weather_data=sample_weather_high_rain
        )
        
        # Verify price change calculation
        assert result.prophet_change == pytest.approx(7.5, rel=0.01)
        
        # Verify rain probability is captured
        assert result.rain_probability == 75.0
        
        # Verify Marathi recommendation contains "wait for weather" concept
        assert "प्रतीक्षा" in result.recommendation or "हवामान" in result.recommendation
        
        # Verify English recommendation contains "wait"
        assert "wait" in result.recommendation_en.lower()
    
    def test_insight_price_decreasing_low_rain_sell_immediately(
        self, generator, sample_weather_low_rain
    ):
        """
        Test recommendation: Price decreasing + Low rain → "Sell immediately"
        
        Requirements: 5.2, 5.5
        """
        result = generator.generate_insight(
            prophet_prediction=1900.0,  # 5% decrease
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        # Verify price change calculation
        assert result.prophet_change == pytest.approx(-5.0, rel=0.01)
        
        # Verify rain probability is captured
        assert result.rain_probability == 30.0
        
        # Verify Marathi recommendation contains "sell immediately" concept
        assert "ताबडतोब" in result.recommendation or "विक्री करा" in result.recommendation
        
        # Verify English recommendation contains "immediately"
        assert "immediately" in result.recommendation_en.lower()
    
    def test_insight_price_decreasing_high_rain_urgent_sale(
        self, generator, sample_weather_high_rain
    ):
        """
        Test recommendation: Price decreasing + High rain → "Urgent sale before rain"
        
        Requirements: 5.2, 5.5
        """
        result = generator.generate_insight(
            prophet_prediction=1850.0,  # 7.5% decrease
            current_price=2000.0,
            weather_data=sample_weather_high_rain
        )
        
        # Verify price change calculation
        assert result.prophet_change == pytest.approx(-7.5, rel=0.01)
        
        # Verify rain probability is captured
        assert result.rain_probability == 75.0
        
        # Verify Marathi recommendation contains "urgent" concept
        assert "तातडीने" in result.recommendation or "अत्यंत आवश्यक" in result.recommendation
        
        # Verify English recommendation contains "urgent"
        assert "urgent" in result.recommendation_en.lower()
    
    def test_insight_includes_prophet_change_percentage(
        self, generator, sample_weather_low_rain
    ):
        """
        Test that insight includes specific Prophet prediction percentage.
        
        Requirements: 5.8
        """
        result = generator.generate_insight(
            prophet_prediction=2200.0,  # 10% increase
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        # Verify prophet_change is calculated correctly
        assert result.prophet_change == pytest.approx(10.0, rel=0.01)
    
    def test_insight_includes_weather_conditions(
        self, generator, sample_weather_high_rain
    ):
        """
        Test that insight includes specific weather conditions.
        
        Requirements: 5.9
        """
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=sample_weather_high_rain
        )
        
        # Verify rain probability is included
        assert result.rain_probability == 75.0
        
        # Verify rain probability appears in recommendation text
        assert "75.0" in result.recommendation or "75" in result.recommendation
    
    def test_insight_marathi_primary_language(
        self, generator, sample_weather_low_rain
    ):
        """
        Test that Marathi is the primary language in recommendations.
        
        Requirements: 5.7
        """
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        # Verify Marathi recommendation is not empty
        assert len(result.recommendation) > 0
        
        # Verify Marathi recommendation contains Devanagari script
        # Check for common Marathi characters
        has_devanagari = any(
            '\u0900' <= char <= '\u097F' for char in result.recommendation
        )
        assert has_devanagari, "Marathi recommendation should contain Devanagari script"
    
    def test_insight_english_secondary_language(
        self, generator, sample_weather_low_rain
    ):
        """
        Test that English is provided as secondary language.
        
        Requirements: 5.7
        """
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        # Verify English recommendation is not empty
        assert len(result.recommendation_en) > 0
        
        # Verify English recommendation is in English (basic check)
        assert result.recommendation_en.isascii() or any(
            char in result.recommendation_en for char in "abcdefghijklmnopqrstuvwxyz"
        )
    
    def test_confidence_high_with_strong_signal_and_fresh_data(
        self, generator, sample_weather_low_rain
    ):
        """
        Test high confidence with strong price signal and fresh weather data.
        
        Requirements: 5.1
        """
        # Create fresh weather data (just now)
        fresh_weather = WeatherData(
            temperature=28.5,
            humidity=65,
            description="Clear sky",
            description_marathi="स्वच्छ आकाश",
            rain_probability=30.0,
            timestamp=datetime.utcnow(),
            location="Nashik"
        )
        
        result = generator.generate_insight(
            prophet_prediction=2120.0,  # 6% increase (strong signal)
            current_price=2000.0,
            weather_data=fresh_weather
        )
        
        assert result.confidence == "high"
    
    def test_confidence_medium_with_moderate_signal(
        self, generator, sample_weather_low_rain
    ):
        """
        Test medium confidence with moderate price signal.
        
        Requirements: 5.1
        """
        result = generator.generate_insight(
            prophet_prediction=2060.0,  # 3% increase (moderate signal)
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        assert result.confidence == "medium"
    
    def test_confidence_low_with_weak_signal(
        self, generator, sample_weather_low_rain
    ):
        """
        Test low confidence with weak price signal.
        
        Requirements: 5.1
        """
        result = generator.generate_insight(
            prophet_prediction=2020.0,  # 1% increase (weak signal)
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        assert result.confidence == "low"
    
    def test_confidence_low_with_stale_weather_data(self, generator):
        """
        Test low confidence with stale weather data (>30 minutes old).
        
        Requirements: 5.1
        """
        # Create stale weather data (35 minutes old)
        stale_weather = WeatherData(
            temperature=28.5,
            humidity=65,
            description="Clear sky",
            description_marathi="स्वच्छ आकाश",
            rain_probability=30.0,
            timestamp=datetime.utcnow() - timedelta(minutes=35),
            location="Nashik"
        )
        
        result = generator.generate_insight(
            prophet_prediction=2020.0,  # 1% increase
            current_price=2000.0,
            weather_data=stale_weather
        )
        
        assert result.confidence == "low"
    
    def test_rain_threshold_boundary_at_60_percent(self, generator):
        """
        Test that rain threshold is exactly 60% (boundary test).
        """
        # Test at exactly 60% - should be low rain
        weather_at_threshold = WeatherData(
            temperature=28.5,
            humidity=65,
            description="Cloudy",
            description_marathi="ढगाळ",
            rain_probability=60.0,
            timestamp=datetime.utcnow(),
            location="Nashik"
        )
        
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=weather_at_threshold
        )
        
        # At exactly 60%, should recommend "sell soon" (low rain behavior)
        assert "sell soon" in result.recommendation_en.lower()
        
        # Test at 60.1% - should be high rain
        weather_above_threshold = WeatherData(
            temperature=28.5,
            humidity=65,
            description="Cloudy",
            description_marathi="ढगाळ",
            rain_probability=60.1,
            timestamp=datetime.utcnow(),
            location="Nashik"
        )
        
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=weather_above_threshold
        )
        
        # Above 60%, should recommend "wait" (high rain behavior)
        assert "wait" in result.recommendation_en.lower()
    
    def test_timestamp_is_set(self, generator, sample_weather_low_rain):
        """Test that insight timestamp is set to current time."""
        before = datetime.utcnow()
        
        result = generator.generate_insight(
            prophet_prediction=2100.0,
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        after = datetime.utcnow()
        
        # Verify timestamp is between before and after
        assert before <= result.timestamp <= after
    
    def test_zero_price_change_handled(self, generator, sample_weather_low_rain):
        """Test handling of zero price change (no change in price)."""
        result = generator.generate_insight(
            prophet_prediction=2000.0,  # No change
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        # Should handle zero change gracefully
        assert result.prophet_change == 0.0
        assert result.confidence == "low"  # Weak signal
    
    def test_negative_price_change_calculation(
        self, generator, sample_weather_low_rain
    ):
        """Test that negative price changes are calculated correctly."""
        result = generator.generate_insight(
            prophet_prediction=1800.0,  # 10% decrease
            current_price=2000.0,
            weather_data=sample_weather_low_rain
        )
        
        assert result.prophet_change == pytest.approx(-10.0, rel=0.01)
