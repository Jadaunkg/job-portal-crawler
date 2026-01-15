"""
Crawler Manager

Coordinates execution of multiple portal crawlers and manages the overall crawling process.
"""

from typing import Dict, List, Any
from datetime import datetime
import traceback

from .generic_crawler import GenericCrawler

try:
    from ..data import CrawlHistory, CrawlerStats, generate_timestamp
    from ..data.database import JSONDatabase
    from ..data.processor import DataProcessor
    from ..utils import get_logger, get_config
except ImportError:
    from data import CrawlHistory, CrawlerStats, generate_timestamp
    from data.database import JSONDatabase
    from data.processor import DataProcessor
    from utils import get_logger, get_config


class CrawlerManager:
    """
    Manages multiple portal crawlers
    
    Responsibilities:
    - Load portal configurations
    - Instantiate crawlers
    - Execute crawls (sequential or parallel)
    - Coordinate data processing
    - Track execution statistics
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize crawler manager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.logger = get_logger("manager")
        self.config = get_config(config_dir)
        
        # Load settings
        self.settings = self.config.load_settings()
        
        # Initialize database
        storage_settings = self.settings.get('storage', {})
        self.db = JSONDatabase(
            data_dir=storage_settings.get('data_dir', 'data'),
            backup_enabled=storage_settings.get('backup_enabled', True),
            max_backups=storage_settings.get('max_backups', 10),
            backup_frequency=storage_settings.get('backup_frequency', 5)
        )
        
        # Initialize processor
        self.processor = DataProcessor(self.db)
        
        # Statistics
        self.execution_stats: List[CrawlerStats] = []
    
    def execute_all(self) -> Dict[str, Any]:
        """
        Execute all enabled portal crawlers
        
        Returns:
            Dictionary with execution summary
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting crawler execution")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Get enabled portals
        enabled_portals = self.config.get_enabled_portals()
        
        if not enabled_portals:
            self.logger.warning("No portals enabled in configuration")
            return {
                'status': 'no_portals',
                'message': 'No portals enabled',
                'portals_crawled': 0
            }
        
        self.logger.info(f"Found {len(enabled_portals)} enabled portals")
        
        # Execute crawlers
        total_new_items = 0
        successful_crawls = 0
        failed_crawls = 0
        
        for portal_config in enabled_portals:
            try:
                stats = self._execute_portal(portal_config)
                self.execution_stats.append(stats)
                
                if stats.status == 'success':
                    successful_crawls += 1
                    total_new_items += stats.new_entries
                else:
                    failed_crawls += 1
                
            except Exception as e:
                self.logger.error(f"Fatal error crawling {portal_config.get('name')}: {e}")
                self.logger.error(traceback.format_exc())
                failed_crawls += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("Crawler Execution Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Portals crawled: {len(enabled_portals)}")
        self.logger.info(f"Successful: {successful_crawls}")
        self.logger.info(f"Failed: {failed_crawls}")
        self.logger.info(f"New items found: {total_new_items}")
        self.logger.info(f"Total duration: {duration:.2f}s")
        self.logger.info("=" * 60)
        
        return {
            'status': 'completed',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'portals_crawled': len(enabled_portals),
            'successful': successful_crawls,
            'failed': failed_crawls,
            'new_items': total_new_items,
            'portal_stats': [stat.to_dict() for stat in self.execution_stats]
        }
    
    def _execute_portal(self, portal_config: Dict[str, Any]) -> CrawlerStats:
        """
        Execute crawler for a single portal
        
        Args:
            portal_config: Portal configuration dictionary
        
        Returns:
            CrawlerStats object with execution results
        """
        portal_name = portal_config.get('name', 'Unknown')
        
        self.logger.info(f"\n{'='*40}")
        self.logger.info(f"Crawling: {portal_name}")
        self.logger.info(f"{'='*40}")
        
        stats = CrawlerStats(
            portal_name=portal_name,
            start_time=datetime.now()
        )
        
        try:
            # Instantiate crawler
            crawler = GenericCrawler(portal_config, self.settings)
            
            # Execute crawl
            crawl_results = crawler.crawl()
            
            # Process results
            jobs = crawl_results.get('jobs', [])
            results = crawl_results.get('results', [])
            admit_cards = crawl_results.get('admit_cards', [])
            notifications = crawl_results.get('notifications', [])
            
            # Process each category
            job_stats = self.processor.process_jobs(jobs)
            result_stats = self.processor.process_results(results)
            admit_card_stats = self.processor.process_admit_cards(admit_cards)
            notif_stats = self.processor.process_notifications(notifications)
            
            # Update stats
            stats.jobs_found = len(jobs)
            stats.results_found = len(results)
            stats.admit_cards_found = len(admit_cards)
            stats.notifications_found = len(notifications)
            stats.new_entries = (
                job_stats['new'] +
                result_stats['new'] +
                admit_card_stats['new'] +
                notif_stats['new']
            )
            
            # Mark as successful
            stats.end_time = datetime.now()
            stats.status = 'success'
            
            # Log results
            self.logger.info(f"\nResults for {portal_name}:")
            self.logger.info(f"  Jobs: {len(jobs)} found, {job_stats['new']} new")
            self.logger.info(f"  Results: {len(results)} found, {result_stats['new']} new")
            self.logger.info(f"  Admit Cards: {len(admit_cards)} found, {admit_card_stats['new']} new")
            self.logger.info(f"  Total new items: {stats.new_entries}")
            self.logger.info(f"  Duration: {stats.duration:.2f}s")
            
            # Store crawl history
            categories_crawled = []
            if jobs:
                categories_crawled.append('jobs')
            if results:
                categories_crawled.append('results')
            if admit_cards:
                categories_crawled.append('admit_cards')
            
            history = CrawlHistory(
                id=f"{portal_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                portal_name=portal_name,
                crawl_time=generate_timestamp(),
                status='success',
                items_found=stats.total_items,
                new_items=stats.new_entries,
                duration_seconds=stats.duration,
                categories_crawled=categories_crawled
            )
            self.processor.process_crawl_history(history)
            
        except Exception as e:
            # Handle errors
            stats.end_time = datetime.now()
            stats.status = 'failed'
            error_msg = str(e)
            stats.errors.append(error_msg)
            
            self.logger.error(f"Error crawling {portal_name}: {error_msg}")
            self.logger.error(traceback.format_exc())
            
            # Store failed crawl history
            history = CrawlHistory(
                id=f"{portal_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                portal_name=portal_name,
                crawl_time=generate_timestamp(),
                status='failed',
                items_found=0,
                new_items=0,
                duration_seconds=stats.duration,
                error_message=error_msg
            )
            self.processor.process_crawl_history(history)
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current execution statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'executions': len(self.execution_stats),
            'portal_stats': [stat.to_dict() for stat in self.execution_stats],
            'database_stats': self.processor.get_statistics()
        }
    
    def get_recent_items(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent items from a category
        
        Args:
            category: Category name
            limit: Number of items to return
        
        Returns:
            List of items
        """
        return self.processor.get_recent_entries(category, limit)
