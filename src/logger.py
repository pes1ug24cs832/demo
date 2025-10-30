"""
Logger Module
Handles application logging and audit trails.
Implements PRJ-SEC-003 (Log admin actions with timestamp, action, details, user).
"""

from datetime import datetime
from typing import List, Dict
from .storage import StorageManager


class LogManager:
    """Manages logging operations."""

    def __init__(self, storage: StorageManager = None):
        """
        Initialize log manager.
        
        Args:
            storage: StorageManager instance (optional, creates new if not provided)
        """
        self.storage = storage or StorageManager()

    def log_action(self, user: str, action: str, details: str = ""):
        """
        Log an action to the database (PRJ-SEC-003).
        
        Args:
            user: Username performing the action
            action: Action being performed (e.g., "DELETE_PRODUCT", "CREATE_BACKUP")
            details: Additional details about the action
        """
        self.storage.add_log(user, action, details)

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get recent log entries.
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log dictionaries with id, user, timestamp, action, details
        """
        return self.storage.get_logs(limit)

    def get_logs_by_user(self, username: str, limit: int = 100) -> List[Dict]:
        """
        Get logs for a specific user.
        
        Args:
            username: Username to filter logs
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log dictionaries for the specified user
        """
        all_logs = self.get_recent_logs(limit * 2)  # Get more to ensure enough after filtering
        user_logs = [log for log in all_logs if log['user'] == username]
        return user_logs[:limit]

    def get_logs_by_action(self, action: str, limit: int = 100) -> List[Dict]:
        """
        Get logs for a specific action type.
        
        Args:
            action: Action type to filter (e.g., "DELETE_PRODUCT")
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log dictionaries for the specified action
        """
        all_logs = self.get_recent_logs(limit * 2)
        action_logs = [log for log in all_logs if action.lower() in log['action'].lower()]
        return action_logs[:limit]

    def format_log_entry(self, log: Dict) -> str:
        """
        Format a log entry for display.
        
        Args:
            log: Log dictionary
            
        Returns:
            Formatted string representation of log
        """
        timestamp = log.get('timestamp', 'N/A')
        user = log.get('user', 'N/A')
        action = log.get('action', 'N/A')
        details = log.get('details', '')
        
        if details:
            return f"[{timestamp}] {user}: {action} - {details}"
        else:
            return f"[{timestamp}] {user}: {action}"

    def display_logs(self, logs: List[Dict]):
        """
        Display logs in a formatted manner.
        
        Args:
            logs: List of log dictionaries to display
        """
        if not logs:
            print("No logs found.")
            return
        
        print("\n" + "="*80)
        print(f"{'Timestamp':<25} {'User':<15} {'Action':<20} {'Details':<20}")
        print("="*80)
        
        for log in logs:
            timestamp = log.get('timestamp', 'N/A')[:19]  # Truncate milliseconds
            user = log.get('user', 'N/A')[:14]
            action = log.get('action', 'N/A')[:19]
            details = log.get('details', '')[:19]
            
            print(f"{timestamp:<25} {user:<15} {action:<20} {details:<20}")
        
        print("="*80 + "\n")
