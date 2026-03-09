"""
Unit tests for Cache Layer Component

Tests TTL-based caching, LRU eviction, and thread safety.
Property-based tests for caching behavior.
"""

import pytest
import time
import threading
from hypothesis import given, strategies as st, assume, settings

# Import the component
import sys
sys.path.insert(0, 'src/components')
from cache_layer import CacheLayer


class TestCacheLayer:
    """Test suite for CacheLayer component"""
    
    def test_set_and_get_success(self):
        """Test basic set and get operations"""
        cache = CacheLayer()
        
        cache.set("test_key", "test_value", ttl_seconds=60)
        value = cache.get("test_key")
        
        assert value == "test_value"
    
    def test_get_nonexistent_key(self):
        """Test get returns None for non-existent key"""
        cache = CacheLayer()
        
        value = cache.get("nonexistent")
        
        assert value is None
    
    def test_ttl_expiration(self):
        """Test that cached values expire after TTL"""
        cache = CacheLayer()
        
        # Set with 1 second TTL
        cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should exist immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("test_key") is None
    
    def test_invalidate_existing_key(self):
        """Test invalidate removes existing key"""
        cache = CacheLayer()
        
        cache.set("test_key", "test_value", ttl_seconds=60)
        result = cache.invalidate("test_key")
        
        assert result is True
        assert cache.get("test_key") is None
    
    def test_invalidate_nonexistent_key(self):
        """Test invalidate returns False for non-existent key"""
        cache = CacheLayer()
        
        result = cache.invalidate("nonexistent")
        
        assert result is False
    
    def test_update_existing_key(self):
        """Test updating an existing key"""
        cache = CacheLayer()
        
        cache.set("test_key", "value1", ttl_seconds=60)
        cache.set("test_key", "value2", ttl_seconds=60)
        
        assert cache.get("test_key") == "value2"
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = CacheLayer(max_size=3)
        
        # Fill cache
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        cache.set("key3", "value3", ttl_seconds=60)
        
        # Add fourth item, should evict key1 (least recently used)
        cache.set("key4", "value4", ttl_seconds=60)
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_lru_with_access(self):
        """Test LRU eviction considers access order"""
        cache = CacheLayer(max_size=3)
        
        # Fill cache
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        cache.set("key3", "value3", ttl_seconds=60)
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add fourth item, should evict key2 (now least recently used)
        cache.set("key4", "value4", ttl_seconds=60)
        
        assert cache.get("key1") == "value1"  # Not evicted
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_clear(self):
        """Test clear removes all entries"""
        cache = CacheLayer()
        
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.size() == 0
    
    def test_size(self):
        """Test size returns correct count"""
        cache = CacheLayer()
        
        assert cache.size() == 0
        
        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.size() == 1
        
        cache.set("key2", "value2", ttl_seconds=60)
        assert cache.size() == 2
        
        cache.invalidate("key1")
        assert cache.size() == 1
    
    def test_cleanup_expired(self):
        """Test cleanup_expired removes only expired entries"""
        cache = CacheLayer()
        
        # Add entries with different TTLs
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=60)
        
        # Wait for key1 to expire
        time.sleep(1.1)
        
        # Cleanup
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_get_stats(self):
        """Test get_stats returns correct statistics"""
        cache = CacheLayer(max_size=10)
        
        stats = cache.get_stats()
        assert stats['size'] == 0
        assert stats['max_size'] == 10
        assert stats['utilization'] == 0
        
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        
        stats = cache.get_stats()
        assert stats['size'] == 2
        assert stats['utilization'] == 20.0
    
    def test_thread_safety(self):
        """Test thread-safe concurrent access"""
        cache = CacheLayer()
        results = []
        
        def writer(key, value):
            cache.set(key, value, ttl_seconds=60)
        
        def reader(key):
            value = cache.get(key)
            results.append(value)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            t1 = threading.Thread(target=writer, args=(f"key{i}", f"value{i}"))
            t2 = threading.Thread(target=reader, args=(f"key{i}",))
            threads.extend([t1, t2])
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify no crashes occurred
        assert cache.size() <= 10
    
    def test_cache_different_types(self):
        """Test caching different data types"""
        cache = CacheLayer()
        
        # String
        cache.set("str", "text", ttl_seconds=60)
        assert cache.get("str") == "text"
        
        # Integer
        cache.set("int", 42, ttl_seconds=60)
        assert cache.get("int") == 42
        
        # List
        cache.set("list", [1, 2, 3], ttl_seconds=60)
        assert cache.get("list") == [1, 2, 3]
        
        # Dict
        cache.set("dict", {"key": "value"}, ttl_seconds=60)
        assert cache.get("dict") == {"key": "value"}


# Property-Based Tests
class TestCacheLayerProperties:
    """Property-based tests for Cache Layer"""
    
    @settings(deadline=None)
    @given(
        key=st.text(min_size=1, max_size=50),
        value=st.text(min_size=0, max_size=100),
        ttl=st.integers(min_value=1, max_value=3600)
    )
    def test_property_cache_roundtrip(self, key, value, ttl):
        """
        Property 30: Weather Data Caching
        
        GIVEN any key, value, and TTL
        WHEN data is cached
        THEN it can be retrieved before expiration
        
        Validates: Requirement 19.3
        """
        cache = CacheLayer()
        
        cache.set(key, value, ttl_seconds=ttl)
        retrieved = cache.get(key)
        
        assert retrieved == value
    
    @settings(deadline=None)
    @given(
        key=st.text(min_size=1, max_size=50),
        value=st.text(min_size=0, max_size=100)
    )
    def test_property_ttl_expiration(self, key, value):
        """
        Property 31: Historical Price Data Caching
        
        GIVEN cached data with short TTL
        WHEN TTL expires
        THEN data is no longer retrievable
        
        Validates: Requirement 19.4
        """
        cache = CacheLayer()
        
        # Set with 1 second TTL
        cache.set(key, value, ttl_seconds=1)
        
        # Should exist immediately
        assert cache.get(key) == value
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get(key) is None
    
    @settings(deadline=None, max_examples=50)
    @given(
        num_items=st.integers(min_value=5, max_value=20)
    )
    def test_property_lru_eviction(self, num_items):
        """
        Property: LRU Eviction
        
        GIVEN a cache with limited size
        WHEN more items are added than max_size
        THEN least recently used items are evicted
        
        Validates: Requirement 19.4
        """
        max_size = 10
        cache = CacheLayer(max_size=max_size)
        
        # Add more items than max_size
        for i in range(num_items):
            cache.set(f"key{i}", f"value{i}", ttl_seconds=60)
        
        # Cache size should not exceed max_size
        assert cache.size() <= max_size
        
        # Most recent items should still be in cache
        if num_items > max_size:
            # Oldest items should be evicted
            assert cache.get("key0") is None
            # Newest items should exist
            assert cache.get(f"key{num_items-1}") == f"value{num_items-1}"
