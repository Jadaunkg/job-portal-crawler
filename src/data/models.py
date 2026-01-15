"""
Data Models for Job Crawler System

This module defines all data models used across the crawler system.
Each model is implemented as a dataclass for type safety and validation.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EntryStatus(Enum):
    """Status of a job/result/admit card entry"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CrawlStatus(Enum):
    """Status of a crawl execution"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


@dataclass
class JobEntry:
    """
    Model for a job posting entry
    """
    id: str
    portal_name: str
    title: str
    organization: str
    url: str
    discovered_at: str
    post_date: Optional[str] = None
    last_date: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: str = EntryStatus.ACTIVE.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    detailed_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobEntry':
        """Create instance from dictionary"""
        return cls(**data)
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.id:
            raise ValueError("Job entry must have an ID")
        if not self.title:
            raise ValueError("Job entry must have a title")
        if not self.url:
            raise ValueError("Job entry must have a URL")


@dataclass
class ResultEntry:
    """
    Model for an exam/test result entry
    """
    id: str
    portal_name: str
    title: str
    organization: str
    url: str
    discovered_at: str
    result_date: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    detailed_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultEntry':
        """Create instance from dictionary"""
        return cls(**data)
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.id:
            raise ValueError("Result entry must have an ID")
        if not self.title:
            raise ValueError("Result entry must have a title")


@dataclass
class AdmitCardEntry:
    """
    Model for an admit card entry
    """
    id: str
    portal_name: str
    title: str
    organization: str
    url: str
    discovered_at: str
    exam_date: Optional[str] = None
    download_start: Optional[str] = None
    download_end: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    detailed_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdmitCardEntry':
        """Create instance from dictionary"""
        return cls(**data)
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.id:
            raise ValueError("Admit card entry must have an ID")
        if not self.title:
            raise ValueError("Admit card entry must have a title")


@dataclass
class NotificationEntry:
    """
    Model for other notification entries
    """
    id: str
    portal_name: str
    title: str
    url: str
    discovered_at: str
    notification_type: str = "general"
    organization: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationEntry':
        """Create instance from dictionary"""
        return cls(**data)


@dataclass
class CrawlHistory:
    """
    Model for tracking crawler execution history
    """
    id: str
    portal_name: str
    crawl_time: str
    status: str
    items_found: int = 0
    new_items: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    categories_crawled: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlHistory':
        """Create instance from dictionary"""
        return cls(**data)


@dataclass
class CrawlerStats:
    """
    Statistics for a crawler execution
    """
    portal_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = CrawlStatus.SUCCESS.value
    jobs_found: int = 0
    results_found: int = 0
    admit_cards_found: int = 0
    notifications_found: int = 0
    new_entries: int = 0
    errors: list = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """Calculate duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def total_items(self) -> int:
        """Total items found"""
        return (self.jobs_found + self.results_found + 
                self.admit_cards_found + self.notifications_found)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'portal_name': self.portal_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'jobs_found': self.jobs_found,
            'results_found': self.results_found,
            'admit_cards_found': self.admit_cards_found,
            'notifications_found': self.notifications_found,
            'new_entries': self.new_entries,
            'total_items': self.total_items,
            'duration_seconds': self.duration,
            'errors': self.errors
        }


def generate_timestamp() -> str:
    """
    Generate ISO format timestamp string
    
    Returns:
        str: Current timestamp in ISO format
    """
    return datetime.now().isoformat()


def generate_entry_id(title: str, organization: str, portal: str) -> str:
    """
    Generate a unique ID for an entry based on key fields
    
    Args:
        title: Entry title
        organization: Organization name
        portal: Portal name
    
    Returns:
        str: MD5 hash as unique identifier
    """
    import hashlib
    unique_string = f"{title}_{organization}_{portal}".lower()
    return hashlib.md5(unique_string.encode()).hexdigest()
