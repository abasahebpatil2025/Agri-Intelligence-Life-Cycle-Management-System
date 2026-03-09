"""
QR Generator Component

Generates QR codes for agricultural produce lot tracking.
Encodes lot data (crop, grade, harvest date, farmer ID) into QR codes.
Stores QR codes in S3 and lot data in DynamoDB.

Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6
"""

import json
import uuid
import qrcode
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image


class QRGenerator:
    """
    QR code generator for agricultural produce tracking.
    
    Generates QR codes with embedded lot data for supply chain traceability.
    Validates grade, stores QR images in S3, and logs data in DynamoDB.
    """
    
    # Valid grades
    VALID_GRADES = ['A', 'B', 'C']
    
    def __init__(
        self,
        dynamodb_store,
        s3_client: Optional[Any] = None,
        bucket_name: Optional[str] = None
    ):
        """
        Initialize QR Generator.
        
        Args:
            dynamodb_store: DynamoDB store instance
            s3_client: Boto3 S3 client (optional)
            bucket_name: S3 bucket name for QR storage (optional)
        """
        self.dynamodb_store = dynamodb_store
        self.s3_client = s3_client
        self.bucket_name = bucket_name
    
    def encode_lot_data(self, lot_data: Dict[str, Any]) -> str:
        """
        Encode lot data as JSON string.
        
        Args:
            lot_data: Dictionary with lot information
            
        Returns:
            JSON string representation of lot data
        """
        return json.dumps(lot_data, ensure_ascii=False)
    
    def decode_lot_data(self, qr_data: str) -> Dict[str, Any]:
        """
        Decode lot data from JSON string.
        
        Args:
            qr_data: JSON string from QR code
            
        Returns:
            Dictionary with lot information
        """
        return json.loads(qr_data)
    
    def generate_qr_code(
        self,
        lot_id: str,
        crop_type: str,
        grade: str,
        harvest_date: str,
        farmer_id: str
    ) -> Image.Image:
        """
        Generate QR code for produce lot.
        
        Args:
            lot_id: Unique lot identifier
            crop_type: Type of crop (e.g., 'Onion', 'Tomato')
            grade: Quality grade ('A', 'B', or 'C')
            harvest_date: Harvest date (ISO 8601 format)
            farmer_id: Farmer identifier
            
        Returns:
            PIL Image object containing QR code
            
        Raises:
            ValueError: If grade is not 'A', 'B', or 'C'
        """
        # Validate grade
        if grade not in self.VALID_GRADES:
            raise ValueError(f"Grade must be one of {self.VALID_GRADES}, got '{grade}'")
        
        # Create lot data dictionary
        lot_data = {
            'lot_id': lot_id,
            'crop_type': crop_type,
            'grade': grade,
            'harvest_date': harvest_date,
            'farmer_id': farmer_id
        }
        
        # Encode lot data as JSON
        qr_data = self.encode_lot_data(lot_data)
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,  # Auto-adjust size
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,  # Size of each box in pixels
            border=4  # Border size in boxes
        )
        
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create PIL Image
        img = qr.make_image(fill_color="black", back_color="white")
        
        return img
    
    def save_qr_data(self, lot_data: Dict[str, Any]) -> str:
        """
        Save lot data to DynamoDB.
        
        Args:
            lot_data: Dictionary with lot information
            
        Returns:
            lot_id of saved data
        """
        # Generate lot_id if not provided
        if 'lot_id' not in lot_data:
            lot_data['lot_id'] = str(uuid.uuid4())
        
        # Save to DynamoDB
        self.dynamodb_store.save_qr_data(lot_data)
        
        return lot_data['lot_id']
    
    def save_qr_to_s3(
        self,
        qr_image: Image.Image,
        farmer_id: str,
        lot_id: str
    ) -> Optional[str]:
        """
        Upload QR code image to S3.
        
        Args:
            qr_image: PIL Image object
            farmer_id: Farmer identifier
            lot_id: Lot identifier
            
        Returns:
            S3 URL of uploaded image, or None if S3 not configured
        """
        if self.s3_client is None or self.bucket_name is None:
            return None
        
        # Create S3 key
        s3_key = f"qr-codes/{farmer_id}/{lot_id}.png"
        
        # Convert PIL Image to bytes
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType='image/png'
            )
            
            # Return S3 URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            return url
        
        except Exception as e:
            # Log error but don't fail
            print(f"Error uploading to S3: {e}")
            return None
    
    def create_lot_qr(
        self,
        crop_type: str,
        grade: str,
        harvest_date: str,
        farmer_id: str,
        lot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: generate QR, save to DynamoDB and S3.
        
        Args:
            crop_type: Type of crop
            grade: Quality grade ('A', 'B', or 'C')
            harvest_date: Harvest date
            farmer_id: Farmer identifier
            lot_id: Optional lot identifier (generated if not provided)
            
        Returns:
            Dictionary with lot_id, qr_image, and s3_url
        """
        # Generate lot_id if not provided
        if lot_id is None:
            lot_id = str(uuid.uuid4())
        
        # Generate QR code
        qr_image = self.generate_qr_code(
            lot_id,
            crop_type,
            grade,
            harvest_date,
            farmer_id
        )
        
        # Save lot data to DynamoDB
        lot_data = {
            'lot_id': lot_id,
            'crop_type': crop_type,
            'grade': grade,
            'harvest_date': harvest_date,
            'farmer_id': farmer_id
        }
        self.save_qr_data(lot_data)
        
        # Upload QR to S3
        s3_url = self.save_qr_to_s3(qr_image, farmer_id, lot_id)
        
        return {
            'lot_id': lot_id,
            'qr_image': qr_image,
            's3_url': s3_url
        }
