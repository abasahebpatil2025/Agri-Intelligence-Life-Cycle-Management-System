"""
Unit tests for Market Locator Component

Tests market discovery, distance calculation, rate comparison.
Property-based tests for distance and sorting correctness.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings

# Import the component
import sys
sys.path.insert(0, 'src')
from market_locator import MarketLocator


class TestMarketLocator:
    """Test suite for MarketLocator component"""
    
    def test_initialization(self):
        """Test market locator initialization"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        assert locator.agmarknet_client == mock_client
        assert locator.avg_speed_kmh == 40
        assert len(locator.markets) > 0
    
    def test_load_market_locations(self):
        """Test loading market locations from JSON"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        markets = locator.markets
        
        assert isinstance(markets, list)
        assert len(markets) > 0
        
        # Check first market has required fields
        market = markets[0]
        assert 'market_name' in market
        assert 'latitude' in market
        assert 'longitude' in market
        assert 'district' in market
    
    def test_load_market_locations_from_cache(self):
        """Test loading market locations from cache"""
        mock_client = Mock()
        mock_cache = Mock()
        
        cached_markets = [
            {
                'market_name': 'Test APMC',
                'latitude': 20.0,
                'longitude': 75.0,
                'district': 'Test'
            }
        ]
        mock_cache.get = Mock(return_value=cached_markets)
        
        locator = MarketLocator(agmarknet_client=mock_client, cache=mock_cache)
        
        assert locator.markets == cached_markets
        mock_cache.get.assert_called_once_with('apmc_markets')
    
    def test_calculate_distance(self):
        """Test distance calculation between coordinates"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Nashik to Pune (approx 180-190 km)
        nashik = (20.1391, 74.2364)
        pune = (18.5204, 73.8567)
        
        distance = locator.calculate_distance(nashik, pune)
        
        assert distance > 0
        assert 180 <= distance <= 190  # Approximate range
    
    def test_calculate_distance_same_location(self):
        """Test distance calculation for same location"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        location = (20.0, 75.0)
        distance = locator.calculate_distance(location, location)
        
        assert distance == 0.0
    
    def test_calculate_travel_time(self):
        """Test travel time estimation"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # 40 km at 40 km/hr = 60 minutes
        travel_time = locator._calculate_travel_time(40.0)
        
        assert travel_time == 60
    
    def test_calculate_travel_time_zero_distance(self):
        """Test travel time for zero distance"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        travel_time = locator._calculate_travel_time(0.0)
        
        assert travel_time == 0
    
    def test_geocode_location_success(self):
        """Test successful location geocoding"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Mock geocoder result
        mock_result = Mock()
        mock_result.latitude = 20.1391
        mock_result.longitude = 74.2364
        
        with patch.object(locator.geocoder, 'geocode', return_value=mock_result):
            coords = locator._geocode_location("Nashik, Maharashtra")
        
        assert coords is not None
        assert coords == (20.1391, 74.2364)
    
    def test_geocode_location_failure(self):
        """Test geocoding failure returns None"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        with patch.object(locator.geocoder, 'geocode', return_value=None):
            coords = locator._geocode_location("Invalid Location")
        
        assert coords is None
    
    def test_geocode_location_from_cache(self):
        """Test geocoding retrieves from cache"""
        mock_client = Mock()
        mock_cache = Mock()
        
        cached_coords = (20.1391, 74.2364)
        mock_cache.get = Mock(return_value=cached_coords)
        
        locator = MarketLocator(agmarknet_client=mock_client, cache=mock_cache)
        
        coords = locator._geocode_location("Nashik, Maharashtra")
        
        assert coords == cached_coords
        mock_cache.get.assert_called()
    
    def test_find_nearest_markets_success(self):
        """Test finding nearest markets"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Mock geocoding
        mock_result = Mock()
        mock_result.latitude = 20.1391
        mock_result.longitude = 74.2364
        
        with patch.object(locator.geocoder, 'geocode', return_value=mock_result):
            markets = locator.find_nearest_markets("Nashik, Maharashtra", count=5)
        
        assert len(markets) == 5
        
        # Check first market has required fields
        market = markets[0]
        assert 'market_name' in market
        assert 'distance_km' in market
        assert 'latitude' in market
        assert 'longitude' in market
        assert 'travel_time_minutes' in market
        assert 'district' in market
    
    def test_find_nearest_markets_sorted_by_distance(self):
        """Test markets are sorted by distance"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Mock geocoding
        mock_result = Mock()
        mock_result.latitude = 20.1391
        mock_result.longitude = 74.2364
        
        with patch.object(locator.geocoder, 'geocode', return_value=mock_result):
            markets = locator.find_nearest_markets("Nashik, Maharashtra", count=5)
        
        # Verify sorted in ascending order
        distances = [m['distance_km'] for m in markets]
        assert distances == sorted(distances)
    
    def test_find_nearest_markets_geocoding_failure(self):
        """Test find_nearest_markets returns empty list on geocoding failure"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        with patch.object(locator.geocoder, 'geocode', return_value=None):
            markets = locator.find_nearest_markets("Invalid Location")
        
        assert markets == []
    
    def test_get_market_rates_success(self):
        """Test fetching market rates"""
        mock_client = Mock()
        
        # Mock Agmarknet client response
        mock_df = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500],
            'market': ['Nashik']
        })
        mock_client.fetch_live_prices = Mock(return_value=mock_df)
        
        locator = MarketLocator(agmarknet_client=mock_client)
        
        rates = locator.get_market_rates(['Nashik', 'Pune'], 'Onion')
        
        assert not rates.empty
        assert 'market' in rates.columns
        assert 'price' in rates.columns
    
    def test_get_market_rates_empty_markets(self):
        """Test get_market_rates with empty market list"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        rates = locator.get_market_rates([], 'Onion')
        
        assert rates.empty
        assert list(rates.columns) == ['market', 'commodity', 'price', 'date']
    
    def test_get_market_rates_api_failure(self):
        """Test get_market_rates handles API failures"""
        mock_client = Mock()
        mock_client.fetch_live_prices = Mock(side_effect=Exception("API Error"))
        
        locator = MarketLocator(agmarknet_client=mock_client)
        
        rates = locator.get_market_rates(['Nashik'], 'Onion')
        
        assert rates.empty
    
    def test_compare_rates_success(self):
        """Test rate comparison"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        rates_df = pd.DataFrame({
            'market': ['Nashik', 'Pune', 'Mumbai'],
            'price': [2500, 2700, 2600],
            'commodity': ['Onion', 'Onion', 'Onion']
        })
        
        comparison = locator.compare_rates(rates_df)
        
        assert comparison['best_market'] == 'Pune'
        assert comparison['best_price'] == 2700
        assert comparison['avg_price'] == 2600.0
        assert comparison['price_range'] == (2500.0, 2700.0)
        assert comparison['market_count'] == 3
    
    def test_compare_rates_empty_dataframe(self):
        """Test compare_rates with empty DataFrame"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        rates_df = pd.DataFrame(columns=['market', 'price', 'commodity'])
        
        comparison = locator.compare_rates(rates_df)
        
        assert comparison['best_market'] is None
        assert comparison['best_price'] == 0.0
        assert comparison['market_count'] == 0
    
    def test_compare_rates_single_market(self):
        """Test compare_rates with single market"""
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        rates_df = pd.DataFrame({
            'market': ['Nashik'],
            'price': [2500],
            'commodity': ['Onion']
        })
        
        comparison = locator.compare_rates(rates_df)
        
        assert comparison['best_market'] == 'Nashik'
        assert comparison['best_price'] == 2500
        assert comparison['avg_price'] == 2500.0
        assert comparison['price_range'] == (2500.0, 2500.0)


# Property-Based Tests
class TestMarketLocatorProperties:
    """Property-based tests for Market Locator"""
    
    @settings(deadline=None, max_examples=20)
    @given(
        lat1=st.floats(min_value=15.0, max_value=25.0, allow_nan=False, allow_infinity=False),
        lon1=st.floats(min_value=70.0, max_value=80.0, allow_nan=False, allow_infinity=False),
        lat2=st.floats(min_value=15.0, max_value=25.0, allow_nan=False, allow_infinity=False),
        lon2=st.floats(min_value=70.0, max_value=80.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_distance_non_negative(self, lat1, lon1, lat2, lon2):
        """
        Property 44: Market Distance Calculation
        
        GIVEN any two valid coordinates
        WHEN distance is calculated
        THEN distance is non-negative
        
        Validates: Requirements 25.1, 25.4
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        origin = (lat1, lon1)
        destination = (lat2, lon2)
        
        distance = locator.calculate_distance(origin, destination)
        
        assert distance >= 0.0
    
    @settings(deadline=None, max_examples=20)
    @given(
        lat=st.floats(min_value=15.0, max_value=25.0, allow_nan=False, allow_infinity=False),
        lon=st.floats(min_value=70.0, max_value=80.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_distance_same_location_zero(self, lat, lon):
        """
        Property 44: Market Distance Calculation (Same Location)
        
        GIVEN same coordinates for origin and destination
        WHEN distance is calculated
        THEN distance is zero
        
        Validates: Requirements 25.1, 25.4
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        location = (lat, lon)
        distance = locator.calculate_distance(location, location)
        
        assert distance == 0.0
    
    @settings(deadline=None, max_examples=20)
    @given(
        distance_km=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_travel_time_proportional(self, distance_km):
        """
        Property: Travel Time Calculation
        
        GIVEN any positive distance >= 1 km
        WHEN travel time is calculated
        THEN travel time is proportional to distance
        
        Validates: Requirements 25.4
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        travel_time = locator._calculate_travel_time(distance_km)
        
        # Travel time should be distance / 40 * 60 minutes
        expected_time = round((distance_km / 40) * 60)
        
        assert travel_time == expected_time
        assert travel_time > 0
    
    @settings(deadline=None, max_examples=20)
    @given(
        num_markets=st.integers(min_value=1, max_value=10)
    )
    def test_property_compare_rates_identifies_max(self, num_markets):
        """
        Property 46: Market Rate Comparison
        
        GIVEN any set of market rates
        WHEN rates are compared
        THEN best_market has the highest price
        
        Validates: Requirements 26.4
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Generate market rates with known max
        prices = [2000 + i * 100 for i in range(num_markets)]
        markets = [f'Market_{i}' for i in range(num_markets)]
        
        rates_df = pd.DataFrame({
            'market': markets,
            'price': prices,
            'commodity': ['Onion'] * num_markets
        })
        
        comparison = locator.compare_rates(rates_df)
        
        # Best market should have the highest price
        assert comparison['best_price'] == max(prices)
        
        # Find market with max price
        max_idx = rates_df['price'].idxmax()
        expected_best = rates_df.loc[max_idx, 'market']
        
        assert comparison['best_market'] == expected_best
    
    @settings(deadline=None, max_examples=10)
    @given(
        count=st.integers(min_value=1, max_value=10)
    )
    def test_property_nearest_markets_count(self, count):
        """
        Property 45: Nearest Markets Sorting
        
        GIVEN a request for N nearest markets
        WHEN markets are found
        THEN exactly N markets are returned (or fewer if not enough markets exist)
        
        Validates: Requirements 25.2, 25.3
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Mock geocoding
        mock_result = Mock()
        mock_result.latitude = 20.0
        mock_result.longitude = 75.0
        
        with patch.object(locator.geocoder, 'geocode', return_value=mock_result):
            markets = locator.find_nearest_markets("Test Location", count=count)
        
        # Should return at most 'count' markets
        assert len(markets) <= count
        
        # If we have enough markets, should return exactly 'count'
        if len(locator.markets) >= count:
            assert len(markets) == count
    
    def test_property_nearest_markets_sorted_ascending(self):
        """
        Property 62: Nearest Markets Sorting (Ascending Order)
        
        GIVEN any farmer location
        WHEN nearest markets are found
        THEN markets are sorted by distance in ascending order
        
        Validates: Requirements 25.3
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Mock geocoding
        mock_result = Mock()
        mock_result.latitude = 20.0
        mock_result.longitude = 75.0
        
        with patch.object(locator.geocoder, 'geocode', return_value=mock_result):
            markets = locator.find_nearest_markets("Test Location", count=5)
        
        if len(markets) > 1:
            distances = [m['distance_km'] for m in markets]
            
            # Verify sorted in ascending order
            for i in range(len(distances) - 1):
                assert distances[i] <= distances[i + 1]
    
    def test_property_market_data_completeness(self):
        """
        Property 63: Market Data Completeness
        
        GIVEN any market returned by find_nearest_markets
        WHEN market data is examined
        THEN all required fields are present
        
        Validates: Requirements 25.4
        """
        mock_client = Mock()
        locator = MarketLocator(agmarknet_client=mock_client)
        
        # Mock geocoding
        mock_result = Mock()
        mock_result.latitude = 20.0
        mock_result.longitude = 75.0
        
        with patch.object(locator.geocoder, 'geocode', return_value=mock_result):
            markets = locator.find_nearest_markets("Test Location", count=5)
        
        required_fields = [
            'market_name',
            'distance_km',
            'latitude',
            'longitude',
            'travel_time_minutes',
            'district'
        ]
        
        for market in markets:
            for field in required_fields:
                assert field in market
                assert market[field] is not None
