"""
QR Scanner Component

Scans and verifies QR codes for agricultural produce tracking.
Decodes QR data, verifies against DynamoDB, and logs scan attempts.
Provides Marathi error messages for invalid QR codes.

Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6
"""

import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from pyzbar import pyzbar


class QRScanner:
    """
    QR code scanner for agricultural produce verification.
    
    Scans QR codes, decodes lot data, verifies against DynamoDB,
    and maintains audit trail of all scan attempts.
    """
    
    def __init__(self, dynamodb_store):
        """
        Initialize QR Scanner.
        
        Args:
            dynamodb_store: DynamoDB store instance for verification
        """
        self.dynamodb_store = dynamodb_store
        self.scan_log = []
    
    def decode_lot_data(self, qr_data: str) -> Dict[str, Any]:
        """
        Decode lot data from JSON string.
        
        Args:
            qr_data: JSON string from QR code
            
        Returns:
            Dictionary with lot information
            
        Raises:
            json.JSONDecodeError: If data is not valid JSON
        """
        return json.loads(qr_data)
    
    def scan_qr_code(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """
        Scan QR code from PIL Image and extract lot data.
        
        Args:
            image: PIL Image containing QR code
            
        Returns:
            Dictionary with lot data, or None if no QR code found
        """
        try:
            # Decode QR codes from image
            decoded_objects = pyzbar.decode(image)
            
            if not decoded_objects:
                return None
            
            # Get first QR code
            qr_obj = decoded_objects[0]
            qr_data = qr_obj.data.decode('utf-8')
            
            # Parse JSON data
            lot_data = self.decode_lot_data(qr_data)
            
            return lot_data
        
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
            # Corrupted QR code
            return None
        except Exception as e:
            # Other errors
            return None
    
    def verify_lot(self, lot_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify lot against DynamoDB.
        
        Args:
            lot_id: Lot identifier to verify
            
        Returns:
            Tuple of (is_valid, lot_data)
            - is_valid: True if lot exists, False otherwise
            - lot_data: Lot data from DynamoDB, or None if not found
        """
        try:
            # Query DynamoDB
            lot_data = self.dynamodb_store.get_qr_data(lot_id)
            
            if lot_data:
                # Log successful verification
                self._log_scan(lot_id, 'verified', lot_data)
                return (True, lot_data)
            else:
                # Lot not found
                self._log_scan(lot_id, 'not_found', None)
                return (False, None)
        
        except Exception as e:
            # Database error
            self._log_scan(lot_id, 'error', {'error': str(e)})
            return (False, None)
    
    def scan_and_verify(self, image: Image.Image) -> Dict[str, Any]:
        """
        Complete workflow: scan QR code and verify against database.
        
        Args:
            image: PIL Image containing QR code
            
        Returns:
            Dictionary with verification results:
            - success: True if valid, False otherwise
            - lot_data: Lot data if valid
            - message: Status message (Marathi for errors)
        """
        try:
            # Scan QR code
            lot_data = self.scan_qr_code(image)
            
            if lot_data is None:
                return {
                    'success': False,
                    'lot_data': None,
                    'message': 'QR कोड अवैध आहे'  # QR code is invalid
                }
            
            # Extract lot_id
            lot_id = lot_data.get('lot_id')
            
            if not lot_id:
                return {
                    'success': False,
                    'lot_data': None,
                    'message': 'QR कोड अवैध आहे'  # QR code is invalid
                }
            
            # Verify against database
            is_valid, db_lot_data = self.verify_lot(lot_id)
            
            if is_valid:
                return {
                    'success': True,
                    'lot_data': db_lot_data,
                    'message': 'QR कोड वैध आहे'  # QR code is valid
                }
            else:
                return {
                    'success': False,
                    'lot_data': None,
                    'message': 'QR कोड अवैध आहे'  # QR code is invalid
                }
        
        except Exception as e:
            # Handle any unexpected errors
            return {
                'success': False,
                'lot_data': None,
                'message': 'QR कोड अवैध आहे'  # QR code is invalid
            }
    
    def _log_scan(
        self,
        lot_id: str,
        status: str,
        details: Optional[Dict[str, Any]]
    ):
        """
        Log scan attempt for audit trail.
        
        Args:
            lot_id: Lot identifier
            status: Scan status (verified, not_found, error)
            details: Additional details
        """
        log_entry = {
            'lot_id': lot_id,
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'details': details
        }
        self.scan_log.append(log_entry)
    
    def get_scan_log(self, limit: Optional[int] = None) -> list:
        """
        Get scan audit log.
        
        Args:
            limit: Maximum number of entries to return (None for all)
            
        Returns:
            List of scan log entries
        """
        if limit:
            return self.scan_log[-limit:]
        return self.scan_log.copy()
    
    def clear_scan_log(self):
        """Clear scan audit log."""
        self.scan_log.clear()
