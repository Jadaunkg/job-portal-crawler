"""
Job-related API endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from .schemas import (
    JobResponseSchema, PaginatedJobResponse, 
    SearchJobRequest, ApiErrorResponse
)
from .database import ApiDatabase

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
db = ApiDatabase()


@router.get(
    "",
    response_model=PaginatedJobResponse,
    summary="List all jobs",
    description="Retrieve paginated list of all jobs with metadata"
)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get paginated list of all jobs.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `limit`: Items per page, max 100 (default: 10)
    """
    jobs, total = db.get_all_jobs(page=page, limit=limit)
    total_pages = (total + limit - 1) // limit
    
    return PaginatedJobResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=jobs
    )


@router.get(
    "/{job_id}",
    response_model=JobResponseSchema,
    summary="Get job by ID",
    description="Retrieve detailed information for a specific job"
)
def get_job(job_id: str):
    """
    Get a specific job by ID.
    
    **Path Parameters:**
    - `job_id`: Unique job identifier
    """
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found")
    return job


@router.get(
    "/{job_id}/details",
    response_model=JobResponseSchema,
    summary="Get job with extracted details",
    description="Retrieve job with comprehensive extracted page information"
)
def get_job_details(job_id: str):
    """
    Get job with extracted details from the job posting page.
    
    **Path Parameters:**
    - `job_id`: Unique job identifier
    
    **Note:** Details are only available if the detail crawler has been run for this job.
    """
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found")
    
    if not job.get('detailed_info'):
        raise HTTPException(
            status_code=206,
            detail="Details not yet crawled for this job. Run detail crawler first."
        )
    
    return job


@router.post(
    "/search",
    response_model=PaginatedJobResponse,
    summary="Search jobs",
    description="Search and filter jobs with multiple criteria"
)
def search_jobs(request: SearchJobRequest):
    """
    Search jobs with filters.
    
    **Request Body:**
    - `keyword`: Search in title (substring match)
    - `portal`: Filter by portal name
    - `start_date`: Filter from date (YYYY-MM-DD)
    - `end_date`: Filter to date (YYYY-MM-DD)
    - `details_only`: Show only items with details crawled
    - `page`: Page number
    - `limit`: Items per page
    
    **Example:**
    ```json
    {
        "keyword": "RBI",
        "portal": "sarkari_result",
        "details_only": false,
        "page": 1,
        "limit": 10
    }
    ```
    """
    jobs, total = db.search_jobs(
        keyword=request.keyword,
        portal=request.portal,
        start_date=request.start_date,
        end_date=request.end_date,
        details_only=request.details_only,
        page=request.page,
        limit=request.limit
    )
    
    total_pages = (total + request.limit - 1) // request.limit
    
    return PaginatedJobResponse(
        total=total,
        page=request.page,
        limit=request.limit,
        total_pages=total_pages,
        items=jobs
    )


@router.get(
    "/filter/by-portal/{portal}",
    response_model=PaginatedJobResponse,
    summary="Get jobs by portal",
    description="Retrieve jobs from a specific portal"
)
def get_jobs_by_portal(
    portal: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get jobs from a specific portal.
    
    **Path Parameters:**
    - `portal`: Portal name (e.g., 'sarkari_result')
    
    **Query Parameters:**
    - `page`: Page number
    - `limit`: Items per page
    """
    jobs, total = db.search_jobs(
        portal=portal,
        page=page,
        limit=limit
    )
    
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No jobs found for portal '{portal}'")
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedJobResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=jobs
    )


@router.get(
    "/filter/with-details",
    response_model=PaginatedJobResponse,
    summary="Get jobs with details crawled",
    description="Retrieve only jobs that have detailed information extracted"
)
def get_jobs_with_details(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get only jobs that have details crawled.
    
    **Query Parameters:**
    - `page`: Page number
    - `limit`: Items per page
    """
    jobs, total = db.search_jobs(
        details_only=True,
        page=page,
        limit=limit
    )
    
    if total == 0:
        raise HTTPException(status_code=404, detail="No jobs with details crawled found")
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedJobResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=jobs
    )
