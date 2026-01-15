"""
API routes for fetching detailed information from URLs.
Crawls a URL in real-time and returns complete details.
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from src.crawler.detail_crawler import DetailCrawler
from src.utils import get_config

logger = logging.getLogger("detail_fetcher")
router = APIRouter(tags=["details"])


class DetailFetchRequest(BaseModel):
    """Request body for fetching details from URL."""
    url: str = Field(..., description="Full URL to crawl for details")
    content_type: Optional[str] = Field(
        default="auto",
        description="Type of content: 'job', 'result', 'admit_card', or 'auto' (auto-detect based on content)"
    )
    timeout: Optional[int] = Field(
        default=30,
        description="Request timeout in seconds"
    )


class DetailFetchResponse(BaseModel):
    """Response with detailed information from the URL."""
    success: bool
    url: str
    content_type: str
    details: Dict[str, Any]
    message: Optional[str] = None


def detect_content_type(details: Dict[str, Any]) -> str:
    """
    Auto-detect content type based on extracted details.
    """
    # Check for distinguishing fields
    if "exam_date" in details or "result_date" in details:
        return "result"
    if "admit_card_date" in details or "roll_number" in details:
        return "admit_card"
    # Default to job
    return "job"


def get_detail_crawler() -> DetailCrawler:
    """Initialize DetailCrawler with default portal config."""
    config = get_config("config")
    settings = config.load_settings()
    
    # Use a generic portal config for scraping
    portal_config = {
        "name": "generic",
        "url": "https://sarkariresult.com.cm",
        "request_timeout": settings.get("crawler", {}).get("timeout_seconds", 30),
    }
    
    return DetailCrawler(portal_config, settings)


@router.post(
    "/api/details/fetch",
    response_model=DetailFetchResponse,
    summary="Fetch detailed information from URL",
    description="Crawls a URL in real-time to extract complete information. Useful for enriching jobs, results, or admit cards before publishing."
)
def fetch_details(request: DetailFetchRequest) -> DetailFetchResponse:
    """
    Fetch detailed information from a given URL.
    
    Automatically crawls the URL and extracts:
    - Full description
    - Important dates
    - Requirements
    - How to apply
    - Links and contacts
    
    Perfect for:
    - Fetching missing descriptions for jobs/results
    - Enriching data before publishing to WordPress
    - Getting complete information for analysis
    
    Args:
        request: Object with url and optional content_type
        
    Returns:
        Response with extracted details and metadata
        
    Raises:
        HTTPException: If URL fetch fails or parsing fails
    """
    try:
        crawler = get_detail_crawler()
        
        # Determine content type
        content_type = request.content_type
        
        # Try to crawl based on content type
        details = {}
        if content_type == "job" or content_type == "auto":
            try:
                details = crawler.crawl_job_details(request.url)
                if details and ("full_description" in details or "description" in details):
                    content_type = "job"
                elif content_type == "job":
                    raise ValueError("Failed to extract job details")
            except Exception as e:
                if content_type != "auto":
                    raise
                logger.debug(f"Job extraction failed, trying result: {e}")
        
        if not details and (content_type == "result" or content_type == "auto"):
            try:
                details = crawler.crawl_result_details(request.url)
                if details and ("full_description" in details or "description" in details):
                    content_type = "result"
                elif content_type == "result":
                    raise ValueError("Failed to extract result details")
            except Exception as e:
                if content_type != "auto":
                    raise
                logger.debug(f"Result extraction failed, trying admit_card: {e}")
        
        if not details and (content_type == "admit_card" or content_type == "auto"):
            try:
                details = crawler.crawl_admit_card_details(request.url)
                if details and ("full_description" in details or "description" in details):
                    content_type = "admit_card"
                elif content_type == "admit_card":
                    raise ValueError("Failed to extract admit_card details")
            except Exception as e:
                if content_type != "auto":
                    raise
                raise ValueError(f"Could not extract details from {request.url}: {e}")
        
        if not details:
            raise HTTPException(
                status_code=400,
                detail=f"Could not extract details from URL: {request.url}"
            )
        
        return DetailFetchResponse(
            success=True,
            url=request.url,
            content_type=content_type,
            details=details,
            message="Details fetched successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching details from {request.url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch details: {str(e)}"
        )


@router.get(
    "/api/details/fetch",
    response_model=DetailFetchResponse,
    summary="Fetch detailed information from URL (GET)",
    description="GET variant for fetching details. Simpler for direct URL access."
)
def fetch_details_get(
    url: str = Query(..., description="Full URL to crawl"),
    content_type: Optional[str] = Query(
        default="auto",
        description="Type: job, result, admit_card, or auto"
    ),
    timeout: Optional[int] = Query(default=30)
) -> DetailFetchResponse:
    """
    GET endpoint to fetch details from a URL.
    
    Query Parameters:
    - url: The URL to crawl
    - content_type: 'job', 'result', 'admit_card', or 'auto'
    - timeout: Request timeout in seconds
    
    Example:
    GET /api/details/fetch?url=https://example.com/job/123&content_type=job
    """
    request = DetailFetchRequest(
        url=url,
        content_type=content_type or "auto",
        timeout=timeout
    )
    return fetch_details(request)


@router.post(
    "/api/details/batch",
    summary="Fetch details for multiple URLs",
    description="Fetch details for multiple URLs in one request."
)
def fetch_details_batch(
    urls: list[str] = Query(..., description="List of URLs to crawl"),
    content_type: Optional[str] = Query(default="auto")
) -> Dict[str, Any]:
    """
    Fetch details for multiple URLs at once.
    
    Args:
        urls: List of URLs
        content_type: Content type hint for all URLs
        
    Returns:
        Dictionary mapping URL to DetailFetchResponse
    """
    results = {}
    for url in urls:
        request = DetailFetchRequest(url=url, content_type=content_type or "auto")
        try:
            result = fetch_details(request)
            results[url] = result.dict()
        except HTTPException as e:
            results[url] = {
                "success": False,
                "url": url,
                "error": e.detail
            }
    
    return {
        "total": len(urls),
        "successful": sum(1 for r in results.values() if r.get("success", False)),
        "results": results
    }
