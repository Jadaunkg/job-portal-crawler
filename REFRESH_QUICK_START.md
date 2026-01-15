# Quick Start: Data Refresh Methods

## Method 1: Command Line (Immediate Refresh)

### Run Once
```bash
python run_crawler.py run-once
```
- Crawls all portals once
- Updates `data/jobs.json`, `data/results.json`, `data/admit_cards.json`
- Exits when complete
- Takes 5-15 minutes depending on data size

### Run on Schedule (Runs Forever)
```bash
python run_crawler.py schedule
```
- Crawls every 15 minutes (configurable)
- Keeps running until you press Ctrl+C
- Watch logs: `tail -f logs/crawler.log`
- Perfect for local development

---

## Method 2: API Endpoint (After Deployment)

### Trigger Refresh
```bash
curl -X POST https://your-api.onrender.com/api/refresh/now
```

Response:
```json
{
    "status": "refreshing",
    "message": "Crawler started in background",
    "started_at": "2024-01-15T10:30:45.123456"
}
```

### Check Status
```bash
curl https://your-api.onrender.com/api/refresh/status
```

Response:
```json
{
    "in_progress": true,
    "last_refresh": null,
    "status": "refreshing",
    "message": "Crawler running...",
    "items_found": 0
}
```

### Get Refresh Info
```bash
curl https://your-api.onrender.com/api/refresh/info
```

---

## Method 3: GitHub Actions (Automatic - RECOMMENDED)

**Setup (one-time):**

1. Already added `.github/workflows/scheduled-refresh.yml`
2. Commit and push to GitHub:
   ```bash
   git add .github/
   git commit -m "Add GitHub Actions scheduled refresh"
   git push origin main
   ```
3. Data refreshes automatically every 2 hours
4. Changes automatically committed to GitHub

**Monitor:**
- Go to GitHub repo → Actions tab
- See all refresh runs and their status
- Click any run to see logs

**Manual Trigger:**
- GitHub repo → Actions tab
- Select "Scheduled Crawler Refresh"
- Click "Run workflow"

**Benefits:**
- ✅ Completely free
- ✅ No server needed
- ✅ Automatic every 2 hours
- ✅ Logs stored in GitHub
- ✅ Data backed up on GitHub

---

## Method 4: Python Script with External Scheduler

Create `scripts/external_scheduler.py`:

```python
"""
Run this script on any machine to schedule refreshes
Works with: Windows Task Scheduler, cron, systemd, etc.
"""
import requests
import time
from datetime import datetime

API_URL = "https://your-api.onrender.com"

def refresh_now():
    """Trigger refresh on deployed API"""
    try:
        print(f"[{datetime.now()}] Triggering refresh...")
        response = requests.post(f"{API_URL}/api/refresh/now")
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_status():
    """Check refresh status"""
    try:
        response = requests.get(f"{API_URL}/api/refresh/status")
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"In Progress: {result['in_progress']}")
        print(f"Last Refresh: {result['last_refresh']}")
        print(f"Items Found: {result['items_found']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_status()
    else:
        refresh_now()
```

**Run every 2 hours:**

**Windows Task Scheduler:**
```
Action: Start program
Program: C:\Python311\python.exe
Arguments: scripts/external_scheduler.py
Repeat: Every 2 hours
```

**Linux Cron:**
```bash
# Edit crontab
crontab -e

# Add this line (every 2 hours)
0 */2 * * * cd /path/to/project && python scripts/external_scheduler.py
```

---

## Configuration

### Change Refresh Interval

Edit `config/settings.json`:

```json
{
  "scheduler": {
    "interval_minutes": 15,  // Change this
    "run_on_startup": true,
    "enabled": true
  }
}
```

### Change GitHub Actions Frequency

Edit `.github/workflows/scheduled-refresh.yml`:

```yaml
on:
  schedule:
    # Run every 1 hour (instead of 2)
    - cron: '0 * * * *'
    
    # Run every 30 minutes
    # - cron: '*/30 * * * *'
    
    # Run daily at 2 AM
    # - cron: '0 2 * * *'
```

**Cron Syntax:**
- `0 * * * *` = every hour
- `*/30 * * * *` = every 30 minutes
- `0 2 * * *` = daily at 2 AM
- `0 */4 * * *` = every 4 hours

---

## Monitor Data Freshness

### Check Last Refresh Time
```bash
curl https://your-api.onrender.com/api/system/stats
```

Shows total counts and when data was last updated.

### View Crawler Logs
```bash
tail -f logs/crawler.log
```

### Check Data Files
```bash
# View jobs count
wc -l data/jobs.json

# View last update
ls -lh data/
```

---

## Troubleshooting

### Crawler Not Running
```bash
# Check if error
python run_crawler.py run-once 2>&1 | head -50

# Check logs
cat logs/crawler.log
```

### Data Not Updating
- ✅ Check if crawler is finding data
- ✅ Check network connectivity
- ✅ Check portal URLs are still valid
- ✅ Review logs for errors

### GitHub Actions Not Running
- ✅ Check `.github/workflows/scheduled-refresh.yml` is committed
- ✅ Go to Actions tab → check for errors
- ✅ May need to enable Actions in repo settings

### API Refresh Endpoint Not Working
- ✅ Make sure `routes_refresh.py` is imported in `app.py`
- ✅ Restart API server
- ✅ Check logs for import errors

---

## Best Practices

1. **Local Development**
   - Use `python run_crawler.py schedule`
   - Leave it running in background
   - Data updates every 15 minutes

2. **Deployed to Cloud**
   - Use GitHub Actions for automatic refresh
   - Use API endpoint for manual refresh when needed
   - Keep refresh logs for monitoring

3. **Data Backup**
   - Git keeps automatic backups
   - JSONDatabase auto-creates backups folder
   - Keep at least 7 days of history

4. **Monitoring**
   - Set up email alerts on GitHub Actions failure
   - Monitor API refresh status endpoint
   - Log refresh times for debugging

---

## Summary

| Method | Setup | Effort | Cost | Best For |
|--------|-------|--------|------|----------|
| Command Line | 0 | Low | Free | Development |
| API Endpoint | 5 min | Low | Free | Manual refresh |
| GitHub Actions | 5 min | Low | Free | **Automatic (BEST)** |
| External Scheduler | 15 min | Medium | Free | Custom timing |

**Recommendation:** Use GitHub Actions + API endpoint combo:
- ✅ Automatic refresh every 2 hours (GitHub)
- ✅ Manual refresh anytime (API endpoint)
- ✅ Completely free
- ✅ No server needed
