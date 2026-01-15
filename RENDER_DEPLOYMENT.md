# Deploy to Render - Complete Guide

## Step 1: Verify Everything is Committed to GitHub

First, make sure all your files are committed and pushed to GitHub:

```bash
git status
git add .
git commit -m "Add Render deployment configuration files"
git push origin main
```

Expected files pushed:
- ✅ `Procfile` - Render process configuration
- ✅ `render.yaml` - Render infrastructure configuration
- ✅ `.render` - Render environment variables
- ✅ Updated `requirements.txt` with gunicorn

---

## Step 2: Create Render Account

1. Go to [https://render.com](https://render.com)
2. Click **Sign Up**
3. Choose **Sign up with GitHub** (easiest)
4. Authorize Render to access your GitHub account
5. You'll be redirected to Render dashboard

---

## Step 3: Create New Web Service

1. In Render Dashboard, click **New +** (top right)
2. Select **Web Service**
3. Choose **Deploy an existing repository**
4. Search for your GitHub repository: `Job Crawler`
5. Click **Connect**

---

## Step 4: Configure Web Service

### Basic Settings

**Name:** `job-crawler-api` (or your preferred name)

**Environment:** `Python 3`

**Region:** `Oregon` (US West) - or choose closest to you

**Branch:** `main`

### Build Configuration

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT src.api.app:app
```

### Plan

**Select:** `Free` (or Starter if you want better performance)

### Environment Variables (Optional)

No required environment variables for basic deployment. If you add later:

```
PYTHONUNBUFFERED=true
LOG_LEVEL=info
```

### Advanced Settings

Leave everything as default for now.

---

## Step 5: Deploy

1. Click **Create Web Service**
2. Render will:
   - Connect to GitHub
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Run build command
   - Start the application with your start command

3. Watch the logs in real-time:
   - You'll see deployment progress
   - Build output
   - Application startup logs

---

## Step 6: Verify Deployment

Once deployment is complete (you'll see "Live" status):

### Get Your URL

Your API will be available at:
```
https://job-crawler-api.onrender.com
```

(The exact name depends on what you named your service)

### Test the API

```bash
# Test health check
curl https://job-crawler-api.onrender.com/health

# Expected response:
{"status":"ok"}
```

```bash
# Test root endpoint
curl https://job-crawler-api.onrender.com/

# Expected response:
{
  "message": "Welcome to Job Portal Crawler API",
  "version": "1.0.0",
  "docs": "/api/docs",
  ...
}
```

### View API Documentation

Open in browser:
```
https://job-crawler-api.onrender.com/api/docs
```

You'll see the interactive Swagger UI with all endpoints.

---

## Step 7: Test All Endpoints

### Get Jobs
```bash
curl https://job-crawler-api.onrender.com/api/jobs
```

### Get Results
```bash
curl https://job-crawler-api.onrender.com/api/results
```

### Get Admit Cards
```bash
curl https://job-crawler-api.onrender.com/api/admit-cards
```

### Trigger Data Refresh
```bash
curl -X POST https://job-crawler-api.onrender.com/api/refresh/now
```

### Check Refresh Status
```bash
curl https://job-crawler-api.onrender.com/api/refresh/status
```

### System Stats
```bash
curl https://job-crawler-api.onrender.com/api/stats
```

---

## Step 8: Set Up Automatic Redeploy

By default, Render automatically redeploys when you push to GitHub. To verify or change:

1. In Render dashboard, go to your web service
2. Click **Settings** (tab)
3. Under **Auto-Deploy**, make sure it says **Yes**

This means every time you push to GitHub, Render will automatically rebuild and redeploy!

---

## Step 9: Configure GitHub Actions for Data Refresh

Your GitHub Actions workflow (`.github/workflows/scheduled-refresh.yml`) will run every 2 hours and crawl new data.

The workflow will:
1. Run crawler
2. Update data files
3. Auto-commit changes to GitHub
4. Render automatically sees the changes
5. Redeploys with updated data

---

## Step 10: Monitor Deployment

### View Logs

In Render dashboard:
1. Click your web service
2. Click **Logs** (tab)
3. See real-time logs

### Check Deployment History

1. Click **Deploys** (tab)
2. See all deployment attempts
3. Click any deployment to see detailed logs

---

## Important Notes

### Free Tier Limitations

- ✅ Unlimited deployments
- ✅ Automatic SSL/HTTPS
- ✅ GitHub auto-deploy
- ⚠️ Service spins down after 15 minutes of inactivity
- ⚠️ Takes ~30 seconds to wake up on first request after spin-down

### If API Becomes Unresponsive

This is normal on free tier. Solutions:

**Option 1: Keep Alive (Recommended)**
- Set up a cron job to ping `/health` every 10 minutes
- Prevent spin-down
- Cost: Free (included with free tier)

**Option 2: Upgrade to Starter ($7/month)**
- No spin-down
- Better performance
- Better for production

---

## Troubleshooting

### Deployment Fails

**Check logs:**
1. Go to Render dashboard
2. Click your service
3. Click **Logs**
4. Look for error messages

**Common issues:**
- `ModuleNotFoundError` - Missing dependency in requirements.txt
- `Port already in use` - Render handles this, not your problem
- `Permission denied` - Check file permissions (shouldn't happen)

**Solution:**
1. Fix the error locally
2. Commit and push to GitHub
3. Render auto-redeploys
4. Check logs again

### API Not Responding

**If service is spinning down:**
1. Make first request (wait 30 seconds)
2. Service wakes up
3. Next requests are instant

**To prevent spin-down:**
- Use crawler refresh every 2 hours (GitHub Actions)
- Or upgrade to Starter plan

### Port Issues

Render automatically assigns port via `$PORT` environment variable. Our Procfile already handles this:

```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT src.api.app:app
```

The `$PORT` variable is automatically set by Render.

---

## Success Checklist

- ✅ All files committed to GitHub
- ✅ Render account created
- ✅ Web service created and connected
- ✅ Deployment completed (status: Live)
- ✅ Health check works
- ✅ API endpoints respond
- ✅ Swagger docs accessible
- ✅ GitHub Actions workflow runs every 2 hours
- ✅ Data refreshes automatically

---

## Next Steps

1. **Monitor first deployment** - Check logs for any errors
2. **Test all endpoints** - Verify API works as expected
3. **Check GitHub Actions** - Verify crawlers run every 2 hours
4. **Share API URL** - Your API is now public!

Example API endpoint to share:
```
https://job-crawler-api.onrender.com/api/docs
```

---

## API Documentation

Once deployed, access:

- **Swagger UI (Interactive):** `https://job-crawler-api.onrender.com/api/docs`
- **ReDoc (Read-only):** `https://job-crawler-api.onrender.com/api/redoc`
- **OpenAPI JSON:** `https://job-crawler-api.onrender.com/api/openapi.json`

---

## Support

If deployment fails:

1. Check Render logs
2. Check GitHub Actions logs
3. Verify files exist in GitHub repo
4. Try redeploying manually (Render dashboard → Deploy → Latest)

Most issues are resolved by fixing the error and pushing a new commit.
