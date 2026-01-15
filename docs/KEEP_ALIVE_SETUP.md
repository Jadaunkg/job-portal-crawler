# Keep-Alive Mechanism Setup

This document explains how to keep your Render API alive and prevent it from spinning down after 15 minutes of inactivity (free tier limitation).

## Overview

On Render's free tier, services automatically spin down after 15 minutes of inactivity. When a request comes in, it takes 30-90 seconds to "cold start" the service again. This can be prevented using keep-alive mechanisms.

## Solutions Implemented

### Option 1: GitHub Actions (Recommended) ✨

Uses GitHub Actions to ping your API every 10 minutes automatically.

**Setup:**

1. **Add GitHub Secret:**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `RENDER_API_URL`
   - Value: Your Render API URL (e.g., `https://your-app.onrender.com`)

2. **Enable Workflow:**
   - The workflow file is already created at `.github/workflows/keep-alive.yml`
   - It will automatically run every 10 minutes
   - You can also trigger it manually from the Actions tab

3. **Verify:**
   - Go to Actions tab in your GitHub repository
   - Check if the workflow runs successfully every 10 minutes

**Pros:**
- ✓ Free (GitHub Actions free tier: 2000 minutes/month, this uses ~72 minutes)
- ✓ Reliable and independent of your service
- ✓ Easy to monitor and debug
- ✓ No code changes needed in your app

**Cons:**
- ✗ Requires GitHub repository
- ✗ 10-minute interval (may have brief downtime if ping fails)

---

### Option 2: External Monitoring Services

Use free external services to ping your API:

#### UptimeRobot (Recommended)
- Website: https://uptimerobot.com/
- **Free tier:** 50 monitors, 5-minute intervals
- **Setup:**
  1. Create free account
  2. Add new monitor (HTTP(s) type)
  3. URL: `https://your-app.onrender.com/health`
  4. Monitoring interval: 5 minutes

#### Cron-Job.org
- Website: https://cron-job.org/
- **Free tier:** Unlimited jobs, 1-minute intervals
- **Setup:**
  1. Create free account
  2. Create new cronjob
  3. URL: `https://your-app.onrender.com/health`
  4. Interval: Every 10 minutes

#### Better Uptime
- Website: https://betteruptime.com/
- Free monitoring with 3-minute checks

**Pros:**
- ✓ Very reliable
- ✓ Additional monitoring features (email alerts, status pages)
- ✓ No GitHub required
- ✓ Shorter intervals possible

**Cons:**
- ✗ Requires external service account
- ✗ Less control over the process

---

### Option 3: Self-Ping (Internal Mechanism)

Use the built-in Python keep-alive service (already implemented in `src/utils/keep_alive.py`).

**Setup:**

Add this to your `src/api/app.py`:

```python
import os
from .utils.keep_alive import get_keep_alive_service

@app.on_event("startup")
async def startup_event():
    # Only enable on Render (not locally)
    if os.getenv("RENDER"):
        base_url = os.getenv("RENDER_EXTERNAL_URL")
        if base_url:
            keep_alive = get_keep_alive_service(base_url)
            keep_alive.start()
            
@app.on_event("shutdown")
async def shutdown_event():
    from .utils.keep_alive import _keep_alive_service
    if _keep_alive_service:
        await _keep_alive_service.stop()
```

**Pros:**
- ✓ No external dependencies
- ✓ Fully self-contained

**Cons:**
- ✗ Uses service resources (minimal, but still counted)
- ✗ Doesn't work if service is completely stopped
- ✗ More complex to debug

---

## Recommended Approach

**Best Solution: GitHub Actions + UptimeRobot**

Combine both for maximum reliability:
- GitHub Actions pings every 10 minutes (primary)
- UptimeRobot as backup every 5 minutes (also monitors uptime)

This ensures:
- Service stays alive 24/7
- You get alerts if the service goes down
- Free tier limits are not exceeded
- Redundancy if one method fails

---

## Testing

Test your keep-alive setup:

```bash
# Manually trigger GitHub Action
# Go to: Repository → Actions → Keep Render Service Alive → Run workflow

# Test health endpoint
curl https://your-app.onrender.com/health

# Check system status
curl https://your-app.onrender.com/api/system/status
```

---

## Important Notes

1. **Still have cold starts:** If you don't set up keep-alive, first request after 15 minutes will be slow
2. **Free tier limits:** Render's free tier has 750 hours/month (enough for 24/7 with one service)
3. **Rate limiting:** Don't ping more often than every 5 minutes to avoid unnecessary load
4. **Upgrade option:** Render paid plans ($7/month) don't have spin-down and are always active

---

## Troubleshooting

**GitHub Action fails:**
- Verify `RENDER_API_URL` secret is set correctly
- Check if your Render service is running
- Look at Action logs for error details

**Service still spins down:**
- Verify keep-alive pings are actually reaching your service
- Check Render logs to see if requests are being received
- Ensure health endpoint returns 200 status code

**Monitoring:**
- Check Render dashboard for request metrics
- Monitor GitHub Actions success rate
- Set up UptimeRobot email alerts
