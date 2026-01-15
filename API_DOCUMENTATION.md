# Job Portal Crawler API Documentation 📚

## Overview

The Job Portal Crawler API is a RESTful web service that provides programmatic access to crawled job postings, exam results, and admit cards. It supports advanced search, filtering, and pagination capabilities.

**Base URL:** `http://localhost:8000/api`  
**API Version:** 1.0.0  
**Documentation:** `http://localhost:8000/api/docs` (Interactive Swagger UI)

---

## Quick Start

### 1. Installation

```bash
# Install additional dependencies
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Method 1: Using the startup script
python run_api.py

# Method 2: Direct uvicorn command
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Verify Installation

```bash
# Check API status
curl http://localhost:8000/api/status

# View interactive documentation
# Open browser to: http://localhost:8000/api/docs
```

---

## API Endpoints Overview

### Root Endpoints
- `GET /` - API information and available endpoints
- `GET /health` - Health check

### Jobs Endpoints
- `GET /api/jobs` - List all jobs (paginated)
- `GET /api/jobs/{job_id}` - Get specific job
- `GET /api/jobs/{job_id}/details` - Get job with extracted details
- `POST /api/jobs/search` - Search jobs with filters
- `GET /api/jobs/filter/by-portal/{portal}` - Get jobs by portal
- `GET /api/jobs/filter/with-details` - Get jobs with details crawled

### Results Endpoints
- `GET /api/results` - List all results
- `GET /api/results/{result_id}` - Get specific result
- `GET /api/results/{result_id}/details` - Get result with details
- `POST /api/results/search` - Search results
- `GET /api/results/filter/by-portal/{portal}` - Get results by portal
- `GET /api/results/filter/with-details` - Get results with details

### Admit Cards Endpoints
- `GET /api/admit-cards` - List all admit cards
- `GET /api/admit-cards/{card_id}` - Get specific admit card
- `GET /api/admit-cards/{card_id}/details` - Get admit card with details
- `POST /api/admit-cards/search` - Search admit cards
- `GET /api/admit-cards/filter/by-portal/{portal}` - Get by portal
- `GET /api/admit-cards/filter/with-details` - Get with details

### System Endpoints
- `GET /api/status` - API health and uptime
- `GET /api/stats` - Database statistics
- `GET /api/stats/by-portal` - Statistics per portal

---

## Detailed API Reference

### Jobs API

#### List All Jobs
```http
GET /api/jobs?page=1&limit=10
```

**Query Parameters:**
- `page` (int, default: 1) - Page number (min: 1)
- `limit` (int, default: 10) - Items per page (max: 100)

**Response (200):**
```json
{
  "total": 103,
  "page": 1,
  "limit": 10,
  "total_pages": 11,
  "items": [
    {
      "id": "job_001",
      "title": "RBI Bank Office Attendant",
      "posted_date": "2024-01-15",
      "url": "https://www.sarkariresult.com/...",
      "portal": "sarkari_result",
      "scraped_at": "2024-01-15T10:30:00",
      "details_crawled": true,
      "detailed_info": {...}
    }
  ]
}
```

---

#### Get Specific Job
```http
GET /api/jobs/{job_id}
```

**Path Parameters:**
- `job_id` (string) - Unique job identifier

**Response (200):**
```json
{
  "id": "job_001",
  "title": "RBI Bank Office Attendant",
  "posted_date": "2024-01-15",
  "url": "https://www.sarkariresult.com/...",
  "portal": "sarkari_result",
  "scraped_at": "2024-01-15T10:30:00",
  "details_crawled": true,
  "detailed_info": null
}
```

**Response (404):**
```json
{
  "detail": "Job with ID 'invalid_id' not found"
}
```

---

#### Get Job with Details
```http
GET /api/jobs/{job_id}/details
```

**Path Parameters:**
- `job_id` (string) - Unique job identifier

**Response (200):**
```json
{
  "id": "job_001",
  "title": "RBI Bank Office Attendant",
  "posted_date": "2024-01-15",
  "url": "https://www.sarkariresult.com/...",
  "portal": "sarkari_result",
  "scraped_at": "2024-01-15T10:30:00",
  "details_crawled": true,
  "detailed_info": {
    "description": "Full page text content...",
    "tables": [
      {
        "headers": ["Column1", "Column2"],
        "rows": [["Value1", "Value2"]]
      }
    ],
    "links": {
      "official_notifications": ["https://..."],
      "apply": ["https://..."]
    },
    "eligibility": "12th Pass, Indian Citizen",
    "application_fee": "₹450 (General), ₹50 (SC/ST)",
    "important_dates": "Application: 01-01-2024 to 31-01-2024"
  }
}
```

---

#### Search Jobs
```http
POST /api/jobs/search
Content-Type: application/json

{
  "keyword": "RBI",
  "portal": "sarkari_result",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "details_only": false,
  "page": 1,
  "limit": 10
}
```

**Request Body:**
- `keyword` (string, optional) - Search in title
- `portal` (string, optional) - Filter by portal
- `start_date` (string, optional) - From date (YYYY-MM-DD)
- `end_date` (string, optional) - To date (YYYY-MM-DD)
- `details_only` (boolean, default: false) - Show only items with details
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 10) - Items per page

**Response (200):** Same format as list jobs

---

#### Filter Jobs by Portal
```http
GET /api/jobs/filter/by-portal/sarkari_result?page=1&limit=10
```

**Response (200):** Same as list jobs

---

#### Get Jobs with Details
```http
GET /api/jobs/filter/with-details?page=1&limit=10
```

**Response (200):** Returns only jobs with `detailed_info` populated

---

### Results API

Similar to Jobs API with endpoints:
- `GET /api/results`
- `GET /api/results/{result_id}`
- `GET /api/results/{result_id}/details`
- `POST /api/results/search`
- `GET /api/results/filter/by-portal/{portal}`
- `GET /api/results/filter/with-details`

---

### Admit Cards API

Similar to Jobs API with endpoints:
- `GET /api/admit-cards`
- `GET /api/admit-cards/{card_id}`
- `GET /api/admit-cards/{card_id}/details`
- `POST /api/admit-cards/search`
- `GET /api/admit-cards/filter/by-portal/{portal}`
- `GET /api/admit-cards/filter/with-details`

---

### System Endpoints

#### API Status
```http
GET /api/status
```

**Response (200):**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "total_requests": 150,
  "database_connected": true,
  "last_updated": "2024-01-15T10:30:00"
}
```

---

#### Database Statistics
```http
GET /api/stats
```

**Response (200):**
```json
{
  "total_jobs": 103,
  "total_results": 102,
  "total_admit_cards": 101,
  "jobs_with_details": 25,
  "results_with_details": 15,
  "admit_cards_with_details": 10,
  "last_crawl_time": "2024-01-15T10:30:00",
  "database_size_mb": 2.5
}
```

---

#### Statistics by Portal
```http
GET /api/stats/by-portal
```

**Response (200):**
```json
[
  {
    "portal": "sarkari_result",
    "job_count": 103,
    "result_count": 102,
    "admit_card_count": 101
  }
]
```

---

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error type",
  "detail": "Detailed error message"
}
```

### HTTP Status Codes
- `200 OK` - Successful request
- `206 Partial Content` - Details not yet crawled
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Common Examples

### Example 1: Get Latest 5 Jobs

```bash
curl -X GET "http://localhost:8000/api/jobs?page=1&limit=5"
```

```python
import requests

response = requests.get('http://localhost:8000/api/jobs', params={
    'page': 1,
    'limit': 5
})
data = response.json()
print(f"Found {data['total']} jobs")
for job in data['items']:
    print(f"- {job['title']} ({job['posted_date']})")
```

---

### Example 2: Search for RBI Jobs

```bash
curl -X POST "http://localhost:8000/api/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "RBI",
    "limit": 5
  }'
```

```python
import requests

response = requests.post('http://localhost:8000/api/jobs/search', json={
    'keyword': 'RBI',
    'limit': 5
})
jobs = response.json()['items']
for job in jobs:
    print(f"{job['title']} - {job['url']}")
```

---

### Example 3: Get Job with Full Details

```bash
curl -X GET "http://localhost:8000/api/jobs/job_001/details"
```

```python
import requests

response = requests.get('http://localhost:8000/api/jobs/job_001/details')
job = response.json()

if response.status_code == 200:
    print(f"Title: {job['title']}")
    print(f"Description: {job['detailed_info']['description'][:200]}...")
    print(f"Application Fee: {job['detailed_info']['application_fee']}")
else:
    print("Details not yet crawled")
```

---

### Example 4: Search Results with Filters

```python
import requests

# Search for IBPS results from Jan 2024
response = requests.post('http://localhost:8000/api/results/search', json={
    'keyword': 'IBPS',
    'start_date': '2024-01-01',
    'end_date': '2024-01-31',
    'page': 1,
    'limit': 10
})

results = response.json()
print(f"Found {results['total']} matching results")
```

---

### Example 5: Get Statistics

```bash
curl -X GET "http://localhost:8000/api/stats"
```

```python
import requests

response = requests.get('http://localhost:8000/api/stats')
stats = response.json()

print(f"Total Jobs: {stats['total_jobs']}")
print(f"Jobs with Details: {stats['jobs_with_details']}")
print(f"Database Size: {stats['database_size_mb']} MB")
```

---

## Error Handling

### Handling Different Status Codes

```python
import requests

try:
    response = requests.get('http://localhost:8000/api/jobs/invalid_id')
    
    if response.status_code == 200:
        job = response.json()
        print(f"Found: {job['title']}")
    
    elif response.status_code == 206:
        print("Details not yet crawled. Run detail crawler first.")
    
    elif response.status_code == 404:
        error = response.json()
        print(f"Error: {error['detail']}")
    
    elif response.status_code == 500:
        print("Server error. Try again later.")
    
except requests.exceptions.RequestException as e:
    print(f"Connection error: {e}")
```

---

## Pagination

All list endpoints support pagination:

```python
import requests

page = 1
limit = 20

while True:
    response = requests.get('http://localhost:8000/api/jobs', params={
        'page': page,
        'limit': limit
    })
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

Currently no rate limiting is enforced. For production, consider:
- Adding rate limiting middleware
- Implementing IP-based throttling
- Using API keys for authentication

---

## CORS

The API allows requests from all origins by default. For production, modify CORS settings in `src/api/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Performance Tips

### 1. Use Pagination
Always use pagination to limit data transfer:
```python
requests.get('http://localhost:8000/api/jobs', params={'limit': 50})
```

### 2. Filter Before Fetching
Use search/filter endpoints instead of fetching all data:
```python
# Good: Server-side filtering
requests.post('http://localhost:8000/api/jobs/search', json={
    'keyword': 'RBI'
})

# Avoid: Client-side filtering of all data
requests.get('http://localhost:8000/api/jobs?limit=10000')
```

### 3. Use Details Only Filter
Fetch only items with details already crawled:
```python
requests.get('http://localhost:8000/api/jobs/filter/with-details')
```

---

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run_api.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  crawler:
    image: job-crawler:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
```

---

## Troubleshooting

### Issue: API won't start
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:** Install dependencies
```bash
pip install fastapi uvicorn pydantic
```

### Issue: 404 errors on endpoints
- Check base URL: `http://localhost:8000/api`
- Verify API is running: `curl http://localhost:8000/health`
- Check endpoint path matches documentation

### Issue: Empty results
- Verify data has been crawled: `curl http://localhost:8000/api/stats`
- Run crawler first: `python run_crawler.py crawl`
- Check database files exist in `data/` directory

### Issue: Connection refused
- Verify server is running on port 8000
- Check firewall settings
- Try different port: `uvicorn src.api.app:app --port 8001`

---

## API Documentation Tools

### Swagger UI (Interactive)
Open browser to `http://localhost:8000/api/docs`

### ReDoc (Alternative docs)
Open browser to `http://localhost:8000/api/redoc`

### OpenAPI Schema (JSON)
`http://localhost:8000/api/openapi.json`

---

## Security Considerations

### For Production:
1. **Authentication:** Add API key or JWT authentication
2. **Rate Limiting:** Implement request rate limiting
3. **HTTPS:** Deploy with SSL/TLS certificates
4. **Input Validation:** Already handled by Pydantic
5. **CORS:** Restrict to specific domains
6. **Database Security:** Use credentials for sensitive data

---

## Future Enhancements

- [ ] Authentication and API keys
- [ ] Rate limiting and throttling
- [ ] Advanced filtering (by salary, location, etc.)
- [ ] Export formats (CSV, Excel, PDF)
- [ ] Webhooks for new job notifications
- [ ] Full-text search capabilities
- [ ] Machine learning recommendations
- [ ] GraphQL endpoint

---

## Support

For issues or questions:
1. Check API logs: `tail -f logs/crawler.log`
2. Review interactive docs: `/api/docs`
3. Verify database: Check `data/jobs.json`, `data/results.json`, `data/admit_cards.json`
4. Check GitHub issues: `https://github.com/Jadaunkg/job-portal-crawler`

---

**Last Updated:** January 15, 2026  
**API Version:** 1.0.0  
**Status:** Production Ready ✅
