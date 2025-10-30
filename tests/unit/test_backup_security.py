"""
Unit tests for backup_security module.
Tests PRJ-SEC-002, PRJ-SEC-005, INV-NF-004.
"""

import pytest
import tempfile
import os
import shutil
from src.backup_security import BackupManager, SecurityManager
from src.storage import StorageManager
from src.logger import LogManager
from cryptography.fernet import Fernet


class TestBackupManager:
    """Test backup manager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def temp_db(self, temp_dir):
        """Create temporary database for testing."""
        db_path = os.path.join(temp_dir, 'test.db')
        storage = StorageManager(db_path)
        # Add some data
        storage.add_product("TEST001", "Product", 10.00, "Cat", 50)
        return db_path

    @pytest.fixture
    def backup_manager(self, temp_dir, temp_db):
        """Create backup manager with temporary paths."""
        backup_dir = os.path.join(temp_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        storage = StorageManager(temp_db)
        logger = LogManager(storage)
        bm = BackupManager(logger)
        
        # Override paths for testing
        bm.backup_dir = backup_dir
        bm.db_path = temp_db
        
        return bm

    def test_create_backup_success(self, backup_manager):
        """Test creating backup successfully (INV-NF-004, PRJ-SEC-002)."""
        backup_path = backup_manager.create_backup("admin")
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.enc')

    def test_backup_file_encrypted(self, backup_manager):
        """Test that backup file is encrypted (PRJ-SEC-002)."""
        backup_path = backup_manager.create_backup("admin")
        
        # Read backup file
        with open(backup_path, 'rb') as f:
            content = f.read()
        
        # Should not be readable as plain SQLite (encrypted)
        assert not content.startswith(b'SQLite')

    def test_list_backups(self, backup_manager):
        """Test listing backups."""
        # Create multiple backups
        backup_manager.create_backup("admin")
        backup_manager.create_backup("admin")
        
        backups = backup_manager.list_backups()
        
        assert len(backups) >= 2
        assert all(b.endswith('.enc') for b in backups)

    def test_restore_backup_success(self, backup_manager, temp_db):
        """Test restoring from backup successfully."""
        # Create backup
        backup_path = backup_manager.create_backup("admin")
        backup_filename = os.path.basename(backup_path)
        
        # Modify database
        storage = StorageManager(temp_db)
        storage.add_product("NEW001", "New Product", 20.00, "Cat", 100)
        
        # Restore backup
        success = backup_manager.restore_backup(backup_filename, "admin")
        
        assert success is True

    def test_restore_backup_nonexistent(self, backup_manager):
        """Test restoring from non-existent backup fails."""
        success = backup_manager.restore_backup("nonexistent.enc", "admin")
        
        assert success is False

    def test_delete_backup_success(self, backup_manager):
        """Test deleting backup successfully."""
        # Create backup
        backup_path = backup_manager.create_backup("admin")
        backup_filename = os.path.basename(backup_path)
        
        # Delete backup
        success = backup_manager.delete_backup(backup_filename, "admin")
        
        assert success is True
        assert not os.path.exists(backup_path)

    def test_delete_backup_nonexistent(self, backup_manager):
        """Test deleting non-existent backup fails."""
        success = backup_manager.delete_backup("nonexistent.enc", "admin")
        
        assert success is False


class TestSecurityManager:
    """Test security manager."""

    @pytest.fixture
    def security_manager(self):
        """Create security manager."""
        return SecurityManager()

    def test_encrypt_data(self, security_manager):
        """Test encrypting data (PRJ-SEC-002)."""
        original_data = b"This is sensitive data"
        
        encrypted = security_manager.encrypt_data(original_data)
        
        assert encrypted is not None
        assert encrypted != original_data
        assert isinstance(encrypted, bytes)

    def test_decrypt_data(self, security_manager):
        """Test decrypting data (PRJ-SEC-002)."""
        original_data = b"This is sensitive data"
        
        encrypted = security_manager.encrypt_data(original_data)
        decrypted = security_manager.decrypt_data(encrypted)
        
        assert decrypted == original_data

    def test_encryption_consistency(self, security_manager):
        """Test that encryption/decryption is consistent."""
        test_data = b"Test data for encryption"
        
        # Encrypt and decrypt multiple times
        for _ in range(5):
            encrypted = security_manager.encrypt_data(test_data)
            decrypted = security_manager.decrypt_data(encrypted)
            assert decrypted == test_data

    def test_verify_backup_integrity_valid(self, security_manager, temp_dir):
        """Test verifying valid backup integrity."""
        # Create encrypted backup file
        test_data = b"Backup data"
        encrypted = security_manager.encrypt_data(test_data)
        
        backup_path = os.path.join(temp_dir, 'test_backup.enc')
        with open(backup_path, 'wb') as f:
            f.write(encrypted)
        
        # Verify integrity
        is_valid = security_manager.verify_backup_integrity(backup_path)
        
        assert is_valid is True
        
        # Cleanup
        os.unlink(backup_path)

    def test_verify_backup_integrity_invalid(self, security_manager, temp_dir):
        """Test verifying corrupted backup fails."""
        # Create invalid backup file
        backup_path = os.path.join(temp_dir, 'corrupted_backup.enc')
        with open(backup_path, 'wb') as f:
            f.write(b"This is not encrypted data")
        
        # Verify integrity should fail
        is_valid = security_manager.verify_backup_integrity(backup_path)
        
        assert is_valid is False
        
        # Cleanup
        os.unlink(backup_path)


def temp_dir():
    """Fixture for temporary directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
