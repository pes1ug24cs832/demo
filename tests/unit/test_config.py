"""
Unit tests for config module.
"""

import os
import pytest
from src.config import ConfigManager, DB_PATH, BACKUP_PATH, LOW_STOCK_THRESHOLD


class TestConfig:
    """Test configuration module."""

    def test_config_paths_exist(self):
        """Test that config paths are defined."""
        assert DB_PATH is not None
        assert BACKUP_PATH is not None
        assert isinstance(DB_PATH, str)
        assert isinstance(BACKUP_PATH, str)

    def test_low_stock_threshold(self):
        """Test low stock threshold configuration."""
        assert LOW_STOCK_THRESHOLD == 5
        assert isinstance(LOW_STOCK_THRESHOLD, int)

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        config = ConfigManager()
        assert config.db_path == DB_PATH
        assert config.backup_path == BACKUP_PATH
        assert config.low_stock_threshold == LOW_STOCK_THRESHOLD

    def test_config_manager_get_config(self):
        """Test get_config method."""
        config = ConfigManager()
        assert config.get_config('db_path') == DB_PATH
        assert config.get_config('backup_path') == BACKUP_PATH
        assert config.get_config('low_stock_threshold') == LOW_STOCK_THRESHOLD
        assert config.get_config('invalid_key') is None

    def test_encryption_key_exists(self):
        """Test that encryption key is generated."""
        from src.config import ENCRYPTION_KEY
        assert ENCRYPTION_KEY is not None
        assert isinstance(ENCRYPTION_KEY, bytes)
        assert len(ENCRYPTION_KEY) > 0
