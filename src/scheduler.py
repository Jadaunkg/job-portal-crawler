"""
Scheduler Service

Manages scheduled execution of crawlers at regular intervals.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

try:
    from ..crawler import CrawlerManager
    from ..utils import get_logger, get_config
except ImportError:
    from crawler import CrawlerManager
    from utils import get_logger, get_config


class CrawlerScheduler:
    """
    Scheduler for automated crawler execution
    
    Uses APScheduler to run crawlers at configured intervals
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize scheduler
        
        Args:
            config_dir: Configuration directory path
        """
        self.logger = get_logger("scheduler")
        self.config = get_config(config_dir)
        self.settings = self.config.load_settings()
        
        # Get scheduler settings
        scheduler_config = self.settings.get('scheduler', {})
        self.interval_minutes = scheduler_config.get('interval_minutes', 15)
        self.run_on_startup = scheduler_config.get('run_on_startup', True)
        
        # Initialize crawler manager
        self.manager = CrawlerManager(config_dir)
        
        # Initialize APScheduler
        self.scheduler = BlockingScheduler()
        
        # Track execution
        self.last_execution: Optional[datetime] = None
        self.execution_count = 0
    
    def _execute_crawlers(self) -> None:
        """Execute crawlers (called by scheduler)"""
        try:
            self.logger.info(f"\n{'#'*60}")
            self.logger.info(f"Scheduled Execution #{self.execution_count + 1}")
            self.logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"{'#'*60}\n")
            
            # Execute crawlers
            results = self.manager.execute_all()
            
            # Update tracking
            self.last_execution = datetime.now()
            self.execution_count += 1
            
            # Log summary
            self.logger.info(f"\nExecution #{self.execution_count} completed successfully")
            self.logger.info(f"New items found: {results.get('new_items', 0)}")
            self.logger.info(f"Next execution in {self.interval_minutes} minutes\n")
            
        except Exception as e:
            self.logger.error(f"Error during scheduled execution: {e}", exc_info=True)
    
    def start(self) -> None:
        """
        Start the scheduler
        
        This will block the current thread and run indefinitely until interrupted.
        """
        self.logger.info("=" * 60)
        self.logger.info("Job Crawler Scheduler Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Interval: {self.interval_minutes} minutes")
        self.logger.info(f"Run on startup: {self.run_on_startup}")
        self.logger.info("=" * 60)
        
        # Run immediately if configured
        if self.run_on_startup:
            self.logger.info("Executing initial crawl...")
            self._execute_crawlers()
        
        # Schedule periodic execution
        self.scheduler.add_job(
            self._execute_crawlers,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='crawler_job',
            name='Execute Crawlers',
            replace_existing=True
        )
        
        self.logger.info(f"\nScheduler started. Crawlers will run every {self.interval_minutes} minutes.")
        self.logger.info("Press Ctrl+C to stop.\n")
        
        try:
            # Start scheduler (blocks)
            self.scheduler.start()
        
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("\nShutdown signal received")
            self.stop()
    
    def stop(self) -> None:
        """Stop the scheduler"""
        self.logger.info("Stopping scheduler...")
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        
        self.logger.info("Scheduler stopped")
        self.logger.info(f"Total executions: {self.execution_count}")
        
        if self.last_execution:
            self.logger.info(f"Last execution: {self.last_execution.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run_once(self) -> None:
        """
        Run crawlers once without scheduling
        
        Useful for manual execution or testing
        """
        self.logger.info("Running crawlers once (no scheduling)")
        self._execute_crawlers()
    
    def get_status(self) -> dict:
        """
        Get scheduler status
        
        Returns:
            Dictionary with scheduler status information
        """
        return {
            'running': self.scheduler.running if hasattr(self, 'scheduler') else False,
            'interval_minutes': self.interval_minutes,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.scheduler.get_jobs()[0].next_run_time.isoformat()
                            if self.scheduler.running and self.scheduler.get_jobs()
                            else None
        }
