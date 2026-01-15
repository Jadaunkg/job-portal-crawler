"""
Exam Results API endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from .schemas import (
    ResultResponseSchema, PaginatedResultResponse,
    SearchResultRequest
)
from .database import ApiDatabase

router = APIRouter(prefix="/results", tags=["Results"])
db = ApiDatabase()


@router.get(
    "",
    response_model=PaginatedResultResponse,
    summary="List all results",
    description="Retrieve paginated list of all exam results"
)
def list_results(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get paginated list of all exam results.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `limit`: Items per page, max 100 (default: 10)
    """
    results, total = db.get_all_results(page=page, limit=limit)
    total_pages = (total + limit - 1) // limit
    
    return PaginatedResultResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=results
    )


@router.get(
    "/{result_id}",
    response_model=ResultResponseSchema,
    summary="Get result by ID",
    description="Retrieve information for a specific exam result"
)
def get_result(result_id: str):
    """
    Get a specific exam result by ID.
    
    **Path Parameters:**
    - `result_id`: Unique result identifier
    """
    result = db.get_result_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Result with ID '{result_id}' not found")
    return result


@router.get(
    "/{result_id}/details",
    response_model=ResultResponseSchema,
    summary="Get result with extracted details",
    description="Retrieve result with comprehensive extracted page information"
)
def get_result_details(result_id: str):
    """
    Get exam result with extracted details.
    
    **Path Parameters:**
    - `result_id`: Unique result identifier
    
    **Note:** Details are only available if the detail crawler has been run for this result.
    """
    result = db.get_result_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Result with ID '{result_id}' not found")
    
    if not result.get('detailed_info'):
        raise HTTPException(
            status_code=206,
            detail="Details not yet crawled for this result. Run detail crawler first."
        )
    
    return result


@router.post(
    "/search",
    response_model=PaginatedResultResponse,
    summary="Search results",
    description="Search and filter exam results with multiple criteria"
)
def search_results(request: SearchResultRequest):
    """
    Search exam results with filters.
    
    **Request Body:**
    - `keyword`: Search in title
    - `portal`: Filter by portal name
    - `start_date`: Filter from date (YYYY-MM-DD)
    - `end_date`: Filter to date (YYYY-MM-DD)
    - `details_only`: Show only items with details crawled
    - `page`: Page number
    - `limit`: Items per page
    
    **Example:**
    ```json
    {
        "keyword": "IBPS",
        "portal": "sarkari_result",
        "page": 1,
        "limit": 10
    }
    ```
    """
    results, total = db.search_results(
        keyword=request.keyword,
        portal=request.portal,
        start_date=request.start_date,
        end_date=request.end_date,
        details_only=request.details_only,
        page=request.page,
        limit=request.limit
    )
    
    total_pages = (total + request.limit - 1) // request.limit
    
    return PaginatedResultResponse(
        total=total,
        page=request.page,
        limit=request.limit,
        total_pages=total_pages,
        items=results
    )


@router.get(
    "/filter/by-portal/{portal}",
    response_model=PaginatedResultResponse,
    summary="Get results by portal",
    description="Retrieve results from a specific portal"
)
def get_results_by_portal(
    portal: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get results from a specific portal.
    
    **Path Parameters:**
    - `portal`: Portal name
    
    **Query Parameters:**
    - `page`: Page number
    - `limit`: Items per page
    """
    results, total = db.search_results(
        portal=portal,
        page=page,
        limit=limit
    )
    
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No results found for portal '{portal}'")
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedResultResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=results
    )


@router.get(
    "/filter/with-details",
    response_model=PaginatedResultResponse,
    summary="Get results with details crawled",
    description="Retrieve only results with detailed information"
)
def get_results_with_details(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get only results with details crawled.
    
    **Query Parameters:**
    - `page`: Page number
    - `limit`: Items per page
    """
    results, total = db.search_results(
        details_only=True,
        page=page,
        limit=limit
    )
    
    if total == 0:
        raise HTTPException(status_code=404, detail="No results with details crawled found")
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedResultResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=results
    )
