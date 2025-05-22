"""Persistent storage for PR review state.

This module provides file-based storage for tracking PR review state
using JSON format for simplicity and human readability.
"""

import json
import os
import threading
from typing import Dict, List, Optional
from dataclasses import asdict
from datetime import datetime, timezone


class PRStateStore:
    """File-based storage for PR review state."""
    
    def __init__(self, storage_path: str):
        """Initialize the PR state store.
        
        Args:
            storage_path: Path to the JSON file for storing state
        """
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists."""
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
    
    def _load_data(self) -> Dict[str, dict]:
        """Load data from storage file.
        
        Returns:
            Dictionary mapping PR numbers (as strings) to review records
        """
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Log error but continue with empty data
            print(f"Warning: Could not load PR state from {self.storage_path}: {e}")
        
        return {}
    
    def _save_data(self, data: Dict[str, dict]) -> None:
        """Save data to storage file.
        
        Args:
            data: Dictionary mapping PR numbers to review records
        """
        try:
            # Create a backup first
            backup_path = self.storage_path + '.backup'
            if os.path.exists(self.storage_path):
                os.rename(self.storage_path, backup_path)
            
            # Write new data
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            
            # Remove backup on success
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except IOError as e:
            # Restore backup if write failed
            if os.path.exists(backup_path):
                os.rename(backup_path, self.storage_path)
            raise IOError(f"Failed to save PR state to {self.storage_path}: {e}")
    
    def get_review_record(self, pr_number: int):
        """Get the review record for a specific PR.
        
        Args:
            pr_number: GitHub PR number
            
        Returns:
            PRReviewRecord if found, None otherwise
        """
        with self._lock:
            data = self._load_data()
            record_data = data.get(str(pr_number))
            
            if record_data is None:
                return None
            
            # Import here to avoid circular import
            from ..models.pr_review_state import PRReviewRecord
            
            try:
                return PRReviewRecord(**record_data)
            except TypeError as e:
                print(f"Warning: Invalid record format for PR {pr_number}: {e}")
                return None
    
    def save_review_record(self, record) -> None:
        """Save a review record.
        
        Args:
            record: PRReviewRecord instance to save
        """
        with self._lock:
            data = self._load_data()
            data[str(record.pr_number)] = asdict(record)
            self._save_data(data)
    
    def get_all_records(self) -> List:
        """Get all review records.
        
        Returns:
            List of all PRReviewRecord instances
        """
        with self._lock:
            data = self._load_data()
            
            # Import here to avoid circular import
            from ..models.pr_review_state import PRReviewRecord
            
            records = []
            for pr_number, record_data in data.items():
                try:
                    record = PRReviewRecord(**record_data)
                    records.append(record)
                except TypeError as e:
                    print(f"Warning: Invalid record format for PR {pr_number}: {e}")
                    continue
            
            return records
    
    def cleanup_closed_prs(self, open_pr_numbers: List[int]) -> int:
        """Remove records for PRs that are no longer open.
        
        Args:
            open_pr_numbers: List of currently open PR numbers
            
        Returns:
            Number of records removed
        """
        open_pr_set = set(str(n) for n in open_pr_numbers)
        
        with self._lock:
            data = self._load_data()
            original_count = len(data)
            
            # Keep only records for open PRs
            data = {pr_num: record for pr_num, record in data.items() 
                   if pr_num in open_pr_set}
            
            self._save_data(data)
            removed_count = original_count - len(data)
            
            if removed_count > 0:
                print(f"Cleaned up {removed_count} closed PR records")
            
            return removed_count
    
    def clear_all_records(self) -> None:
        """Clear all review records."""
        with self._lock:
            self._save_data({})
    
    def delete_record(self, pr_number: int) -> bool:
        """Delete a specific review record.
        
        Args:
            pr_number: GitHub PR number
            
        Returns:
            True if record was deleted, False if not found
        """
        with self._lock:
            data = self._load_data()
            pr_key = str(pr_number)
            
            if pr_key in data:
                del data[pr_key]
                self._save_data(data)
                return True
            
            return False
    
    def backup_state(self, backup_path: str) -> None:
        """Create a backup of the current state.
        
        Args:
            backup_path: Path for the backup file
        """
        with self._lock:
            data = self._load_data()
            
            backup_dir = os.path.dirname(backup_path)
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
            
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
    
    def restore_state(self, backup_path: str) -> None:
        """Restore state from a backup file.
        
        Args:
            backup_path: Path to the backup file
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        with self._lock:
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            self._save_data(data)
    
    def get_storage_info(self) -> Dict[str, any]:
        """Get information about the storage file.
        
        Returns:
            Dictionary with storage file information
        """
        info = {
            'storage_path': self.storage_path,
            'exists': os.path.exists(self.storage_path),
            'size_bytes': 0,
            'last_modified': None,
            'record_count': 0
        }
        
        if info['exists']:
            try:
                stat = os.stat(self.storage_path)
                info['size_bytes'] = stat.st_size
                info['last_modified'] = datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat()
                
                with self._lock:
                    data = self._load_data()
                    info['record_count'] = len(data)
                    
            except (OSError, IOError) as e:
                print(f"Warning: Could not get storage info: {e}")
        
        return info