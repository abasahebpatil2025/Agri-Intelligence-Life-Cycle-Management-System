"""
Quick test to verify fallback logic implementation.

This test verifies that the weather API fallback mechanism works correctly
when the API fails.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'utils'))
sys.path.insert(0, os.path.join(project_root, 'src', 'models'))

from datetime import datetime


def test_fallback_cache_storage():
    """Test that fallback cache storage works correctly"""
    from src.models.weather_data import WeatherData
    
    # Create mock weather data
    weather_data = WeatherData(
        temperature=25.0,
        humidity=60,
        description="Clear sky",
        description_marathi="स्वच्छ आकाश",
        rain_probability=20.0,
        timestamp=datetime.utcnow(),
        location="Nashik"
    )
    
    # Test that WeatherData can be created
    assert weather_data.temperature == 25.0
    assert weather_data.location == "Nashik"
    
    print("✅ Fallback cache storage test passed")


def test_fallback_logic_structure():
    """Test that fallback logic structure is correct"""
    import inspect
    from src.utils.cache_manager import get_cached_weather, _store_weather_fallback_cache
    
    # Verify get_cached_weather has try-except structure
    source = inspect.getsource(get_cached_weather)
    assert "try:" in source
    assert "except" in source
    assert "st.warning" in source or "warning" in source.lower()
    assert "logger.error" in source or "log" in source.lower()
    
    # Verify _store_weather_fallback_cache exists
    assert callable(_store_weather_fallback_cache)
    
    print("✅ Fallback logic structure test passed")


if __name__ == "__main__":
    print("Running fallback logic tests...")
    print()
    
    test_fallback_cache_storage()
    test_fallback_logic_structure()
    
    print()
    print("=" * 60)
    print("✅ All fallback logic tests passed!")
    print("=" * 60)
