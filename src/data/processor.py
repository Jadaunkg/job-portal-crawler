"""
Data Processor

Handles data processing, validation, deduplication, and normalization
before storing entries in the database.
"""

from typing import List, Dict, Any, Set
from datetime import datetime
import sys
from pathlib import Path

# Add src directory to path if needed
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from .models import (
        JobEntry,
        ResultEntry,
        AdmitCardEntry,
        NotificationEntry,
        CrawlHistory,
        generate_entry_id
    )
    from .database import JSONDatabase
except ImportError:
    try:
        from data.models import (
            JobEntry,
            ResultEntry,
            AdmitCardEntry,
            NotificationEntry,
            CrawlHistory,
            generate_entry_id
        )
        from data.database import JSONDatabase
    except ImportError:
        from models import (
            JobEntry,
            ResultEntry,
            AdmitCardEntry,
            NotificationEntry,
            CrawlHistory,
            generate_entry_id
        )
        from database import JSONDatabase

try:
    from utils.logger import get_logger
except ImportError:
    try:
        from .utils.logger import get_logger
    except ImportError:
        from ..utils import get_logger


class DataProcessor:
    """
    Process, validate, and deduplicate crawler data
    """
    
    def __init__(self, database: JSONDatabase):
        """
        Initialize data processor
        
        Args:
            database: JSONDatabase instance
        """
        self.db = database
        self.logger = get_logger("processor")
        
        # Cache of existing IDs for faster lookups
        self._id_cache: Dict[str, Set[str]] = {}
        self._load_id_cache()
    
    def _load_id_cache(self) -> None:
        """Load existing entry IDs into cache"""
        categories = ['jobs', 'results', 'admit_cards', 'notifications']
        
        for category in categories:
            self._id_cache[category] = set()
            entries = self.db.get_all(category)
            for entry in entries:
                entry_id = entry.get('id')
                if entry_id:
                    self._id_cache[category].add(entry_id)
        
        self.logger.debug(f"Loaded ID cache: {sum(len(ids) for ids in self._id_cache.values())} total IDs")
    
    def process_jobs(self, jobs: List[JobEntry]) -> Dict[str, Any]:
        """
        Process and store job entries
        
        Args:
            jobs: List of JobEntry objects
        
        Returns:
            Dictionary with processing statistics
        """
        if not jobs:
            return {'total': 0, 'new': 0, 'duplicates': 0, 'updated': 0}
        
        self.logger.info(f"Processing {len(jobs)} job entries")
        
        new_jobs = []
        duplicate_count = 0
        updated_count = 0
        
        # Get existing jobs from database for duplicate checking
        existing_jobs = self.db.get_all('jobs')
        existing_by_id = {job.get('id'): job for job in existing_jobs}
        
        for job in jobs:
            # Validate
            if not self._validate_job(job):
                continue
            
            job_dict = job.to_dict()
            
            # Check for duplicates
            if job.id in existing_by_id:
                # It's a duplicate - mark it with metadata
                old_job = existing_by_id[job.id]
                job_dict['is_new'] = False
                job_dict['is_duplicate'] = True
                job_dict['previous_discovered_at'] = old_job.get('discovered_at', '')
                job_dict['times_seen'] = old_job.get('times_seen', 1) + 1
                
                # Remove from existing (will be re-added at top)
                existing_jobs = [j for j in existing_jobs if j.get('id') != job.id]
                
                duplicate_count += 1
                updated_count += 1
                self.logger.debug(f"Duplicate job moved to top: {job.title}")
            else:
                # New job
                job_dict['is_new'] = True
                job_dict['is_duplicate'] = False
                job_dict['times_seen'] = 1
                self._id_cache['jobs'].add(job.id)
            
            new_jobs.append(job_dict)
        
        # Store in database: new jobs at top + remaining old jobs
        if new_jobs:
            all_jobs = new_jobs + existing_jobs
            self.db._write_file(self.db.files['jobs'], all_jobs)
            self.logger.info(f"Stored {len(new_jobs)} jobs ({len(new_jobs) - updated_count} new, {updated_count} updated)")
        
        return {
            'total': len(jobs),
            'new': len(new_jobs) - updated_count,
            'duplicates': duplicate_count,
            'updated': updated_count
        }
    
    def process_results(self, results: List[ResultEntry]) -> Dict[str, Any]:
        """
        Process and store result entries
        
        Args:
            results: List of ResultEntry objects
        
        Returns:
            Dictionary with processing statistics
        """
        if not results:
            return {'total': 0, 'new': 0, 'duplicates': 0, 'updated': 0}
        
        self.logger.info(f"Processing {len(results)} result entries")
        
        new_results = []
        duplicate_count = 0
        updated_count = 0
        
        # Get existing results from database
        existing_results = self.db.get_all('results')
        existing_by_id = {r.get('id'): r for r in existing_results}
        
        for result in results:
            # Validate
            if not self._validate_result(result):
                continue
            
            result_dict = result.to_dict()
            
            # Check for duplicates
            if result.id in existing_by_id:
                # It's a duplicate - mark with metadata
                old_result = existing_by_id[result.id]
                result_dict['is_new'] = False
                result_dict['is_duplicate'] = True
                result_dict['previous_discovered_at'] = old_result.get('discovered_at', '')
                result_dict['times_seen'] = old_result.get('times_seen', 1) + 1
                
                # Remove from existing (will be re-added at top)
                existing_results = [r for r in existing_results if r.get('id') != result.id]
                
                duplicate_count += 1
                updated_count += 1
            else:
                # New result
                result_dict['is_new'] = True
                result_dict['is_duplicate'] = False
                result_dict['times_seen'] = 1
                self._id_cache['results'].add(result.id)
            
            new_results.append(result_dict)
        
        # Store: new results at top + remaining old results
        if new_results:
            all_results = new_results + existing_results
            self.db._write_file(self.db.files['results'], all_results)
            self.logger.info(f"Stored {len(new_results)} results ({len(new_results) - updated_count} new, {updated_count} updated)")
        
        return {
            'total': len(results),
            'new': len(new_results) - updated_count,
            'duplicates': duplicate_count,
            'updated': updated_count
        }
    
    def process_admit_cards(self, admit_cards: List[AdmitCardEntry]) -> Dict[str, Any]:
        """
        Process and store admit card entries
        
        Args:
            admit_cards: List of AdmitCardEntry objects
        
        Returns:
            Dictionary with processing statistics
        """
        if not admit_cards:
            return {'total': 0, 'new': 0, 'duplicates': 0, 'updated': 0}
        
        self.logger.info(f"Processing {len(admit_cards)} admit card entries")
        
        new_cards = []
        duplicate_count = 0
        updated_count = 0
        
        # Get existing admit cards from database
        existing_cards = self.db.get_all('admit_cards')
        existing_by_id = {c.get('id'): c for c in existing_cards}
        
        for card in admit_cards:
            # Validate
            if not self._validate_admit_card(card):
                continue
            
            card_dict = card.to_dict()
            
            # Check for duplicates
            if card.id in existing_by_id:
                # It's a duplicate - mark with metadata
                old_card = existing_by_id[card.id]
                card_dict['is_new'] = False
                card_dict['is_duplicate'] = True
                card_dict['previous_discovered_at'] = old_card.get('discovered_at', '')
                card_dict['times_seen'] = old_card.get('times_seen', 1) + 1
                
                # Remove from existing (will be re-added at top)
                existing_cards = [c for c in existing_cards if c.get('id') != card.id]
                
                duplicate_count += 1
                updated_count += 1
            else:
                # New admit card
                card_dict['is_new'] = True
                card_dict['is_duplicate'] = False
                card_dict['times_seen'] = 1
                self._id_cache['admit_cards'].add(card.id)
            
            new_cards.append(card_dict)
        
        # Store: new cards at top + remaining old cards
        if new_cards:
            all_cards = new_cards + existing_cards
            self.db._write_file(self.db.files['admit_cards'], all_cards)
            self.logger.info(f"Stored {len(new_cards)} admit cards ({len(new_cards) - updated_count} new, {updated_count} updated)")
        
        return {
            'total': len(admit_cards),
            'new': len(new_cards) - updated_count,
            'duplicates': duplicate_count,
            'updated': updated_count
        }
    
    def process_notifications(self, notifications: List[NotificationEntry]) -> Dict[str, Any]:
        """
        Process and store notification entries
        
        Args:
            notifications: List of NotificationEntry objects
        
        Returns:
            Dictionary with processing statistics
        """
        if not notifications:
            return {'total': 0, 'new': 0, 'duplicates': 0}
        
        self.logger.info(f"Processing {len(notifications)} notification entries")
        
        new_notifications = []
        duplicate_count = 0
        
        for notif in notifications:
            # Validate
            if not self._validate_notification(notif):
                continue
            
            # Check for duplicates
            if notif.id in self._id_cache.get('notifications', set()):
                duplicate_count += 1
                continue
            
            # Add to new notifications list
            new_notifications.append(notif.to_dict())
            self._id_cache['notifications'].add(notif.id)
        
        # Store in database
        if new_notifications:
            self.db.insert_many('notifications', new_notifications)
            self.logger.info(f"Stored {len(new_notifications)} new notifications")
        
        return {
            'total': len(notifications),
            'new': len(new_notifications),
            'duplicates': duplicate_count
        }
    
    def process_crawl_history(self, history: CrawlHistory) -> bool:
        """
        Store crawl history entry
        
        Args:
            history: CrawlHistory object
        
        Returns:
            True if successful
        """
        try:
            self.db.insert('crawl_history', history.to_dict())
            return True
        except Exception as e:
            self.logger.error(f"Error storing crawl history: {e}")
            return False
    
    def _validate_job(self, job: JobEntry) -> bool:
        """
        Validate job entry
        
        Args:
            job: JobEntry object
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not job.id or not job.title or not job.url:
                self.logger.warning(f"Invalid job entry: missing required fields")
                return False
            
            # Check URL format
            if not job.url.startswith(('http://', 'https://')):
                self.logger.warning(f"Invalid URL in job: {job.url}")
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error validating job: {e}")
            return False
    
    def _validate_result(self, result: ResultEntry) -> bool:
        """Validate result entry"""
        try:
            if not result.id or not result.title or not result.url:
                return False
            
            if not result.url.startswith(('http://', 'https://')):
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error validating result: {e}")
            return False
    
    def _validate_admit_card(self, card: AdmitCardEntry) -> bool:
        """Validate admit card entry"""
        try:
            if not card.id or not card.title or not card.url:
                return False
            
            if not card.url.startswith(('http://', 'https://')):
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error validating admit card: {e}")
            return False
    
    def _validate_notification(self, notif: NotificationEntry) -> bool:
        """Validate notification entry"""
        try:
            if not notif.id or not notif.title or not notif.url:
                return False
            
            if not notif.url.startswith(('http://', 'https://')):
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error validating notification: {e}")
            return False
    
    def get_recent_entries(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent entries from a category
        
        Args:
            category: Data category
            limit: Number of entries to return
        
        Returns:
            List of recent entries
        """
        return self.db.get_all(category, limit=limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics
        
        Returns:
            Dictionary with statistics for all categories
        """
        stats = self.db.get_stats()
        
        return {
            'total_entries': sum(stats.values()),
            'by_category': stats,
            'cache_size': {
                category: len(ids)
                for category, ids in self._id_cache.items()
            }
        }
    
    def refresh_cache(self) -> None:
        """Refresh ID cache from database"""
        self.logger.info("Refreshing ID cache")
        self._id_cache.clear()
        self._load_id_cache()
