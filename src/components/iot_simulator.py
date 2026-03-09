"""
IoT Simulator Component

Simulates IoT sensor readings for onion storage (कांदा चाळ) monitoring.
Generates realistic temperature and humidity data with time-of-day patterns.
Uses sine wave logic for natural day/night temperature variations.
Integrates with DynamoDB for persistence and CloudLogger for tracking.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6
"""

import random
import threading
import time
import math
from datetime import datetime
from typing import Dict, Any, Optional

# Import config constants
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.config import IoTConfig


class IoTSimulator:
    """
    IoT sensor simulator for onion storage (कांदा चाळ) monitoring.
    
    Generates realistic temperature and humidity readings with:
    - Sine wave patterns for natural day/night temperature cycles
    - Peak warmth during 12 PM - 4 PM (दुपार)
    - Coolest temperatures at night (रात्री)
    - Weather correlation (adjusts based on actual weather)
    - Continuous background simulation every 5 minutes
    - DynamoDB persistence with CloudLogger tracking
    
    Optimal storage conditions for onions (कांदा):
    - Temperature: 15-35°C (optimal: 20-30°C)
    - Humidity: 40-90% (optimal: 50-70%)
    """
    
    def __init__(
        self,
        storage_id: str,
        dynamodb_store,
        cloud_logger=None,
        weather_client=None,
        location: str = "Pune"
    ):
        """
        Initialize IoT Simulator for onion storage.
        
        Args:
            storage_id: Unique identifier for storage location (e.g., "कांदा_चाळ_001")
            dynamodb_store: DynamoDB store instance for persistence
            cloud_logger: CloudLogger instance for operation tracking (optional)
            weather_client: Weather client for correlation (optional)
            location: Location for weather correlation (default: Pune)
        """
        self.storage_id = storage_id
        self.dynamodb_store = dynamodb_store
        self.cloud_logger = cloud_logger
        self.weather_client = weather_client
        self.location = location
        
        # Simulation state
        self.is_running = False
        self.timer = None
        self.latest_reading = None
        self.reading_count = 0
        
        # Use config constants for thresholds
        self.temp_min = IoTConfig.TEMP_MIN
        self.temp_max = IoTConfig.TEMP_MAX
        self.humidity_min = IoTConfig.HUMIDITY_MIN
        self.humidity_max = IoTConfig.HUMIDITY_MAX
        
        # Sine wave parameters for realistic day/night cycle
        self.temp_amplitude = 8.0  # Temperature swing: ±8°C from base
        self.base_temp = 25.0  # Base temperature (average)
        
        # Log initialization
        if self.cloud_logger:
            self.cloud_logger.log_operation(
                operation_type="initialization",
                service="iot_simulator",
                details={
                    "storage_id": storage_id,
                    "location": location,
                    "temp_range": f"{self.temp_min}-{self.temp_max}°C",
                    "humidity_range": f"{self.humidity_min}-{self.humidity_max}%"
                }
            )
    
    def _get_sine_wave_temperature(self) -> float:
        """
        Calculate temperature using sine wave for realistic day/night cycle.
        
        Peak temperature at 2 PM (14:00), lowest at 2 AM (02:00).
        Uses sine wave: temp = base + amplitude * sin(2π * (hour - 2) / 24)
        
        Returns:
            Temperature adjustment from sine wave (-amplitude to +amplitude)
        """
        current_hour = datetime.now().hour
        current_minute = datetime.now().minute
        
        # Convert to decimal hours (e.g., 14:30 = 14.5)
        decimal_hour = current_hour + (current_minute / 60.0)
        
        # Shift sine wave so peak is at 14:00 (2 PM)
        # sin(0) = 0, sin(π/2) = 1, so we shift by 8 hours to peak at 14:00
        phase_shift = 8.0
        hour_angle = 2 * math.pi * (decimal_hour - phase_shift) / 24.0
        
        # Calculate sine wave value (-1 to +1)
        sine_value = math.sin(hour_angle)
        
        # Scale by amplitude
        temp_adjustment = self.temp_amplitude * sine_value
        
        return temp_adjustment
    
    def _get_weather_correlation(self) -> Dict[str, float]:
        """
        Get weather-based adjustment factors.
        
        Returns:
            Dictionary with temp_adjustment and humidity_adjustment
        """
        # Skip weather correlation if no weather client
        if not self.weather_client:
            return {
                'temp_adjustment': 0.0,
                'humidity_adjustment': 0.0
            }
        
        try:
            # Fetch current weather
            weather = self.weather_client.fetch_current_weather(self.location)
            
            # Extract weather data
            outdoor_temp = weather.get('temp', 25.0)
            outdoor_humidity = weather.get('humidity', 60.0)
            
            # Calculate adjustments (storage influenced by outdoor conditions)
            # Storage temp correlates ~40% with outdoor temp (onion storage is semi-insulated)
            temp_adjustment = (outdoor_temp - 25.0) * 0.4
            
            # Storage humidity correlates ~30% with outdoor humidity
            humidity_adjustment = (outdoor_humidity - 60.0) * 0.3
            
            return {
                'temp_adjustment': temp_adjustment,
                'humidity_adjustment': humidity_adjustment
            }
        except Exception as e:
            # If weather fetch fails, log and return neutral adjustments
            if self.cloud_logger:
                self.cloud_logger.log_operation(
                    operation_type="weather_correlation",
                    service="iot_simulator",
                    details={"storage_id": self.storage_id},
                    error=str(e)
                )
            return {
                'temp_adjustment': 0.0,
                'humidity_adjustment': 0.0
            }
    
    def generate_reading(self) -> Dict[str, Any]:
        """
        Generate a single sensor reading for onion storage.
        
        Uses sine wave for realistic day/night temperature patterns:
        - Peak temperature: 12 PM - 4 PM (दुपार)
        - Lowest temperature: 2 AM - 4 AM (रात्री)
        - Smooth transitions throughout the day
        
        Returns:
            Dictionary with timestamp, temperature, humidity, storage_id
        """
        # Get sine wave temperature adjustment
        sine_temp_adjustment = self._get_sine_wave_temperature()
        
        # Get weather correlation
        weather_corr = self._get_weather_correlation()
        
        # Calculate temperature
        # Base temp + sine wave + weather correlation + random noise
        temperature = (
            self.base_temp +
            sine_temp_adjustment +
            weather_corr['temp_adjustment'] +
            random.uniform(-1.5, 1.5)  # Small random variation
        )
        
        # Clamp to valid range
        temperature = max(self.temp_min, min(self.temp_max, temperature))
        temperature = round(temperature, 2)
        
        # Calculate humidity (inverse correlation with temperature)
        # Onion storage: higher temp → lower humidity
        base_humidity = (self.humidity_min + self.humidity_max) / 2.0
        
        # Inverse relationship: -2% humidity per 1°C above base
        humidity_temp_factor = -(temperature - self.base_temp) * 2.0
        
        # Apply weather correlation
        humidity_adjustment = weather_corr['humidity_adjustment']
        
        # Add random variation
        humidity_variation = random.uniform(-3.0, 3.0)
        
        # Calculate final humidity
        humidity = base_humidity + humidity_temp_factor + humidity_adjustment + humidity_variation
        humidity = max(self.humidity_min, min(self.humidity_max, humidity))
        humidity = round(humidity, 2)
        
        # Create reading
        reading = {
            'storage_id': self.storage_id,
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'humidity': humidity,
            'status': self._get_storage_status(temperature, humidity)
        }
        
        # Store as latest reading
        self.latest_reading = reading
        self.reading_count += 1
        
        # Log reading generation
        if self.cloud_logger:
            self.cloud_logger.log_operation(
                operation_type="sensor_reading",
                service="iot_simulator",
                details={
                    "storage_id": self.storage_id,
                    "temperature": temperature,
                    "humidity": humidity,
                    "status": reading['status'],
                    "reading_number": self.reading_count
                }
            )
        
        return reading
    
    def _get_storage_status(self, temp: float, humidity: float) -> str:
        """
        Determine storage condition status for onions.
        
        Args:
            temp: Current temperature
            humidity: Current humidity
            
        Returns:
            Status string: "optimal", "acceptable", "warning", "critical"
        """
        temp_status = IoTConfig.get_temperature_status(temp)
        humidity_status = IoTConfig.get_humidity_status(humidity)
        
        # Both optimal
        if temp_status == "optimal" and humidity_status == "optimal":
            return "optimal"
        
        # Both acceptable or better
        if temp_status in ["optimal", "acceptable"] and humidity_status in ["optimal", "acceptable"]:
            return "acceptable"
        
        # One critical condition
        if temp_status in ["too_cold", "too_hot"] or humidity_status in ["too_dry", "too_humid"]:
            return "critical"
        
        # Otherwise warning
        return "warning"
    
    def _simulation_loop(self, interval_seconds: int):
        """
        Internal simulation loop (runs in background).
        
        Args:
            interval_seconds: Interval between readings
        """
        if not self.is_running:
            return
        
        try:
            # Generate and save reading
            reading = self.generate_reading()
            success = self.dynamodb_store.save_sensor_reading(reading)
            
            if not success and self.cloud_logger:
                self.cloud_logger.log_operation(
                    operation_type="save_reading",
                    service="iot_simulator",
                    details={"storage_id": self.storage_id},
                    error="Failed to save reading to DynamoDB"
                )
        except Exception as e:
            # Log error but continue simulation
            if self.cloud_logger:
                self.cloud_logger.log_operation(
                    operation_type="simulation_loop",
                    service="iot_simulator",
                    details={"storage_id": self.storage_id},
                    error=str(e)
                )
        
        # Schedule next reading
        if self.is_running:
            self.timer = threading.Timer(
                interval_seconds,
                self._simulation_loop,
                args=[interval_seconds]
            )
            self.timer.daemon = True
            self.timer.start()
    
    def start_simulation(self, interval_seconds: int = 300):
        """
        Start continuous sensor simulation for onion storage.
        
        Default interval: 300 seconds (5 minutes) as per IoT requirements.
        
        Args:
            interval_seconds: Interval between readings (default: 300 = 5 minutes)
        """
        if self.is_running:
            return  # Already running
        
        self.is_running = True
        
        # Log simulation start
        if self.cloud_logger:
            self.cloud_logger.log_operation(
                operation_type="start_simulation",
                service="iot_simulator",
                details={
                    "storage_id": self.storage_id,
                    "interval_seconds": interval_seconds,
                    "location": self.location
                }
            )
        
        # Generate and save initial reading immediately
        try:
            reading = self.generate_reading()
            self.dynamodb_store.save_sensor_reading(reading)
        except Exception as e:
            if self.cloud_logger:
                self.cloud_logger.log_operation(
                    operation_type="initial_reading",
                    service="iot_simulator",
                    details={"storage_id": self.storage_id},
                    error=str(e)
                )
        
        # Start background loop
        self.timer = threading.Timer(
            interval_seconds,
            self._simulation_loop,
            args=[interval_seconds]
        )
        self.timer.daemon = True
        self.timer.start()
    
    def stop_simulation(self):
        """
        Stop continuous sensor simulation.
        """
        self.is_running = False
        
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        
        # Log simulation stop
        if self.cloud_logger:
            self.cloud_logger.log_operation(
                operation_type="stop_simulation",
                service="iot_simulator",
                details={
                    "storage_id": self.storage_id,
                    "total_readings": self.reading_count
                }
            )
    
    def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent sensor reading.
        
        Returns:
            Latest reading dictionary or None if no readings yet
        """
        return self.latest_reading
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get simulator status for onion storage (कांदा चाळ).
        
        Returns:
            Dictionary with status information
        """
        status = {
            'storage_id': self.storage_id,
            'storage_type': 'Onion Storage (कांदा चाळ)',
            'is_running': self.is_running,
            'location': self.location,
            'latest_reading': self.latest_reading,
            'total_readings': self.reading_count,
            'temp_range': f"{self.temp_min}°C - {self.temp_max}°C",
            'humidity_range': f"{self.humidity_min}% - {self.humidity_max}%",
            'optimal_temp': f"{IoTConfig.TEMP_OPTIMAL_MIN}°C - {IoTConfig.TEMP_OPTIMAL_MAX}°C",
            'optimal_humidity': f"{IoTConfig.HUMIDITY_OPTIMAL_MIN}% - {IoTConfig.HUMIDITY_OPTIMAL_MAX}%"
        }
        
        # Add current condition status if we have a reading
        if self.latest_reading:
            status['current_status'] = self.latest_reading.get('status', 'unknown')
        
        return status
