"""
AgmarknetAPIClient for Agmarknet API integration.

Requirements: 3.1, 3.2, 3.3, 3.4
"""

import requests
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from src.models.market_price_data import MarketPriceData
from src.models.exceptions import APIError


class AgmarknetAPIClient:
    """
    Client for fetching market price data from Agmarknet API.
    
    This client handles:
    - Live market price data fetching
    - API authentication
    - Response parsing
    - Handling cases where crop/location has no data
    - Returning most recent price if today's data not available
    - Error handling (HTTP errors, network errors)
    """
    
    BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    TIMEOUT = 10  # seconds (reduced for faster response)
    
    def __init__(self, api_key: str):
        """
        Initialize AgmarknetAPIClient with API key.
        
        Args:
            api_key: Agmarknet API key from st.secrets
            
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        self.api_key = api_key
    
    def get_live_price(self, crop: str, location: str) -> MarketPriceData:
        """
        Fetch today's live market price for a crop.
        
        Args:
            crop: Crop name (e.g., "Onion", "Tomato")
            location: Market location (e.g., "Nashik")
            
        Returns:
            MarketPriceData object with price information
            
        Raises:
            APIError: When API request fails or no data available
        """
        if not crop:
            raise ValueError("Crop cannot be empty")
        if not location:
            raise ValueError("Location cannot be empty")
        
        try:
            params = self._build_request_params(crop, location)
            response = requests.get(self.BASE_URL, params=params, timeout=self.TIMEOUT)
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise APIError(
                    "Invalid API key",
                    api_name="Agmarknet",
                    status_code=401
                )
            elif response.status_code == 429:
                raise APIError(
                    "API rate limit exceeded",
                    api_name="Agmarknet",
                    status_code=429
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"HTTP error {response.status_code}",
                    api_name="Agmarknet",
                    status_code=response.status_code
                )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            return self._parse_response(response_data, crop, location)
            
        except requests.Timeout:
            raise APIError(
                "Request timeout - API is slow or unresponsive",
                api_name="Agmarknet"
            )
        except requests.ConnectionError:
            raise APIError(
                "Connection error - check internet connection",
                api_name="Agmarknet"
            )
        except requests.RequestException as e:
            raise APIError(
                f"Request failed: {str(e)}",
                api_name="Agmarknet"
            )
        except (KeyError, ValueError, TypeError) as e:
            raise APIError(
                f"Failed to parse API response: {str(e)}",
                api_name="Agmarknet"
            )
    
    def _build_request_params(self, crop: str, location: str) -> Dict[str, str]:
        """
        Build API request parameters.
        
        Args:
            crop: Crop name
            location: Market location
            
        Returns:
            Dictionary of request parameters
        """
        return {
            "api-key": self.api_key,
            "format": "json",
            "filters[commodity]": crop,
            "filters[market]": location,
            "limit": "100"  # Get recent records to find most recent price
        }
    
    def _parse_response(self, response: Dict[str, Any], crop: str, location: str) -> MarketPriceData:
        """
        Parse API response into MarketPriceData object.
        
        Returns the most recent price if today's data is not yet available.
        
        Args:
            response: JSON response from Agmarknet API
            crop: Crop name
            location: Market location
            
        Returns:
            MarketPriceData object
            
        Raises:
            APIError: If no data available for crop/location
            KeyError: If required fields are missing
            ValueError: If data types are invalid
        """
        # Check if records exist
        if "records" not in response or not response["records"]:
            raise APIError(
                f"No market data available for {crop} in {location}",
                api_name="Agmarknet"
            )
        
        records = response["records"]
        
        # Sort records by date to get most recent
        # Try to parse dates and sort
        records_with_dates = []
        for record in records:
            try:
                # Parse arrival_date field
                date_str = record.get("arrival_date", "")
                if date_str:
                    # Try different date formats
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                        except ValueError:
                            continue
                    
                    records_with_dates.append((date_obj, record))
            except (KeyError, ValueError):
                continue
        
        if not records_with_dates:
            raise APIError(
                f"No valid date records found for {crop} in {location}",
                api_name="Agmarknet"
            )
        
        # Sort by date descending (most recent first)
        records_with_dates.sort(key=lambda x: x[0], reverse=True)
        most_recent_date, most_recent_record = records_with_dates[0]
        
        # Extract price (try modal_price first, then max_price)
        price = None
        if "modal_price" in most_recent_record and most_recent_record["modal_price"]:
            try:
                price = float(most_recent_record["modal_price"])
            except (ValueError, TypeError):
                pass
        
        if price is None and "max_price" in most_recent_record and most_recent_record["max_price"]:
            try:
                price = float(most_recent_record["max_price"])
            except (ValueError, TypeError):
                pass
        
        if price is None:
            raise APIError(
                f"No valid price data found for {crop} in {location}",
                api_name="Agmarknet"
            )
        
        # Extract market name
        market_name = most_recent_record.get("market", location)
        
        # Create MarketPriceData object
        return MarketPriceData(
            crop=crop,
            price=price,
            market_name=market_name,
            location=location,
            timestamp=most_recent_date.replace(tzinfo=timezone.utc)
        )
