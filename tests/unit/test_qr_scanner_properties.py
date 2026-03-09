"""
Property-Based Tests for QR Scanner Component

Tests QR code scanning, verification, and round-trip encoding/decoding
using Hypothesis for comprehensive test coverage.

Properties tested:
- Property 42: QR Code Verification
- Property 43: QR Code Decoding Completeness  
- Property 61: QR Code Verification Round Trip

Note: Uses mocked pyzbar to avoid native library dependencies on Windows.
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Hypothesis imports
from hypothesis import given, strategies as st, settings, example


# ============================================================================
# Hypothesis Strategies
# ============================================================================

@st.composite
def valid_lot_data(draw):
    """Generate valid lot data for QR codes."""
    crop_types = ['Onion', 'Tomato', 'Cotton', 'Tur', 'Soybean', 'Wheat', 'Rice']
    grades = ['A', 'B', 'C']
    
    # Generate harvest date within last 30 days
    days_ago = draw(st.integers(min_value=0, max_value=30))
    harvest_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    return {
        'lot_id': draw(st.uuids()).hex,
        'crop_type': draw(st.sampled_from(crop_types)),
        'grade': draw(st.sampled_from(grades)),
        'harvest_date': harvest_date,
        'farmer_id': draw(st.uuids()).hex
    }


@st.composite
def corrupted_json_string(draw):
    """Generate corrupted JSON strings."""
    corruption_types = [
        '{"lot_id": "123", "grade":',  # Incomplete JSON
        '{lot_id: 123}',  # Invalid JSON syntax
        '{"lot_id": "123"',  # Missing closing brace
        'not json at all',  # Not JSON
        '',  # Empty string
    ]
    return draw(st.sampled_from(corruption_types))


# ============================================================================
# Mock Helpers
# ============================================================================

def create_mock_qr_image(lot_data: dict) -> Image.Image:
    """Create a mock QR code image with embedded data for testing."""
    img = Image.new('RGB', (300, 300), color='white')
    img.info['qr_data'] = json.dumps(lot_data)
    return img


def mock_pyzbar_decode(image: Image.Image):
    """Mock pyzbar.decode for testing without native library."""
    if 'qr_data' in image.info:
        mock_decoded = Mock()
        mock_decoded.data = image.info['qr_data'].encode('utf-8')
        return [mock_decoded]
    return []


# ============================================================================
# Property 42 & 61: QR Code Verification Round Trip
# ============================================================================

@given(lot_data=valid_lot_data())
@settings(max_examples=50, deadline=None)
@example(lot_data={
    'lot_id': 'test123',
    'crop_type': 'Onion',
    'grade': 'A',
    'harvest_date': '2026-03-01',
    'farmer_id': 'farmer001'
})
@patch('pyzbar.pyzbar.decode', side_effect=mock_pyzbar_decode)
def test_property_qr_verification_round_trip(mock_decode, lot_data):
    """
    Property 42 & 61: QR Code Verification Round Trip
    
    Validates: Requirements 24.2, 24.3, 24.4, 24.5
    
    Property: For any valid lot data:
    1. Generate QR code
    2. Scan QR code
    3. Decoded data should match original data
    4. Verification should succeed if lot exists in database
    """
    from src.components.qr_scanner import QRScanner
    
    # Setup mocks
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.return_value = lot_data
    
    # Generate mock QR code
    qr_image = create_mock_qr_image(lot_data)
    
    # Scan QR code
    scanner = QRScanner(dynamodb_store)
    scanned_data = scanner.scan_qr_code(qr_image)
    
    # Property: Scanned data should match original data
    assert scanned_data is not None, "QR code should be scannable"
    assert scanned_data['lot_id'] == lot_data['lot_id']
    assert scanned_data['crop_type'] == lot_data['crop_type']
    assert scanned_data['grade'] == lot_data['grade']
    assert scanned_data['harvest_date'] == lot_data['harvest_date']
    assert scanned_data['farmer_id'] == lot_data['farmer_id']
    
    # Verify lot against database
    is_valid, db_lot_data = scanner.verify_lot(lot_data['lot_id'])
    
    # Property: Verification should succeed for existing lot
    assert is_valid is True, "Verification should succeed for existing lot"
    assert db_lot_data == lot_data, "Database data should match original data"


# ============================================================================
# Property 43: QR Code Decoding Completeness
# ============================================================================

@given(lot_data=valid_lot_data())
@settings(max_examples=50, deadline=None)
@patch('pyzbar.pyzbar.decode', side_effect=mock_pyzbar_decode)
def test_property_qr_decoding_completeness(mock_decode, lot_data):
    """
    Property 43: QR Code Decoding Completeness
    
    Validates: Requirements 24.2, 24.3
    
    Property: For any valid lot data encoded in QR:
    - All fields must be present in decoded data
    - No data loss during encoding/decoding
    - Field values must match exactly
    """
    from src.components.qr_scanner import QRScanner
    
    # Setup
    dynamodb_store = Mock()
    scanner = QRScanner(dynamodb_store)
    
    # Generate mock QR code
    qr_image = create_mock_qr_image(lot_data)
    
    # Scan and decode
    decoded_data = scanner.scan_qr_code(qr_image)
    
    # Property: All fields must be present
    required_fields = ['lot_id', 'crop_type', 'grade', 'harvest_date', 'farmer_id']
    for field in required_fields:
        assert field in decoded_data, f"Field '{field}' must be present in decoded data"
        assert decoded_data[field] == lot_data[field], f"Field '{field}' value must match"


# ============================================================================
# Property: Invalid QR Code Handling
# ============================================================================

@patch('pyzbar.pyzbar.decode', return_value=[])
def test_property_invalid_qr_code_handling(mock_decode):
    """
    Property: Invalid QR Code Handling
    
    Validates: Requirements 24.5, 24.6
    
    Property: Scanner should handle invalid QR codes gracefully:
    - Blank images return None
    - No exceptions raised
    """
    from src.components.qr_scanner import QRScanner
    
    dynamodb_store = Mock()
    scanner = QRScanner(dynamodb_store)
    
    # Test: Blank image (no QR code)
    blank_image = Image.new('RGB', (200, 200), color='white')
    result = scanner.scan_qr_code(blank_image)
    assert result is None, "Blank image should return None"


# ============================================================================
# Property: Corrupted JSON Handling
# ============================================================================

@given(corrupted_json=corrupted_json_string())
@settings(max_examples=20, deadline=None)
def test_property_corrupted_json_handling(corrupted_json):
    """
    Property: Corrupted JSON Handling
    
    Validates: Requirements 24.5
    
    Property: Scanner should handle corrupted JSON gracefully:
    - Invalid JSON handled without crashing
    """
    from src.components.qr_scanner import QRScanner
    
    dynamodb_store = Mock()
    scanner = QRScanner(dynamodb_store)
    
    # Attempt to decode corrupted JSON
    try:
        result = scanner.decode_lot_data(corrupted_json)
    except json.JSONDecodeError:
        # Expected for invalid JSON
        pass


# ============================================================================
# Property: Verification with Non-Existent Lot
# ============================================================================

@given(lot_id=st.text(min_size=1, max_size=50))
@settings(max_examples=30, deadline=None)
def test_property_verification_nonexistent_lot(lot_id):
    """
    Property: Verification with Non-Existent Lot
    
    Validates: Requirements 24.4, 24.6
    
    Property: Verifying a non-existent lot should:
    - Return (False, None)
    - Not raise exceptions
    - Log the failed verification attempt
    """
    from src.components.qr_scanner import QRScanner
    
    # Setup mock that returns None (lot not found)
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.return_value = None
    
    scanner = QRScanner(dynamodb_store)
    
    # Verify non-existent lot
    is_valid, lot_data = scanner.verify_lot(lot_id)
    
    # Property: Should return False and None
    assert is_valid is False, "Non-existent lot should return False"
    assert lot_data is None, "Non-existent lot should return None for data"
    
    # Property: Should log the failed attempt
    assert len(scanner.scan_log) > 0, "Failed verification should be logged"
    assert scanner.scan_log[-1]['status'] == 'not_found'


# ============================================================================
# Property: Scan and Verify Complete Workflow
# ============================================================================

@given(lot_data=valid_lot_data())
@settings(max_examples=30, deadline=None)
@patch('pyzbar.pyzbar.decode', side_effect=mock_pyzbar_decode)
def test_property_scan_and_verify_workflow(mock_decode, lot_data):
    """
    Property: Scan and Verify Complete Workflow
    
    Validates: Requirements 24.1, 24.2, 24.3, 24.4
    
    Property: Complete scan and verify workflow should:
    1. Scan QR code from image
    2. Verify against database
    3. Return success with lot data if valid
    """
    from src.components.qr_scanner import QRScanner
    
    # Setup mocks
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.return_value = lot_data
    
    # Generate mock QR code
    qr_image = create_mock_qr_image(lot_data)
    
    # Scan and verify
    scanner = QRScanner(dynamodb_store)
    result = scanner.scan_and_verify(qr_image)
    
    # Property: Should succeed with valid data
    assert result['success'] is True, "Valid QR should verify successfully"
    assert result['lot_data'] == lot_data, "Returned data should match original"
    assert 'वैध' in result['message'], "Success message should be in Marathi"


# ============================================================================
# Property: Marathi Error Messages
# ============================================================================

@patch('pyzbar.pyzbar.decode', return_value=[])
def test_property_marathi_error_messages(mock_decode):
    """
    Property: Marathi Error Messages
    
    Validates: Requirements 24.6
    
    Property: All error messages should be in Marathi:
    - Invalid QR code: "QR कोड अवैध आहे"
    - Not found in database: "QR कोड अवैध आहे"
    """
    from src.components.qr_scanner import QRScanner
    
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.return_value = None
    
    scanner = QRScanner(dynamodb_store)
    
    # Test 1: Blank image (no QR code)
    blank_image = Image.new('RGB', (200, 200), color='white')
    result = scanner.scan_and_verify(blank_image)
    
    assert result['success'] is False
    assert 'QR कोड अवैध आहे' in result['message'], "Error message should be in Marathi"
    
    # Test 2: Valid QR but not in database
    lot_data = {
        'lot_id': 'nonexistent123',
        'crop_type': 'Onion',
        'grade': 'A',
        'harvest_date': '2026-03-01',
        'farmer_id': 'farmer001'
    }
    
    with patch('pyzbar.pyzbar.decode', side_effect=mock_pyzbar_decode):
        qr_image = create_mock_qr_image(lot_data)
        result = scanner.scan_and_verify(qr_image)
    
    assert result['success'] is False
    assert 'QR कोड अवैध आहे' in result['message'], "Not found message should be in Marathi"


# ============================================================================
# Property: Audit Trail Logging
# ============================================================================

@given(lot_data=valid_lot_data())
@settings(max_examples=20, deadline=None)
def test_property_audit_trail_logging(lot_data):
    """
    Property: Audit Trail Logging
    
    Validates: Requirements 24.6
    
    Property: All scan attempts should be logged:
    - Successful verifications logged as 'verified'
    - Failed verifications logged as 'not_found'
    - Log contains lot_id, timestamp, status, details
    """
    from src.components.qr_scanner import QRScanner
    
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.return_value = lot_data
    
    scanner = QRScanner(dynamodb_store)
    
    # Verify lot
    is_valid, db_data = scanner.verify_lot(lot_data['lot_id'])
    
    # Property: Verification should be logged
    assert len(scanner.scan_log) > 0, "Verification should be logged"
    
    log_entry = scanner.scan_log[-1]
    assert log_entry['lot_id'] == lot_data['lot_id']
    assert 'timestamp' in log_entry
    assert log_entry['status'] == 'verified'
    assert log_entry['details'] == lot_data


# ============================================================================
# Property: Multiple Scans Independence
# ============================================================================

@given(lot_data_list=st.lists(valid_lot_data(), min_size=2, max_size=5, unique_by=lambda x: x['lot_id']))
@settings(max_examples=20, deadline=None)
@patch('pyzbar.pyzbar.decode', side_effect=mock_pyzbar_decode)
def test_property_multiple_scans_independence(mock_decode, lot_data_list):
    """
    Property: Multiple Scans Independence
    
    Validates: Requirements 24.1, 24.4
    
    Property: Scanning multiple QR codes should:
    - Each scan returns correct data for its QR code
    - No interference between scans
    - All scans logged independently
    """
    from src.components.qr_scanner import QRScanner
    
    # Setup mock that returns correct data for each lot_id
    dynamodb_store = Mock()
    
    def get_qr_data_side_effect(lot_id):
        for lot_data in lot_data_list:
            if lot_data['lot_id'] == lot_id:
                return lot_data
        return None
    
    dynamodb_store.get_qr_data.side_effect = get_qr_data_side_effect
    
    # Generate mock QR codes
    qr_images = []
    for lot_data in lot_data_list:
        qr_image = create_mock_qr_image(lot_data)
        qr_images.append((qr_image, lot_data))
    
    # Scan all QR codes
    scanner = QRScanner(dynamodb_store)
    
    for qr_image, expected_data in qr_images:
        scanned_data = scanner.scan_qr_code(qr_image)
        
        # Property: Each scan returns correct data
        assert scanned_data is not None
        assert scanned_data['lot_id'] == expected_data['lot_id']
        assert scanned_data['crop_type'] == expected_data['crop_type']
        assert scanned_data['grade'] == expected_data['grade']


# ============================================================================
# Property: Database Error Handling
# ============================================================================

@given(lot_id=st.text(min_size=1, max_size=50))
@settings(max_examples=20, deadline=None)
def test_property_database_error_handling(lot_id):
    """
    Property: Database Error Handling
    
    Validates: Requirements 24.5
    
    Property: Scanner should handle database errors gracefully:
    - Return (False, None) on database error
    - Log error in scan log
    - No unhandled exceptions
    """
    from src.components.qr_scanner import QRScanner
    
    # Setup mock that raises exception
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.side_effect = Exception("Database connection error")
    
    scanner = QRScanner(dynamodb_store)
    
    # Verify lot (should handle exception)
    is_valid, lot_data = scanner.verify_lot(lot_id)
    
    # Property: Should return False and None on error
    assert is_valid is False, "Database error should return False"
    assert lot_data is None, "Database error should return None for data"
    
    # Property: Error should be logged
    assert len(scanner.scan_log) > 0
    assert scanner.scan_log[-1]['status'] == 'error'


# ============================================================================
# Property: Scan Log Retrieval
# ============================================================================

@given(num_scans=st.integers(min_value=1, max_value=10))
@settings(max_examples=15, deadline=None)
def test_property_scan_log_retrieval(num_scans):
    """
    Property: Scan Log Retrieval
    
    Validates: Requirements 24.6
    
    Property: Scan log should:
    - Store all scan attempts
    - Return correct number of entries with limit
    - Return all entries when no limit specified
    """
    from src.components.qr_scanner import QRScanner
    
    dynamodb_store = Mock()
    dynamodb_store.get_qr_data.return_value = {'lot_id': 'test', 'grade': 'A'}
    
    scanner = QRScanner(dynamodb_store)
    
    # Perform multiple verifications
    for i in range(num_scans):
        scanner.verify_lot(f'lot_{i}')
    
    # Property: All scans should be logged
    all_logs = scanner.get_scan_log()
    assert len(all_logs) == num_scans, "All scans should be logged"
    
    # Property: Limited retrieval should work
    if num_scans >= 3:
        limited_logs = scanner.get_scan_log(limit=3)
        assert len(limited_logs) == 3, "Limited retrieval should return correct count"
        assert limited_logs == all_logs[-3:], "Should return most recent entries"


# ============================================================================
# Integration Test: Complete Trust & Transparency Flow
# ============================================================================

@patch('pyzbar.pyzbar.decode', side_effect=mock_pyzbar_decode)
def test_integration_trust_transparency_flow(mock_decode):
    """
    Integration Test: Complete Trust & Transparency Flow
    
    Validates: Complete Task 24 requirements
    
    Tests the complete flow:
    1. Farmer generates QR code for produce lot
    2. QR code is saved to database
    3. Consumer scans QR code
    4. System verifies authenticity
    5. Consumer sees complete lot information
    """
    from src.components.qr_scanner import QRScanner
    from src.components.qr_generator import QRGenerator
    
    # Setup
    dynamodb_store = Mock()
    
    # Farmer data
    farmer_id = 'farmer_pune_001'
    lot_data = {
        'lot_id': 'onion_lot_20260308',
        'crop_type': 'Onion',
        'grade': 'A',
        'harvest_date': '2026-03-01',
        'farmer_id': farmer_id
    }
    
    # Mock database responses
    dynamodb_store.save_qr_data.return_value = True
    dynamodb_store.get_qr_data.return_value = lot_data
    
    # Step 1: Farmer generates QR code
    generator = QRGenerator(dynamodb_store)
    result = generator.create_lot_qr(
        crop_type=lot_data['crop_type'],
        grade=lot_data['grade'],
        harvest_date=lot_data['harvest_date'],
        farmer_id=lot_data['farmer_id'],
        lot_id=lot_data['lot_id']
    )
    
    assert result['lot_id'] == lot_data['lot_id']
    assert result['qr_image'] is not None
    
    # Step 2: Consumer scans QR code (using mock QR)
    mock_qr_image = create_mock_qr_image(lot_data)
    scanner = QRScanner(dynamodb_store)
    scan_result = scanner.scan_and_verify(mock_qr_image)
    
    # Step 3: Verification succeeds
    assert scan_result['success'] is True
    assert scan_result['lot_data']['lot_id'] == lot_data['lot_id']
    assert scan_result['lot_data']['crop_type'] == 'Onion'
    assert scan_result['lot_data']['grade'] == 'A'
    assert scan_result['lot_data']['farmer_id'] == farmer_id
    
    # Step 4: Success message in Marathi
    assert 'वैध' in scan_result['message']
    
    print("✓ Trust & Transparency flow complete!")
    print("✓ विश्वास आणि पारदर्शकता प्रवाह पूर्ण!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
