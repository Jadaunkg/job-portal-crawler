"""
Data Refresh Endpoints - Trigger crawler from API

Provides endpoints to manually refresh crawler data or check refresh status.
Runs crawler in background thread to avoid blocking API.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import threading
from typing import Dict, Any

try:
    from ..crawler import CrawlerManager
    from ..utils import get_logger
except ImportError:
    from src.crawler import CrawlerManager
    from src.utils import get_logger

router = APIRouter(prefix="/refresh", tags=["Data Management"])
logger = get_logger("refresh")

# Track refresh status globally
refresh_status = {
    "last_refresh": None,
    "status": "idle",
    "in_progress": False,
    "message": "",
    "items_found": 0
}


@router.post(
    "/now",
    summary="Trigger immediate data refresh",
    description="Starts crawler in background to update all data sources"
)
def trigger_refresh() -> Dict[str, Any]:
    """
    Trigger immediate data refresh (non-blocking)
    
    The crawler runs in a background thread and doesn't block the API response.
    Check /refresh/status to monitor progress.
    
    **Returns:**
    - status: "refreshing" or error message
    - started_at: timestamp when refresh started
    - message: Human readable status
    
    **Example Response:**
    ```json
    {
        "status": "refreshing",
        "message": "Crawler started in background",
        "started_at": "2024-01-15T10:30:45.123456"
    }
    ```
    """
    global refresh_status
    
    # Check if refresh already in progress
    if refresh_status["in_progress"]:
        raise HTTPException(
            status_code=409,
            detail="Refresh already in progress. Check /refresh/status"
        )
    
    def run_refresh():
        """Run refresh in background thread"""
        global refresh_status
        try:
            refresh_status["in_progress"] = True
            refresh_status["status"] = "refreshing"
            refresh_status["message"] = "Crawler running..."
            
            logger.info("Starting background crawler refresh...")
            
            # Initialize and run crawler manager
            manager = CrawlerManager()
            results = manager.execute_all()
            
            # Update status with results
            items_found = results.get('new_items', 0)
            refresh_status["last_refresh"] = datetime.now().isoformat()
            refresh_status["status"] = "completed"
            refresh_status["items_found"] = items_found
            refresh_status["message"] = f"Successfully found {items_found} new items"
            
            logger.info(f"Refresh completed: {refresh_status['message']}")
            
        except Exception as e:
            refresh_status["status"] = "error"
            refresh_status["message"] = f"Refresh failed: {str(e)}"
            logger.error(f"Refresh failed: {e}", exc_info=True)
        finally:
            refresh_status["in_progress"] = False
    
    # Start refresh in daemon thread (won't block API)
    thread = threading.Thread(target=run_refresh, daemon=True)
    thread.start()
    
    return {
        "status": "refreshing",
        "message": "Crawler started in background",
        "started_at": datetime.now().isoformat(),
        "check_status_at": "/api/refresh/status"
    }


@router.get(
    "/status",
    summary="Get refresh status",
    description="Check current status of data refresh operation"
)
def get_refresh_status() -> Dict[str, Any]:
    """
    Get current refresh status
    
    Call this endpoint to check if refresh is complete or still running.
    
    **Returns:**
    - in_progress: Boolean indicating if refresh is currently running
    - last_refresh: ISO timestamp of last completed refresh
    - status: Current status ("idle", "refreshing", "completed", "error")
    - message: Human readable status message
    - items_found: Number of new items in last refresh
    
    **Example Response:**
    ```json
    {
        "in_progress": false,
        "last_refresh": "2024-01-15T10:30:52.123456",
        "status": "completed",
        "message": "Successfully found 15 new items",
        "items_found": 15
    }
    ```
    """
    return {
        "in_progress": refresh_status["in_progress"],
        "last_refresh": refresh_status["last_refresh"],
        "status": refresh_status["status"],
        "message": refresh_status["message"],
        "items_found": refresh_status["items_found"]
    }


@router.post(
    "/reset",
    summary="Reset refresh status",
    description="Clear refresh status (mainly for testing)"
)
def reset_refresh_status() -> Dict[str, Any]:
    """
    Reset refresh status back to idle
    
    Useful for testing or if refresh gets stuck.
    
    **Returns:**
    ```json
    {
        "status": "idle",
        "message": "Status reset successfully"
    }
    ```
    """
    global refresh_status
    
    if refresh_status["in_progress"]:
        raise HTTPException(
            status_code=409,
            detail="Cannot reset while refresh is in progress"
        )
    
    refresh_status = {
        "last_refresh": None,
        "status": "idle",
        "in_progress": False,
        "message": "",
        "items_found": 0
    }
    
    return {
        "status": "idle",
        "message": "Status reset successfully"
    }


@router.get(
    "/info",
    summary="Get refresh information",
    description="Get information about the refresh system"
)
def get_refresh_info() -> Dict[str, Any]:
    """
    Get information about the refresh system
    
    Returns information about how refresh works and configuration.
    
    **Returns:**
    ```json
    {
        "system": "Job Portal Crawler",
        "refresh_method": "Background threading",
        "non_blocking": true,
        "default_interval": "15 minutes",
        "endpoints": {
            "trigger": "POST /api/refresh/now",
            "status": "GET /api/refresh/status",
            "info": "GET /api/refresh/info"
        }
    }
    ```
    """
    return {
        "system": "Job Portal Crawler",
        "description": "On-demand data refresh for crawler",
        "refresh_method": "Background threading (non-blocking)",
        "features": [
            "Trigger refresh immediately",
            "Check refresh status",
            "Non-blocking operation (API stays responsive)",
            "Automatic data backup"
        ],
        "default_interval_minutes": 15,
        "configuration_file": "config/settings.json",
        "endpoints": {
            "trigger_refresh": {
                "method": "POST",
                "path": "/api/refresh/now",
                "description": "Start crawler in background"
            },
            "check_status": {
                "method": "GET",
                "path": "/api/refresh/status",
                "description": "Check current refresh status"
            },
            "reset_status": {
                "method": "POST",
                "path": "/api/refresh/reset",
                "description": "Reset status (for testing)"
            },
            "get_info": {
                "method": "GET",
                "path": "/api/refresh/info",
                "description": "Get refresh system information"
            }
        },
        "alternative_methods": [
            "Command line: python run_crawler.py run-once",
            "Scheduled: python run_crawler.py schedule",
            "GitHub Actions: Automated hourly refresh"
        ]
    }
