"""
SmartInsight model for weather-market-api-integration feature.

Requirements: 5.1, 5.6, 5.7
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any


@dataclass
class SmartInsight:
    """
    Data model for Smart AI Insight recommendations.
    
    Attributes:
        recommendation: Marathi recommendation text
        recommendation_en: English recommendation text
        prophet_change: Predicted price change percentage
        rain_probability: Current rain probability percentage
        confidence: Confidence level ("high", "medium", "low")
        timestamp: When the insight was generated
    """
    recommendation: str
    recommendation_en: str
    prophet_change: float
    rain_probability: float
    confidence: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SmartInsight to dictionary.
        
        Returns:
            Dictionary representation with timestamp as ISO string
        """
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SmartInsight':
        """
        Create SmartInsight from dictionary.
        
        Args:
            data: Dictionary with smart insight data
            
        Returns:
            SmartInsight instance
        """
        # Convert timestamp string back to datetime
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
