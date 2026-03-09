"""
WeatherAPIClient for OpenWeatherMap API integration.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import requests
from datetime import datetime, timezone
from typing import Optional
from src.models.weather_data import WeatherData
from src.models.exceptions import APIError
from src.models.translations import translate_weather_description


class WeatherAPIClient:
    """
    Client for fetching weather data from OpenWeatherMap API.
    
    This client handles:
    - Current weather data fetching
    - API authentication
    - Response parsing
    - Rain probability calculation
    - Error handling (HTTP errors, network errors)
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    TIMEOUT = 10  # seconds
    
    def __init__(self, api_key: str):
        """
        Initialize WeatherAPIClient with API key.
        
        Args:
            api_key: OpenWeatherMap API key from st.secrets
            
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        self.api_key = api_key
    
    def get_current_weather(self, location: str) -> WeatherData:
        """
        Fetch current weather data for a location.
        
        Args:
            location: City name (e.g., "Nashik", "Mumbai")
            
        Returns:
            WeatherData object with current weather information
            
        Raises:
            APIError: When API request fails (network, HTTP errors, parsing errors)
        """
        if not location:
            raise ValueError("Location cannot be empty")
        
        try:
            url = self._build_request_url(location)
            response = requests.get(url, timeout=self.TIMEOUT)
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise APIError(
                    "Invalid API key",
                    api_name="Weather",
                    status_code=401
                )
            elif response.status_code == 404:
                raise APIError(
                    f"Location '{location}' not found",
                    api_name="Weather",
                    status_code=404
                )
            elif response.status_code == 429:
                raise APIError(
                    "API rate limit exceeded",
                    api_name="Weather",
                    status_code=429
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"HTTP error {response.status_code}",
                    api_name="Weather",
                    status_code=response.status_code
                )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            return self._parse_response(response_data, location)
            
        except requests.Timeout:
            raise APIError(
                "Request timeout - API is slow or unresponsive",
                api_name="Weather"
            )
        except requests.ConnectionError:
            raise APIError(
                "Connection error - check internet connection",
                api_name="Weather"
            )
        except requests.RequestException as e:
            raise APIError(
                f"Request failed: {str(e)}",
                api_name="Weather"
            )
        except (KeyError, ValueError, TypeError) as e:
            raise APIError(
                f"Failed to parse API response: {str(e)}",
                api_name="Weather"
            )
    
    def _build_request_url(self, location: str) -> str:
        """
        Build API request URL with parameters.
        
        Args:
            location: City name
            
        Returns:
            Complete URL with query parameters
        """
        params = {
            "q": location,
            "appid": self.api_key,
            "units": "metric"  # Celsius
        }
        
        # Build URL with parameters
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.BASE_URL}?{param_str}"
    
    def _parse_response(self, response: dict, location: str) -> WeatherData:
        """
        Parse API response into WeatherData object.
        
        Args:
            response: JSON response from OpenWeatherMap API
            location: City name
            
        Returns:
            WeatherData object
            
        Raises:
            KeyError: If required fields are missing
            ValueError: If data types are invalid
        """
        # Extract temperature and humidity
        temperature = float(response["main"]["temp"])
        humidity = int(response["main"]["humidity"])
        
        # Extract weather description
        description = response["weather"][0]["description"]
        description_marathi = translate_weather_description(description)
        
        # Calculate rain probability
        rain_probability = self._calculate_rain_probability(response)
        
        # Create WeatherData object
        return WeatherData(
            temperature=temperature,
            humidity=humidity,
            description=description,
            description_marathi=description_marathi,
            rain_probability=rain_probability,
            timestamp=datetime.now(timezone.utc),
            location=location
        )
    
    def _calculate_rain_probability(self, response: dict) -> float:
        """
        Calculate rain probability from API response.
        
        Rain probability is calculated based on:
        1. If 'rain' object present: probability = min(rain["1h"] * 20, 100)
        2. If clouds > 80%: probability = 70%
        3. If clouds > 60%: probability = 50%
        4. Otherwise: probability = 20%
        
        Args:
            response: JSON response from OpenWeatherMap API
            
        Returns:
            Rain probability as percentage (0-100)
        """
        # Check if rain data is present
        if "rain" in response and "1h" in response["rain"]:
            rain_1h = response["rain"]["1h"]  # mm of rain in last hour
            # Convert mm to probability (rough heuristic: 1mm = 20% probability)
            probability = min(rain_1h * 20, 100)
            return round(probability, 1)
        
        # Fallback to cloud coverage
        if "clouds" in response and "all" in response["clouds"]:
            cloud_coverage = response["clouds"]["all"]
            
            if cloud_coverage > 80:
                return 70.0
            elif cloud_coverage > 60:
                return 50.0
            else:
                return 20.0
        
        # Default low probability
        return 20.0
