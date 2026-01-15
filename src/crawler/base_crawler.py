"""
Base Crawler Class

Abstract base class for all portal-specific crawlers.
Provides common functionality for HTTP requests, HTML parsing, and data extraction.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

try:
    from ..utils import (
        get_logger,
        retry_on_failure,
        clean_text,
        normalize_url,
        is_valid_url
    )
    from ..data import (
        JobEntry,
        ResultEntry,
        AdmitCardEntry,
        NotificationEntry,
        generate_entry_id,
        generate_timestamp
    )
except ImportError:
    from utils import (
        get_logger,
        retry_on_failure,
        clean_text,
        normalize_url,
        is_valid_url
    )
    from data import (
        JobEntry,
        ResultEntry,
        AdmitCardEntry,
        NotificationEntry,
        generate_entry_id,
        generate_timestamp
    )


class BaseCrawler(ABC):
    """
    Abstract base class for portal crawlers
    
    All portal-specific crawlers should inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, portal_config: Dict[str, Any], settings: Dict[str, Any]):
        """
        Initialize base crawler
        
        Args:
            portal_config: Portal-specific configuration
            settings: Global crawler settings
        """
        self.portal_name = portal_config.get('name', 'Unknown')
        self.base_url = portal_config.get('base_url', '')
        self.portal_config = portal_config
        self.settings = settings
        
        # Get crawler settings
        crawler_config = settings.get('crawler', {})
        self.timeout = crawler_config.get('timeout_seconds', 30)
        self.max_retries = crawler_config.get('max_retries', 3)
        self.user_agent = crawler_config.get('user_agent', 'Mozilla/5.0')
        self.request_delay = crawler_config.get('request_delay', 1)
        self.max_pages = crawler_config.get('max_pages_per_run', 50)
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Logger
        self.logger = get_logger(f"crawler.{self.portal_name}")
        
        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'items_found': 0,
            'errors': []
        }
    
    @abstractmethod
    def crawl(self) -> Dict[str, List[Any]]:
        """
        Main crawl method - must be implemented by subclasses
        
        Returns:
            Dictionary with lists of entries by category:
            {
                'jobs': [...],
                'results': [...],
                'admit_cards': [...],
                'notifications': [...]
            }
        """
        pass
    
    @retry_on_failure(max_retries=3, delay=2.0)
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch web page content
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content or None if failed
        """
        try:
            self.logger.debug(f"Fetching: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Add delay to be respectful
            time.sleep(self.request_delay)
            
            self.stats['pages_crawled'] += 1
            
            return response.text
        
        except requests.Timeout:
            self.logger.error(f"Timeout fetching {url}")
            self.stats['errors'].append(f"Timeout: {url}")
            return None
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            self.stats['errors'].append(f"Request error: {url} - {str(e)}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content
        
        Args:
            html: HTML string
        
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')
    
    def extract_text(self, element, selector: str, default: str = "") -> str:
        """
        Extract and clean text from element using CSS selector
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            default: Default value if not found
        
        Returns:
            Cleaned text
        """
        try:
            found = element.select_one(selector)
            if found:
                return clean_text(found.get_text())
            return default
        except Exception as e:
            self.logger.debug(f"Error extracting text with selector '{selector}': {e}")
            return default
    
    def extract_attribute(self, element, selector: str, attribute: str, 
                         default: str = "") -> str:
        """
        Extract attribute value from element
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            attribute: Attribute name (e.g., 'href', 'src')
            default: Default value if not found
        
        Returns:
            Attribute value
        """
        try:
            found = element.select_one(selector)
            if found:
                value = found.get(attribute, default)
                return str(value) if value else default
            return default
        except Exception as e:
            self.logger.debug(f"Error extracting attribute '{attribute}': {e}")
            return default
    
    def extract_link(self, element, selector: str) -> str:
        """
        Extract and normalize link from element
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
        
        Returns:
            Normalized absolute URL
        """
        href = self.extract_attribute(element, selector, 'href')
        if href:
            return normalize_url(href, self.base_url)
        return ""
    
    def crawl_jobs(self, category_config: Dict[str, Any]) -> List[JobEntry]:
        """
        Crawl jobs from configured URL
        
        Args:
            category_config: Configuration for jobs category
        
        Returns:
            List of JobEntry objects
        """
        if not category_config.get('enabled', False):
            return []
        
        url = category_config.get('url', '')
        if not url:
            self.logger.warning(f"No URL configured for jobs in {self.portal_name}")
            return []
        
        self.logger.info(f"Crawling jobs from {url}")
        
        html = self.fetch_page(url)
        if not html:
            return []
        
        soup = self.parse_html(html)
        selectors = category_config.get('selectors', {})
        
        jobs = []
        containers = soup.select(selectors.get('container', ''))
        
        for container in containers:
            try:
                title = self.extract_text(container, selectors.get('title', ''))
                if not title:
                    continue
                
                organization = self.extract_text(container, selectors.get('organization', ''))
                url_link = self.extract_link(container, selectors.get('link', ''))
                
                if not url_link or not is_valid_url(url_link):
                    continue
                
                # Generate unique ID
                entry_id = generate_entry_id(title, organization, self.portal_name)
                
                # Create job entry
                job = JobEntry(
                    id=entry_id,
                    portal_name=self.portal_name,
                    title=title,
                    organization=organization,
                    url=url_link,
                    post_date=self.extract_text(container, selectors.get('post_date', '')),
                    last_date=self.extract_text(container, selectors.get('last_date', '')),
                    location=self.extract_text(container, selectors.get('location', '')),
                    category=self.extract_text(container, selectors.get('category', '')),
                    description=self.extract_text(container, selectors.get('description', '')),
                    discovered_at=generate_timestamp()
                )
                
                jobs.append(job)
                self.stats['items_found'] += 1
                
            except Exception as e:
                self.logger.error(f"Error parsing job entry: {e}")
                self.stats['errors'].append(f"Parse error: {str(e)}")
        
        self.logger.info(f"Found {len(jobs)} jobs")
        return jobs
    
    def crawl_results(self, category_config: Dict[str, Any]) -> List[ResultEntry]:
        """
        Crawl results from configured URL
        
        Args:
            category_config: Configuration for results category
        
        Returns:
            List of ResultEntry objects
        """
        if not category_config.get('enabled', False):
            return []
        
        url = category_config.get('url', '')
        if not url:
            return []
        
        self.logger.info(f"Crawling results from {url}")
        
        html = self.fetch_page(url)
        if not html:
            return []
        
        soup = self.parse_html(html)
        selectors = category_config.get('selectors', {})
        
        results = []
        containers = soup.select(selectors.get('container', ''))
        
        for container in containers:
            try:
                title = self.extract_text(container, selectors.get('title', ''))
                if not title:
                    continue
                
                organization = self.extract_text(container, selectors.get('organization', ''))
                url_link = self.extract_link(container, selectors.get('link', ''))
                
                if not url_link or not is_valid_url(url_link):
                    continue
                
                entry_id = generate_entry_id(title, organization, self.portal_name)
                
                result = ResultEntry(
                    id=entry_id,
                    portal_name=self.portal_name,
                    title=title,
                    organization=organization,
                    url=url_link,
                    result_date=self.extract_text(container, selectors.get('result_date', '')),
                    description=self.extract_text(container, selectors.get('description', '')),
                    discovered_at=generate_timestamp()
                )
                
                results.append(result)
                self.stats['items_found'] += 1
                
            except Exception as e:
                self.logger.error(f"Error parsing result entry: {e}")
                self.stats['errors'].append(f"Parse error: {str(e)}")
        
        self.logger.info(f"Found {len(results)} results")
        return results
    
    def crawl_admit_cards(self, category_config: Dict[str, Any]) -> List[AdmitCardEntry]:
        """
        Crawl admit cards from configured URL
        
        Args:
            category_config: Configuration for admit cards category
        
        Returns:
            List of AdmitCardEntry objects
        """
        if not category_config.get('enabled', False):
            return []
        
        url = category_config.get('url', '')
        if not url:
            return []
        
        self.logger.info(f"Crawling admit cards from {url}")
        
        html = self.fetch_page(url)
        if not html:
            return []
        
        soup = self.parse_html(html)
        selectors = category_config.get('selectors', {})
        
        admit_cards = []
        containers = soup.select(selectors.get('container', ''))
        
        for container in containers:
            try:
                title = self.extract_text(container, selectors.get('title', ''))
                if not title:
                    continue
                
                organization = self.extract_text(container, selectors.get('organization', ''))
                url_link = self.extract_link(container, selectors.get('link', ''))
                
                if not url_link or not is_valid_url(url_link):
                    continue
                
                entry_id = generate_entry_id(title, organization, self.portal_name)
                
                admit_card = AdmitCardEntry(
                    id=entry_id,
                    portal_name=self.portal_name,
                    title=title,
                    organization=organization,
                    url=url_link,
                    exam_date=self.extract_text(container, selectors.get('exam_date', '')),
                    download_start=self.extract_text(container, selectors.get('download_start', '')),
                    download_end=self.extract_text(container, selectors.get('download_end', '')),
                    description=self.extract_text(container, selectors.get('description', '')),
                    discovered_at=generate_timestamp()
                )
                
                admit_cards.append(admit_card)
                self.stats['items_found'] += 1
                
            except Exception as e:
                self.logger.error(f"Error parsing admit card entry: {e}")
                self.stats['errors'].append(f"Parse error: {str(e)}")
        
        self.logger.info(f"Found {len(admit_cards)} admit cards")
        return admit_cards
    
    def get_stats(self) -> Dict[str, Any]:
        """Get crawler statistics"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self.stats = {
            'pages_crawled': 0,
            'items_found': 0,
            'errors': []
        }
