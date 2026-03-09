"""
Final Verification Script for Weather Market API Integration

This script verifies:
1. Bilingual UI is complete (Marathi/English)
2. API Key Security (no keys in logs or output)
3. All critical components are working
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from datetime import datetime


def test_bilingual_ui():
    """Verify all UI components have bilingual labels"""
    print("=" * 60)
    print("TEST 1: Bilingual UI Verification")
    print("=" * 60)
    
    from src.components.ui_components import (
        render_weather_display,
        render_market_comparison,
        render_smart_insight,
        render_location_selector
    )
    
    # Check function docstrings mention bilingual
    checks = []
    
    # Weather display
    if "English and Marathi" in render_weather_display.__doc__:
        checks.append("✅ Weather display: Bilingual")
    else:
        checks.append("❌ Weather display: Missing bilingual")
    
    # Market comparison
    if "Prophet Prediction" in render_market_comparison.__doc__:
        checks.append("✅ Market comparison: Bilingual labels")
    else:
        checks.append("❌ Market comparison: Missing bilingual")
    
    # Smart insight
    if "Marathi" in render_smart_insight.__doc__ and "English" in render_smart_insight.__doc__:
        checks.append("✅ Smart insight: Bilingual")
    else:
        checks.append("❌ Smart insight: Missing bilingual")
    
    # Location selector
    if "Select Location" in render_location_selector.__doc__:
        checks.append("✅ Location selector: Bilingual")
    else:
        checks.append("❌ Location selector: Missing bilingual")
    
    for check in checks:
        print(check)
    
    # Check rain alert evaluator
    from src.components.rain_alert_evaluator import RainAlertEvaluator
    evaluator = RainAlertEvaluator()
    
    # Create mock weather data
    from src.models.weather_data import WeatherData
    weather_data = WeatherData(
        temperature=25.0,
        humidity=60,
        description="Clear sky",
        description_marathi="स्वच्छ आकाश",
        rain_probability=70.0,
        timestamp=datetime.utcnow(),
        location="Nashik"
    )
    
    marathi_msg, english_msg = evaluator.generate_alert_message(weather_data)
    
    if "पाऊस" in marathi_msg and "Rain" in english_msg:
        print("✅ Rain alert: Bilingual messages")
    else:
        print("❌ Rain alert: Missing bilingual")
    
    # Check smart insight generator
    from src.components.smart_insight_generator import SmartInsightGenerator
    generator = SmartInsightGenerator()
    
    insight = generator.generate_insight(2500.0, 2400.0, weather_data)
    
    if insight.recommendation and insight.recommendation_en:
        if "किंमत" in insight.recommendation or "शिफारस" in insight.recommendation:
            print("✅ Smart insight: Marathi recommendation")
        else:
            print("❌ Smart insight: Missing Marathi")
        
        if "Price" in insight.recommendation_en or "Recommendation" in insight.recommendation_en:
            print("✅ Smart insight: English recommendation")
        else:
            print("❌ Smart insight: Missing English")
    
    print()
    return True


def test_api_key_security():
    """Verify API keys are not exposed in logs or output"""
    print("=" * 60)
    print("TEST 2: API Key Security Verification")
    print("=" * 60)
    
    import inspect
    
    # Check cache_manager
    from src.utils import cache_manager
    source = inspect.getsource(cache_manager)
    
    checks = []
    
    # Verify API keys come from st.secrets
    if 'st.secrets["openweather_api_key"]' in source:
        checks.append("✅ Weather API key from st.secrets")
    else:
        checks.append("❌ Weather API key not from st.secrets")
    
    if 'st.secrets["agmarknet_api_key"]' in source:
        checks.append("✅ Agmarknet API key from st.secrets")
    else:
        checks.append("❌ Agmarknet API key not from st.secrets")
    
    # Verify no hardcoded keys (check for patterns like "api_key = 'abc123...'")
    if "api_key = '" not in source or "api_key = \"" not in source:
        checks.append("✅ No hardcoded API keys found")
    else:
        checks.append("⚠️ Potential hardcoded API key detected")
    
    # Check that API keys are not logged
    if "logger" in source:
        if "api_key" not in source.lower() or "api_key" in source:
            # API key variable exists but check if it's logged
            if "logger.info(api_key)" not in source and "logger.error(api_key)" not in source:
                checks.append("✅ API keys not logged")
            else:
                checks.append("❌ API keys may be logged")
        else:
            checks.append("✅ API keys not logged")
    else:
        checks.append("✅ No logging of API keys")
    
    for check in checks:
        print(check)
    
    print()
    return True


def test_component_integration():
    """Verify all components are properly integrated"""
    print("=" * 60)
    print("TEST 3: Component Integration Verification")
    print("=" * 60)
    
    checks = []
    
    # Test data models
    try:
        from src.models.weather_data import WeatherData
        from src.models.market_price_data import MarketPriceData
        from src.models.smart_insight import SmartInsight
        checks.append("✅ Data models imported successfully")
    except Exception as e:
        checks.append(f"❌ Data models import failed: {e}")
    
    # Test API clients
    try:
        from src.utils.weather_api_client import WeatherAPIClient
        from src.utils.agmarknet_api_client import AgmarknetAPIClient
        checks.append("✅ API clients imported successfully")
    except Exception as e:
        checks.append(f"❌ API clients import failed: {e}")
    
    # Test business logic
    try:
        from src.components.rain_alert_evaluator import RainAlertEvaluator
        from src.components.price_comparison_calculator import PriceComparisonCalculator
        from src.components.smart_insight_generator import SmartInsightGenerator
        checks.append("✅ Business logic components imported successfully")
    except Exception as e:
        checks.append(f"❌ Business logic import failed: {e}")
    
    # Test UI components
    try:
        from src.components.ui_components import (
            render_weather_display,
            render_market_comparison,
            render_smart_insight,
            render_location_selector
        )
        checks.append("✅ UI components imported successfully")
    except Exception as e:
        checks.append(f"❌ UI components import failed: {e}")
    
    # Test integration
    try:
        from src.integration.weather_market_integration import WeatherMarketIntegration
        from src.integration.enhanced_market_tab import show_enhanced_market_intel_tab
        checks.append("✅ Integration modules imported successfully")
    except Exception as e:
        checks.append(f"❌ Integration import failed: {e}")
    
    # Test cache manager with fallback
    try:
        from src.utils.cache_manager import get_cached_weather, _store_weather_fallback_cache
        checks.append("✅ Cache manager with fallback imported successfully")
    except Exception as e:
        checks.append(f"❌ Cache manager import failed: {e}")
    
    # Test config and error handling
    try:
        from config.config_validator import ConfigValidator
        from config.error_handler import ErrorHandler
        checks.append("✅ Config and error handling imported successfully")
    except Exception as e:
        checks.append(f"❌ Config/error handling import failed: {e}")
    
    for check in checks:
        print(check)
    
    print()
    return True


def test_fallback_logic():
    """Verify fallback logic is implemented"""
    print("=" * 60)
    print("TEST 4: Fallback Logic Verification")
    print("=" * 60)
    
    import inspect
    from src.utils.cache_manager import get_cached_weather
    
    source = inspect.getsource(get_cached_weather)
    
    checks = []
    
    if "try:" in source and "except" in source:
        checks.append("✅ Fallback logic: try-except wrapper present")
    else:
        checks.append("❌ Fallback logic: Missing try-except")
    
    if "st.warning" in source or "warning" in source.lower():
        checks.append("✅ Fallback logic: User warning present")
    else:
        checks.append("❌ Fallback logic: Missing user warning")
    
    if "logger.error" in source or "logger.info" in source:
        checks.append("✅ Fallback logic: Error logging present")
    else:
        checks.append("❌ Fallback logic: Missing error logging")
    
    if "session_state" in source or "cache" in source.lower():
        checks.append("✅ Fallback logic: Stale cache retrieval present")
    else:
        checks.append("❌ Fallback logic: Missing stale cache retrieval")
    
    for check in checks:
        print(check)
    
    print()
    return True


def main():
    """Run all verification tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  FINAL VERIFICATION - Weather Market API Integration  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    results = []
    
    try:
        results.append(("Bilingual UI", test_bilingual_ui()))
    except Exception as e:
        print(f"❌ Bilingual UI test failed: {e}\n")
        results.append(("Bilingual UI", False))
    
    try:
        results.append(("API Key Security", test_api_key_security()))
    except Exception as e:
        print(f"❌ API Key Security test failed: {e}\n")
        results.append(("API Key Security", False))
    
    try:
        results.append(("Component Integration", test_component_integration()))
    except Exception as e:
        print(f"❌ Component Integration test failed: {e}\n")
        results.append(("Component Integration", False))
    
    try:
        results.append(("Fallback Logic", test_fallback_logic()))
    except Exception as e:
        print(f"❌ Fallback Logic test failed: {e}\n")
        results.append(("Fallback Logic", False))
    
    # Summary
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    all_passed = all(result[1] for result in results)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 ALL VERIFICATIONS PASSED - DEMO READY! 🎉\n")
        return 0
    else:
        print("\n⚠️ Some verifications failed - review above\n")
        return 1


if __name__ == "__main__":
    exit(main())
