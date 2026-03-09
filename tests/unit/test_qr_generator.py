import pytest
from unittest.mock import Mock, MagicMock
from PIL import Image
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from qr_generator import QRGenerator

class TestQRGenerator:
    def test_init(self):
        gen = QRGenerator(Mock(), Mock(), 'bucket')
        assert gen is not None
    
    def test_encode_decode(self):
        gen = QRGenerator(Mock())
        data = {'lot_id': '123', 'grade': 'A'}
        encoded = gen.encode_lot_data(data)
        decoded = gen.decode_lot_data(encoded)
        assert decoded == data
    
    def test_grade_validation_valid(self):
        gen = QRGenerator(Mock())
        img = gen.generate_qr_code('lot1', 'Onion', 'A', '2026-03-07', 'farmer1')
        assert hasattr(img, 'save')  # This checks if it's a valid PIL-compatible image
    
    def test_grade_validation_invalid(self):
        gen = QRGenerator(Mock())
        with pytest.raises(ValueError, match='Grade must be one of'):
            gen.generate_qr_code('lot1', 'Onion', 'D', '2026-03-07', 'farmer1')
    
    def test_qr_specs(self):
        gen = QRGenerator(Mock())
        img = gen.generate_qr_code('lot1', 'Onion', 'B', '2026-03-07', 'farmer1')
        assert img.size[0] > 0
        assert img.size[1] > 0
    
    def test_save_qr_data(self):
        store = Mock()
        gen = QRGenerator(store)
        lot_id = gen.save_qr_data({'lot_id': 'test123', 'grade': 'A'})
        assert lot_id == 'test123'
        assert store.save_qr_data.called
    
    def test_save_qr_to_s3(self):
        s3 = Mock()
        s3.put_object.return_value = {}
        gen = QRGenerator(Mock(), s3, 'test-bucket')
        img = Image.new('RGB', (100, 100))
        url = gen.save_qr_to_s3(img, 'farmer1', 'lot1')
        assert 'qr-codes/farmer1/lot1.png' in url
        assert s3.put_object.called
    
    def test_create_lot_qr(self):
        store = Mock()
        s3 = Mock()
        s3.put_object.return_value = {}
        gen = QRGenerator(store, s3, 'test-bucket')
        result = gen.create_lot_qr('Tomato', 'A', '2026-03-07', 'farmer1')
        assert 'lot_id' in result
        assert 'qr_image' in result
        assert 's3_url' in result
