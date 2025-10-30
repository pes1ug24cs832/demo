"""
Backup and Security Module
Handles data backup and security operations.
Implements PRJ-SEC-002 (Backup encryption with AES Fernet).
Implements PRJ-SEC-005 (Protect backup integrity).
Implements INV-NF-004 (Daily backup creation).
"""

import os
import shutil
from datetime import datetime
from cryptography.fernet import Fernet
from typing import Optional
from .config import DB_PATH, BACKUP_PATH, ENCRYPTION_KEY
from .logger import LogManager


class BackupManager:
    """Manages backup operations."""

    def __init__(self, logger: LogManager = None):
        """
        Initialize backup manager.
        
        Args:
            logger: LogManager instance (optional)
        """
        self.logger = logger or LogManager()
        self.backup_dir = BACKUP_PATH
        self.db_path = DB_PATH
        self.encryption_key = ENCRYPTION_KEY
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Set restrictive permissions on backup directory (PRJ-SEC-005)
        try:
            os.chmod(self.backup_dir, 0o700)  # Read/write/execute for owner only
        except Exception:
            pass  # Windows may not support chmod

    def create_backup(self, user: str = "system") -> Optional[str]:
        """
        Create encrypted database backup (INV-NF-004, PRJ-SEC-002).
        
        Args:
            user: Username performing the backup
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            # Check if database exists
            if not os.path.exists(self.db_path):
                print(f"Error: Database not found at {self.db_path}")
                return None
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.enc"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Read database file
            with open(self.db_path, 'rb') as f:
                db_data = f.read()
            
            # Encrypt data (PRJ-SEC-002)
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(db_data)
            
            # Write encrypted backup
            with open(backup_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions on backup file (PRJ-SEC-005)
            try:
                os.chmod(backup_path, 0o400)  # Read-only for owner
            except Exception:
                pass  # Windows may not support chmod
            
            # Log action (PRJ-SEC-003)
            self.logger.log_action(
                user,
                "CREATE_BACKUP",
                f"Created encrypted backup: {backup_filename}"
            )
            
            print(f"✓ Backup created successfully: {backup_filename}")
            return backup_path
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return None

    def restore_backup(self, backup_filename: str, user: str = "system") -> bool:
        """
        Restore database from encrypted backup.
        
        Args:
            backup_filename: Name of backup file to restore
            user: Username performing the restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Check if backup file exists
            if not os.path.exists(backup_path):
                print(f"Error: Backup file not found: {backup_filename}")
                return False
            
            # Read encrypted backup
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data (PRJ-SEC-002)
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Create backup of current database before restoring
            current_backup = os.path.join(self.backup_dir, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, current_backup)
            
            # Write restored database
            with open(self.db_path, 'wb') as f:
                f.write(decrypted_data)
            
            # Log action (PRJ-SEC-003)
            self.logger.log_action(
                user,
                "RESTORE_BACKUP",
                f"Restored database from backup: {backup_filename}"
            )
            
            print(f"✓ Database restored successfully from: {backup_filename}")
            print(f"  Previous database backed up to: {os.path.basename(current_backup)}")
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {str(e)}")
            return False

    def list_backups(self) -> list:
        """
        List all available backup files.
        
        Returns:
            List of backup filenames sorted by date (newest first)
        """
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.endswith('.enc')]
            backups.sort(reverse=True)  # Newest first
            return backups
        except Exception:
            return []

    def display_backups(self):
        """Display available backups in a formatted list."""
        backups = self.list_backups()
        
        if not backups:
            print("\nNo backups found.")
            return
        
        print("\n" + "="*80)
        print("Available Backups:")
        print("="*80)
        
        for i, backup in enumerate(backups, 1):
            # Extract timestamp from filename
            try:
                timestamp_str = backup.replace('backup_', '').replace('.enc', '')
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                formatted_date = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Get file size
                backup_path = os.path.join(self.backup_dir, backup)
                size_bytes = os.path.getsize(backup_path)
                size_kb = size_bytes / 1024
                
                print(f"{i:3}. {backup:<40} | {formatted_date} | {size_kb:.2f} KB")
            except Exception:
                print(f"{i:3}. {backup}")
        
        print("="*80 + "\n")

    def delete_backup(self, backup_filename: str, user: str = "system") -> bool:
        """
        Delete a backup file (admin only).
        
        Args:
            backup_filename: Name of backup file to delete
            user: Username performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                print(f"Error: Backup file not found: {backup_filename}")
                return False
            
            # Delete file
            os.remove(backup_path)
            
            # Log action (PRJ-SEC-003)
            self.logger.log_action(
                user,
                "DELETE_BACKUP",
                f"Deleted backup: {backup_filename}"
            )
            
            print(f"✓ Backup deleted: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Error deleting backup: {str(e)}")
            return False


class SecurityManager:
    """Manages security operations."""

    def __init__(self):
        """Initialize security manager."""
        self.encryption_key = ENCRYPTION_KEY

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data using Fernet (AES).
        
        Args:
            data: Raw bytes to encrypt
            
        Returns:
            Encrypted bytes
        """
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data using Fernet (AES).
        
        Args:
            encrypted_data: Encrypted bytes
            
        Returns:
            Decrypted bytes
        """
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_data)

    def verify_backup_integrity(self, backup_path: str) -> bool:
        """
        Verify backup file can be decrypted (integrity check).
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid and can be decrypted, False otherwise
        """
        try:
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()
            
            fernet = Fernet(self.encryption_key)
            fernet.decrypt(encrypted_data)
            return True
        except Exception:
            return False
