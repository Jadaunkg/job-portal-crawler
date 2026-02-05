"""
JSON Database Handler

Thread-safe JSON file-based database for storing crawler data.
Implements CRUD operations with automatic backups and data integrity checks.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from filelock import FileLock
import shutil


class JSONDatabase:
    """
    Thread-safe JSON file database handler
    
    Features:
    - Thread-safe read/write operations using file locks
    - Automatic backups
    - Data validation
    - Support for multiple data categories
    """
    
    def __init__(self, data_dir: str = "data", backup_enabled: bool = True, 
                 max_backups: int = 10, backup_frequency: int = 5):
        """
        Initialize JSON database
        
        Args:
            data_dir: Directory to store data files
            backup_enabled: Enable automatic backups
            max_backups: Maximum number of backup files to keep
            backup_frequency: Backup every N writes (0 = every write)
        """
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "backups"
        self.backup_enabled = backup_enabled
        self.max_backups = max_backups
        self.backup_frequency = backup_frequency
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if backup_enabled:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Track write counts for backup frequency
        self._write_counts: Dict[str, int] = {}
        
        # File paths for different data categories
        self.files = {
            'jobs': self.data_dir / 'jobs.json',
            'results': self.data_dir / 'results.json',
            'admit_cards': self.data_dir / 'admit_cards.json',
            'notifications': self.data_dir / 'notifications.json',
            'crawl_history': self.data_dir / 'crawl_history.json'
        }
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self) -> None:
        """Initialize JSON files with empty arrays if they don't exist"""
        for category, file_path in self.files.items():
            if not file_path.exists():
                self._write_file(file_path, [])
                self._write_counts[category] = 0
    
    def _get_lock_path(self, file_path: Path) -> Path:
        """Get lock file path for a data file"""
        return file_path.parent / f"{file_path.name}.lock"
    
    def _read_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Read JSON file with file locking
        
        Args:
            file_path: Path to JSON file
        
        Returns:
            List of entries from the file
        """
        lock_path = self._get_lock_path(file_path)
        lock = FileLock(str(lock_path), timeout=10)
        
        try:
            with lock:
                if not file_path.exists():
                    return []
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            return []
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
    
    def _write_file(self, file_path: Path, data: List[Dict[str, Any]]) -> bool:
        """
        Write data to JSON file with file locking
        
        Args:
            file_path: Path to JSON file
            data: List of entries to write
        
        Returns:
            bool: True if successful, False otherwise
        """
        lock_path = self._get_lock_path(file_path)
        lock = FileLock(str(lock_path), timeout=10)
        
        try:
            with lock:
                # Write to temporary file first
                temp_path = file_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Atomically replace original file
                temp_path.replace(file_path)
                return True
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")
            return False
    
    def _create_backup(self, category: str) -> None:
        """
        Create a backup of the data file
        
        Args:
            category: Data category (jobs, results, etc.)
        """
        if not self.backup_enabled:
            return
        
        file_path = self.files[category]
        if not file_path.exists():
            return
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{category}_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(file_path, backup_path)
            self._cleanup_old_backups(category)
        except Exception as e:
            print(f"Error creating backup for {category}: {e}")
    
    def _cleanup_old_backups(self, category: str) -> None:
        """
        Remove old backup files keeping only max_backups most recent
        
        Args:
            category: Data category
        """
        pattern = f"{category}_backup_*.json"
        backups = sorted(self.backup_dir.glob(pattern))
        
        # Remove oldest backups if exceeding max_backups
        if len(backups) > self.max_backups:
            for backup in backups[:-self.max_backups]:
                try:
                    backup.unlink()
                except Exception as e:
                    print(f"Error deleting old backup {backup}: {e}")
    
    def insert(self, category: str, entry: Dict[str, Any]) -> bool:
        """
        Insert a new entry into the database
        
        Args:
            category: Data category (jobs, results, etc.)
            entry: Entry data as dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        file_path = self.files[category]
        data = self._read_file(file_path)
        
        # Add entry at the beginning (newest first)
        data.insert(0, entry)
        
        # Write back to file
        success = self._write_file(file_path, data)
        
        if success:
            # Handle backups
            self._write_counts[category] = self._write_counts.get(category, 0) + 1
            if (self.backup_frequency == 0 or 
                self._write_counts[category] % self.backup_frequency == 0):
                self._create_backup(category)
        
        return success
    
    def insert_many(self, category: str, entries: List[Dict[str, Any]]) -> bool:
        """
        Insert multiple entries into the database
        
        Args:
            category: Data category
            entries: List of entry dictionaries
        
        Returns:
            bool: True if successful, False otherwise
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        if not entries:
            return True
        
        file_path = self.files[category]
        data = self._read_file(file_path)
        
        # Add new entries at the beginning (in the order received)
        data = entries + data
        
        # Write back to file
        success = self._write_file(file_path, data)
        
        if success:
            self._write_counts[category] = self._write_counts.get(category, 0) + len(entries)
            if (self.backup_frequency == 0 or 
                self._write_counts[category] % self.backup_frequency == 0):
                self._create_backup(category)
        
        return success
    
    def get_all(self, category: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all entries from a category
        
        Args:
            category: Data category
            limit: Maximum number of entries to return (None = all)
        
        Returns:
            List of entries
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        data = self._read_file(self.files[category])
        
        if limit:
            return data[:limit]
        return data
    
    def get_by_id(self, category: str, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific entry by ID
        
        Args:
            category: Data category
            entry_id: Entry ID to search for
        
        Returns:
            Entry dictionary if found, None otherwise
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        data = self._read_file(self.files[category])
        
        for entry in data:
            if entry.get('id') == entry_id:
                return entry
        
        return None
    
    def exists(self, category: str, entry_id: str) -> bool:
        """
        Check if an entry exists
        
        Args:
            category: Data category
            entry_id: Entry ID to check
        
        Returns:
            bool: True if exists, False otherwise
        """
        return self.get_by_id(category, entry_id) is not None
    
    def update(self, category: str, entry_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update an existing entry
        
        Args:
            category: Data category
            entry_id: Entry ID to update
            updated_data: New data for the entry
        
        Returns:
            bool: True if successful, False otherwise
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        file_path = self.files[category]
        data = self._read_file(file_path)
        
        # Find and update entry
        updated = False
        for i, entry in enumerate(data):
            if entry.get('id') == entry_id:
                data[i] = updated_data
                updated = True
                break
        
        if not updated:
            return False
        
        return self._write_file(file_path, data)
    
    def delete(self, category: str, entry_id: str) -> bool:
        """
        Delete an entry
        
        Args:
            category: Data category
            entry_id: Entry ID to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        file_path = self.files[category]
        data = self._read_file(file_path)
        
        # Filter out entry to delete
        original_len = len(data)
        data = [entry for entry in data if entry.get('id') != entry_id]
        
        if len(data) == original_len:
            return False  # Entry not found
        
        return self._write_file(file_path, data)
    
    def count(self, category: str) -> int:
        """
        Get count of entries in a category
        
        Args:
            category: Data category
        
        Returns:
            Number of entries
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        return len(self._read_file(self.files[category]))
    
    def search(self, category: str, field: str, value: Any) -> List[Dict[str, Any]]:
        """
        Search for entries matching a field value
        
        Args:
            category: Data category
            field: Field name to search
            value: Value to match
        
        Returns:
            List of matching entries
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        data = self._read_file(self.files[category])
        return [entry for entry in data if entry.get(field) == value]
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics for all categories
        
        Returns:
            Dictionary with counts for each category
        """
        stats = {}
        for category in self.files.keys():
            stats[category] = self.count(category)
        return stats
    
    def clear_category(self, category: str) -> bool:
        """
        Clear all entries from a category
        
        Args:
            category: Data category to clear
        
        Returns:
            bool: True if successful
        """
        if category not in self.files:
            raise ValueError(f"Invalid category: {category}")
        
        # Create backup before clearing
        if self.backup_enabled:
            self._create_backup(category)
        
        return self._write_file(self.files[category], [])
