"""Package initialization for crawler module"""
from .base_crawler import BaseCrawler
from .generic_crawler import GenericCrawler
from .manager import CrawlerManager

__all__ = [
    'BaseCrawler',
    'GenericCrawler',
    'CrawlerManager'
]
