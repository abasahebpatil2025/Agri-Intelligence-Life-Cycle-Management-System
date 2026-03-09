"""
Market Locator Component

Finds nearest APMC markets using geopy and fetches live rates.
Calculates distances, estimates travel time, and compares market rates.

Requirements: 25.1, 25.2, 25.3, 25.4, 26.1, 26.2, 26.3, 26.4
"""

import json
import os
from typing import List, Dict, Optional, Tuple
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class MarketLocator:
    """
    Locates nearest APMC markets and fetches live commodity rates.
    
    Features:
    - Finds nearest markets using geopy geodesic distance
    - Geocodes farmer location strings to coordinates
    - Estimates travel time based on distance
    - Fetches live market rates from Agmarknet
    - Compares rates across markets to find best prices
    - Caches market locations for performance
    """
    
    def __init__(self, agmarknet_client, cache=None):
        """
        Initialize MarketLocator.
        
        Args:
            agmarknet_client: AgmarknetClient instance for fetching rates
            cache: Optional CacheLayer instance for caching
        """
        self.agmarknet_client = agmarknet_client
        self.cache = cache
        
        # Initialize geocoder with user agent
        self.geocoder = Nominatim(user_agent="agri-intelligence-system")
        
        # Load APMC market locations
        self.markets = self._load_market_data()
        
        # Average travel speed in km/hr
        self.avg_speed_kmh = 40
    
    def _load_market_data(self) -> List[Dict]:
        """
        Load APMC market locations from JSON file or cache.
        
        Returns:
            List of market dictionaries with name, latitude, longitude, district
        """
        # Check cache first
        if self.cache:
            cached_markets = self.cache.get('apmc_markets')
            if cached_markets is not None:
                return cached_markets
        
        # Try multiple possible paths
        possible_paths = [
            'data/apmc_markets.json',
            '../data/apmc_markets.json',
            os.path.join(os.path.dirname(__file__), '..', 'data', 'apmc_markets.json')
        ]
        
        markets = []
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    markets = json.load(f)
                    break
        
        # Cache for 7 days if found
        if markets and self.cache:
            self.cache.set('apmc_markets', markets, 604800)
        
        return markets
    
    def _parse_location(self, location_string: str) -> Optional[Tuple[float, float]]:
        """
        Parse location string to coordinates using geocoding.
        
        Args:
            location_string: Location as string (e.g., "Pune, Maharashtra")
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        # Check cache first
        cache_key = f"geocode_{location_string}"
        if self.cache:
            cached_coords = self.cache.get(cache_key)
            if cached_coords is not None:
                return cached_coords
        
        try:
            # Geocode the location
            location = self.geocoder.geocode(location_string, timeout=10)
            
            if location:
                coords = (location.latitude, location.longitude)
                
                # Cache for 7 days (locations don't change)
                if self.cache:
                    self.cache.set(cache_key, coords, 604800)
                
                return coords
            
            return None
        
        except (GeocoderTimedOut, GeocoderServiceError):
            return None
    
    def _geocode_location(self, location_string: str) -> Optional[Tuple[float, float]]:
        """
        Alias for _parse_location for backward compatibility.
        
        Args:
            location_string: Location as string (e.g., "Pune, Maharashtra")
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        return self._parse_location(location_string)
    
    def calculate_distance(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
        """
        Calculate geodesic distance between two coordinates.
        
        Args:
            origin: Tuple of (latitude, longitude)
            destination: Tuple of (latitude, longitude)
            
        Returns:
            Distance in kilometers
        """
        return geodesic(origin, destination).kilometers
    
    def _estimate_travel_time(self, distance_km: float) -> float:
        """
        Estimate travel time based on distance.
        
        Args:
            distance_km: Distance in kilometers
            
        Returns:
            Estimated travel time in minutes
        """
        # Formula: (distance_km / avg_speed_kmh) * 60
        return round((distance_km / self.avg_speed_kmh) * 60)
    
    def _calculate_travel_time(self, distance_km: float) -> float:
        """
        Alias for _estimate_travel_time for backward compatibility.
        
        Args:
            distance_km: Distance in kilometers
            
        Returns:
            Estimated travel time in minutes
        """
        return self._estimate_travel_time(distance_km)
    
    def find_nearest_markets(
        self,
        farmer_location: str,
        count: int = 5
    ) -> List[Dict]:
        """
        Find nearest APMC markets to farmer location.
        
        Args:
            farmer_location: Location string (e.g., "Pune, Maharashtra")
            count: Number of nearest markets to return (default: 5)
            
        Returns:
            List of market dictionaries with:
            - market_name: Name of the market
            - distance_km: Distance in kilometers
            - latitude: Market latitude
            - longitude: Market longitude
            - travel_time_minutes: Estimated travel time in minutes
        """
        # Parse farmer location to coordinates
        farmer_coords = self._parse_location(farmer_location)
        
        if not farmer_coords:
            return []
        
        # Calculate distances to all markets
        market_distances = []
        
        for market in self.markets:
            market_coords = (market['latitude'], market['longitude'])
            distance = self.calculate_distance(farmer_coords, market_coords)
            travel_time = self._estimate_travel_time(distance)
            
            market_distances.append({
                'market_name': market['market_name'],
                'distance_km': round(distance, 2),
                'latitude': market['latitude'],
                'longitude': market['longitude'],
                'travel_time_minutes': round(travel_time, 1),
                'district': market.get('district', '')
            })
        
        # Sort by distance (ascending)
        market_distances.sort(key=lambda x: x['distance_km'])
        
        # Return top N markets
        return market_distances[:count]
    
    def get_market_rates(
        self,
        markets: List[str],
        commodity: str
    ) -> pd.DataFrame:
        """
        Fetch live rates for markets from Agmarknet.
        
        Args:
            markets: List of market names (strings)
            commodity: Commodity name (e.g., 'Onion')
            
        Returns:
            DataFrame with columns: market, commodity, price, date
        """
        if not markets:
            return pd.DataFrame(columns=['market', 'commodity', 'price', 'date'])
        
        all_rates = []
        
        for market_name in markets:
            try:
                # Fetch live prices for this market
                rates_df = self.agmarknet_client.fetch_live_prices(
                    commodity=commodity,
                    market=market_name
                )
                
                if not rates_df.empty:
                    # Ensure commodity column exists
                    if 'commodity' not in rates_df.columns:
                        rates_df['commodity'] = commodity
                    
                    # Add market info if not present
                    if 'market' not in rates_df.columns or rates_df['market'].isnull().all():
                        rates_df['market'] = market_name
                    
                    all_rates.append(rates_df)
            
            except Exception:
                # Skip markets that fail
                continue
        
        # Combine all rates
        if all_rates:
            combined_df = pd.concat(all_rates, ignore_index=True)
            
            # Ensure all required columns exist
            for col in ['market', 'commodity', 'price', 'date']:
                if col not in combined_df.columns:
                    combined_df[col] = None
            
            return combined_df[['market', 'commodity', 'price', 'date']]
        
        return pd.DataFrame(columns=['market', 'commodity', 'price', 'date'])
    
    def compare_rates(self, rates_df: pd.DataFrame) -> Dict:
        """
        Compare rates across markets and identify highest price.
        
        Args:
            rates_df: DataFrame with market rates (columns: market, price, commodity, date)
            
        Returns:
            Dictionary with:
            - best_market: Market with highest price
            - best_price: Highest price value
            - avg_price: Average price across all markets
            - price_range: Tuple of (min_price, max_price)
            - market_count: Number of markets
        """
        if rates_df.empty:
            return {
                'best_market': None,
                'best_price': 0.0,
                'avg_price': 0.0,
                'price_range': (0.0, 0.0),
                'market_count': 0
            }
        
        # Group by market and get average price
        market_avg_prices = rates_df.groupby('market')['price'].mean().reset_index()
        market_avg_prices = market_avg_prices.sort_values('price', ascending=False)
        
        # Find market with highest price
        highest_market = market_avg_prices.iloc[0]
        
        # Calculate statistics
        all_prices = rates_df['price']
        avg_price = all_prices.mean()
        min_price = all_prices.min()
        max_price = all_prices.max()
        market_count = len(market_avg_prices)
        
        return {
            'best_market': highest_market['market'],
            'best_price': round(highest_market['price'], 2) if pd.notna(highest_market['price']) else 0.0,
            'avg_price': round(avg_price, 2) if pd.notna(avg_price) else 0.0,
            'price_range': (round(min_price, 2) if pd.notna(min_price) else 0.0, 
                           round(max_price, 2) if pd.notna(max_price) else 0.0),
            'market_count': market_count
        }
