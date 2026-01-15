"""
Keep-alive utility for preventing service spin-down on free hosting tiers.
"""
import asyncio
import httpx
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class KeepAliveService:
    """Service to keep the API alive by self-pinging."""
    
    def __init__(self, base_url: str, interval_minutes: int = 10):
        """
        Initialize keep-alive service.
        
        Args:
            base_url: The base URL of the API (e.g., https://your-app.onrender.com)
            interval_minutes: How often to ping (default: 10 minutes)
        """
        self.base_url = base_url.rstrip('/')
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
    async def ping_health(self) -> bool:
        """
        Ping the health endpoint.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    logger.info(f"✓ Keep-alive ping successful at {datetime.now()}")
                    return True
                else:
                    logger.warning(f"⚠ Keep-alive ping returned {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"✗ Keep-alive ping failed: {e}")
            return False
    
    async def _keep_alive_loop(self):
        """Main keep-alive loop."""
        logger.info(f"Keep-alive service started (interval: {self.interval_minutes} minutes)")
        
        while self.is_running:
            try:
                # Wait for the interval
                await asyncio.sleep(self.interval_seconds)
                
                # Ping the health endpoint
                if self.is_running:  # Check again after sleep
                    await self.ping_health()
                    
            except asyncio.CancelledError:
                logger.info("Keep-alive service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in keep-alive loop: {e}")
                # Continue running even if one ping fails
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def start(self):
        """Start the keep-alive service."""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._keep_alive_loop())
            logger.info("Keep-alive service scheduled to start")
    
    async def stop(self):
        """Stop the keep-alive service."""
        if self.is_running:
            self.is_running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Keep-alive service stopped")


# Global instance
_keep_alive_service: Optional[KeepAliveService] = None


def get_keep_alive_service(base_url: str = None) -> Optional[KeepAliveService]:
    """
    Get or create the global keep-alive service instance.
    
    Args:
        base_url: The base URL (required on first call)
        
    Returns:
        KeepAliveService instance or None if not configured
    """
    global _keep_alive_service
    
    if _keep_alive_service is None and base_url:
        _keep_alive_service = KeepAliveService(base_url)
    
    return _keep_alive_service
