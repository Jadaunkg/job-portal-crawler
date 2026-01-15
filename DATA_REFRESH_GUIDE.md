# Data Refresh & Database Strategy Guide

## Current Architecture

```
Crawler System:
  ├── Metadata Crawler (generic_crawler.py)
  │   └── Scrapes job listings, results, admit cards
  │
  ├── Detail Crawler (detail_crawler.py)  
  │   └── Extracts detailed information from pages
  │
  ├── Data Processor (processor.py)
  │   └── Validates & processes scraped data
  │
  ├── Storage Layer
  │   ├── JSON Files (data/jobs.json, etc.) - CURRENT
  │   └── Optional: PostgreSQL/MongoDB - UPGRADE
  │
  └── API Layer (REST API for access)
      └── Reads from storage & serves data
```

---

## Option 1: Refresh Data Using Existing Crawler (Current Setup)

### **Run Crawler Once**
```bash
python run_crawler.py run-once
```
This will:
- ✅ Scrape latest data from all portals
- ✅ Update `data/jobs.json`, `data/results.json`, `data/admit_cards.json`
- ✅ Keep backups of old data
- ✅ Exit when complete

### **Run Crawler on Schedule** (Recommended)
```bash
python run_crawler.py schedule
```
This will:
- ✅ Run crawler automatically every 15 minutes (configurable)
- ✅ Update JSON files continuously
- ✅ Keep running until you stop it (Ctrl+C)
- ✅ Log all activity to `logs/crawler.log`

---

## Option 2: Refresh Data from Deployed API

Create a **refresh endpoint** that triggers the crawler from your deployed API:

### **Add Refresh Endpoint to API**

Create new file: [src/api/routes_refresh.py](src/api/routes_refresh.py)

```python
"""
Data Refresh Endpoints - Trigger crawler from API
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import subprocess
import threading
from typing import Dict, Any

try:
    from ..crawler import CrawlerManager
    from ..utils import get_logger
except ImportError:
    from src.crawler import CrawlerManager
    from src.utils import get_logger

router = APIRouter(prefix="/api/refresh", tags=["Data Management"])
logger = get_logger("refresh")

# Track last refresh status
refresh_status = {
    "last_refresh": None,
    "status": "idle",
    "in_progress": False,
    "message": ""
}


@router.post("/now")
def trigger_refresh() -> Dict[str, Any]:
    """
    Trigger immediate data refresh (non-blocking)
    
    Returns:
    - status: "refreshing" or error message
    - started_at: timestamp
    """
    global refresh_status
    
    if refresh_status["in_progress"]:
        raise HTTPException(
            status_code=409,
            detail="Refresh already in progress"
        )
    
    def run_refresh():
        """Run refresh in background thread"""
        global refresh_status
        try:
            refresh_status["in_progress"] = True
            refresh_status["status"] = "refreshing"
            refresh_status["message"] = "Crawler running..."
            
            manager = CrawlerManager()
            results = manager.execute_all()
            
            refresh_status["last_refresh"] = datetime.now().isoformat()
            refresh_status["status"] = "completed"
            refresh_status["message"] = f"Found {results.get('new_items', 0)} new items"
            
            logger.info(f"Refresh completed: {refresh_status['message']}")
            
        except Exception as e:
            refresh_status["status"] = "error"
            refresh_status["message"] = str(e)
            logger.error(f"Refresh failed: {e}")
        finally:
            refresh_status["in_progress"] = False
    
    # Start refresh in background thread
    thread = threading.Thread(target=run_refresh, daemon=True)
    thread.start()
    
    return {
        "status": "refreshing",
        "message": "Crawler started in background",
        "started_at": datetime.now().isoformat()
    }


@router.get("/status")
def get_refresh_status() -> Dict[str, Any]:
    """
    Get current refresh status
    
    Returns:
    - in_progress: Is refresh running?
    - last_refresh: Last refresh timestamp
    - status: Current status
    - message: Status message
    """
    return {
        "in_progress": refresh_status["in_progress"],
        "last_refresh": refresh_status["last_refresh"],
        "status": refresh_status["status"],
        "message": refresh_status["message"]
    }


@router.post("/scheduled")
def enable_scheduled_refresh() -> Dict[str, Any]:
    """
    Enable automatic scheduled refresh every N minutes
    
    Note: For production, use external scheduler (cron, APScheduler, etc.)
    """
    return {
        "message": "Use 'python run_crawler.py schedule' for scheduled refreshes",
        "current_interval": "15 minutes (configurable)",
        "config_file": "config/settings.json"
    }
```

### **Update API App to Include Refresh Routes**

Edit [src/api/app.py](src/api/app.py):

Add this import:
```python
from .routes_refresh import router as refresh_router
```

Add this after other routers:
```python
app.include_router(refresh_router, prefix="/api")
```

---

## Option 3: Upgrade to Cloud Database (PostgreSQL)

### **Why Upgrade from JSON to Database?**

| Feature | JSON Files | PostgreSQL |
|---------|-----------|-----------|
| **Scalability** | Limited (large files slow) | Excellent |
| **Concurrent Access** | File locks | Full locking support |
| **Query Performance** | Slow (entire file scan) | Fast (indexed queries) |
| **Backup/Recovery** | Manual copies | Built-in tools |
| **Data Integrity** | Manually validated | Constraints enforced |
| **Cost** | Free | Free tier available |

### **Step 1: Create Database Abstraction Layer**

Create [src/data/db_adapter.py](src/data/db_adapter.py):

```python
"""
Database Adapter - Supports both JSON and SQL databases
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class DatabaseAdapter(ABC):
    """Abstract base for database implementations"""
    
    @abstractmethod
    def save_items(self, category: str, items: List[Dict[str, Any]]) -> int:
        """Save items to database. Returns count saved."""
        pass
    
    @abstractmethod
    def get_items(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get items from database"""
        pass
    
    @abstractmethod
    def search(self, category: str, keyword: str) -> List[Dict[str, Any]]:
        """Search items by keyword"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """Get statistics for all categories"""
        pass


class JSONDatabaseAdapter(DatabaseAdapter):
    """JSON file implementation"""
    
    def __init__(self, data_dir: str = "data"):
        from .database import JSONDatabase
        self.db = JSONDatabase(data_dir)
    
    def save_items(self, category: str, items: List[Dict[str, Any]]) -> int:
        self.db.save_category(category, items)
        return len(items)
    
    def get_items(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        items = self.db.load_category(category)
        return items[:limit]
    
    def search(self, category: str, keyword: str) -> List[Dict[str, Any]]:
        items = self.db.load_category(category)
        keyword_lower = keyword.lower()
        return [
            item for item in items
            if keyword_lower in str(item).lower()
        ]
    
    def get_stats(self) -> Dict[str, int]:
        return {
            'jobs': len(self.db.load_category('jobs')),
            'results': len(self.db.load_category('results')),
            'admit_cards': len(self.db.load_category('admit_cards'))
        }


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL implementation (optional upgrade)"""
    
    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL adapter
        
        Example:
            postgresql://user:password@localhost/jobcrawler
        """
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        self.connection_string = connection_string
        self.conn = psycopg2.connect(connection_string)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
    
    def save_items(self, category: str, items: List[Dict[str, Any]]) -> int:
        """Save items to PostgreSQL"""
        # Implementation would insert items into appropriate table
        # e.g., INSERT INTO jobs (id, title, url, ...) VALUES (...)
        pass
    
    def get_items(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get items from PostgreSQL"""
        # SELECT * FROM {category} LIMIT {limit}
        pass
    
    def search(self, category: str, keyword: str) -> List[Dict[str, Any]]:
        """Search items in PostgreSQL"""
        # SELECT * FROM {category} WHERE title ILIKE '%keyword%'
        pass
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics from PostgreSQL"""
        # SELECT COUNT(*) FROM each table
        pass
```

### **Step 2: Use Database Abstraction in Crawler**

Update [src/crawler/manager.py](src/crawler/manager.py):

```python
from ..data.db_adapter import DatabaseAdapter, JSONDatabaseAdapter

class CrawlerManager:
    def __init__(self, db_adapter: Optional[DatabaseAdapter] = None):
        self.db = db_adapter or JSONDatabaseAdapter()
    
    def save_results(self, results: Dict[str, List]):
        """Save crawled data to database"""
        self.db.save_items('jobs', results.get('jobs', []))
        self.db.save_items('results', results.get('results', []))
        self.db.save_items('admit_cards', results.get('admit_cards', []))
```

---

## Option 4: Scheduling in Deployed Environment

### **For Render/Railway Deployment:**

Create [scripts/refresh.sh](scripts/refresh.sh):

```bash
#!/bin/bash
# Run crawler every 15 minutes
while true; do
    echo "Running crawler refresh..."
    python run_crawler.py run-once
    echo "Waiting 15 minutes until next refresh..."
    sleep 900  # 15 minutes
done
```

Then deploy as a **background worker** (separate from API server).

### **Or Use External Scheduler:**

Create [scripts/cron_refresh.py](scripts/cron_refresh.py):

```python
"""
External scheduler trigger - Call from external service
"""
import requests
import schedule
import time

API_URL = "https://your-api.onrender.com"
REFRESH_ENDPOINT = f"{API_URL}/api/refresh/now"

def refresh_data():
    """Trigger refresh on deployed API"""
    try:
        response = requests.post(REFRESH_ENDPOINT)
        print(f"Refresh triggered: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

# Schedule refresh every 15 minutes
schedule.every(15).minutes.do(refresh_data)

if __name__ == "__main__":
    print("Scheduler started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)
```

Run this on any server (including free tiers):
```bash
python scripts/cron_refresh.py
```

---

## Option 5: GitHub Actions Scheduled Refresh

Create [.github/workflows/scheduled-refresh.yml](.github/workflows/scheduled-refresh.yml):

```yaml
name: Scheduled Crawler Refresh

on:
  schedule:
    # Run every 15 minutes
    - cron: '*/15 * * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run crawler
        run: python run_crawler.py run-once
      
      - name: Commit changes
        run: |
          git config --local user.name "GitHub Actions"
          git config --local user.email "actions@github.com"
          git add data/
          git commit -m "Auto: Update crawled data [skip ci]" || true
          git push
```

**Benefits:**
- ✅ Free (GitHub Actions has free tier)
- ✅ Automatic every 15 minutes
- ✅ Data pushed back to GitHub
- ✅ No server needed

---

## Complete Implementation Steps

### **Quick Setup (Recommended)**

**Step 1: Create requirements.txt**
```bash
pip freeze > requirements.txt
```

**Step 2: Run crawler manually**
```bash
python run_crawler.py run-once
```

**Step 3: Add refresh endpoint to API** (use code above)

**Step 4: Deploy to Render/Railway**

**Step 5: Trigger refresh manually**
```bash
curl -X POST https://your-api.onrender.com/api/refresh/now
```

---

## Configuration

### **Scheduler Settings** - Edit [config/settings.json](config/settings.json):

```json
{
  "scheduler": {
    "interval_minutes": 15,
    "run_on_startup": true,
    "enabled": true
  },
  "crawler": {
    "timeout_seconds": 30,
    "max_retries": 3,
    "headless_browser": true
  },
  "database": {
    "backup_enabled": true,
    "max_backups": 10,
    "backup_frequency": 5
  }
}
```

---

## Summary Table

| Method | Setup Time | Cost | Reliability | Recommended |
|--------|-----------|------|------------|-------------|
| `run_crawler.py run-once` | <5 min | Free | Manual | Quick testing |
| `run_crawler.py schedule` | <5 min | Free | Good | Local development |
| Refresh API Endpoint | 10 min | Free | Good | Cloud deployment |
| GitHub Actions | 15 min | Free | Excellent | **Best option** |
| PostgreSQL + Scheduler | 30 min | Free tier | Excellent | Large scale |

---

**Recommended Approach for Your Project:**

1. **Immediate:** Use GitHub Actions for automatic hourly refreshes
2. **Add:** Refresh endpoint in API for manual triggers
3. **Later:** Upgrade to PostgreSQL when data grows large

Would you like me to set up any of these options?
