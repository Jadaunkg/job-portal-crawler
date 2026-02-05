"""
Generic Portal Crawler

Crawls all categories (jobs, results, admit cards) directly from the homepage
where the latest items are displayed first.
"""

from typing import Dict, Any, List
from bs4 import BeautifulSoup

from .base_crawler import BaseCrawler

try:
    from ..utils import clean_text, normalize_url, is_valid_url
    from ..data import (
        JobEntry,
        ResultEntry,
        AdmitCardEntry,
        generate_entry_id,
        generate_timestamp
    )
except ImportError:
    from utils import clean_text, normalize_url, is_valid_url
    from data import (
        JobEntry,
        ResultEntry,
        AdmitCardEntry,
        generate_entry_id,
        generate_timestamp
    )


class GenericCrawler(BaseCrawler):
    """
    Crawler that extracts all categories from the homepage.
    
    The homepage displays categorized sections with headers:
    - "Results" 
    - "Admit Cards"
    - "Latest Jobs"
    
    Each section has a list with items linked via wp-block-latest-posts
    """
    
    # Section header mappings
    SECTION_MAPPINGS = {
        'results': ['Results', 'Result'],
        'admit_cards': ['Admit Cards', 'Admit Card'],
        'jobs': ['Latest Jobs', 'Jobs', 'Latest Job']
    }
    
    def crawl(self) -> Dict[str, List[Any]]:
        """
        Crawl all categories from the homepage
        
        Returns:
            Dictionary with lists of entries by category
        """
        self.logger.info(f"Starting homepage crawl for {self.portal_name}")
        self.reset_stats()
        
        results = {
            'jobs': [],
            'results': [],
            'admit_cards': [],
            'notifications': []
        }
        
        # Fetch the homepage
        homepage_url = self.portal_config.get('homepage_url', self.base_url)
        if not homepage_url:
            homepage_url = self.base_url
        
        self.logger.info(f"Fetching homepage: {homepage_url}")
        
        html = self.fetch_page(homepage_url)
        if not html:
            self.logger.error("Failed to fetch homepage")
            return results
        
        soup = self.parse_html(html)
        
        # Extract featured items (shown at the top)
        featured_jobs = self._extract_featured_jobs(soup)
        results['jobs'].extend(featured_jobs)
        
        # Extract categorized sections
        results['results'] = self._extract_section_items(soup, 'results')
        results['admit_cards'] = self._extract_section_items(soup, 'admit_cards')
        results['jobs'].extend(self._extract_section_items(soup, 'jobs'))
        
        self.logger.info(
            f"Crawl complete. Found {len(results['jobs'])} jobs, "
            f"{len(results['results'])} results, {len(results['admit_cards'])} admit cards"
        )
        
        return results
    
    def _extract_featured_jobs(self, soup: BeautifulSoup) -> List[JobEntry]:
        """Extract featured jobs from the top section of the homepage."""
        jobs = []
        
        # Featured items are in p.gb-headline elements at the top
        featured_links = soup.select('div.gb-grid-wrapper p.gb-headline a')
        
        for link in featured_links[:10]:  # Limit to first 10
            try:
                title = clean_text(link.get_text())
                if not title:
                    continue
                
                url = link.get('href', '')
                if not url or not is_valid_url(url):
                    continue
                
                url = normalize_url(url, self.base_url)
                entry_id = generate_entry_id(title, '', self.portal_name)
                
                job = JobEntry(
                    id=entry_id,
                    portal_name=self.portal_name,
                    title=title,
                    organization='',
                    url=url,
                    post_date='',
                    last_date='',
                    location='',
                    category='Featured',
                    description='',
                    discovered_at=generate_timestamp()
                )
                
                jobs.append(job)
                self.stats['items_found'] += 1
                
            except Exception as e:
                self.logger.debug(f"Error extracting featured job: {e}")
        
        self.logger.info(f"Found {len(jobs)} featured jobs")
        return jobs
    
    def _extract_section_items(self, soup: BeautifulSoup, category: str) -> List[Any]:
        """Extract items from a section based on its header text."""
        headers = self.SECTION_MAPPINGS.get(category, [])
        items = []
        
        for header_text in headers:
            section = self._find_section_by_header(soup, header_text)
            if section:
                # Get all list items
                list_items = section.select('ul.wp-block-latest-posts__list li a.wp-block-latest-posts__post-title')
                if not list_items:
                    list_items = section.select('ul.wp-block-latest-posts li a')
                
                for link in list_items:
                    try:
                        title = clean_text(link.get_text())
                        if not title:
                            continue
                        
                        url = link.get('href', '')
                        if not url or not is_valid_url(url):
                            continue
                        
                        url = normalize_url(url, self.base_url)
                        entry = self._create_entry(category, title, url)
                        if entry:
                            items.append(entry)
                            self.stats['items_found'] += 1
                            
                    except Exception as e:
                        self.logger.debug(f"Error extracting {category} item: {e}")
                break
        
        self.logger.info(f"Found {len(items)} {category}")
        return items
    
    def _find_section_by_header(self, soup: BeautifulSoup, header_text: str):
        """Find a section container by its header text."""
        headlines = soup.select('p.gb-headline')
        
        for headline in headlines:
            text = clean_text(headline.get_text())
            if text == header_text:
                # Find parent container
                for parent_class in ['gb-inside-container', 'gb-container', 'gb-grid-column']:
                    parent = headline.find_parent('div', class_=parent_class)
                    if parent:
                        return parent
        return None
    
    def _create_entry(self, category: str, title: str, url: str):
        """Create an entry object based on category."""
        entry_id = generate_entry_id(title, '', self.portal_name)
        timestamp = generate_timestamp()
        
        if category == 'jobs':
            return JobEntry(
                id=entry_id,
                portal_name=self.portal_name,
                title=title,
                organization='',
                url=url,
                post_date='',
                last_date='',
                location='',
                category='Latest Jobs',
                description='',
                discovered_at=timestamp
            )
        
        elif category == 'results':
            return ResultEntry(
                id=entry_id,
                portal_name=self.portal_name,
                title=title,
                organization='',
                url=url,
                result_date='',
                description='',
                discovered_at=timestamp
            )
        
        elif category == 'admit_cards':
            return AdmitCardEntry(
                id=entry_id,
                portal_name=self.portal_name,
                title=title,
                organization='',
                url=url,
                exam_date='',
                download_start='',
                download_end='',
                description='',
                discovered_at=timestamp
            )
        
        return None
