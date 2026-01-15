# API Quick Reference Card 📋

## Start the API
```bash
python run_api.py
```
**Runs on:** `http://localhost:8000/api`

---

## Interactive Documentation
```
Browser: http://localhost:8000/api/docs
```

---

## Common API Calls

### Get Jobs (5 per page)
```bash
curl "http://localhost:8000/api/jobs?page=1&limit=5"
```

### Search for RBI Jobs
```bash
curl -X POST "http://localhost:8000/api/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "RBI", "limit": 5}'
```

### Get Job Details
```bash
curl "http://localhost:8000/api/jobs/job_001/details"
```

### Get All Results
```bash
curl "http://localhost:8000/api/results?limit=10"
```

### Search Results
```bash
curl -X POST "http://localhost:8000/api/results/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "IBPS"}'
```

### Get Admit Cards
```bash
curl "http://localhost:8000/api/admit-cards?limit=10"
```

### Get Statistics
```bash
curl "http://localhost:8000/api/stats"
```

### Check API Status
```bash
curl "http://localhost:8000/api/status"
```

---

## Python Integration

### Install
```bash
pip install requests
```

### Basic Usage
```python
import requests

# Get jobs
response = requests.get('http://localhost:8000/api/jobs', params={'limit': 5})
jobs = response.json()

# Search
response = requests.post('http://localhost:8000/api/jobs/search', json={
    'keyword': 'RBI',
    'limit': 5
})
results = response.json()

# Get details
response = requests.get('http://localhost:8000/api/jobs/job_001/details')
job_details = response.json()
```

### Using Client Class
```python
from crawler_client import CrawlerAPIClient

client = CrawlerAPIClient()

# Get jobs
jobs = client.get_jobs(page=1, limit=10)

# Search
results = client.search_jobs(keyword='RBI')

# Get details
details = client.get_job_details('job_001')

# Get stats
stats = client.get_stats()
```

---

## JavaScript/Node.js Integration

### Install
```bash
npm install axios
```

### Basic Usage
```javascript
const axios = require('axios');

const API = 'http://localhost:8000/api';

// Get jobs
axios.get(`${API}/jobs?limit=5`).then(res => {
    console.log(res.data);
});

// Search
axios.post(`${API}/jobs/search`, {
    keyword: 'RBI',
    limit: 5
}).then(res => {
    console.log(res.data);
});
```

---

## Response Format

### Paginated Response
```json
{
  "total": 103,
  "page": 1,
  "limit": 10,
  "total_pages": 11,
  "items": [...]
}
```

### Single Item
```json
{
  "id": "job_001",
  "title": "Job Title",
  "posted_date": "2024-01-15",
  "url": "https://...",
  "portal": "sarkari_result",
  "scraped_at": "2024-01-15T10:30:00",
  "details_crawled": true,
  "detailed_info": {...}
}
```

### Statistics
```json
{
  "total_jobs": 103,
  "total_results": 102,
  "total_admit_cards": 101,
  "jobs_with_details": 25,
  "results_with_details": 15,
  "admit_cards_with_details": 10,
  "database_size_mb": 2.5
}
```

---

## Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | List jobs |
| POST | `/jobs/search` | Search jobs |
| GET | `/jobs/{id}` | Get job |
| GET | `/jobs/{id}/details` | Get job details |
| GET | `/results` | List results |
| POST | `/results/search` | Search results |
| GET | `/results/{id}` | Get result |
| GET | `/results/{id}/details` | Get result details |
| GET | `/admit-cards` | List admit cards |
| POST | `/admit-cards/search` | Search admit cards |
| GET | `/admit-cards/{id}` | Get admit card |
| GET | `/admit-cards/{id}/details` | Get admit card details |
| GET | `/status` | API status |
| GET | `/stats` | Database stats |
| GET | `/stats/by-portal` | Portal stats |

---

## Query Parameters

### Pagination
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 10, max: 100)

### Search Filters
- `keyword` - Search in title
- `portal` - Filter by portal
- `start_date` - From date (YYYY-MM-DD)
- `end_date` - To date (YYYY-MM-DD)
- `details_only` - Only items with details (true/false)

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 206 | Partial (details not yet crawled) |
| 400 | Bad request |
| 404 | Not found |
| 500 | Server error |

---

## Error Handling

```python
try:
    response = requests.get('http://localhost:8000/api/jobs')
    response.raise_for_status()
    data = response.json()
except requests.exceptions.Timeout:
    print("API timeout")
except requests.exceptions.ConnectionError:
    print("Cannot connect to API")
except Exception as e:
    print(f"Error: {e}")
```

---

## Documentation Links

📚 [Full API Documentation](API_DOCUMENTATION.md)  
🔌 [Integration Guide](API_INTEGRATION_GUIDE.md)  
📊 [Implementation Summary](API_IMPLEMENTATION_SUMMARY.md)  
📖 [README](README.md)

---

## Common Tasks

### Fetch Latest 10 Jobs
```bash
curl "http://localhost:8000/api/jobs?limit=10"
```

### Find All Bank Jobs
```bash
curl -X POST "http://localhost:8000/api/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "Bank"}'
```

### Get Jobs with Extracted Details
```bash
curl "http://localhost:8000/api/jobs/filter/with-details?limit=20"
```

### Monitor Database
```bash
curl "http://localhost:8000/api/stats"
```

### Check API Is Running
```bash
curl "http://localhost:8000/api/status"
```

---

## Pagination Example

```python
# Get all jobs (paginate through results)
page = 1
while True:
    response = requests.get('http://localhost:8000/api/jobs', 
                          params={'page': page, 'limit': 50})
    data = response.json()
    
    # Process items
    for job in data['items']:
        print(job['title'])
    
    # Check if more pages
    if page >= data['total_pages']:
        break
    
    page += 1
```

---

## Rate Limiting

Currently unlimited. For production:
1. Implement request throttling
2. Add API key authentication
3. Use rate limiting middleware
4. Monitor request logs

---

## Troubleshooting

**API won't start**
```bash
pip install fastapi uvicorn pydantic
python run_api.py
```

**Cannot connect**
```bash
# Verify server is running
curl http://localhost:8000/api/status
```

**Empty results**
```bash
# Run crawler to collect data
python run_crawler.py crawl

# Or check stats
curl http://localhost:8000/api/stats
```

**CORS errors**
- API already allows all origins
- Edit CORS in `src/api/app.py` for production

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** January 15, 2026
