#!/usr/bin/env python3
"""
API Server startup script.
Runs the FastAPI application with Uvicorn server.
"""
import uvicorn
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Start the API server."""
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
