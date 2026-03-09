"""
Smart Storage Monitor Component

Monitors storage conditions and sends alerts for adverse conditions.
Calculates health status based on temperature and humidity thresholds.
Sends SNS notifications in Marathi for critical alerts.

Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7
"""

import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


class SmartStorageMonitor:
    """
    Smart storage monitoring system with health status calculation and alerting.
    
    Monitors temperature and humidity conditions in agricultural storage.
    Sends SNS alerts in Marathi when conditions become critical.
    Caches historical data to reduce DynamoDB reads.
    """
    
    # Health status thresholds
    ALERT_TEMP_THRESHOLD = 30.0  # °C
    WARNING_TEMP_MIN = 25.0  # °C
    WARNING_TEMP_MAX = 30.0  # °C
    
    ALERT_HUMIDITY_THRESHOLD = 80.0  # %
    WARNING_HUMIDITY_MIN = 70.0  # %
    WARNING_HUMIDITY_MAX = 80.0  # %
    
    # Cache TTL (5 minutes)
    CACHE_TTL_SECONDS = 300
    
    def __init__(
        self,
        iot_simulator,
        dynamodb_store,
        sns_client,
        logger,
        sns_topic_arn: Optional[str] = None
    ):
        """
        Initialize Smart Storage Monitor.
        
        Args:
            iot_simulator: IoT simulator instance
            dynamodb_store: DynamoDB store for historical data
            sns_client: Boto3 SNS client for alerts
            logger: CloudLogger instance
            sns_topic_arn: SNS topic ARN for alerts (optional)
        """
        self.iot_simulator = iot_simulator
        self.dynamodb_store = dynamodb_store
        self.sns_client = sns_client
        self.logger = logger
        self.sns_topic_arn = sns_topic_arn
        
        # Cache for historical data
        self.cache = {}
        self.cache_timestamps = {}
        
        # Track last alert status to avoid duplicate alerts
        self.last_alert_status = {}
    
    def calculate_health_status(
        self,
        temperature: float,
        humidity: float
    ) -> str:
        """
        Calculate health status based on temperature and humidity.
        
        Args:
            temperature: Temperature in °C
            humidity: Humidity in %
            
        Returns:
            Health status: 'Alert', 'Warning', or 'Safe'
        """
        # Check for Alert conditions
        if temperature > self.ALERT_TEMP_THRESHOLD or humidity > self.ALERT_HUMIDITY_THRESHOLD:
            return 'Alert'
        
        # Check for Warning conditions
        if (self.WARNING_TEMP_MIN <= temperature <= self.WARNING_TEMP_MAX or
            self.WARNING_HUMIDITY_MIN <= humidity <= self.WARNING_HUMIDITY_MAX):
            return 'Warning'
        
        # Otherwise Safe
        return 'Safe'
    
    def analyze_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a sensor reading and calculate health metrics.
        
        Args:
            reading: Sensor reading dict with temperature and humidity
            
        Returns:
            Analysis dict with health_status, health_score, and issues
        """
        temperature = reading.get('temperature', 0.0)
        humidity = reading.get('humidity', 0.0)
        
        # Calculate health status
        health_status = self.calculate_health_status(temperature, humidity)
        
        # Calculate health score (0-100, higher is better)
        temp_score = 100.0
        humidity_score = 100.0
        
        # Temperature scoring
        if temperature > self.ALERT_TEMP_THRESHOLD:
            temp_score = max(0, 100 - (temperature - self.ALERT_TEMP_THRESHOLD) * 10)
        elif temperature > self.WARNING_TEMP_MIN:
            temp_score = 100 - (temperature - self.WARNING_TEMP_MIN) * 5
        
        # Humidity scoring
        if humidity > self.ALERT_HUMIDITY_THRESHOLD:
            humidity_score = max(0, 100 - (humidity - self.ALERT_HUMIDITY_THRESHOLD) * 10)
        elif humidity > self.WARNING_HUMIDITY_MIN:
            humidity_score = 100 - (humidity - self.WARNING_HUMIDITY_MIN) * 5
        
        # Overall health score (average)
        health_score = (temp_score + humidity_score) / 2.0
        
        # Identify issues
        issues = []
        if temperature > self.ALERT_TEMP_THRESHOLD:
            issues.append('high_temperature')
        elif temperature > self.WARNING_TEMP_MIN:
            issues.append('elevated_temperature')
        
        if humidity > self.ALERT_HUMIDITY_THRESHOLD:
            issues.append('high_humidity')
        elif humidity > self.WARNING_HUMIDITY_MIN:
            issues.append('elevated_humidity')
        
        return {
            'health_status': health_status,
            'health_score': round(health_score, 2),
            'issues': issues
        }
    
    def get_current_status(self, storage_id: str) -> Dict[str, Any]:
        """
        Get current storage status.
        
        Args:
            storage_id: Storage location identifier
            
        Returns:
            Dictionary with temperature, humidity, health_status, timestamp
        """
        # Get latest reading from IoT simulator
        reading = self.iot_simulator.get_latest_reading()
        
        if reading is None:
            return {
                'storage_id': storage_id,
                'temperature': None,
                'humidity': None,
                'health_status': 'Unknown',
                'timestamp': None
            }
        
        # Calculate health status
        health_status = self.calculate_health_status(
            reading['temperature'],
            reading['humidity']
        )
        
        return {
            'storage_id': storage_id,
            'temperature': reading['temperature'],
            'humidity': reading['humidity'],
            'health_status': health_status,
            'timestamp': reading['timestamp']
        }
    
    def get_historical_data(
        self,
        storage_id: str,
        hours: int = 24
    ) -> pd.DataFrame:
        """
        Get historical sensor data for charting.
        
        Args:
            storage_id: Storage location identifier
            hours: Number of hours of history to retrieve
            
        Returns:
            DataFrame with timestamp, temperature, humidity columns
        """
        # Check cache
        cache_key = f"{storage_id}_{hours}"
        current_time = time.time()
        
        if cache_key in self.cache:
            cache_age = current_time - self.cache_timestamps[cache_key]
            if cache_age < self.CACHE_TTL_SECONDS:
                # Return cached data
                return self.cache[cache_key]
        
        # Fetch from DynamoDB
        try:
            readings = self.dynamodb_store.get_sensor_history(storage_id, hours)
            
            # Convert to DataFrame
            if readings:
                df = pd.DataFrame(readings)
                
                # Ensure required columns
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp')
                
                # Cache the result
                self.cache[cache_key] = df
                self.cache_timestamps[cache_key] = current_time
                
                return df
            else:
                # Return empty DataFrame with correct structure
                return pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'storage_id'])
        
        except Exception as e:
            self.logger.log_dynamodb_operation(
                'get_sensor_history',
                'SensorReadings',
                {'error': str(e)}
            )
            return pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'storage_id'])
    
    def get_recommendation(
        self,
        health_status: str,
        temperature: float,
        humidity: float
    ) -> str:
        """
        Get Marathi recommendation based on health status.
        
        Args:
            health_status: Current health status
            temperature: Current temperature
            humidity: Current humidity
            
        Returns:
            Marathi recommendation string
        """
        if health_status == 'Alert':
            if temperature > self.ALERT_TEMP_THRESHOLD and humidity > self.ALERT_HUMIDITY_THRESHOLD:
                return "तातडीने कारवाई करा! तापमान आणि आर्द्रता दोन्ही धोकादायक पातळीवर आहेत. साठवणूक केंद्र तपासा आणि वायुवीजन सुधारा."
            elif temperature > self.ALERT_TEMP_THRESHOLD:
                return "तापमान खूप वाढले आहे! साठवणूक केंद्र थंड करा. वायुवीजन सुरू करा किंवा पंखे चालू करा."
            else:
                return "आर्द्रता खूप जास्त आहे! साठवणूक केंद्रात हवा येण्याची व्यवस्था करा. पाणी गळती तपासा."
        
        elif health_status == 'Warning':
            if self.WARNING_TEMP_MIN <= temperature <= self.WARNING_TEMP_MAX:
                return "तापमान वाढत आहे. साठवणूक केंद्र नियमितपणे तपासा. वायुवीजन सुधारण्याचा विचार करा."
            else:
                return "आर्द्रता वाढत आहे. साठवणूक केंद्रात हवा येण्याची व्यवस्था करा."
        
        else:
            return "साठवणूक परिस्थिती चांगली आहे. नियमित तपासणी चालू ठेवा."
    
    def send_alert(
        self,
        storage_id: str,
        status: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Send SNS alert notification.
        
        Args:
            storage_id: Storage location identifier
            status: Health status
            details: Alert details (temperature, humidity, etc.)
            
        Returns:
            True if alert sent successfully, False otherwise
        """
        # Only send alert if status is 'Alert'
        if status != 'Alert':
            return False
        
        # Check if we already sent alert for this storage
        if storage_id in self.last_alert_status:
            if self.last_alert_status[storage_id] == 'Alert':
                # Already in alert state, don't send duplicate
                return False
        
        # Update last alert status
        self.last_alert_status[storage_id] = status
        
        # Format Marathi message
        temperature = details.get('temperature', 0.0)
        humidity = details.get('humidity', 0.0)
        timestamp = details.get('timestamp', datetime.now().isoformat())
        
        recommendation = self.get_recommendation(status, temperature, humidity)
        
        message = f"""
🚨 साठवणूक अलर्ट / Storage Alert 🚨

साठवणूक ID / Storage ID: {storage_id}
स्थिती / Status: {status}
तापमान / Temperature: {temperature}°C
आर्द्रता / Humidity: {humidity}%
वेळ / Time: {timestamp}

शिफारस / Recommendation:
{recommendation}

कृपया तातडीने कारवाई करा!
Please take immediate action!
"""
        
        try:
            # Send SNS notification
            if self.sns_topic_arn:
                response = self.sns_client.publish(
                    TopicArn=self.sns_topic_arn,
                    Subject=f"🚨 साठवणूक अलर्ट - {storage_id}",
                    Message=message
                )
                
                message_id = response.get('MessageId', 'unknown')
                
                # Log SNS operation
                self.logger.log_sns_operation('publish_alert', message_id)
                
                return True
            else:
                # No topic ARN configured, log warning
                self.logger.log_sns_operation('publish_alert', 'no_topic_arn')
                return False
        
        except Exception as e:
            # Log error
            self.logger.log_sns_operation('publish_alert', f'error: {str(e)}')
            return False
    
    def check_and_alert(self, storage_id: str) -> Dict[str, Any]:
        """
        Check current status and send alert if needed.
        
        Args:
            storage_id: Storage location identifier
            
        Returns:
            Dictionary with status and alert_sent flag
        """
        # Get current status
        status = self.get_current_status(storage_id)
        
        # Send alert if needed
        alert_sent = False
        if status['health_status'] == 'Alert':
            alert_sent = self.send_alert(
                storage_id,
                status['health_status'],
                status
            )
        else:
            # Update last alert status (no longer in alert)
            if storage_id in self.last_alert_status:
                self.last_alert_status[storage_id] = status['health_status']
        
        return {
            'status': status,
            'alert_sent': alert_sent
        }
