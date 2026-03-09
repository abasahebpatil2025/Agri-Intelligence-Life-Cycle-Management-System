"""
Unit tests for Agmarknet Client Component

Tests API integration, caching, retry logic, and data validation.
Property-based tests for data quality.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime
from hypothesis import given, strategies as st, settings

# Import the component
import sys
sys.path.insert(0, 'src/components')
from agmarknet_client import AgmarknetClient


class TestAgmarknetClient:
    """Test suite for AgmarknetClient component"""
    
    def test_initialization(self):
        """Test client initialization"""
        client = AgmarknetClient(api_key="test-key")
        
        assert client.api_key == "test-key"
        assert client.max_retries == 3
        assert len(client.retry_delays) == 3
    
    def test_fetch_live_prices_success(self):
        """Test successful live prices fetch"""
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        
        client = AgmarknetClient(api_key="test-key", cache=mock_cache)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            'records': [
                {'arrival_date': '2024-01-01', 'modal_price': '2500', 'market_name': 'Nashik'},
                {'arrival_date': '2024-01-02', 'modal_price': '2600', 'market_name': 'Nashik'}
            ]
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            df = client.fetch_live_prices('Onion', 'Nashik')
        
        assert not df.empty
        assert len(df) == 2
        assert 'date' in df.columns
        assert 'price' in df.columns
        assert 'market' in df.columns
    
    def test_fetch_live_prices_from_cache(self):
        """Test live prices retrieved from cache"""
        cached_df = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [2500],
            'market': ['Nashik']
        })
        
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=cached_df)
        
        client = AgmarknetClient(api_key="test-key", cache=mock_cache)
        
        df = client.fetch_live_prices('Onion', 'Nashik')
        
        assert not df.empty
        assert len(df) == 1
        mock_cache.get.assert_called_once()
    
    def test_fetch_live_prices_api_failure(self):
        """Test live prices returns empty DataFrame on API failure"""
        client = AgmarknetClient(api_key="test-key")
        
        # Mock failed API response
        with patch.object(client.session, 'request', side_effect=Exception("API Error")):
            df = client.fetch_live_prices('Onion')
        
        assert df.empty
        assert list(df.columns) == ['date', 'price', 'market']
    
    def test_fetch_historical_prices_success(self):
        """Test successful historical prices fetch"""
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        
        client = AgmarknetClient(api_key="test-key", cache=mock_cache)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            'records': [
                {'arrival_date': '2024-01-01', 'modal_price': '2500', 'market_name': 'Nashik'},
                {'arrival_date': '2024-01-02', 'modal_price': '2600', 'market_name': 'Nashik'}
            ],
            'total': 2
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            df = client.fetch_historical_prices(
                'Onion',
                'Nashik',
                date(2024, 1, 1),
                date(2024, 1, 31)
            )
        
        assert not df.empty
        assert len(df) == 2
        # Verify 24-hour cache
        mock_cache.set.assert_called_once()
        assert mock_cache.set.call_args[0][2] == 86400  # 24 hours in seconds
    
    def test_fetch_historical_prices_pagination(self):
        """Test historical prices handles pagination"""
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        
        client = AgmarknetClient(api_key="test-key", cache=mock_cache)
        
        # Mock paginated responses
        responses = [
            Mock(json=Mock(return_value={
                'records': [{'arrival_date': '2024-01-01', 'modal_price': '2500', 'market_name': 'Nashik'}],
                'total': 2
            })),
            Mock(json=Mock(return_value={
                'records': [{'arrival_date': '2024-01-02', 'modal_price': '2600', 'market_name': 'Nashik'}],
                'total': 2
            }))
        ]
        
        for r in responses:
            r.raise_for_status = Mock()
        
        with patch.object(client.session, 'request', side_effect=responses):
            df = client.fetch_historical_prices(
                'Onion',
                'Nashik',
                date(2024, 1, 1),
                date(2024, 1, 31)
            )
        
        assert not df.empty
        assert len(df) == 2
    
    def test_validate_data_removes_invalid_prices(self):
        """Test validate_data removes invalid prices"""
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'price': [2500, -100, 0],  # One valid, two invalid
            'market': ['Nashik', 'Nashik', 'Nashik']
        })
        
        validated = client.validate_data(df)
        
        assert len(validated) == 1
        assert validated.iloc[0]['price'] == 2500
    
    def test_validate_data_removes_invalid_dates(self):
        """Test validate_data removes invalid dates"""
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'date': ['2024-01-01', 'invalid-date', None],
            'price': [2500, 2600, 2700],
            'market': ['Nashik', 'Nashik', 'Nashik']
        })
        
        validated = client.validate_data(df)
        
        assert len(validated) == 1
        assert validated.iloc[0]['date'] == '2024-01-01'
    
    def test_validate_data_converts_dates_to_iso8601(self):
        """Test validate_data converts dates to ISO 8601 format"""
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'date': ['01/01/2024', '2024-01-02'],
            'price': [2500, 2600],
            'market': ['Nashik', 'Nashik']
        })
        
        validated = client.validate_data(df)
        
        # Check dates are in YYYY-MM-DD format
        for date_str in validated['date']:
            assert len(date_str) == 10
            assert date_str[4] == '-'
            assert date_str[7] == '-'
    
    def test_standardize_columns(self):
        """Test column standardization"""
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'arrival_date': ['2024-01-01'],
            'modal_price': [2500],
            'market_name': ['Nashik']
        })
        
        standardized = client._standardize_columns(df)
        
        assert 'date' in standardized.columns
        assert 'price' in standardized.columns
        assert 'market' in standardized.columns
    
    def test_get_data_quality_metrics(self):
        """Test data quality metrics calculation"""
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'price': [2500, 2600],
            'market': ['Nashik', 'Nashik']
        })
        
        metrics = client.get_data_quality_metrics(df)
        
        assert metrics['total_records'] == 2
        assert metrics['valid_prices_pct'] == 100.0
        assert metrics['date_range'] is not None
    
    def test_get_data_quality_metrics_empty_df(self):
        """Test data quality metrics for empty DataFrame"""
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame(columns=['date', 'price', 'market'])
        
        metrics = client.get_data_quality_metrics(df)
        
        assert metrics['total_records'] == 0
        assert metrics['missing_values_pct'] == 0


# Property-Based Tests
class TestAgmarknetClientProperties:
    """Property-based tests for Agmarknet Client"""
    
    @settings(deadline=None, max_examples=20)
    @given(
        price=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_valid_prices_preserved(self, price):
        """
        Property 2: API Response Structure Validation
        
        GIVEN valid price data
        WHEN validated
        THEN valid prices are preserved
        
        Validates: Requirement 2.3
        """
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [price],
            'market': ['Nashik']
        })
        
        validated = client.validate_data(df)
        
        assert not validated.empty
        assert validated.iloc[0]['price'] == price
    
    @settings(deadline=None, max_examples=20)
    @given(
        invalid_price=st.one_of(
            st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
            st.just(-100)
        )
    )
    def test_property_invalid_prices_removed(self, invalid_price):
        """
        Property 4: Data Filtering Correctness
        
        GIVEN invalid price data (≤ 0)
        WHEN validated
        THEN invalid prices are removed
        
        Validates: Requirement 20.1
        """
        client = AgmarknetClient(api_key="test-key")
        
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'price': [invalid_price],
            'market': ['Nashik']
        })
        
        validated = client.validate_data(df)
        
        assert validated.empty
    
    @settings(deadline=None, max_examples=20)
    @given(
        num_records=st.integers(min_value=1, max_value=100)
    )
    def test_property_dataframe_structure(self, num_records):
        """
        Property 7: Time-Series Data Format
        
        GIVEN any number of price records
        WHEN converted to DataFrame
        THEN DataFrame has required columns
        
        Validates: Requirement 4.3
        """
        client = AgmarknetClient(api_key="test-key")
        
        # Use pd.date_range to generate valid calendar dates
        dates = pd.date_range(start='2024-01-01', periods=num_records, freq='D')
        
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d').tolist(),
            'price': [2500 + i * 10 for i in range(num_records)],
            'market': ['Nashik'] * num_records
        })
        
        validated = client.validate_data(df)
        
        assert 'date' in validated.columns
        assert 'price' in validated.columns
        assert 'market' in validated.columns
        assert len(validated) == num_records
