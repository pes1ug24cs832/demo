"""
Unit tests for logger module.
Tests PRJ-SEC-003 (logging admin actions).
"""

import pytest
import tempfile
import os
from src.logger import LogManager
from src.storage import StorageManager


class TestLogManager:
    """Test log manager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def log_manager(self, temp_db):
        """Create log manager with temporary database."""
        storage = StorageManager(temp_db)
        return LogManager(storage)

    def test_log_action_success(self, log_manager):
        """Test logging action successfully (PRJ-SEC-003)."""
        log_manager.log_action("admin", "TEST_ACTION", "Test details")
        
        # Verify log was created
        logs = log_manager.get_recent_logs(10)
        
        assert len(logs) >= 1
        assert logs[0]['user'] == "admin"
        assert logs[0]['action'] == "TEST_ACTION"
        assert logs[0]['details'] == "Test details"

    def test_log_action_with_timestamp(self, log_manager):
        """Test that log entries include timestamp."""
        log_manager.log_action("admin", "TEST_ACTION", "Test details")
        
        logs = log_manager.get_recent_logs(1)
        
        assert 'timestamp' in logs[0]
        assert logs[0]['timestamp'] is not None

    def test_get_recent_logs(self, log_manager):
        """Test getting recent logs."""
        # Create multiple log entries
        for i in range(5):
            log_manager.log_action(f"user{i}", f"ACTION_{i}", f"Details {i}")
        
        logs = log_manager.get_recent_logs(3)
        
        assert len(logs) == 3

    def test_get_recent_logs_limit(self, log_manager):
        """Test that limit parameter works correctly."""
        # Create 10 logs
        for i in range(10):
            log_manager.log_action("user", f"ACTION_{i}", f"Details {i}")
        
        # Get only 5
        logs = log_manager.get_recent_logs(5)
        
        assert len(logs) == 5

    def test_get_logs_by_user(self, log_manager):
        """Test filtering logs by user."""
        log_manager.log_action("admin", "ADMIN_ACTION", "Admin details")
        log_manager.log_action("user1", "USER_ACTION", "User details")
        log_manager.log_action("admin", "ANOTHER_ADMIN_ACTION", "More admin details")
        
        admin_logs = log_manager.get_logs_by_user("admin")
        
        assert len(admin_logs) >= 2
        assert all(log['user'] == "admin" for log in admin_logs)

    def test_get_logs_by_action(self, log_manager):
        """Test filtering logs by action type."""
        log_manager.log_action("admin", "DELETE_PRODUCT", "Deleted product 1")
        log_manager.log_action("admin", "ADD_PRODUCT", "Added product 2")
        log_manager.log_action("admin", "DELETE_PRODUCT", "Deleted product 3")
        
        delete_logs = log_manager.get_logs_by_action("DELETE_PRODUCT")
        
        assert len(delete_logs) >= 2
        assert all("delete" in log['action'].lower() for log in delete_logs)

    def test_format_log_entry_with_details(self, log_manager):
        """Test formatting log entry with details."""
        log_entry = {
            'timestamp': '2025-01-01 12:00:00',
            'user': 'admin',
            'action': 'DELETE_PRODUCT',
            'details': 'Deleted product ID 123'
        }
        
        formatted = log_manager.format_log_entry(log_entry)
        
        assert '2025-01-01 12:00:00' in formatted
        assert 'admin' in formatted
        assert 'DELETE_PRODUCT' in formatted
        assert 'Deleted product ID 123' in formatted

    def test_format_log_entry_without_details(self, log_manager):
        """Test formatting log entry without details."""
        log_entry = {
            'timestamp': '2025-01-01 12:00:00',
            'user': 'admin',
            'action': 'LOGIN',
            'details': ''
        }
        
        formatted = log_manager.format_log_entry(log_entry)
        
        assert '2025-01-01 12:00:00' in formatted
        assert 'admin' in formatted
        assert 'LOGIN' in formatted

    def test_log_ordering(self, log_manager):
        """Test that logs are returned in reverse chronological order."""
        import time
        
        log_manager.log_action("user", "ACTION_1", "First")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        log_manager.log_action("user", "ACTION_2", "Second")
        time.sleep(0.01)
        log_manager.log_action("user", "ACTION_3", "Third")
        
        logs = log_manager.get_recent_logs(10)
        
        # Most recent should be first
        assert logs[0]['action'] == "ACTION_3"
        assert logs[1]['action'] == "ACTION_2"
        assert logs[2]['action'] == "ACTION_1"

    def test_log_multiple_users(self, log_manager):
        """Test logging actions from multiple users."""
        log_manager.log_action("admin", "ADMIN_ACTION", "Admin activity")
        log_manager.log_action("user1", "USER_ACTION", "User 1 activity")
        log_manager.log_action("user2", "USER_ACTION", "User 2 activity")
        
        logs = log_manager.get_recent_logs(10)
        
        users = set(log['user'] for log in logs)
        assert 'admin' in users
        assert 'user1' in users
        assert 'user2' in users
