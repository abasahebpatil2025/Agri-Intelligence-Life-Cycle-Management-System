"""
Weather Client Component

Fetches current weather and forecast data from OpenWeatherMap API.
Integrates with CacheLayer and CloudLogger.
Includes Marathi translations for weather descriptions.

Requirements: 3.1, 3.2, 3.3, 3.4, 16.2
"""

import requests
import pandas as pd
import time
from datetime import datetime
from typing import Optional, Dict, Any


class WeatherClient:
    """
    Client for OpenWeatherMap API with caching and retry logic.
    
    Fetches current weather and forecast data.
    Provides Marathi translations for weather descriptions.
    """
    
    # Marathi translations for common weather descriptions
    WEATHER_TRANSLATIONS = {
        'clear sky': 'निरभ्र आकाश',
        'few clouds': 'थोडे ढग',
        'scattered clouds': 'विखुरलेले ढग',
        'broken clouds': 'तुटलेले ढग',
        'overcast clouds': 'ढगाळ',
        'light rain': 'हलका पाऊस',
        'moderate rain': 'मध्यम पाऊस',
        'heavy rain': 'मुसळधार पाऊस',
        'thunderstorm': 'वादळी पाऊस',
        'drizzle': 'रिमझिम पाऊस',
        'mist': 'धुके',
        'fog': 'दाट धुके',
        'haze': 'धुसर',
        'smoke': 'धूर',
        'dust': 'धूळ',
        'sand': 'वाळू',
        'snow': 'बर्फ',
        'light snow': 'हलका बर्फ',
        'heavy snow': 'जोरदार बर्फ',
        'rain': 'पाऊस',
        'clouds': 'ढग'
    }
    
    def __init__(self, api_key: str, cache=None, logger=None):
        """
        Initialize Weather Client.
        
        Args:
            api_key: OpenWeatherMap API key
            cache: Optional CacheLayer instance
            logger: Optional CloudLogger instance
        """
        self.api_key = api_key
        self.cache = cache
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Agri-Intelligence-System/1.0',
            'Accept': 'application/json'
        })
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
        
        # OpenWeatherMap API endpoints
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.current_weather_endpoint = f"{self.base_url}/weather"
        self.forecast_endpoint = f"{self.base_url}/forecast"
    
    def _retry_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Execute HTTP request with exponential backoff retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object or None if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                response.raise_for_status()
                
                # Log successful request
                if self.logger:
                    self.logger.log_ml_operation(
                        operation='weather_api_request',
                        duration=0.0,
                        details={
                            'url': url,
                            'method': method,
                            'attempt': attempt + 1,
                            'status_code': response.status_code
                        }
                    )
                
                return response
            
            except requests.exceptions.RequestException as e:
                last_error = e
                
                # Log error
                if self.logger:
                    self.logger.log_ml_operation(
                        operation='weather_api_request',
                        duration=0.0,
                        details={
                            'url': url,
                            'method': method,
                            'attempt': attempt + 1
                        },
                        error=str(e)
                    )
                
                # Retry with exponential backoff
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
                else:
                    return None
        
        return None
    
    def _translate_to_marathi(self, description: str) -> str:
        """
        Translate weather description to Marathi.
        
        Args:
            description: English weather description
            
        Returns:
            Marathi translation or original if not found
        """
        description_lower = description.lower()
        return self.WEATHER_TRANSLATIONS.get(description_lower, description)
    
    def fetch_current_weather(self, city_name: str) -> Dict[str, Any]:
        """
        Fetch current weather for a city.
        
        Args:
            city_name: City name (e.g., 'Nashik', 'Mumbai')
            
        Returns:
            Dictionary with weather data:
            - temp: Temperature in Celsius
            - humidity: Humidity percentage
            - description: Weather description in English
            - description_mr: Weather description in Marathi
            - icon: Weather icon code
            - precipitation: Precipitation in mm (if available)
            - wind_speed: Wind speed in m/s
            - pressure: Atmospheric pressure in hPa
        """
        try:
            # Check cache first (30-minute TTL)
            cache_key = f"current_weather_{city_name}"
            if self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # Build request parameters
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric',  # Celsius
                'lang': 'en'
            }
            
            # Make API request
            response = self._retry_request('GET', self.current_weather_endpoint, params=params)
            
            if response is None:
                # Fallback to cached data if available (even if expired)
                if self.cache:
                    # Try to get expired cache data
                    for key, value in self.cache.cache.items():
                        if key == cache_key:
                            if self.logger:
                                self.logger.log_ml_operation(
                                    operation='weather_cache_fallback',
                                    duration=0.0,
                                    details={'city': city_name, 'reason': 'API failure'}
                                )
                            return value['value']
                
                # Return empty dict if no cache available
                return {}
            
            data = response.json()
            
            # Extract weather information
            weather_data = {
                'temp': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'description_mr': self._translate_to_marathi(data['weather'][0]['description']),
                'icon': data['weather'][0]['icon'],
                'precipitation': data.get('rain', {}).get('1h', 0),  # Rain in last hour
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'feels_like': data['main']['feels_like'],
                'temp_min': data['main']['temp_min'],
                'temp_max': data['main']['temp_max']
            }
            
            # Cache for 30 minutes
            if self.cache:
                self.cache.set(cache_key, weather_data, 1800)
            
            return weather_data
        
        except Exception as e:
            if self.logger:
                self.logger.log_ml_operation(
                    operation='fetch_current_weather',
                    duration=0.0,
                    details={'city': city_name},
                    error=str(e)
                )
            
            # Try cache fallback on any error
            if self.cache:
                cache_key = f"current_weather_{city_name}"
                for key, value in self.cache.cache.items():
                    if key == cache_key:
                        return value['value']
            
            return {}
    
    def fetch_forecast(self, city_name: str, days: int = 5) -> pd.DataFrame:
        """
        Fetch weather forecast for a city.
        
        Args:
            city_name: City name (e.g., 'Nashik', 'Mumbai')
            days: Number of days to forecast (max 5)
            
        Returns:
            DataFrame with forecast data (3-hour intervals):
            - datetime: Forecast datetime
            - temp: Temperature in Celsius
            - humidity: Humidity percentage
            - description: Weather description in English
            - description_mr: Weather description in Marathi
            - precipitation: Precipitation probability (0-1)
            - wind_speed: Wind speed in m/s
            - pressure: Atmospheric pressure in hPa
        """
        try:
            # Check cache first (30-minute TTL)
            cache_key = f"forecast_{city_name}_{days}"
            if self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # Build request parameters
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric',  # Celsius
                'lang': 'en',
                'cnt': min(days * 8, 40)  # 8 intervals per day (3-hour), max 40
            }
            
            # Make API request
            response = self._retry_request('GET', self.forecast_endpoint, params=params)
            
            if response is None:
                # Fallback to cached data if available (even if expired)
                if self.cache:
                    for key, value in self.cache.cache.items():
                        if key == cache_key:
                            if self.logger:
                                self.logger.log_ml_operation(
                                    operation='forecast_cache_fallback',
                                    duration=0.0,
                                    details={'city': city_name, 'reason': 'API failure'}
                                )
                            return value['value']
                
                # Return empty DataFrame if no cache available
                return pd.DataFrame(columns=['datetime', 'temp', 'humidity', 'description', 
                                            'description_mr', 'precipitation', 'wind_speed', 'pressure'])
            
            data = response.json()
            
            # Extract forecast data
            forecast_list = []
            for item in data['list']:
                forecast_list.append({
                    'datetime': item['dt_txt'],
                    'temp': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'description': item['weather'][0]['description'],
                    'description_mr': self._translate_to_marathi(item['weather'][0]['description']),
                    'precipitation': item.get('pop', 0),  # Probability of precipitation
                    'wind_speed': item['wind']['speed'],
                    'pressure': item['main']['pressure'],
                    'feels_like': item['main']['feels_like'],
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max']
                })
            
            # Convert to DataFrame
            df = pd.DataFrame(forecast_list)
            
            # Cache for 30 minutes
            if self.cache:
                self.cache.set(cache_key, df, 1800)
            
            return df
        
        except Exception as e:
            if self.logger:
                self.logger.log_ml_operation(
                    operation='fetch_forecast',
                    duration=0.0,
                    details={'city': city_name, 'days': days},
                    error=str(e)
                )
            
            # Try cache fallback on any error
            if self.cache:
                cache_key = f"forecast_{city_name}_{days}"
                for key, value in self.cache.cache.items():
                    if key == cache_key:
                        return value['value']
            
            return pd.DataFrame(columns=['datetime', 'temp', 'humidity', 'description', 
                                        'description_mr', 'precipitation', 'wind_speed', 'pressure'])
    
    def get_weather_summary(self, city_name: str) -> Dict[str, Any]:
        """
        Get a comprehensive weather summary for a city.
        
        Args:
            city_name: City name
            
        Returns:
            Dictionary with current weather and forecast summary
        """
        current = self.fetch_current_weather(city_name)
        forecast = self.fetch_forecast(city_name, days=3)
        
        summary = {
            'current': current,
            'forecast_available': not forecast.empty,
            'forecast_periods': len(forecast) if not forecast.empty else 0
        }
        
        if not forecast.empty:
            summary['avg_temp_next_24h'] = forecast.head(8)['temp'].mean()
            summary['max_temp_next_24h'] = forecast.head(8)['temp'].max()
            summary['min_temp_next_24h'] = forecast.head(8)['temp'].min()
            summary['rain_probability_next_24h'] = forecast.head(8)['precipitation'].max()
        
        return summary
