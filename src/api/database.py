"""
Database query operations for API endpoints.
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class ApiDatabase:
    """Database operations for API queries."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.jobs_file = self.data_dir / "jobs.json"
        self.results_file = self.data_dir / "results.json"
        self.admit_cards_file = self.data_dir / "admit_cards.json"

    def _load_json_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """Load JSON file safely."""
        if not filepath.exists():
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    # ==================== Jobs ====================

    def get_all_jobs(self, page: int = 1, limit: int = 10) -> tuple[List[Dict], int]:
        """Get paginated jobs."""
        jobs = self._load_json_file(self.jobs_file)
        total = len(jobs)
        start = (page - 1) * limit
        end = start + limit
        paginated = jobs[start:end]
        return paginated, total

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get single job by ID."""
        jobs = self._load_json_file(self.jobs_file)
        for job in jobs:
            if job.get('id') == job_id:
                return job
        return None

    def search_jobs(self, keyword: Optional[str] = None, 
                   portal: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   details_only: bool = False,
                   page: int = 1,
                   limit: int = 10) -> tuple[List[Dict], int]:
        """Search jobs with filters."""
        jobs = self._load_json_file(self.jobs_file)
        
        # Apply filters
        filtered = []
        for job in jobs:
            # Keyword filter
            if keyword:
                keyword_lower = keyword.lower()
                title = job.get('title', '').lower()
                if keyword_lower not in title:
                    continue
            
            # Portal filter
            if portal and job.get('portal') != portal:
                continue
            
            # Date filters
            if start_date and job.get('posted_date', '') < start_date:
                continue
            if end_date and job.get('posted_date', '') > end_date:
                continue
            
            # Details filter
            if details_only and not job.get('detailed_info'):
                continue
            
            filtered.append(job)
        
        # Pagination
        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        paginated = filtered[start:end]
        
        return paginated, total

    # ==================== Results ====================

    def get_all_results(self, page: int = 1, limit: int = 10) -> tuple[List[Dict], int]:
        """Get paginated results."""
        results = self._load_json_file(self.results_file)
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated = results[start:end]
        return paginated, total

    def get_result_by_id(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get single result by ID."""
        results = self._load_json_file(self.results_file)
        for result in results:
            if result.get('id') == result_id:
                return result
        return None

    def search_results(self, keyword: Optional[str] = None,
                      portal: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      details_only: bool = False,
                      page: int = 1,
                      limit: int = 10) -> tuple[List[Dict], int]:
        """Search results with filters."""
        results = self._load_json_file(self.results_file)
        
        filtered = []
        for result in results:
            if keyword:
                keyword_lower = keyword.lower()
                title = result.get('title', '').lower()
                if keyword_lower not in title:
                    continue
            
            if portal and result.get('portal') != portal:
                continue
            
            if start_date and result.get('posted_date', '') < start_date:
                continue
            if end_date and result.get('posted_date', '') > end_date:
                continue
            
            if details_only and not result.get('detailed_info'):
                continue
            
            filtered.append(result)
        
        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        paginated = filtered[start:end]
        
        return paginated, total

    # ==================== Admit Cards ====================

    def get_all_admit_cards(self, page: int = 1, limit: int = 10) -> tuple[List[Dict], int]:
        """Get paginated admit cards."""
        admit_cards = self._load_json_file(self.admit_cards_file)
        total = len(admit_cards)
        start = (page - 1) * limit
        end = start + limit
        paginated = admit_cards[start:end]
        return paginated, total

    def get_admit_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get single admit card by ID."""
        admit_cards = self._load_json_file(self.admit_cards_file)
        for card in admit_cards:
            if card.get('id') == card_id:
                return card
        return None

    def search_admit_cards(self, keyword: Optional[str] = None,
                          portal: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          details_only: bool = False,
                          page: int = 1,
                          limit: int = 10) -> tuple[List[Dict], int]:
        """Search admit cards with filters."""
        admit_cards = self._load_json_file(self.admit_cards_file)
        
        filtered = []
        for card in admit_cards:
            if keyword:
                keyword_lower = keyword.lower()
                title = card.get('title', '').lower()
                if keyword_lower not in title:
                    continue
            
            if portal and card.get('portal') != portal:
                continue
            
            if start_date and card.get('posted_date', '') < start_date:
                continue
            if end_date and card.get('posted_date', '') > end_date:
                continue
            
            if details_only and not card.get('detailed_info'):
                continue
            
            filtered.append(card)
        
        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        paginated = filtered[start:end]
        
        return paginated, total

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        jobs = self._load_json_file(self.jobs_file)
        results = self._load_json_file(self.results_file)
        admit_cards = self._load_json_file(self.admit_cards_file)
        
        jobs_with_details = len([j for j in jobs if j.get('detailed_info')])
        results_with_details = len([r for r in results if r.get('detailed_info')])
        cards_with_details = len([c for c in admit_cards if c.get('detailed_info')])
        
        # Calculate database size
        db_size = 0
        for filepath in [self.jobs_file, self.results_file, self.admit_cards_file]:
            if filepath.exists():
                db_size += os.path.getsize(filepath)
        db_size_mb = db_size / (1024 * 1024)
        
        # Find last crawl time
        last_crawl = None
        for data_list in [jobs, results, admit_cards]:
            if data_list:
                latest = max([item.get('scraped_at', '') for item in data_list])
                if not last_crawl or latest > last_crawl:
                    last_crawl = latest
        
        return {
            'total_jobs': len(jobs),
            'total_results': len(results),
            'total_admit_cards': len(admit_cards),
            'jobs_with_details': jobs_with_details,
            'results_with_details': results_with_details,
            'admit_cards_with_details': cards_with_details,
            'last_crawl_time': last_crawl,
            'database_size_mb': round(db_size_mb, 2)
        }

    def get_portal_stats(self) -> List[Dict[str, Any]]:
        """Get statistics per portal."""
        jobs = self._load_json_file(self.jobs_file)
        results = self._load_json_file(self.results_file)
        admit_cards = self._load_json_file(self.admit_cards_file)
        
        portal_stats = {}
        
        # Count jobs per portal
        for job in jobs:
            portal = job.get('portal', 'unknown')
            if portal not in portal_stats:
                portal_stats[portal] = {'job_count': 0, 'result_count': 0, 'admit_card_count': 0}
            portal_stats[portal]['job_count'] += 1
        
        # Count results per portal
        for result in results:
            portal = result.get('portal', 'unknown')
            if portal not in portal_stats:
                portal_stats[portal] = {'job_count': 0, 'result_count': 0, 'admit_card_count': 0}
            portal_stats[portal]['result_count'] += 1
        
        # Count admit cards per portal
        for card in admit_cards:
            portal = card.get('portal', 'unknown')
            if portal not in portal_stats:
                portal_stats[portal] = {'job_count': 0, 'result_count': 0, 'admit_card_count': 0}
            portal_stats[portal]['admit_card_count'] += 1
        
        return [{'portal': portal, **stats} for portal, stats in portal_stats.items()]
