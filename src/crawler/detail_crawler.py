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
            'links': [],
            'key_details': {},
            'tables': [],
            'sections': {},
            'raw_html': ''
        }
        
        # Select main content using robust strategy
        article = self._select_main_content(soup, url)
        
        if not article:
            logger.error(f"Could not find any content area for {url}")
            return details
        
        # Store raw HTML for debugging
        details['raw_html'] = str(article)[:5000]  # First 5000 chars
        
        # Extract full description - comprehensive text extraction
        details['full_description'] = self._extract_clean_text(article)
        
        # Extract sections by headings - comprehensive approach
        details['sections'] = self._extract_sections_by_headings(article)
        
        # Extract all tables (often contain important information)
        tables = article.find_all('table')
        for idx, table in enumerate(tables):
            table_data = self._extract_table_data(table)
            if table_data:
                table_html = str(table)[:1000]  # Store HTML snippet
                details['tables'].append({
                    'index': idx,
                    'headers': list(table_data[0].keys()) if table_data else [],
                    'rows': table_data,
                    'row_count': len(table_data),
                    'html_preview': table_html
                })
        # Global table fallback if none found in article
        if not details['tables']:
            global_tables = soup.find_all('table')
            for idx, table in enumerate(global_tables):
                table_data = self._extract_table_data(table)
                if table_data:
                    details['tables'].append({
                        'index': idx,
                        'headers': list(table_data[0].keys()) if table_data else [],
                        'rows': table_data,
                        'row_count': len(table_data)
                    })
        
        # Extract all links (download links, official website, etc.)
        seen_urls = set()
        links = article.find_all('a', href=True)
        for link in links:
            link_text = link.get_text(strip=True)
            link_url = link.get('href', '').strip()
            
            # Skip empty, duplicates, and navigation links
            if not link_url or link_url in seen_urls:
                continue
            if not link_text or len(link_text) < 2:
                continue
            if link_url.startswith('#') or link_url.startswith('javascript:'):
                continue
            if any(skip in link_text.lower() for skip in ['home', 'menu', 'search', 'back to', 'previous', 'next']):
                continue
            
            seen_urls.add(link_url)
            details['important_links'].append({
                'text': link_text,
                'url': link_url
            })

        # Unified links field for consistency
        details['links'] = list(details['important_links'])
        
        # Extract structured information from sections
        self._parse_structured_data(details)
        
        return details
    
    def _extract_clean_text(self, element) -> str:
        """Extract clean, readable text from HTML element"""
        # Get all text with newline separators
        text = element.get_text(separator='\n', strip=True)
        
        # Clean up multiple newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def _extract_sections_by_headings(self, article) -> Dict[str, str]:
        """Extract content organized by section headings"""
        sections = {}
        
        # Find all headings
        headings = article.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
        
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            
            # Skip short headings (likely not section titles)
            if len(heading_text) < 3:
                continue
            
            # Extract content after heading until next heading
            content_parts = []
            for sibling in heading.find_next_siblings():
                # Stop at next heading
                if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                # Collect text from this element
                text = sibling.get_text(separator='\n', strip=True)
                if text:
                    content_parts.append(text)
            
            if content_parts:
                sections[heading_text] = '\n'.join(content_parts)
        
        return sections
    
    def _parse_structured_data(self, details: Dict[str, Any]):
        """Parse structured information from sections and populate specific fields"""
        sections = details.get('sections', {})
        
        # Parse important dates
        for heading, content in sections.items():
            heading_lower = heading.lower()
            
            if any(keyword in heading_lower for keyword in ['important date', 'last date', 'application date', 'key date']):
                details['important_dates'][heading] = content
                
            elif any(keyword in heading_lower for keyword in ['eligibility', 'qualification', 'educational', 'age limit']):
                details['eligibility'][heading] = content
                
            elif any(keyword in heading_lower for keyword in ['application fee', 'fee details', 'exam fee']):
                if not details['application_fee']:
                    details['application_fee'] = content
                else:
                    details['application_fee'] += '\n' + content
                    
            elif any(keyword in heading_lower for keyword in ['how to apply', 'application process', 'application procedure']):
                if not details['how_to_apply']:
                    details['how_to_apply'] = content
                else:
                    details['how_to_apply'] += '\n' + content
                    
            elif any(keyword in heading_lower for keyword in ['vacancy', 'post details', 'posts', 'positions']):
                details['key_details'][heading] = content
                
            elif any(keyword in heading_lower for keyword in ['selection', 'exam pattern', 'syllabus']):
                details['key_details'][heading] = content
        
        # If no structured dates found, try to extract from full description
        if not details['important_dates']:
            self._extract_dates_from_text(details)
    
    def _extract_dates_from_text(self, details: Dict[str, Any]):
        """Extract date information from text using patterns"""
        import re
        text = details.get('full_description', '')
        
        # Common date patterns
        date_patterns = [
            r'Last Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'Application (?:Start|Begin)[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'Application End[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'Exam Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                key = pattern.split('[')[0].strip()
                details['important_dates'][key] = matches[0]
        
        return details
    
    def _extract_result_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed result information"""
        details = {
            'url': url,
            'full_description': '',
            'result_type': '',
            'exam_name': '',
            'result_links': [],
            'important_links': [],
            'links': [],
            'cutoff_marks': {},
            'merit_list': [],
            'important_dates': {},
            'tables': [],
            'sections': {}
        }
        
        # Use same powerful content detection as jobs
        article = self._select_main_content(soup, url)
        if not article:
            return details
        
        # Extract full description
        details['full_description'] = self._extract_clean_text(article)
        
        # Extract sections
        details['sections'] = self._extract_sections_by_headings(article)
        
        # Extract tables
        tables = article.find_all('table')
        for idx, table in enumerate(tables):
            table_data = self._extract_table_data(table)
            if table_data:
                details['tables'].append({
                    'index': idx,
                    'headers': list(table_data[0].keys()) if table_data else [],
                    'rows': table_data,
                    'row_count': len(table_data)
                })
        if not details['tables']:
            for idx, table in enumerate(soup.find_all('table')):
                table_data = self._extract_table_data(table)
                if table_data:
                    details['tables'].append({
                        'index': idx,
                        'headers': list(table_data[0].keys()) if table_data else [],
                        'rows': table_data,
                        'row_count': len(table_data)
                    })
        
        # Extract download/result links (broadened heuristics)
        seen_urls = set()
        links = article.find_all('a', href=True)
        for link in links:
            link_text_full = link.get_text(strip=True)
            link_text = link_text_full.lower()
            link_url = link.get('href', '').strip()

            if not link_url or link_url in seen_urls:
                continue

            # Skip anchors with no meaningful text and no meaningful href
            if not link_text_full and not link_url:
                continue

            href_lower = link_url.lower()

            text_keywords = [
                'result', 'download', 'pdf', 'merit', 'list', 'cutoff', 'answer key',
                'click here', 'here', 'view', 'check', 'score', 'marks'
            ]
            href_keywords = [
                'pdf', 'download', 'wp-content/uploads', 'drive.google.com', 'docs.google.com',
                '/result', '/results', 'scorecard', 'mark', 'merit', 'list', 'cutoff'
            ]

            is_match = (
                any(k in link_text for k in text_keywords) or
                any(k in href_lower for k in href_keywords)
            )

            if is_match:
                seen_urls.add(link_url)
                details['result_links'].append({
                    'text': link_text_full,
                    'url': link_url
                })

        # Also collect general anchors as important_links (similar to jobs)
        general_seen = set(l['url'] for l in details['result_links'])
        for link in article.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            link_url = link.get('href', '').strip()
            if not link_url or link_url in general_seen:
                continue
            if not link_text or len(link_text) < 2:
                continue
            if link_url.startswith('#') or link_url.startswith('javascript:'):
                continue
            if any(skip in link_text.lower() for skip in ['home', 'menu', 'search', 'back to', 'previous', 'next']):
                continue
            general_seen.add(link_url)
            details['important_links'].append({'text': link_text, 'url': link_url})

        # Unified links union (dedupe by URL)
        combined = {}
        for link in details['result_links'] + details['important_links']:
            combined[link['url']] = link
        details['links'] = list(combined.values())
        
        return details
    
    def _extract_admit_card_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed admit card information"""
        details = {
            'url': url,
            'full_description': '',
            'exam_name': '',
            'exam_date': '',
            'download_links': [],
            'important_links': [],
            'links': [],
            'important_instructions': '',
            'exam_centers': [],
            'important_dates': {},
            'tables': [],
            'sections': {}
        }
        
        # Use same powerful content detection
        article = self._select_main_content(soup, url)
        if not article:
            return details
        
        # Extract full description
        details['full_description'] = self._extract_clean_text(article)
        
        # Extract sections
        details['sections'] = self._extract_sections_by_headings(article)
        
        # Extract tables
        tables = article.find_all('table')
        for idx, table in enumerate(tables):
            table_data = self._extract_table_data(table)
            if table_data:
                details['tables'].append({
                    'index': idx,
                    'headers': list(table_data[0].keys()) if table_data else [],
                    'rows': table_data,
                    'row_count': len(table_data)
                })
        if not details['tables']:
            for idx, table in enumerate(soup.find_all('table')):
                table_data = self._extract_table_data(table)
                if table_data:
                    details['tables'].append({
                        'index': idx,
                        'headers': list(table_data[0].keys()) if table_data else [],
                        'rows': table_data,
                        'row_count': len(table_data)
                    })
        
        # Extract download links with broadened heuristics (similar to results)
        seen_urls = set()
        links = article.find_all('a', href=True)
        for link in links:
            link_text_full = link.get_text(strip=True)
            link_text = link_text_full.lower()
            link_url = link.get('href', '').strip()

            if not link_url or link_url in seen_urls:
                continue

            href_lower = link_url.lower()
            text_keywords = [
                'admit card', 'download', 'hall ticket', 'pdf', 'call letter',
                'click here', 'here', 'view', 'check'
            ]
            href_keywords = [
                'pdf', 'download', 'wp-content/uploads', 'drive.google.com', 'docs.google.com',
                'admit', 'hall', 'ticket', 'call-letter'
            ]

            is_match = (
                any(k in link_text for k in text_keywords) or
                any(k in href_lower for k in href_keywords)
            )
            if is_match:
                seen_urls.add(link_url)
                details['download_links'].append({
                    'text': link_text_full,
                    'url': link_url
                })

        # Always include general anchors as important_links (not only fallback)
        general_seen = set(l['url'] for l in details['download_links'])
        for link in article.find_all('a', href=True):
            link_text_full = link.get_text(strip=True)
            link_url = link.get('href', '').strip()
            if link_url and link_text_full and link_url not in general_seen:
                if not (link_url.startswith('#') or link_url.startswith('javascript:')):
                    general_seen.add(link_url)
                    details['important_links'].append({
                        'text': link_text_full,
                        'url': link_url
                    })

        # Unified links union (dedupe by URL)
        combined = {}
        for link in details['download_links'] + details['important_links']:
            combined[link['url']] = link
        details['links'] = list(combined.values())
        
        return details

    def _select_main_content(self, soup: BeautifulSoup, url: str):
        """Robustly select the main content region from a page."""
        content_selectors = [
            ('div', {'class': 'site-content'}),
            ('div', {'class': 'content-area'}),
            ('article', {}),
            ('div', {'class': 'entry-content'}),
            ('div', {'class': 'post-content'}),
            ('main', {}),
            ('div', {'id': 'content'}),
        ]
        for tag, attrs in content_selectors:
            candidate = soup.find(tag, attrs) if attrs else soup.find(tag)
            if candidate and len(candidate.get_text(strip=True)) > 300:
                return candidate
        # Keyword class selection, choose largest
        candidates = []
        for div in soup.find_all('div'):
            div_class = ' '.join(div.get('class', [])).lower()
            if any(k in div_class for k in ['content', 'post', 'article', 'entry']):
                tlen = len(div.get_text(strip=True))
                if tlen > 300:
                    candidates.append((tlen, div))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        # Fallback to body cleaned
        body = soup.find('body')
        if body:
            for tag in body.find_all(['header', 'footer', 'nav', 'aside']):
                tag.decompose()
            return body
        return None
    
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
