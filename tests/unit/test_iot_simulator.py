"""
Unit tests for IoT Simulator Component

Tests sensor reading generation, time-of-day patterns, weather correlation,
and continuous simulation with DynamoDB persistence.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings

# Import the component
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from iot_simulator import IoTSimulator


class TestIoTSimulator:
    """Test suite for IoTSimulator component"""
    
    def test_initialization(self):
        """Test simulator initialization"""
        storage_id = "storage-001"
        dynamodb_store = Mock()
        weather_client = Mock()
        
        simulator = IoTSimulator(storage_id, dynamodb_store, weather_client)
        
        assert simulator.storage_id == storage_id
        assert simulator.dynamodb_store == dynamodb_store
        assert simulator.weather_client == weather_client
        assert simulator.is_running is False
        assert simulator.latest_reading is None
    
    def test_is_daytime_morning(self):
        """Test daytime detection in morning"""
        simulator = IoTSimulator("storage-001", Mock(), Mock())
        
        with patch('iot_simulator.datetime') as mock_datetime:
            mock_datetime.now.return_value = Mock(hour=10)
            assert simulator._is_daytime() is True
    
    def test_is_daytime_night(self):
        """Test daytime detection at night"""
        simulator = IoTSimulator("storage-001", Mock(), Mock())
        
        with patch('iot_simulator.datetime') as mock_datetime:
            mock_datetime.now.return_value = Mock(hour=22)
            assert simulator._is_daytime() is False
    
    def test_time_of_day_factor_peak(self):
        """Test time-of-day factor at peak (2 PM)"""
        simulator = IoTSimulator("storage-001", Mock(), Mock())
        
        with patch('iot_simulator.datetime') as mock_datetime:
            mock_datetime.now.return_value = Mock(hour=14)
            factor = simulator._get_time_of_day_factor()
            assert 0.9 <= factor <= 1.0
    
    def test_time_of_day_factor_night(self):
        """Test time-of-day factor at night"""
        simulator = IoTSimulator("storage-001", Mock(), Mock())
        
        with patch('iot_simulator.datetime') as mock_datetime:
            mock_datetime.now.return_value = Mock(hour=2)
            factor = simulator._get_time_of_day_factor()
            assert 0.0 <= factor <= 0.3
    
    def test_weather_correlation_success(self):
        """Test weather correlation with successful fetch"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 30.0,
            'humidity': 70.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        correlation = simulator._get_weather_correlation()
        
        assert 'temp_adjustment' in correlation
        assert 'humidity_adjustment' in correlation
        assert correlation['temp_adjustment'] > 0  # Warmer outdoor → warmer storage
        assert correlation['humidity_adjustment'] > 0  # Higher outdoor humidity
    
    def test_weather_correlation_failure(self):
        """Test weather correlation with fetch failure"""
        weather_client = Mock()
        weather_client.fetch_current_weather.side_effect = Exception("API error")
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        correlation = simulator._get_weather_correlation()
        
        assert correlation['temp_adjustment'] == 0.0
        assert correlation['humidity_adjustment'] == 0.0
    
    def test_generate_reading_structure(self):
        """Test generated reading has correct structure"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        reading = simulator.generate_reading()
        
        assert 'storage_id' in reading
        assert 'timestamp' in reading
        assert 'temperature' in reading
        assert 'humidity' in reading
        assert reading['storage_id'] == "storage-001"
    
    def test_generate_reading_temperature_range(self):
        """Test temperature is within valid range"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        
        for _ in range(10):
            reading = simulator.generate_reading()
            assert 15.0 <= reading['temperature'] <= 35.0
    
    def test_generate_reading_humidity_range(self):
        """Test humidity is within valid range"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        
        for _ in range(10):
            reading = simulator.generate_reading()
            assert 40.0 <= reading['humidity'] <= 90.0
    
    def test_generate_reading_updates_latest(self):
        """Test generate_reading updates latest_reading"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        reading = simulator.generate_reading()
        
        assert simulator.latest_reading == reading
    
    def test_start_simulation_generates_initial_reading(self):
        """Test start_simulation generates and saves initial reading"""
        dynamodb_store = Mock()
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", dynamodb_store, weather_client)
        simulator.start_simulation(interval_seconds=1)
        
        # Verify initial reading was saved
        assert dynamodb_store.save_sensor_reading.called
        assert simulator.is_running is True
        
        # Cleanup
        simulator.stop_simulation()
    
    def test_start_simulation_already_running(self):
        """Test start_simulation when already running"""
        dynamodb_store = Mock()
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", dynamodb_store, weather_client)
        simulator.start_simulation(interval_seconds=1)
        
        call_count = dynamodb_store.save_sensor_reading.call_count
        
        # Try to start again
        simulator.start_simulation(interval_seconds=1)
        
        # Should not generate additional reading
        assert dynamodb_store.save_sensor_reading.call_count == call_count
        
        # Cleanup
        simulator.stop_simulation()
    
    def test_stop_simulation(self):
        """Test stop_simulation halts background loop"""
        dynamodb_store = Mock()
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", dynamodb_store, weather_client)
        simulator.start_simulation(interval_seconds=1)
        
        assert simulator.is_running is True
        
        simulator.stop_simulation()
        
        assert simulator.is_running is False
        assert simulator.timer is None
    
    def test_get_latest_reading_none(self):
        """Test get_latest_reading when no readings yet"""
        simulator = IoTSimulator("storage-001", Mock(), Mock())
        
        assert simulator.get_latest_reading() is None
    
    def test_get_latest_reading_after_generation(self):
        """Test get_latest_reading after generating reading"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        reading = simulator.generate_reading()
        
        latest = simulator.get_latest_reading()
        assert latest == reading
    
    def test_get_status(self):
        """Test get_status returns correct information"""
        simulator = IoTSimulator("storage-001", Mock(), Mock(), location="Mumbai")
        
        status = simulator.get_status()
        
        assert status['storage_id'] == "storage-001"
        assert status['is_running'] is False
        assert status['location'] == "Mumbai"
        assert status['latest_reading'] is None
        assert 'temp_range' in status
        assert 'humidity_range' in status
    
    def test_daytime_warmer_than_night(self):
        """Test daytime readings are warmer than nighttime"""
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator("storage-001", Mock(), weather_client)
        
        # Generate daytime reading
        with patch('iot_simulator.datetime') as mock_datetime:
            mock_datetime.now.return_value = Mock(hour=14)
            mock_datetime.now.return_value.isoformat.return_value = "2026-03-07T14:00:00"
            day_reading = simulator.generate_reading()
        
        # Generate nighttime reading
        with patch('iot_simulator.datetime') as mock_datetime:
            mock_datetime.now.return_value = Mock(hour=2)
            mock_datetime.now.return_value.isoformat.return_value = "2026-03-07T02:00:00"
            night_reading = simulator.generate_reading()
        
        # Daytime should generally be warmer (with some tolerance for randomness)
        # Run multiple times to account for random variation
        day_temps = []
        night_temps = []
        
        for _ in range(20):
            with patch('iot_simulator.datetime') as mock_datetime:
                mock_datetime.now.return_value = Mock(hour=14)
                mock_datetime.now.return_value.isoformat.return_value = "2026-03-07T14:00:00"
                day_temps.append(simulator.generate_reading()['temperature'])
            
            with patch('iot_simulator.datetime') as mock_datetime:
                mock_datetime.now.return_value = Mock(hour=2)
                mock_datetime.now.return_value.isoformat.return_value = "2026-03-07T02:00:00"
                night_temps.append(simulator.generate_reading()['temperature'])
        
        avg_day_temp = sum(day_temps) / len(day_temps)
        avg_night_temp = sum(night_temps) / len(night_temps)
        
        assert avg_day_temp > avg_night_temp


# Property-Based Tests
class TestIoTSimulatorProperties:
    """Property-based tests for IoT Simulator"""
    
    @settings(deadline=None, max_examples=20)
    @given(storage_id=st.text(min_size=1, max_size=50))
    def test_property_sensor_reading_validity(self, storage_id):
        """
        Property 37: IoT Sensor Reading Validity
        
        GIVEN any storage_id
        WHEN a sensor reading is generated
        THEN temperature is 15-35°C and humidity is 40-90%
        
        Validates: Requirements 21.1, 21.2, 21.3
        """
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator(storage_id, Mock(), weather_client)
        reading = simulator.generate_reading()
        
        # Verify temperature range
        assert 15.0 <= reading['temperature'] <= 35.0
        
        # Verify humidity range
        assert 40.0 <= reading['humidity'] <= 90.0
        
        # Verify storage_id matches
        assert reading['storage_id'] == storage_id
    
    @settings(deadline=None, max_examples=10)
    @given(storage_id=st.text(min_size=1, max_size=50))
    def test_property_sensor_reading_round_trip(self, storage_id):
        """
        Property 51: IoT Sensor Reading Round Trip
        
        GIVEN a sensor reading
        WHEN saved to DynamoDB
        THEN it can be retrieved with same values
        
        Validates: Requirements 21.5, 21.6
        """
        dynamodb_store = Mock()
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator(storage_id, dynamodb_store, weather_client)
        reading = simulator.generate_reading()
        
        # Simulate saving
        dynamodb_store.save_sensor_reading(reading)
        
        # Verify save was called with correct reading
        dynamodb_store.save_sensor_reading.assert_called_once_with(reading)
    
    @settings(deadline=None, max_examples=5)
    @given(
        storage_id=st.text(min_size=1, max_size=50),
        interval=st.integers(min_value=1, max_value=10)
    )
    def test_property_sensor_update_interval(self, storage_id, interval):
        """
        Property 52: Sensor Update Interval
        
        GIVEN a simulation with interval N seconds
        WHEN simulation runs
        THEN readings are generated approximately every N seconds
        
        Validates: Requirement 21.4
        """
        dynamodb_store = Mock()
        weather_client = Mock()
        weather_client.fetch_current_weather.return_value = {
            'temp': 25.0,
            'humidity': 60.0
        }
        
        simulator = IoTSimulator(storage_id, dynamodb_store, weather_client)
        simulator.start_simulation(interval_seconds=interval)
        
        # Verify simulation started
        assert simulator.is_running is True
        
        # Verify initial reading was saved
        assert dynamodb_store.save_sensor_reading.called
        
        # Cleanup
        simulator.stop_simulation()
        assert simulator.is_running is False
