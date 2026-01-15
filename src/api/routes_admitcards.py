"""
Admit Cards API endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from .schemas import (
    AdmitCardResponseSchema, PaginatedAdmitCardResponse,
    SearchAdmitCardRequest
)
from .database import ApiDatabase

router = APIRouter(prefix="/admit-cards", tags=["Admit Cards"])
db = ApiDatabase()


@router.get(
    "",
    response_model=PaginatedAdmitCardResponse,
    summary="List all admit cards",
    description="Retrieve paginated list of all admit cards"
)
def list_admit_cards(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get paginated list of all admit cards.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `limit`: Items per page, max 100 (default: 10)
    """
    cards, total = db.get_all_admit_cards(page=page, limit=limit)
    total_pages = (total + limit - 1) // limit
    
    return PaginatedAdmitCardResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=cards
    )


@router.get(
    "/{card_id}",
    response_model=AdmitCardResponseSchema,
    summary="Get admit card by ID",
    description="Retrieve information for a specific admit card"
)
def get_admit_card(card_id: str):
    """
    Get a specific admit card by ID.
    
    **Path Parameters:**
    - `card_id`: Unique admit card identifier
    """
    card = db.get_admit_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Admit card with ID '{card_id}' not found")
    return card


@router.get(
    "/{card_id}/details",
    response_model=AdmitCardResponseSchema,
    summary="Get admit card with extracted details",
    description="Retrieve admit card with comprehensive extracted page information"
)
def get_admit_card_details(card_id: str):
    """
    Get admit card with extracted details.
    
    **Path Parameters:**
    - `card_id`: Unique admit card identifier
    
    **Note:** Details are only available if the detail crawler has been run for this card.
    """
    card = db.get_admit_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Admit card with ID '{card_id}' not found")
    
    if not card.get('detailed_info'):
        raise HTTPException(
            status_code=206,
            detail="Details not yet crawled for this admit card. Run detail crawler first."
        )
    
    return card


@router.post(
    "/search",
    response_model=PaginatedAdmitCardResponse,
    summary="Search admit cards",
    description="Search and filter admit cards with multiple criteria"
)
def search_admit_cards(request: SearchAdmitCardRequest):
    """
    Search admit cards with filters.
    
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
        "keyword": "BPSC",
        "portal": "sarkari_result",
        "page": 1,
        "limit": 10
    }
    ```
    """
    cards, total = db.search_admit_cards(
        keyword=request.keyword,
        portal=request.portal,
        start_date=request.start_date,
        end_date=request.end_date,
        details_only=request.details_only,
        page=request.page,
        limit=request.limit
    )
    
    total_pages = (total + request.limit - 1) // request.limit
    
    return PaginatedAdmitCardResponse(
        total=total,
        page=request.page,
        limit=request.limit,
        total_pages=total_pages,
        items=cards
    )


@router.get(
    "/filter/by-portal/{portal}",
    response_model=PaginatedAdmitCardResponse,
    summary="Get admit cards by portal",
    description="Retrieve admit cards from a specific portal"
)
def get_admit_cards_by_portal(
    portal: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get admit cards from a specific portal.
    
    **Path Parameters:**
    - `portal`: Portal name
    
    **Query Parameters:**
    - `page`: Page number
    - `limit`: Items per page
    """
    cards, total = db.search_admit_cards(
        portal=portal,
        page=page,
        limit=limit
    )
    
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No admit cards found for portal '{portal}'")
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedAdmitCardResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=cards
    )


@router.get(
    "/filter/with-details",
    response_model=PaginatedAdmitCardResponse,
    summary="Get admit cards with details crawled",
    description="Retrieve only admit cards with detailed information"
)
def get_admit_cards_with_details(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get only admit cards with details crawled.
    
    **Query Parameters:**
    - `page`: Page number
    - `limit`: Items per page
    """
    cards, total = db.search_admit_cards(
        details_only=True,
        page=page,
        limit=limit
    )
    
    if total == 0:
        raise HTTPException(status_code=404, detail="No admit cards with details crawled found")
    
    total_pages = (total + limit - 1) // limit
    
    return PaginatedAdmitCardResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=cards
    )
