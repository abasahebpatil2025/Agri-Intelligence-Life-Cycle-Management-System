"""
Unit tests for DynamoDB Store Component

Tests CRUD operations, retry logic, and data persistence.
Property-based tests for data integrity.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from hypothesis import given, strategies as st, settings

# Import the component
import sys
sys.path.insert(0, 'src/components')
from dynamodb_store import DynamoDBStore


class TestDynamoDBStore:
    """Test suite for DynamoDBStore component"""
    
    def test_save_farmer_profile_success(self):
        """Test successful farmer profile save"""
        mock_client = Mock()
        mock_client.put_item = Mock(return_value={})
        mock_logger = Mock()
        
        store = DynamoDBStore(boto3_client=mock_client, logger=mock_logger)
        
        profile = {
            'farmer_id': '123',
            'name': 'Ramesh Patil',
            'location': 'Nashik'
        }
        
        result = store.save_farmer_profile(profile)
        
        assert result is True
        mock_client.put_item.assert_called_once()
    
    def test_get_farmer_profile_success(self):
        """Test successful farmer profile retrieval"""
        mock_client = Mock()
        mock_client.get_item = Mock(return_value={
            'Item': {
                'farmer_id': {'S': '123'},
                'name': {'S': 'Ramesh Patil'},
                'location': {'S': 'Nashik'}
            }
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        profile = store.get_farmer_profile('123')
        
        assert profile is not None
        assert profile['farmer_id'] == '123'
        assert profile['name'] == 'Ramesh Patil'
    
    def test_get_farmer_profile_not_found(self):
        """Test farmer profile not found"""
        mock_client = Mock()
        mock_client.get_item = Mock(return_value={})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        profile = store.get_farmer_profile('nonexistent')
        
        assert profile is None
    
    def test_save_price_trend_success(self):
        """Test successful price trend save"""
        mock_client = Mock()
        mock_client.put_item = Mock(return_value={})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        trend = {
            'commodity': 'Onion',
            'date': '2024-01-01',
            'price': 2500
        }
        
        result = store.save_price_trend(trend)
        
        assert result is True
    
    def test_get_price_trends_success(self):
        """Test successful price trends retrieval"""
        mock_client = Mock()
        mock_client.query = Mock(return_value={
            'Items': [
                {
                    'commodity': {'S': 'Onion'},
                    'date': {'S': '2024-01-01'},
                    'price': {'N': '2500'}
                }
            ]
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        trends = store.get_price_trends('Onion', days=30)
        
        assert len(trends) == 1
        assert trends[0]['commodity'] == 'Onion'
        assert trends[0]['price'] == 2500
    
    def test_save_sensor_reading_adds_ttl(self):
        """Test sensor reading save adds TTL"""
        mock_client = Mock()
        mock_client.put_item = Mock(return_value={})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        reading = {
            'storage_id': 'storage-1',
            'timestamp': datetime.now().isoformat(),
            'temperature': 25.5,
            'humidity': 65.0
        }
        
        result = store.save_sensor_reading(reading)
        
        assert result is True
        # Verify TTL was added
        call_args = mock_client.put_item.call_args
        assert 'expires_at' in reading
    
    def test_get_sensor_history_success(self):
        """Test successful sensor history retrieval"""
        mock_client = Mock()
        mock_client.query = Mock(return_value={
            'Items': [
                {
                    'storage_id': {'S': 'storage-1'},
                    'timestamp': {'S': datetime.now().isoformat()},
                    'temperature': {'N': '25.5'},
                    'humidity': {'N': '65.0'}
                }
            ]
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        history = store.get_sensor_history('storage-1', hours=24)
        
        assert len(history) == 1
        assert history[0]['storage_id'] == 'storage-1'
    
    def test_save_qr_data_success(self):
        """Test successful QR data save"""
        mock_client = Mock()
        mock_client.put_item = Mock(return_value={})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        qr_data = {
            'lot_id': 'lot-123',
            'farmer_id': 'farmer-456',
            'crop_type': 'Onion',
            'grade': 'A'
        }
        
        result = store.save_qr_data(qr_data)
        
        assert result is True
    
    def test_get_qr_data_success(self):
        """Test successful QR data retrieval"""
        mock_client = Mock()
        mock_client.get_item = Mock(return_value={
            'Item': {
                'lot_id': {'S': 'lot-123'},
                'farmer_id': {'S': 'farmer-456'},
                'crop_type': {'S': 'Onion'},
                'grade': {'S': 'A'}
            }
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        qr_data = store.get_qr_data('lot-123')
        
        assert qr_data is not None
        assert qr_data['lot_id'] == 'lot-123'
        assert qr_data['grade'] == 'A'
    
    def test_save_user_account_success(self):
        """Test successful user account save"""
        mock_client = Mock()
        mock_client.put_item = Mock(return_value={})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        account = {
            'farmer_id': '123',
            'phone': '9876543210',
            'name': 'Ramesh Patil'
        }
        
        result = store.save_user_account(account)
        
        assert result is True
    
    def test_get_user_account_success(self):
        """Test successful user account retrieval"""
        mock_client = Mock()
        mock_client.get_item = Mock(return_value={
            'Item': {
                'farmer_id': {'S': '123'},
                'phone': {'S': '9876543210'},
                'name': {'S': 'Ramesh Patil'}
            }
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        account = store.get_user_account('123')
        
        assert account is not None
        assert account['farmer_id'] == '123'
        assert account['phone'] == '9876543210'
    
    def test_query_user_by_phone_success(self):
        """Test successful user query by phone using GSI"""
        mock_client = Mock()
        mock_client.query = Mock(return_value={
            'Items': [
                {
                    'farmer_id': {'S': '123'},
                    'phone': {'S': '9876543210'},
                    'name': {'S': 'Ramesh Patil'}
                }
            ]
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        account = store.query_user_by_phone('9876543210')
        
        assert account is not None
        assert account['phone'] == '9876543210'
        # Verify GSI was used
        call_args = mock_client.query.call_args
        assert call_args[1]['IndexName'] == 'phone-index'
    
    def test_query_user_by_phone_not_found(self):
        """Test user query by phone returns None when not found"""
        mock_client = Mock()
        mock_client.query = Mock(return_value={'Items': []})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        account = store.query_user_by_phone('0000000000')
        
        assert account is None
    
    def test_python_to_dynamodb_conversion(self):
        """Test Python to DynamoDB format conversion"""
        store = DynamoDBStore()
        
        data = {
            'string_field': 'test',
            'int_field': 42,
            'float_field': 3.14,
            'bool_field': True
        }
        
        result = store._python_to_dynamodb(data)
        
        assert result['string_field'] == {'S': 'test'}
        assert result['int_field'] == {'N': '42'}
        assert result['float_field'] == {'N': '3.14'}
        assert result['bool_field'] == {'BOOL': True}
    
    def test_dynamodb_to_python_conversion(self):
        """Test DynamoDB to Python format conversion"""
        store = DynamoDBStore()
        
        data = {
            'string_field': {'S': 'test'},
            'int_field': {'N': '42'},
            'float_field': {'N': '3.14'},
            'bool_field': {'BOOL': True}
        }
        
        result = store._dynamodb_to_python(data)
        
        assert result['string_field'] == 'test'
        assert result['int_field'] == 42
        assert result['float_field'] == 3.14
        assert result['bool_field'] is True


# Property-Based Tests
class TestDynamoDBStoreProperties:
    """Property-based tests for DynamoDB Store"""
    
    @settings(deadline=None, max_examples=20)
    @given(
        farmer_id=st.text(min_size=1, max_size=50),
        name=st.text(min_size=1, max_size=100),
        location=st.text(min_size=1, max_size=100)
    )
    def test_property_farmer_profile_persistence(self, farmer_id, name, location):
        """
        Property 23: Farmer Profile Persistence
        
        GIVEN any farmer profile data
        WHEN saved to DynamoDB
        THEN it can be retrieved with same values
        
        Validates: Requirements 12.3, 12.4
        """
        mock_client = Mock()
        
        # Mock save
        mock_client.put_item = Mock(return_value={})
        
        # Mock retrieve
        mock_client.get_item = Mock(return_value={
            'Item': {
                'farmer_id': {'S': farmer_id},
                'name': {'S': name},
                'location': {'S': location}
            }
        })
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        # Save
        profile = {
            'farmer_id': farmer_id,
            'name': name,
            'location': location
        }
        save_result = store.save_farmer_profile(profile)
        assert save_result is True
        
        # Retrieve
        retrieved = store.get_farmer_profile(farmer_id)
        assert retrieved is not None
        assert retrieved['farmer_id'] == farmer_id
        assert retrieved['name'] == name
        assert retrieved['location'] == location
    
    @settings(deadline=None, max_examples=20)
    @given(
        storage_id=st.text(min_size=1, max_size=50),
        temperature=st.floats(min_value=15.0, max_value=35.0, allow_nan=False, allow_infinity=False),
        humidity=st.floats(min_value=40.0, max_value=90.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_sensor_reading_persistence(self, storage_id, temperature, humidity):
        """
        Property 39: Sensor Reading Persistence
        
        GIVEN any sensor reading data
        WHEN saved to DynamoDB
        THEN it includes TTL and can be retrieved
        
        Validates: Requirement 21.5
        """
        mock_client = Mock()
        mock_client.put_item = Mock(return_value={})
        
        store = DynamoDBStore(boto3_client=mock_client)
        
        reading = {
            'storage_id': storage_id,
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'humidity': humidity
        }
        
        result = store.save_sensor_reading(reading)
        
        assert result is True
        # Verify TTL was added
        assert 'expires_at' in reading
        assert isinstance(reading['expires_at'], int)
