"""
Detail Crawler Module

Crawls individual job/result/admit card pages to extract comprehensive information.
"""

import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

try:
    from .base_crawler import BaseCrawler
except ImportError:
    from base_crawler import BaseCrawler

logger = logging.getLogger('job_crawler')


class DetailCrawler(BaseCrawler):
    """
    Crawls individual pages to extract detailed information
    """
    
    def __init__(self, portal_config: Dict[str, Any], settings: Optional[Dict[str, Any]] = None):
        # Provide default settings if not provided
        if settings is None:
            settings = {
                'crawler': {
                    'timeout_seconds': portal_config.get('request_timeout', 10),
                    'max_retries': 3,
                    'user_agent': 'Mozilla/5.0',
                    'request_delay': 1,
                    'max_pages_per_run': 50
                }
            }
        super().__init__(portal_config, settings)
        self.portal_name = portal_config['name']
    
    def crawl(self):
        """
        Dummy implementation of abstract method - not used for detail crawling
        """
        pass
    
    def crawl_job_details(self, url: str) -> Dict[str, Any]:
        """
        Extract detailed information from a job page
        
        Args:
            url: Full URL of the job page
            
        Returns:
            Dictionary containing detailed job information
        """
        logger.info(f"Crawling job details from: {url}")
        
        html_content = self.fetch_page(url)
        if not html_content:
            logger.error(f"Failed to fetch job details from {url}")
            return {}
        
        soup = self.parse_html(html_content)
        details = self._extract_job_details(soup, url)
        
        return details
    
    def crawl_result_details(self, url: str) -> Dict[str, Any]:
        """
        Extract detailed information from a result page
        
        Args:
            url: Full URL of the result page
            
        Returns:
            Dictionary containing detailed result information
        """
        logger.info(f"Crawling result details from: {url}")
        
        html_content = self.fetch_page(url)
        if not html_content:
            logger.error(f"Failed to fetch result details from {url}")
            return {}
        
        soup = self.parse_html(html_content)
        details = self._extract_result_details(soup, url)
        
        return details
    
    def crawl_admit_card_details(self, url: str) -> Dict[str, Any]:
        """
        Extract detailed information from an admit card page
        
        Args:
            url: Full URL of the admit card page
            
        Returns:
            Dictionary containing detailed admit card information
        """
        logger.info(f"Crawling admit card details from: {url}")
        
        html_content = self.fetch_page(url)
        if not html_content:
            logger.error(f"Failed to fetch admit card details from {url}")
            return {}
        
        soup = self.parse_html(html_content)
        details = self._extract_admit_card_details(soup, url)
        
        return details
    
    def _extract_job_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract structured job information from parsed HTML
        
        Returns dictionary with job details including:
        - full_description
        - important_dates
        - eligibility
        - application_fee
        - how_to_apply
        - important_links
        - key_details (age limit, qualification, etc.)
        """
        details = {
            'url': url,
            'full_description': '',
            'important_dates': {},
            'eligibility': {},
            'application_fee': '',
            'how_to_apply': '',
            'important_links': [],
            'key_details': {},
            'tables': []
        }
        
        # Extract main content area - try multiple selectors
        article = (soup.find('article') or 
                  soup.find('div', class_=['entry-content', 'post-content', 'content']) or
                  soup.find('main') or
                  soup.find('div', id='content') or
                  soup.find('div', class_='site-content'))
        
        if not article:
            logger.warning(f"Could not find main content area for {url}")
            return details
        
        # Extract full description/content - get all text from main content area
        details['full_description'] = article.get_text(separator='\n', strip=True)
        
        # Also try to find specific content div for cleaner text
        content_div = article.find('div', class_=['entry-content', 'post-content', 'content'])
        if content_div:
            # Use content div text if available (usually cleaner)
            content_text = content_div.get_text(separator='\n', strip=True)
            if len(content_text) > len(details['full_description']) * 0.8:  # If similar length, prefer content div
                details['full_description'] = content_text
        
        # Extract all tables (often contain important information)
        tables = article.find_all('table')
        for idx, table in enumerate(tables):
            table_data = self._extract_table_data(table)
            if table_data:
                details['tables'].append({
                    'index': idx,
                    'data': table_data
                })
        
        # Extract all links (download links, official website, etc.)
        links = article.find_all('a', href=True)
        for link in links:
            link_text = link.get_text(strip=True)
            link_url = link.get('href', '')
            
            if link_url and link_text:
                # Skip navigation and internal links
                if not any(skip in link_text.lower() for skip in ['home', 'menu', 'search', 'back to']):
                    details['important_links'].append({
                        'text': link_text,
                        'url': link_url
                    })
        
        # Extract key details from headings and paragraphs
        headings = article.find_all(['h2', 'h3', 'h4', 'strong'])
        for heading in headings:
            heading_text = heading.get_text(strip=True).lower()
            
            # Look for common sections
            if any(keyword in heading_text for keyword in ['important date', 'last date', 'application date']):
                next_element = heading.find_next(['p', 'ul', 'table'])
                if next_element:
                    details['important_dates']['raw'] = next_element.get_text(separator='\n', strip=True)
            
            elif any(keyword in heading_text for keyword in ['eligibility', 'qualification', 'educational']):
                next_element = heading.find_next(['p', 'ul', 'table'])
                if next_element:
                    details['eligibility']['raw'] = next_element.get_text(separator='\n', strip=True)
            
            elif any(keyword in heading_text for keyword in ['application fee', 'fee details']):
                next_element = heading.find_next(['p', 'ul', 'table'])
                if next_element:
                    details['application_fee'] = next_element.get_text(separator='\n', strip=True)
            
            elif any(keyword in heading_text for keyword in ['how to apply', 'application process']):
                next_element = heading.find_next(['p', 'ul', 'ol', 'div'])
                if next_element:
                    details['how_to_apply'] = next_element.get_text(separator='\n', strip=True)
        
        return details
    
    def _extract_result_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed result information"""
        details = {
            'url': url,
            'full_description': '',
            'result_type': '',
            'exam_name': '',
            'result_links': [],
            'cutoff_marks': {},
            'merit_list': [],
            'important_dates': {},
            'tables': []
        }
        
        article = (soup.find('article') or 
                  soup.find('div', class_=['entry-content', 'post-content', 'content']) or
                  soup.find('main') or
                  soup.find('div', id='content') or
                  soup.find('div', class_='site-content'))
        
        if not article:
            return details
        
        # Extract full description from main content
        details['full_description'] = article.get_text(separator='\n', strip=True)
        
        # Extract content from content div if available (usually cleaner)
        content_div = article.find('div', class_=['entry-content', 'post-content'])
        if content_div:
            content_text = content_div.get_text(separator='\n', strip=True)
            if len(content_text) > len(details['full_description']) * 0.8:
                details['full_description'] = content_text
        
        # Extract tables
        tables = article.find_all('table')
        for idx, table in enumerate(tables):
            table_data = self._extract_table_data(table)
            if table_data:
                details['tables'].append({
                    'index': idx,
                    'data': table_data
                })
        
        # Extract download/result links
        links = article.find_all('a', href=True)
        for link in links:
            link_text = link.get_text(strip=True).lower()
            link_url = link.get('href', '')
            
            if any(keyword in link_text for keyword in ['result', 'download', 'pdf', 'merit list', 'cutoff']):
                details['result_links'].append({
                    'text': link.get_text(strip=True),
                    'url': link_url
                })
        
        return details
    
    def _extract_admit_card_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed admit card information"""
        details = {
            'url': url,
            'full_description': '',
            'exam_name': '',
            'exam_date': '',
            'download_links': [],
            'important_instructions': '',
            'exam_centers': [],
            'important_dates': {},
            'tables': []
        }
        
        article = (soup.find('article') or 
                  soup.find('div', class_=['entry-content', 'post-content', 'content']) or
                  soup.find('main') or
                  soup.find('div', id='content') or
                  soup.find('div', class_='site-content'))
        
        if not article:
            return details
        
        # Extract full description from main content
        details['full_description'] = article.get_text(separator='\n', strip=True)
        
        # Extract content from content div if available (usually cleaner)
        content_div = article.find('div', class_=['entry-content', 'post-content'])
        if content_div:
            content_text = content_div.get_text(separator='\n', strip=True)
            if len(content_text) > len(details['full_description']) * 0.8:
                details['full_description'] = content_text
        
        # Extract tables
        tables = article.find_all('table')
        for idx, table in enumerate(tables):
            table_data = self._extract_table_data(table)
            if table_data:
                details['tables'].append({
                    'index': idx,
                    'data': table_data
                })
        
        # Extract download links
        links = article.find_all('a', href=True)
        for link in links:
            link_text = link.get_text(strip=True).lower()
            link_url = link.get('href', '')
            
            if any(keyword in link_text for keyword in ['admit card', 'download', 'hall ticket', 'pdf']):
                details['download_links'].append({
                    'text': link.get_text(strip=True),
                    'url': link_url
                })
        
        return details
    
    def _extract_table_data(self, table) -> List[Dict[str, str]]:
        """
        Extract data from HTML table
        
        Returns list of dictionaries representing table rows
        """
        table_data = []
        
        # Try to find headers
        headers = []
        header_row = table.find('thead')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        else:
            # Check if first row is header
            first_row = table.find('tr')
            if first_row:
                first_row_cells = first_row.find_all(['th', 'td'])
                if first_row.find('th'):
                    headers = [cell.get_text(strip=True) for cell in first_row_cells]
        
        # Extract rows
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # Skip header row if we already extracted headers
            if headers and row.find('th'):
                continue
            
            if cells:
                if headers and len(cells) == len(headers):
                    row_dict = {headers[i]: cells[i].get_text(strip=True) for i in range(len(cells))}
                    table_data.append(row_dict)
                else:
                    # No headers or mismatched columns - use indices
                    row_dict = {f'column_{i}': cell.get_text(strip=True) for i, cell in enumerate(cells)}
                    table_data.append(row_dict)
        
        return table_data
