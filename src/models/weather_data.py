"""
WeatherData model for weather-market-api-integration feature.

Requirements: 1.1, 1.3, 1.4, 1.5
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any


@dataclass
class WeatherData:
    """
    Data model for weather information.
    
    Attributes:
        temperature: Temperature in Celsius (range: -50 to 60)
        humidity: Humidity percentage (range: 0 to 100)
        description: Weather description in English
        description_marathi: Weather description in Marathi
        rain_probability: Rain probability percentage (range: 0 to 100)
        timestamp: When the data was fetched (UTC)
        location: City name
    """
    temperature: float
    humidity: int
    description: str
    description_marathi: str
    rain_probability: float
    timestamp: datetime
    location: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert WeatherData to dictionary.
        
        Returns:
            Dictionary representation with timestamp as ISO string
        """
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherData':
        """
        Create WeatherData from dictionary.
        
        Args:
            data: Dictionary with weather data
            
        Returns:
            WeatherData instance
        """
        # Convert timestamp string back to datetime
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
