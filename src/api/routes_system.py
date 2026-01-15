"""
System health and statistics endpoints.
"""
from fastapi import APIRouter
from datetime import datetime
import time
from typing import Dict, Any

from .schemas import StatusResponse, StatsResponse, PortalStatsResponse
from .database import ApiDatabase

router = APIRouter(prefix="/api", tags=["System"])
db = ApiDatabase()

# Track API startup time
api_start_time = time.time()
total_requests = 0


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="API health check",
    description="Get API status and health information"
)
def get_status():
    """
    Check API status and uptime.
    
    **Returns:**
    - `status`: "operational" if all systems working
    - `version`: API version
    - `uptime_seconds`: Time since API started
    - `total_requests`: Total requests served
    - `database_connected`: Whether database is accessible
    - `last_updated`: Last crawl timestamp
    """
    global total_requests
    total_requests += 1
    
    uptime = time.time() - api_start_time
    stats = db.get_stats()
    
    return StatusResponse(
        status="operational",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        total_requests=total_requests,
        database_connected=True,
        last_updated=stats.get('last_crawl_time', 'Never')
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Database statistics",
    description="Get comprehensive database statistics"
)
def get_stats():
    """
    Get comprehensive database statistics.
    
    **Returns:**
    - `total_jobs`: Total number of jobs in database
    - `total_results`: Total number of results in database
    - `total_admit_cards`: Total number of admit cards in database
    - `jobs_with_details`: Jobs with extracted details
    - `results_with_details`: Results with extracted details
    - `admit_cards_with_details`: Admit cards with extracted details
    - `last_crawl_time`: Timestamp of last crawl
    - `database_size_mb`: Total database size in MB
    """
    global total_requests
    total_requests += 1
    
    stats = db.get_stats()
    return StatsResponse(**stats)


@router.get(
    "/stats/by-portal",
    response_model=list[PortalStatsResponse],
    summary="Statistics per portal",
    description="Get item counts for each portal"
)
def get_portal_stats():
    """
    Get statistics broken down by portal.
    
    **Returns:** List of portal statistics with item counts
    """
    global total_requests
    total_requests += 1
    
    stats = db.get_portal_stats()
    return stats
