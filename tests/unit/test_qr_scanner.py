import pytest
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from qr_scanner import QRScanner

class TestQRScanner:
    def test_init(self):
        scanner = QRScanner(Mock())
        assert scanner.scan_log == []
    
    def test_decode_lot_data(self):
        scanner = QRScanner(Mock())
        json_str = json.dumps({'lot_id': '123', 'grade': 'A'})
        decoded = scanner.decode_lot_data(json_str)
        assert decoded['lot_id'] == '123'
        assert decoded['grade'] == 'A'
    
    def test_verify_lot_found(self):
        dynamodb_store = Mock()
        dynamodb_store.get_qr_data.return_value = {'lot_id': 'lot1', 'crop_type': 'Onion', 'grade': 'A'}
        scanner = QRScanner(dynamodb_store)
        is_valid, lot_data = scanner.verify_lot('lot1')
        assert is_valid is True
        assert lot_data['lot_id'] == 'lot1'
    
    def test_marathi_error_message(self):
        scanner = QRScanner(Mock())
        # Create a blank image (no QR code)
        img = Image.new('RGB', (100, 100), color='white')
        result = scanner.scan_and_verify(img)
        assert result['success'] is False
        assert 'QR कोड अवैध आहे' in result['message']
