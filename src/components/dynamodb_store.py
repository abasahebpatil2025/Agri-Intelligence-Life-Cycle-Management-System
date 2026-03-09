"""
DynamoDB Store Component

Handles all DynamoDB operations with retry logic and logging.
Integrates with CloudLogger for operation tracking.

Requirements: 12.3, 12.4, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 21.5, 23.4, 29.3
"""

import boto3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from decimal import Decimal


class DynamoDBStore:
    """
    DynamoDB data persistence layer with retry logic and logging.
    
    Handles CRUD operations for all tables:
    - FarmerProfiles
    - PriceTrends
    - SensorReadings
    - QRCodes
    - UserAccounts
    """
    
    def __init__(self, boto3_client=None, logger=None):
        """
        Initialize DynamoDB Store.
        
        Args:
            boto3_client: Optional boto3 DynamoDB client (must use us-east-1)
            logger: Optional CloudLogger instance
        """
        # Ensure us-east-1 region
        if boto3_client is None:
            import boto3
            boto3_client = boto3.client('dynamodb', region_name='us-east-1')
        
        self.client = boto3_client
        self.logger = logger
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
    
    def _retry_operation(self, operation_func, operation_name: str, **kwargs):
        """
        Execute operation with exponential backoff retry logic.
        
        Args:
            operation_func: Function to execute
            operation_name: Name of operation for logging
            **kwargs: Arguments to pass to operation_func
            
        Returns:
            Operation result
            
        Raises:
            ClientError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = operation_func(**kwargs)
                
                # Log successful operation
                if self.logger:
                    self.logger.log_dynamodb_operation(
                        operation=operation_name,
                        table=kwargs.get('TableName', 'unknown'),
                        details={'attempt': attempt + 1}
                    )
                
                return result
            
            except ClientError as e:
                last_error = e
                error_code = e.response['Error']['Code']
                
                # Don't retry on certain errors
                if error_code in ['ResourceNotFoundException', 'ValidationException']:
                    if self.logger:
                        self.logger.log_dynamodb_operation(
                            operation=operation_name,
                            table=kwargs.get('TableName', 'unknown'),
                            details={'error_code': error_code},
                            error=str(e)
                        )
                    raise
                
                # Retry on throttling or connection errors
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delays[attempt])
                else:
                    # Log final failure
                    if self.logger:
                        self.logger.log_dynamodb_operation(
                            operation=operation_name,
                            table=kwargs.get('TableName', 'unknown'),
                            details={'attempts': self.max_retries},
                            error=str(e)
                        )
                    raise
        
        raise last_error
    
    # FarmerProfiles operations
    
    def save_farmer_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Save or update farmer profile.
        
        Args:
            profile: Farmer profile data (must include farmer_id)
            
        Returns:
            True if successful
        """
        try:
            self._retry_operation(
                self.client.put_item,
                'put_item',
                TableName='FarmerProfiles',
                Item=self._python_to_dynamodb(profile)
            )
            return True
        except Exception as e:
            return False
    
    def get_farmer_profile(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve farmer profile by ID.
        
        Args:
            farmer_id: Unique farmer identifier
            
        Returns:
            Farmer profile data or None if not found
        """
        try:
            response = self._retry_operation(
                self.client.get_item,
                'get_item',
                TableName='FarmerProfiles',
                Key={'farmer_id': {'S': farmer_id}}
            )
            
            if 'Item' in response:
                return self._dynamodb_to_python(response['Item'])
            return None
        
        except Exception:
            return None
    
    # PriceTrends operations
    
    def save_price_trend(self, trend_data: Dict[str, Any]) -> bool:
        """
        Save price trend data.
        
        Args:
            trend_data: Price trend (must include commodity and date)
            
        Returns:
            True if successful
        """
        try:
            self._retry_operation(
                self.client.put_item,
                'put_item',
                TableName='PriceTrends',
                Item=self._python_to_dynamodb(trend_data)
            )
            return True
        except Exception:
            return False
    
    def get_price_trends(self, commodity: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieve price trends for a commodity.
        
        Args:
            commodity: Commodity name (e.g., 'Onion')
            days: Number of days to retrieve (default: 30)
            
        Returns:
            List of price trend records
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            response = self._retry_operation(
                self.client.query,
                'query',
                TableName='PriceTrends',
                KeyConditionExpression='commodity = :commodity AND #date BETWEEN :start_date AND :end_date',
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={
                    ':commodity': {'S': commodity},
                    ':start_date': {'S': start_date.strftime('%Y-%m-%d')},
                    ':end_date': {'S': end_date.strftime('%Y-%m-%d')}
                }
            )
            
            items = response.get('Items', [])
            return [self._dynamodb_to_python(item) for item in items]
        
        except Exception:
            return []
    
    # SensorReadings operations
    
    def save_sensor_reading(self, reading: Dict[str, Any]) -> bool:
        """
        Save sensor reading with TTL.
        
        Args:
            reading: Sensor data (must include storage_id and timestamp)
            
        Returns:
            True if successful
        """
        try:
            # Add TTL (30 days from now)
            ttl_timestamp = int((datetime.now() + timedelta(days=30)).timestamp())
            reading['expires_at'] = ttl_timestamp
            
            self._retry_operation(
                self.client.put_item,
                'put_item',
                TableName='SensorReadings',
                Item=self._python_to_dynamodb(reading)
            )
            return True
        except Exception:
            return False
    
    def get_sensor_history(self, storage_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Retrieve sensor reading history.
        
        Args:
            storage_id: Storage location identifier
            hours: Number of hours to retrieve (default: 24)
            
        Returns:
            List of sensor readings
        """
        try:
            # Calculate timestamp range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            response = self._retry_operation(
                self.client.query,
                'query',
                TableName='SensorReadings',
                KeyConditionExpression='storage_id = :storage_id AND #timestamp BETWEEN :start_time AND :end_time',
                ExpressionAttributeNames={'#timestamp': 'timestamp'},
                ExpressionAttributeValues={
                    ':storage_id': {'S': storage_id},
                    ':start_time': {'S': start_time.isoformat()},
                    ':end_time': {'S': end_time.isoformat()}
                }
            )
            
            items = response.get('Items', [])
            return [self._dynamodb_to_python(item) for item in items]
        
        except Exception:
            return []
    
    # QRCodes operations
    
    def save_qr_data(self, lot_data: Dict[str, Any]) -> bool:
        """
        Save QR code data.
        
        Args:
            lot_data: QR code data (must include lot_id and farmer_id)
            
        Returns:
            True if successful
        """
        try:
            self._retry_operation(
                self.client.put_item,
                'put_item',
                TableName='QRCodes',
                Item=self._python_to_dynamodb(lot_data)
            )
            return True
        except Exception:
            return False
    
    def get_qr_data(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve QR code data by lot ID.
        
        Args:
            lot_id: Lot identifier
            
        Returns:
            QR code data or None if not found
        """
        try:
            response = self._retry_operation(
                self.client.get_item,
                'get_item',
                TableName='QRCodes',
                Key={'lot_id': {'S': lot_id}}
            )
            
            if 'Item' in response:
                return self._dynamodb_to_python(response['Item'])
            return None
        
        except Exception:
            return None
    
    # UserAccounts operations
    
    def save_user_account(self, account: Dict[str, Any]) -> bool:
        """
        Save or update user account.
        
        Args:
            account: User account data (must include farmer_id and phone)
            
        Returns:
            True if successful
        """
        try:
            self._retry_operation(
                self.client.put_item,
                'put_item',
                TableName='UserAccounts',
                Item=self._python_to_dynamodb(account)
            )
            return True
        except Exception:
            return False
    
    def get_user_account(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user account by farmer ID.
        
        Args:
            farmer_id: Unique farmer identifier
            
        Returns:
            User account data or None if not found
        """
        try:
            response = self._retry_operation(
                self.client.get_item,
                'get_item',
                TableName='UserAccounts',
                Key={'farmer_id': {'S': farmer_id}}
            )
            
            if 'Item' in response:
                return self._dynamodb_to_python(response['Item'])
            return None
        
        except Exception:
            return None
    
    def query_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Query user account by phone number using GSI.
        
        Args:
            phone: Phone number
            
        Returns:
            User account data or None if not found
        """
        try:
            response = self._retry_operation(
                self.client.query,
                'query',
                TableName='UserAccounts',
                IndexName='phone-index',
                KeyConditionExpression='phone = :phone',
                ExpressionAttributeValues={
                    ':phone': {'S': phone}
                }
            )
            
            items = response.get('Items', [])
            if items:
                return self._dynamodb_to_python(items[0])
            return None
        
        except Exception:
            return None
    
    # Helper methods for type conversion
    
    def _python_to_dynamodb(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Python dict to DynamoDB format.
        
        Args:
            data: Python dictionary
            
        Returns:
            DynamoDB formatted dictionary
        """
        result = {}
        for key, value in data.items():
            if value is None:
                continue
            elif isinstance(value, bool):  # Check bool BEFORE int (bool is subclass of int)
                result[key] = {'BOOL': value}
            elif isinstance(value, str):
                result[key] = {'S': value}
            elif isinstance(value, (int, float)):
                result[key] = {'N': str(value)}
            elif isinstance(value, bytes):
                result[key] = {'B': value}
            elif isinstance(value, dict):
                result[key] = {'M': self._python_to_dynamodb(value)}
            elif isinstance(value, list):
                result[key] = {'L': [self._python_to_dynamodb({'v': item})['v'] for item in value]}
        return result
    
    def _dynamodb_to_python(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert DynamoDB format to Python dict.
        
        Args:
            data: DynamoDB formatted dictionary
            
        Returns:
            Python dictionary
        """
        result = {}
        for key, value in data.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                # Try to convert to int, fallback to float
                try:
                    result[key] = int(value['N'])
                except ValueError:
                    result[key] = float(value['N'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
            elif 'B' in value:
                result[key] = value['B']
            elif 'M' in value:
                result[key] = self._dynamodb_to_python(value['M'])
            elif 'L' in value:
                result[key] = [self._dynamodb_to_python({'v': item})['v'] for item in value['L']]
            elif 'NULL' in value:
                result[key] = None
        return result
