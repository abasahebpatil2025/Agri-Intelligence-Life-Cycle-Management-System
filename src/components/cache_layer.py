"""
Cache Layer Component

TTL-based in-memory caching with LRU eviction.
Thread-safe implementation for concurrent access.

Requirements: 19.3, 19.4
"""

import time
import threading
from typing import Any, Optional
from collections import OrderedDict


class CacheLayer:
    """
    In-memory cache with TTL (Time-To-Live) and LRU eviction.
    
    Features:
    - TTL-based expiration
    - LRU (Least Recently Used) eviction when cache is full
    - Thread-safe operations using threading.Lock
    - Automatic cleanup of expired entries
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize CacheLayer.
        
        Args:
            max_size: Maximum number of items in cache (default: 1000)
        """
        self.max_size = max_size
        self._cache = OrderedDict()  # Maintains insertion order for LRU
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() > entry['expires_at']:
                # Remove expired entry
                del self._cache[key]
                return None
            
            # Move to end (most recently used) for LRU
            self._cache.move_to_end(key)
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
        """
        with self._lock:
            # Calculate expiration timestamp
            expires_at = time.time() + ttl_seconds
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = {
                    'value': value,
                    'expires_at': expires_at
                }
                # Move to end (most recently used)
                self._cache.move_to_end(key)
            else:
                # Check if cache is full
                if len(self._cache) >= self.max_size:
                    # Evict least recently used (first item)
                    self._cache.popitem(last=False)
                
                # Add new entry
                self._cache[key] = {
                    'value': value,
                    'expires_at': expires_at
                }
    
    def invalidate(self, key: str) -> bool:
        """
        Remove entry from cache.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if key was removed, False if key didn't exist
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """
        Get current cache size.
        
        Returns:
            Number of items in cache
        """
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats (size, max_size, utilization)
        """
        with self._lock:
            size = len(self._cache)
            return {
                'size': size,
                'max_size': self.max_size,
                'utilization': (size / self.max_size) * 100 if self.max_size > 0 else 0
            }
