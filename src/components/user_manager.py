"""
User Manager Component

Handles farmer registration, authentication, and account management.
Uses bcrypt for secure PIN hashing.

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6
"""

import uuid
import bcrypt
from typing import Tuple, Dict, Optional
from datetime import datetime


class UserManager:
    """
    Manages farmer registration and authentication.
    
    Stores user accounts in memory (will integrate with DynamoDB later).
    Uses bcrypt for secure PIN hashing.
    """
    
    def __init__(self, dynamodb_store=None):
        """
        Initialize UserManager.
        
        Args:
            dynamodb_store: Optional DynamoDB store for persistence (Phase 2)
        """
        self.dynamodb_store = dynamodb_store
        # In-memory storage for Phase 1 (will use DynamoDB in Phase 2)
        self._users = {}  # phone -> user_account
        self._farmer_ids = {}  # farmer_id -> user_account
    
    def register_farmer(
        self,
        name: str,
        phone: str,
        location: str,
        storage_capacity: float,
        pin: str
    ) -> str:
        """
        Register a new farmer account.
        
        Args:
            name: Farmer's full name
            phone: Phone number (unique identifier)
            location: City/District location
            storage_capacity: Storage capacity in quintals
            pin: 4-digit PIN for authentication
            
        Returns:
            str: Unique farmer_id (UUID)
            
        Raises:
            ValueError: If phone number already registered or invalid input
        """
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        
        if not phone or not phone.strip():
            raise ValueError("Phone number cannot be empty")
        
        if not location or not location.strip():
            raise ValueError("Location cannot be empty")
        
        if storage_capacity < 0:
            raise ValueError("Storage capacity must be non-negative")
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        
        # Check if phone already registered
        if phone in self._users:
            raise ValueError(f"Phone number {phone} is already registered")
        
        # Generate unique farmer_id
        farmer_id = str(uuid.uuid4())
        
        # Hash PIN using bcrypt
        pin_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt())
        
        # Create user account
        user_account = {
            "farmer_id": farmer_id,
            "name": name.strip(),
            "phone": phone.strip(),
            "location": location.strip(),
            "storage_capacity": storage_capacity,
            "pin_hash": pin_hash,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "preferences": {}
        }
        
        # Store in memory
        self._users[phone] = user_account
        self._farmer_ids[farmer_id] = user_account
        
        # Store in DynamoDB if available
        if self.dynamodb_store:
            self.dynamodb_store.save_user_account(user_account)
        
        return farmer_id
    
    def authenticate(self, phone: str, pin: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a farmer using phone number and PIN.
        
        Args:
            phone: Phone number
            pin: 4-digit PIN
            
        Returns:
            Tuple[bool, Optional[str]]: (success, farmer_id)
            - (True, farmer_id) if authentication successful
            - (False, None) if authentication failed
        """
        # Validate inputs
        if not phone or not phone.strip():
            return (False, None)
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            return (False, None)
        
        # Check if user exists
        user_account = self._users.get(phone.strip())
        if not user_account:
            return (False, None)
        
        # Verify PIN
        pin_hash = user_account["pin_hash"]
        if bcrypt.checkpw(pin.encode('utf-8'), pin_hash):
            # Update last login
            user_account["last_login"] = datetime.now().isoformat()
            
            # Update in DynamoDB if available
            if self.dynamodb_store:
                self.dynamodb_store.save_user_account(user_account)
            
            return (True, user_account["farmer_id"])
        
        return (False, None)
    
    def get_user_account(self, farmer_id: str) -> Optional[Dict]:
        """
        Retrieve user account data by farmer_id.
        
        Args:
            farmer_id: Unique farmer identifier
            
        Returns:
            Optional[Dict]: User account data or None if not found
        """
        if not farmer_id:
            return None
        
        # Try in-memory first
        user_account = self._farmer_ids.get(farmer_id)
        
        # Try DynamoDB if not in memory and store available
        if not user_account and self.dynamodb_store:
            user_account = self.dynamodb_store.get_user_account(farmer_id)
            if user_account:
                # Cache in memory
                self._farmer_ids[farmer_id] = user_account
                self._users[user_account["phone"]] = user_account
        
        # Return copy without sensitive data
        if user_account:
            safe_account = user_account.copy()
            safe_account.pop("pin_hash", None)
            return safe_account
        
        return None
    
    def update_preferences(self, farmer_id: str, preferences: Dict) -> bool:
        """
        Update user preferences.
        
        Args:
            farmer_id: Unique farmer identifier
            preferences: Dictionary of user preferences
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not farmer_id:
            return False
        
        user_account = self._farmer_ids.get(farmer_id)
        if not user_account:
            return False
        
        # Update preferences
        user_account["preferences"].update(preferences)
        
        # Update in DynamoDB if available
        if self.dynamodb_store:
            self.dynamodb_store.save_user_account(user_account)
        
        return True
