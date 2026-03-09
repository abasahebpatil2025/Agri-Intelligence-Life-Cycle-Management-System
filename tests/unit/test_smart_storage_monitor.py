"""Unit tests for Smart Storage Monitor Component"""

import pytest
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'components'))
from smart_storage_monitor import SmartStorageMonitor


class TestSmartStorageMonitor:
    """Test suite for SmartStorageMonitor component"""
    
    def test_initialization(self):
        """Test monitor initialization"""
        monitor = SmartStorageMonitor(Mock(), Mock(), Mock(), Mock())
        assert monitor is not None
    
    def test_calculate_health_status_safe(self):
        """Test health status calculation for safe conditions"""
        monitor = SmartStorageMonitor(Mock(), Mock(), Mock(), Mock())
        status = monitor.calculate_health_status(20.0, 50.0)
        assert status == 'Safe'
