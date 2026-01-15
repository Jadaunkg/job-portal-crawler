"""
Helper Utilities

Common utility functions used across the crawler system.
"""

import re
import time
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urljoin, urlparse


def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Input text
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_date(text: str, formats: Optional[list] = None) -> Optional[str]:
    """
    Extract and normalize date from text
    
    Args:
        text: Text containing date
        formats: List of date formats to try
    
    Returns:
        ISO format date string or None
    """
    if not text:
        return None
    
    if formats is None:
        formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%d %b %Y',
            '%B %d, %Y',
        ]
    
    text = clean_text(text)
    
    for fmt in formats:
        try:
            date_obj = datetime.strptime(text, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize and complete URL
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
    
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # If relative URL and base_url provided, make it absolute
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    return url


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                    backoff: float = 2.0, exceptions: tuple = (Exception,)) -> Callable:
    """
    Decorator for retrying function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator


def time_execution(func: Callable) -> Callable:
    """
    Decorator to measure function execution time
    
    Args:
        func: Function to measure
    
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Store execution time in result if it's a dict
        if isinstance(result, dict):
            result['_execution_time'] = execution_time
        
        return result
    
    return wrapper


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def get_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: URL
    
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


def is_expired(date_str: str, date_format: str = '%Y-%m-%d') -> bool:
    """
    Check if a date has expired
    
    Args:
        date_str: Date string
        date_format: Format of the date string
    
    Returns:
        True if expired, False otherwise
    """
    try:
        date_obj = datetime.strptime(date_str, date_format)
        return date_obj.date() < datetime.now().date()
    except Exception:
        return False


def days_until(date_str: str, date_format: str = '%Y-%m-%d') -> Optional[int]:
    """
    Calculate days until a date
    
    Args:
        date_str: Date string
        date_format: Format of the date string
    
    Returns:
        Number of days (negative if past) or None if invalid
    """
    try:
        date_obj = datetime.strptime(date_str, date_format)
        delta = date_obj.date() - datetime.now().date()
        return delta.days
    except Exception:
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Filename to sanitize
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename
