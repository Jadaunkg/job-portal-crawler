"""
Generic Portal Crawler

A generic crawler implementation that can crawl any portal
based on the configuration provided in portals.yaml
"""

from typing import Dict, Any, List

from .base_crawler import BaseCrawler


class GenericCrawler(BaseCrawler):
    """
    Generic crawler that works with any portal configuration
    
    Uses the selectors and configurations from portals.yaml
    to extract data without requiring portal-specific code.
    """
    
    def crawl(self) -> Dict[str, List[Any]]:
        """
        Crawl all enabled categories for this portal
        
        Returns:
            Dictionary with lists of entries by category
        """
        self.logger.info(f"Starting crawl for {self.portal_name}")
        self.reset_stats()
        
        results = {
            'jobs': [],
            'results': [],
            'admit_cards': [],
            'notifications': []
        }
        
        categories = self.portal_config.get('categories', {})
        
        # Crawl jobs
        if 'jobs' in categories:
            results['jobs'] = self.crawl_jobs(categories['jobs'])
        
        # Crawl results
        if 'results' in categories:
            results['results'] = self.crawl_results(categories['results'])
        
        # Crawl admit cards
        if 'admit_cards' in categories:
            results['admit_cards'] = self.crawl_admit_cards(categories['admit_cards'])
        
        # You can add notifications category similarly if needed
        
        self.logger.info(
            f"Crawl complete for {self.portal_name}. "
            f"Found {self.stats['items_found']} items from {self.stats['pages_crawled']} pages"
        )
        
        return results
