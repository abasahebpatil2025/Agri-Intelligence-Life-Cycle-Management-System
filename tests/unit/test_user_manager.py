"""
Unit tests for User Manager Component

Tests farmer registration, authentication, and account management.
Property-based tests for registration uniqueness and authentication validation.
"""

import pytest
import uuid
from hypothesis import given, strategies as st, assume, settings

# Import the component
import sys
sys.path.insert(0, 'src/components')
from user_manager import UserManager


class TestUserManager:
    """Test suite for UserManager component"""
    
    def test_register_farmer_success(self):
        """Test successful farmer registration"""
        manager = UserManager()
        
        farmer_id = manager.register_farmer(
            name="Ramesh Patil",
            phone="9876543210",
            location="Nashik",
            storage_capacity=100.0,
            pin="1234"
        )
        
        # Verify farmer_id is a valid UUID
        assert uuid.UUID(farmer_id)
        
        # Verify account can be retrieved
        account = manager.get_user_account(farmer_id)
        assert account is not None
        assert account["name"] == "Ramesh Patil"
        assert account["phone"] == "9876543210"
        assert account["location"] == "Nashik"
        assert account["storage_capacity"] == 100.0
        assert "pin_hash" not in account  # PIN hash should not be exposed
    
    def test_register_farmer_duplicate_phone(self):
        """Test error when registering duplicate phone number"""
        manager = UserManager()
        
        # Register first farmer
        manager.register_farmer(
            name="Ramesh Patil",
            phone="9876543210",
            location="Nashik",
            storage_capacity=100.0,
            pin="1234"
        )
        
        # Try to register with same phone
        with pytest.raises(ValueError) as exc_info:
            manager.register_farmer(
                name="Suresh Kumar",
                phone="9876543210",
                location="Pune",
                storage_capacity=50.0,
                pin="5678"
            )
        
        assert "already registered" in str(exc_info.value)
    
    def test_register_farmer_invalid_pin(self):
        """Test error when PIN is not 4 digits"""
        manager = UserManager()
        
        # Test with 3 digits
        with pytest.raises(ValueError) as exc_info:
            manager.register_farmer(
                name="Ramesh Patil",
                phone="9876543210",
                location="Nashik",
                storage_capacity=100.0,
                pin="123"
            )
        assert "4 digits" in str(exc_info.value)
        
        # Test with 5 digits
        with pytest.raises(ValueError) as exc_info:
            manager.register_farmer(
                name="Ramesh Patil",
                phone="9876543210",
                location="Nashik",
                storage_capacity=100.0,
                pin="12345"
            )
        assert "4 digits" in str(exc_info.value)
        
        # Test with non-numeric
        with pytest.raises(ValueError) as exc_info:
            manager.register_farmer(
                name="Ramesh Patil",
                phone="9876543210",
                location="Nashik",
                storage_capacity=100.0,
                pin="abcd"
            )
        assert "4 digits" in str(exc_info.value)
    
    def test_register_farmer_empty_fields(self):
        """Test error when required fields are empty"""
        manager = UserManager()
        
        # Empty name
        with pytest.raises(ValueError):
            manager.register_farmer("", "9876543210", "Nashik", 100.0, "1234")
        
        # Empty phone
        with pytest.raises(ValueError):
            manager.register_farmer("Ramesh", "", "Nashik", 100.0, "1234")
        
        # Empty location
        with pytest.raises(ValueError):
            manager.register_farmer("Ramesh", "9876543210", "", 100.0, "1234")
    
    def test_register_farmer_negative_storage(self):
        """Test error when storage capacity is negative"""
        manager = UserManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.register_farmer(
                name="Ramesh Patil",
                phone="9876543210",
                location="Nashik",
                storage_capacity=-10.0,
                pin="1234"
            )
        assert "non-negative" in str(exc_info.value)
    
    def test_authenticate_success(self):
        """Test successful authentication"""
        manager = UserManager()
        
        # Register farmer
        farmer_id = manager.register_farmer(
            name="Ramesh Patil",
            phone="9876543210",
            location="Nashik",
            storage_capacity=100.0,
            pin="1234"
        )
        
        # Authenticate with correct credentials
        success, returned_id = manager.authenticate("9876543210", "1234")
        
        assert success is True
        assert returned_id == farmer_id
    
    def test_authenticate_wrong_pin(self):
        """Test authentication fails with wrong PIN"""
        manager = UserManager()
        
        # Register farmer
        manager.register_farmer(
            name="Ramesh Patil",
            phone="9876543210",
            location="Nashik",
            storage_capacity=100.0,
            pin="1234"
        )
        
        # Try to authenticate with wrong PIN
        success, returned_id = manager.authenticate("9876543210", "9999")
        
        assert success is False
        assert returned_id is None
    
    def test_authenticate_nonexistent_user(self):
        """Test authentication fails for non-existent user"""
        manager = UserManager()
        
        success, returned_id = manager.authenticate("9999999999", "1234")
        
        assert success is False
        assert returned_id is None
    
    def test_authenticate_invalid_pin_format(self):
        """Test authentication fails with invalid PIN format"""
        manager = UserManager()
        
        # Register farmer
        manager.register_farmer(
            name="Ramesh Patil",
            phone="9876543210",
            location="Nashik",
            storage_capacity=100.0,
            pin="1234"
        )
        
        # Try with 3-digit PIN
        success, returned_id = manager.authenticate("9876543210", "123")
        assert success is False
        
        # Try with non-numeric PIN
        success, returned_id = manager.authenticate("9876543210", "abcd")
        assert success is False
    
    def test_get_user_account_not_found(self):
        """Test get_user_account returns None for non-existent farmer"""
        manager = UserManager()
        
        account = manager.get_user_account("non-existent-id")
        assert account is None
    
    def test_update_preferences_success(self):
        """Test successful preference update"""
        manager = UserManager()
        
        # Register farmer
        farmer_id = manager.register_farmer(
            name="Ramesh Patil",
            phone="9876543210",
            location="Nashik",
            storage_capacity=100.0,
            pin="1234"
        )
        
        # Update preferences
        result = manager.update_preferences(
            farmer_id,
            {"language": "Marathi", "notifications": True}
        )
        
        assert result is True
        
        # Verify preferences were updated
        account = manager.get_user_account(farmer_id)
        assert account["preferences"]["language"] == "Marathi"
        assert account["preferences"]["notifications"] is True
    
    def test_update_preferences_nonexistent_user(self):
        """Test update_preferences fails for non-existent user"""
        manager = UserManager()
        
        result = manager.update_preferences(
            "non-existent-id",
            {"language": "Marathi"}
        )
        
        assert result is False


# Property-Based Tests
class TestUserManagerProperties:
    """Property-based tests for User Manager"""
    
    @settings(deadline=None)
    @given(
        name=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))),
        phone=st.text(min_size=10, max_size=15, alphabet=st.characters(whitelist_categories=('Nd',))),
        location=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))),
        storage_capacity=st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
        pin=st.text(min_size=4, max_size=4, alphabet='0123456789')
    )
    def test_property_farmer_registration_uniqueness(self, name, phone, location, storage_capacity, pin):
        """
        Property 49: Farmer Registration Uniqueness
        
        GIVEN any valid farmer registration data
        WHEN a farmer is registered
        THEN a unique farmer_id is generated
        AND the same phone number cannot be registered twice
        
        Validates: Requirement 29.2
        """
        assume(name.strip())  # Ensure non-empty after strip
        assume(location.strip())
        
        manager = UserManager()
        
        # First registration should succeed
        farmer_id_1 = manager.register_farmer(name, phone, location, storage_capacity, pin)
        assert uuid.UUID(farmer_id_1)  # Valid UUID
        
        # Second registration with same phone should fail
        with pytest.raises(ValueError):
            manager.register_farmer(name + "2", phone, location, storage_capacity, pin)
    
    @settings(deadline=None)
    @given(
        name=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))),
        phone=st.text(min_size=10, max_size=15, alphabet=st.characters(whitelist_categories=('Nd',))),
        location=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))),
        storage_capacity=st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
        pin=st.text(min_size=4, max_size=4, alphabet='0123456789')
    )
    def test_property_user_authentication_validation(self, name, phone, location, storage_capacity, pin):
        """
        Property 50: User Authentication Validation
        
        GIVEN a registered farmer with valid credentials
        WHEN authenticating with correct PIN
        THEN authentication succeeds and returns farmer_id
        WHEN authenticating with incorrect PIN
        THEN authentication fails
        
        Validates: Requirement 29.4
        """
        assume(name.strip())
        assume(location.strip())
        
        manager = UserManager()
        
        # Register farmer
        farmer_id = manager.register_farmer(name, phone, location, storage_capacity, pin)
        
        # Correct PIN should authenticate
        success, returned_id = manager.authenticate(phone, pin)
        assert success is True
        assert returned_id == farmer_id
        
        # Wrong PIN should fail
        wrong_pin = "0000" if pin != "0000" else "1111"
        success, returned_id = manager.authenticate(phone, wrong_pin)
        assert success is False
        assert returned_id is None
