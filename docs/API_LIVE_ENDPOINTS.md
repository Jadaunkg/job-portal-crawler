# Job Crawler API — Live Endpoints Reference

Base URL: https://job-crawler-api-0885.onrender.com

Notes:
- All responses are JSON.
- On the Free Render plan, the service can sleep after inactivity; the first request may take ~30s and very rarely a route can 404 while warming up. Re-try once.
- List endpoints use pagination with an envelope: `{ total, page, limit, total_pages, items }`.

---

## Health

- Method: GET
- Path: /health
- Example:
```json
{"status":"ok"}
```

---

## System

### GET /api/system/status
- Returns service status and uptime.
- Example:
```json
{
  "status": "operational",
  "version": "1.0.0",
  "uptime_seconds": 176.89,
  "total_requests": 1,
  "database_connected": true,
  "last_updated": ""
}
```

### GET /api/system/stats
- Aggregated dataset counts.
- Example:
```json
{
  "total_jobs": 103,
  "total_results": 102,
  "total_admit_cards": 101,
  "jobs_with_details": 1,
  "results_with_details": 1,
  "admit_cards_with_details": 1,
  "last_crawl_time": "",
  "database_size_mb": 0.17
}
```

### GET /api/system/stats/by-portal
- Counts grouped by `portal`.
- Example:
```json
[
  {
    "portal": "unknown",
    "job_count": 103,
    "result_count": 102,
    "admit_card_count": 101
  }
]
```

---

## Jobs

### GET /api/jobs
- Query: `page` (optional), `limit` (optional), plus filters as available.
- Returns a paginated list of jobs.
- Example:
```json
{
  "total": 103,
  "page": 0,
  "limit": 10,
  "total_pages": 11,
  "items": [
    {
      "id": "45a4f88c97e60d4510b2fddd52666123",
      "title": "RBI Bank Office Attendant Online Form 2026 – Start",
      "posted_date": null,
      "url": "https://sarkariresult.com.cm/rbi-bank-office-attendant-recruitment-2026/",
      "portal": null,
      "scraped_at": null,
      "details_crawled": false,
      "detailed_info": {
        "url": "https://sarkariresult.com.cm/rbi-bank-office-attendant-recruitment-2026/",
        "full_description": "...trimmed..."
      }
    }
  ]
}
```

### GET /api/jobs/{job_id}
- Returns a single job by ID.

### GET /api/jobs/filter/with-details
- Returns only items where `details_crawled=true`.

### GET /api/jobs/search?q=...
- Full-text search over jobs.

---

## Results

### GET /api/results
- Same pagination envelope as `/api/jobs`.
- Example (trimmed fields):
```json
{
  "total": 102,
  "page": 0,
  "limit": 10,
  "total_pages": 11,
  "items": [
    {
      "id": "fb5028896832c1dc4128df683b28dbcb",
      "title": "IBPS PO MT XV 15 Final Result 2026 – Out",
      "url": "https://sarkariresult.com.cm/ibps-po-mt-xv-15-final-result-2026/",
      "details_crawled": false,
      "detailed_info": { "url": "...", "full_description": "...trimmed..." }
    }
  ]
}
```

### GET /api/results/{result_id}
- Returns a single result by ID.

### GET /api/results/filter/with-details
- Items with `details_crawled=true` only.

### GET /api/results/search?q=...
- Search results by text.

---

## Admit Cards

### GET /api/admit-cards
- Same pagination envelope as jobs/results.

### GET /api/admit-cards/{card_id}
- Returns a single admit card by ID.

### GET /api/admit-cards/filter/with-details
- Items with `details_crawled=true` only.

### GET /api/admit-cards/search?q=...
- Search admit cards by text.

---

## Refresh (On-demand Crawl)

### GET /api/refresh/info
- Returns metadata about refresh capabilities.

### POST /api/refresh/now
- Triggers a background crawl. Returns immediately.
- Example:
```json
{
  "status": "refreshing",
  "message": "Crawler started in background",
  "started_at": "2026-01-15T12:48:56.810889",
  "check_status_at": "/api/refresh/status"
}
```

### GET /api/refresh/status
- Returns current refresh state.
- Example (idle):
```json
{
  "in_progress": false,
  "last_refresh": null,
  "status": "idle",
  "message": "",
  "items_found": 0
}
```

---

## OpenAPI / Docs

- Swagger UI: /api/docs
- ReDoc: /api/redoc
- Raw spec: /api/openapi.json

---

## Example Requests (curl)

```bash
# Health
curl -s https://job-crawler-api-0885.onrender.com/health

# Jobs (first page, limit 5)
curl -s "https://job-crawler-api-0885.onrender.com/api/jobs?limit=5" | jq '.items | length'

# Results (first page, limit 5)
curl -s "https://job-crawler-api-0885.onrender.com/api/results?limit=5" | jq '.items | length'

# Admit cards (first page)
curl -s "https://job-crawler-api-0885.onrender.com/api/admit-cards?limit=5" | jq '.items | length'

# Trigger refresh
curl -s -X POST https://job-crawler-api-0885.onrender.com/api/refresh/now | jq

# Check refresh status
curl -s https://job-crawler-api-0885.onrender.com/api/refresh/status | jq
```

---

## Integration Tips
- Pagination: use `?limit=` and optionally `?page=`; when a `page` is out of range some endpoints may return 404.
- Fields: all list endpoints return `items`; each item includes `id`, `title`, `url`, and optional `detailed_info` when `details_crawled=true`.
- Stability: if the free-tier instance was idle, retry once on a 404 right after startup.
