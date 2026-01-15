"""
Pydantic schemas for API request/response validation.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==================== Base Response Models ====================

class DetailedInfoSchema(BaseModel):
    """Schema for detailed_info extracted from pages."""
    model_config = ConfigDict(extra="allow", validate_assignment=True)
    
    description: Optional[str] = None
    tables: Optional[List[Dict[str, Any]]] = None
    links: Optional[Dict[str, Any]] = None
    eligibility: Optional[str] = None
    application_fee: Optional[str] = None
    important_dates: Optional[str] = None
    age_limits: Optional[str] = None
    total_posts: Optional[str] = None
    vacancy_details: Optional[Dict[str, Any]] = None


class JobResponseSchema(BaseModel):
    """Schema for Job response."""
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    
    id: str
    title: Optional[str] = None
    posted_date: Optional[str] = None
    url: Optional[str] = None
    portal: Optional[str] = None
    scraped_at: Optional[str] = None
    details_crawled: bool = False
    detailed_info: Optional[Dict[str, Any]] = None


class ResultResponseSchema(BaseModel):
    """Schema for Exam Result response."""
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    
    id: str
    title: Optional[str] = None
    posted_date: Optional[str] = None
    url: Optional[str] = None
    portal: Optional[str] = None
    scraped_at: Optional[str] = None
    details_crawled: bool = False
    detailed_info: Optional[Dict[str, Any]] = None


class AdmitCardResponseSchema(BaseModel):
    """Schema for Admit Card response."""
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    
    id: str
    title: Optional[str] = None
    posted_date: Optional[str] = None
    url: Optional[str] = None
    portal: Optional[str] = None
    scraped_at: Optional[str] = None
    details_crawled: bool = False
    detailed_info: Optional[Dict[str, Any]] = None


# ==================== Pagination Response Models ====================

class PaginatedJobResponse(BaseModel):
    """Paginated job list response."""
    total: int
    page: int
    limit: int
    total_pages: int
    items: List[JobResponseSchema]

    class Config:
        from_attributes = True


class PaginatedResultResponse(BaseModel):
    """Paginated result list response."""
    total: int
    page: int
    limit: int
    total_pages: int
    items: List[ResultResponseSchema]

    class Config:
        from_attributes = True


class PaginatedAdmitCardResponse(BaseModel):
    """Paginated admit card list response."""
    total: int
    page: int
    limit: int
    total_pages: int
    items: List[AdmitCardResponseSchema]

    class Config:
        from_attributes = True


# ==================== Search/Filter Request Models ====================

class SearchJobRequest(BaseModel):
    """Request model for job search."""
    keyword: Optional[str] = Field(None, description="Search keyword in title or description")
    portal: Optional[str] = Field(None, description="Filter by portal name")
    start_date: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    details_only: Optional[bool] = Field(False, description="Show only items with details crawled")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")


class SearchResultRequest(BaseModel):
    """Request model for result search."""
    keyword: Optional[str] = Field(None, description="Search keyword in title or description")
    portal: Optional[str] = Field(None, description="Filter by portal name")
    start_date: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    details_only: Optional[bool] = Field(False, description="Show only items with details crawled")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")


class SearchAdmitCardRequest(BaseModel):
    """Request model for admit card search."""
    keyword: Optional[str] = Field(None, description="Search keyword in title or description")
    portal: Optional[str] = Field(None, description="Filter by portal name")
    start_date: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    details_only: Optional[bool] = Field(False, description="Show only items with details crawled")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")


# ==================== API Response Models ====================

class ApiSuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ApiErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class StatsResponse(BaseModel):
    """API statistics response."""
    total_jobs: int
    total_results: int
    total_admit_cards: int
    jobs_with_details: int
    results_with_details: int
    admit_cards_with_details: int
    last_crawl_time: Optional[str]
    database_size_mb: float


class PortalStatsResponse(BaseModel):
    """Per-portal statistics."""
    portal: str
    job_count: int
    result_count: int
    admit_card_count: int


class StatusResponse(BaseModel):
    """API health and status response."""
    status: str
    version: str
    uptime_seconds: float
    total_requests: int
    database_connected: bool
    last_updated: str
