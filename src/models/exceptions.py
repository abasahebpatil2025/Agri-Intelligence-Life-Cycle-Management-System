"""
Exception classes for weather-market-api-integration feature.

Requirements: 8.2, 8.5
"""


class APIError(Exception):
    """
    Base exception class for API-related errors.
    
    Used for weather API and market API failures.
    """
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        """
        Initialize APIError.
        
        Args:
            message: Error message
            api_name: Name of the API that failed (e.g., "Weather", "Agmarknet")
            status_code: HTTP status code if applicable
        """
        self.message = message
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self):
        """String representation of the error."""
        if self.api_name and self.status_code:
            return f"{self.api_name} API Error ({self.status_code}): {self.message}"
        elif self.api_name:
            return f"{self.api_name} API Error: {self.message}"
        else:
            return f"API Error: {self.message}"
