"""
MarketPriceData model for weather-market-api-integration feature.

Requirements: 3.1, 3.3, 3.4
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any


@dataclass
class MarketPriceData:
    """
    Data model for market price information.
    
    Attributes:
        crop: Crop name (e.g., "Onion", "Tomato")
        price: Price per quintal in INR
        market_name: Market name (e.g., "Nashik APMC")
        location: City name
        timestamp: When the price was recorded
    """
    crop: str
    price: float
    market_name: str
    location: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert MarketPriceData to dictionary.
        
        Returns:
            Dictionary representation with timestamp as ISO string
        """
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketPriceData':
        """
        Create MarketPriceData from dictionary.
        
        Args:
            data: Dictionary with market price data
            
        Returns:
            MarketPriceData instance
        """
        # Convert timestamp string back to datetime
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
