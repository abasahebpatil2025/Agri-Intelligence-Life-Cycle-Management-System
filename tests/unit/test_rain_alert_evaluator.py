"""
Unit tests for RainAlertEvaluator.

Tests the rain alert threshold logic and bilingual message generation.

Requirements: 2.1, 2.2, 2.4, 2.5
"""

import pytest
from datetime import datetime
from src.components.rain_alert_evaluator import RainAlertEvaluator
from src.models.weather_data import WeatherData


@pytest.fixture
def evaluator():
    """Create RainAlertEvaluator instance for testing."""
    return RainAlertEvaluator()


@pytest.fixture
def sample_weather_data():
    """Create sample WeatherData for testing."""
    def _create_weather_data(rain_probability: float) -> WeatherData:
        return WeatherData(
            temperature=28.5,
            humidity=65,
            description="scattered clouds",
            description_marathi="विखुरलेले ढग",
            rain_probability=rain_probability,
            timestamp=datetime.now(),
            location="Nashik"
        )
    return _create_weather_data


class TestRainAlertThreshold:
    """Test rain alert threshold logic."""
    
    def test_should_show_alert_above_threshold(self, evaluator, sample_weather_data):
        """
        Test that alert is shown when rain probability exceeds 60%.
        
        Requirements: 2.1, 2.5
        """
        weather_data = sample_weather_data(65.0)
        assert evaluator.should_show_alert(weather_data) is True
    
    def test_should_not_show_alert_at_threshold(self, evaluator, sample_weather_data):
        """
        Test that alert is NOT shown when rain probability equals 60%.
        
        Requirements: 2.1, 2.5
        """
        weather_data = sample_weather_data(60.0)
        assert evaluator.should_show_alert(weather_data) is False
    
    def test_should_not_show_alert_below_threshold(self, evaluator, sample_weather_data):
        """
        Test that alert is NOT shown when rain probability is below 60%.
        
        Requirements: 2.1, 2.5
        """
        weather_data = sample_weather_data(45.0)
        assert evaluator.should_show_alert(weather_data) is False
    
    def test_should_show_alert_high_probability(self, evaluator, sample_weather_data):
        """
        Test that alert is shown for very high rain probability.
        
        Requirements: 2.1, 2.5
        """
        weather_data = sample_weather_data(95.0)
        assert evaluator.should_show_alert(weather_data) is True
    
    def test_should_not_show_alert_zero_probability(self, evaluator, sample_weather_data):
        """
        Test that alert is NOT shown when rain probability is zero.
        
        Requirements: 2.1, 2.5
        """
        weather_data = sample_weather_data(0.0)
        assert evaluator.should_show_alert(weather_data) is False


class TestAlertMessageGeneration:
    """Test bilingual alert message generation."""
    
    def test_generate_alert_message_returns_tuple(self, evaluator, sample_weather_data):
        """
        Test that generate_alert_message returns a tuple of two strings.
        
        Requirements: 2.2, 2.4
        """
        weather_data = sample_weather_data(75.0)
        result = evaluator.generate_alert_message(weather_data)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # Marathi message
        assert isinstance(result[1], str)  # English message
    
    def test_alert_message_includes_probability(self, evaluator, sample_weather_data):
        """
        Test that alert messages include the specific probability percentage.
        
        Requirements: 2.2
        """
        weather_data = sample_weather_data(72.5)
        marathi_msg, english_msg = evaluator.generate_alert_message(weather_data)
        
        # Check that probability is included in both messages
        assert "72.5" in marathi_msg
        assert "72.5" in english_msg
    
    def test_alert_message_marathi_content(self, evaluator, sample_weather_data):
        """
        Test that Marathi message contains actionable advice.
        
        Requirements: 2.4
        """
        weather_data = sample_weather_data(80.0)
        marathi_msg, _ = evaluator.generate_alert_message(weather_data)
        
        # Check for Marathi content
        assert "पाऊस" in marathi_msg  # Rain in Marathi
        assert "इशारा" in marathi_msg  # Alert/Warning in Marathi
        
        # Check for actionable advice keywords
        assert "पीक" in marathi_msg or "धान्य" in marathi_msg  # Crop/grain
        assert "सुरक्षित" in marathi_msg or "संरक्षण" in marathi_msg  # Safe/protection
    
    def test_alert_message_english_content(self, evaluator, sample_weather_data):
        """
        Test that English message contains actionable advice.
        
        Requirements: 2.2
        """
        weather_data = sample_weather_data(80.0)
        _, english_msg = evaluator.generate_alert_message(weather_data)
        
        # Check for English content
        assert "Rain Alert" in english_msg
        assert "probability" in english_msg
        
        # Check for actionable advice keywords
        assert "crops" in english_msg or "produce" in english_msg
        assert "protect" in english_msg or "precautions" in english_msg
    
    def test_alert_message_includes_emoji(self, evaluator, sample_weather_data):
        """
        Test that alert messages include rain emoji icon.
        
        Requirements: 2.2, 2.4
        """
        weather_data = sample_weather_data(70.0)
        marathi_msg, english_msg = evaluator.generate_alert_message(weather_data)
        
        # Check for rain emoji in both messages
        assert "🌧️" in marathi_msg
        assert "🌧️" in english_msg
    
    def test_alert_message_different_probabilities(self, evaluator, sample_weather_data):
        """
        Test that messages correctly reflect different probability values.
        
        Requirements: 2.2
        """
        # Test with different probabilities
        probabilities = [61.0, 75.5, 90.0, 99.9]
        
        for prob in probabilities:
            weather_data = sample_weather_data(prob)
            marathi_msg, english_msg = evaluator.generate_alert_message(weather_data)
            
            # Check that the specific probability appears in messages
            prob_str = f"{prob:.1f}"
            assert prob_str in marathi_msg, f"Probability {prob_str} not found in Marathi message"
            assert prob_str in english_msg, f"Probability {prob_str} not found in English message"


class TestRainThresholdConstant:
    """Test the RAIN_THRESHOLD constant."""
    
    def test_rain_threshold_value(self, evaluator):
        """
        Test that RAIN_THRESHOLD is set to 60.0.
        
        Requirements: 2.1
        """
        assert evaluator.RAIN_THRESHOLD == 60.0
    
    def test_rain_threshold_is_class_attribute(self):
        """
        Test that RAIN_THRESHOLD is accessible as class attribute.
        
        Requirements: 2.1
        """
        assert hasattr(RainAlertEvaluator, 'RAIN_THRESHOLD')
        assert RainAlertEvaluator.RAIN_THRESHOLD == 60.0
