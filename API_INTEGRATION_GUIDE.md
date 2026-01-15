# How to Use Job Portal Crawler API in Your Main Project 🔌

This guide explains how to integrate the Job Portal Crawler API into your main project application.

---

## Table of Contents

1. [Setup & Installation](#setup--installation)
2. [Basic Usage](#basic-usage)
3. [Python Integration](#python-integration)
4. [JavaScript/Node.js Integration](#javascriptnodejs-integration)
5. [Practical Examples](#practical-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Setup & Installation

### Prerequisites

- Job Portal Crawler API running on `http://localhost:8000`
- Your main project (Python, Node.js, etc.)

### Step 1: Start the Crawler API

In the Job Crawler project directory:

```bash
# Start the API server
python run_api.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Verify API is Running

```bash
# Test API status
curl http://localhost:8000/api/status

# Expected response:
{
  "status": "operational",
  "version": "1.0.0",
  ...
}
```

---

## Basic Usage

### API Base URL
```
http://localhost:8000/api
```

### Main Endpoints
```
Jobs:        /api/jobs
Results:     /api/results
Admit Cards: /api/admit-cards
```

---

## Python Integration

### Installation

Add to your project's `requirements.txt`:

```
requests>=2.31.0
```

Install:
```bash
pip install requests
```

### Basic Example

```python
import requests

# API configuration
API_BASE = "http://localhost:8000/api"

def get_jobs():
    """Fetch all jobs from crawler API."""
    response = requests.get(f"{API_BASE}/jobs", params={'limit': 10})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code}")

# Usage
jobs_data = get_jobs()
print(f"Found {jobs_data['total']} jobs")
```

---

### Python Helper Class

Create a `crawler_client.py` in your main project:

```python
"""
Job Portal Crawler API Client.
Simple wrapper for consuming the crawler API.
"""
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime


class CrawlerAPIClient:
    """Client for Job Portal Crawler API."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api", timeout: int = 10):
        """
        Initialize API client.
        
        Args:
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    # ==================== Jobs ====================
    
    def get_jobs(self, page: int = 1, limit: int = 10) -> Dict:
        """Get paginated list of jobs."""
        return self._request('GET', '/jobs', params={'page': page, 'limit': limit})
    
    def get_job(self, job_id: str) -> Dict:
        """Get specific job by ID."""
        return self._request('GET', f'/jobs/{job_id}')
    
    def get_job_details(self, job_id: str) -> Dict:
        """Get job with extracted page details."""
        return self._request('GET', f'/jobs/{job_id}/details')
    
    def search_jobs(self, 
                   keyword: Optional[str] = None,
                   portal: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   details_only: bool = False,
                   page: int = 1,
                   limit: int = 10) -> Dict:
        """Search jobs with filters."""
        payload = {
            'keyword': keyword,
            'portal': portal,
            'start_date': start_date,
            'end_date': end_date,
            'details_only': details_only,
            'page': page,
            'limit': limit
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request('POST', '/jobs/search', json=payload)
    
    def get_jobs_by_portal(self, portal: str, page: int = 1, limit: int = 10) -> Dict:
        """Get jobs from specific portal."""
        return self._request('GET', f'/jobs/filter/by-portal/{portal}', 
                           params={'page': page, 'limit': limit})
    
    def get_jobs_with_details(self, page: int = 1, limit: int = 10) -> Dict:
        """Get only jobs with extracted details."""
        return self._request('GET', '/jobs/filter/with-details',
                           params={'page': page, 'limit': limit})
    
    # ==================== Results ====================
    
    def get_results(self, page: int = 1, limit: int = 10) -> Dict:
        """Get paginated list of results."""
        return self._request('GET', '/results', params={'page': page, 'limit': limit})
    
    def get_result(self, result_id: str) -> Dict:
        """Get specific result by ID."""
        return self._request('GET', f'/results/{result_id}')
    
    def get_result_details(self, result_id: str) -> Dict:
        """Get result with extracted details."""
        return self._request('GET', f'/results/{result_id}/details')
    
    def search_results(self,
                      keyword: Optional[str] = None,
                      portal: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      details_only: bool = False,
                      page: int = 1,
                      limit: int = 10) -> Dict:
        """Search results with filters."""
        payload = {
            'keyword': keyword,
            'portal': portal,
            'start_date': start_date,
            'end_date': end_date,
            'details_only': details_only,
            'page': page,
            'limit': limit
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request('POST', '/results/search', json=payload)
    
    # ==================== Admit Cards ====================
    
    def get_admit_cards(self, page: int = 1, limit: int = 10) -> Dict:
        """Get paginated list of admit cards."""
        return self._request('GET', '/admit-cards', params={'page': page, 'limit': limit})
    
    def get_admit_card(self, card_id: str) -> Dict:
        """Get specific admit card by ID."""
        return self._request('GET', f'/admit-cards/{card_id}')
    
    def get_admit_card_details(self, card_id: str) -> Dict:
        """Get admit card with extracted details."""
        return self._request('GET', f'/admit-cards/{card_id}/details')
    
    def search_admit_cards(self,
                          keyword: Optional[str] = None,
                          portal: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          details_only: bool = False,
                          page: int = 1,
                          limit: int = 10) -> Dict:
        """Search admit cards with filters."""
        payload = {
            'keyword': keyword,
            'portal': portal,
            'start_date': start_date,
            'end_date': end_date,
            'details_only': details_only,
            'page': page,
            'limit': limit
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request('POST', '/admit-cards/search', json=payload)
    
    # ==================== System ====================
    
    def get_status(self) -> Dict:
        """Get API status."""
        return self._request('GET', '/status')
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return self._request('GET', '/stats')
    
    def get_portal_stats(self) -> List[Dict]:
        """Get statistics per portal."""
        return self._request('GET', '/stats/by-portal')


# Usage example
if __name__ == "__main__":
    client = CrawlerAPIClient()
    
    # Get jobs
    jobs = client.get_jobs(limit=5)
    print(f"Total jobs: {jobs['total']}")
    
    # Search
    results = client.search_jobs(keyword="RBI", limit=5)
    print(f"RBI jobs: {results['total']}")
    
    # Get stats
    stats = client.get_stats()
    print(f"Stats: {stats}")
```

### Integration in Your Application

```python
from crawler_client import CrawlerAPIClient

# Initialize client
crawler = CrawlerAPIClient()

# In your view/route
def job_list_view(request):
    """Display jobs in your application."""
    try:
        # Fetch from crawler API
        data = crawler.get_jobs(page=1, limit=20)
        
        return {
            'jobs': data['items'],
            'total': data['total'],
            'pages': data['total_pages']
        }
    except Exception as e:
        return {'error': str(e)}

# Django example
from django.shortcuts import render
from django.http import JsonResponse

def jobs(request):
    """Django view for jobs."""
    page = request.GET.get('page', 1)
    
    try:
        data = crawler.get_jobs(page=int(page), limit=20)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Flask example
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/jobs')
def get_jobs():
    """Flask route for jobs."""
    try:
        data = crawler.get_jobs(limit=20)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## JavaScript/Node.js Integration

### Installation

```bash
npm install axios
# or
npm install fetch-retry
```

### Basic Example

```javascript
// crawler-client.js
const axios = require('axios');

const API_BASE = 'http://localhost:8000/api';

class CrawlerClient {
    constructor(baseUrl = API_BASE, timeout = 10000) {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            timeout: timeout
        });
    }

    // Jobs
    async getJobs(page = 1, limit = 10) {
        const response = await this.client.get('/jobs', {
            params: { page, limit }
        });
        return response.data;
    }

    async getJob(jobId) {
        const response = await this.client.get(`/jobs/${jobId}`);
        return response.data;
    }

    async searchJobs(filters = {}) {
        const response = await this.client.post('/jobs/search', {
            page: filters.page || 1,
            limit: filters.limit || 10,
            keyword: filters.keyword,
            portal: filters.portal,
            ...filters
        });
        return response.data;
    }

    // Results
    async getResults(page = 1, limit = 10) {
        const response = await this.client.get('/results', {
            params: { page, limit }
        });
        return response.data;
    }

    async searchResults(filters = {}) {
        const response = await this.client.post('/results/search', {
            page: filters.page || 1,
            limit: filters.limit || 10,
            ...filters
        });
        return response.data;
    }

    // Admit Cards
    async getAdmitCards(page = 1, limit = 10) {
        const response = await this.client.get('/admit-cards', {
            params: { page, limit }
        });
        return response.data;
    }

    async searchAdmitCards(filters = {}) {
        const response = await this.client.post('/admit-cards/search', {
            page: filters.page || 1,
            limit: filters.limit || 10,
            ...filters
        });
        return response.data;
    }

    // System
    async getStatus() {
        const response = await this.client.get('/status');
        return response.data;
    }

    async getStats() {
        const response = await this.client.get('/stats');
        return response.data;
    }
}

module.exports = CrawlerClient;
```

### Node.js Usage

```javascript
const CrawlerClient = require('./crawler-client');

const crawler = new CrawlerClient();

// Get jobs
async function showJobs() {
    try {
        const data = await crawler.getJobs(1, 10);
        console.log(`Total jobs: ${data.total}`);
        data.items.forEach(job => {
            console.log(`- ${job.title} (${job.posted_date})`);
        });
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Search
async function searchRBIJobs() {
    try {
        const results = await crawler.searchJobs({ keyword: 'RBI' });
        console.log(`Found ${results.total} RBI jobs`);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

showJobs();
searchRBIJobs();
```

### Express.js Integration

```javascript
const express = require('express');
const CrawlerClient = require('./crawler-client');

const app = express();
const crawler = new CrawlerClient();

// Get jobs endpoint
app.get('/api/jobs', async (req, res) => {
    try {
        const page = req.query.page || 1;
        const limit = req.query.limit || 10;
        const data = await crawler.getJobs(page, limit);
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Search jobs endpoint
app.post('/api/jobs/search', async (req, res) => {
    try {
        const results = await crawler.searchJobs(req.body);
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

### React Integration

```javascript
// hooks/useCrawler.js
import { useState, useEffect } from 'react';
import CrawlerClient from '../crawler-client';

const crawler = new CrawlerClient();

export function useJobs(page = 1, limit = 10) {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchJobs() {
            try {
                setLoading(true);
                const data = await crawler.getJobs(page, limit);
                setJobs(data.items);
                setError(null);
            } catch (err) {
                setError(err.message);
                setJobs([]);
            } finally {
                setLoading(false);
            }
        }

        fetchJobs();
    }, [page, limit]);

    return { jobs, loading, error };
}

// Component usage
import { useJobs } from './hooks/useCrawler';

function JobList() {
    const [page, setPage] = useState(1);
    const { jobs, loading, error } = useJobs(page, 10);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            {jobs.map(job => (
                <div key={job.id} className="job-card">
                    <h3>{job.title}</h3>
                    <p>{job.posted_date}</p>
                    <a href={job.url}>View Job</a>
                </div>
            ))}
            <button onClick={() => setPage(page - 1)}>Previous</button>
            <button onClick={() => setPage(page + 1)}>Next</button>
        </div>
    );
}
```

---

## Practical Examples

### Example 1: Django Job Portal

```python
# models.py
from django.db import models

class JobCache(models.Model):
    """Cache crawled jobs in your database."""
    crawler_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    portal = models.CharField(max_length=100)
    posted_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)

# views.py
from django.shortcuts import render
from django.core.paginator import Paginator
from crawler_client import CrawlerAPIClient

crawler = CrawlerAPIClient()

def job_list(request):
    """List jobs from crawler API."""
    try:
        page = request.GET.get('page', 1)
        data = crawler.get_jobs(page=int(page), limit=20)
        
        # Optional: Sync to local cache
        for job in data['items']:
            JobCache.objects.update_or_create(
                crawler_id=job['id'],
                defaults={
                    'title': job['title'],
                    'url': job['url'],
                    'portal': job['portal'],
                    'posted_date': job['posted_date']
                }
            )
        
        context = {
            'jobs': data['items'],
            'total': data['total'],
            'page': page,
            'total_pages': data['total_pages']
        }
        return render(request, 'jobs/list.html', context)
    
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})
```

### Example 2: Flask Search Application

```python
from flask import Flask, render_template, request, jsonify
from crawler_client import CrawlerAPIClient

app = Flask(__name__)
crawler = CrawlerAPIClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Search jobs/results/admit cards."""
    data = request.json
    category = data.get('category', 'jobs')
    keyword = data.get('keyword', '')
    
    try:
        if category == 'jobs':
            results = crawler.search_jobs(keyword=keyword)
        elif category == 'results':
            results = crawler.search_results(keyword=keyword)
        else:  # admit_cards
            results = crawler.search_admit_cards(keyword=keyword)
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Example 3: React Job Search App

```javascript
// App.js
import React, { useState } from 'react';
import CrawlerClient from './crawler-client';
import JobCard from './components/JobCard';
import SearchForm from './components/SearchForm';

const crawler = new CrawlerClient();

function App() {
    const [jobs, setJobs] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(1);

    const handleSearch = async (filters) => {
        setLoading(true);
        try {
            const results = await crawler.searchJobs({
                ...filters,
                page: 1,
                limit: 20
            });
            setJobs(results.items);
            setTotal(results.total);
            setPage(1);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleNextPage = async () => {
        setLoading(true);
        try {
            const results = await crawler.getJobs(page + 1, 20);
            setJobs(results.items);
            setPage(page + 1);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
            <h1>Job Portal</h1>
            <SearchForm onSearch={handleSearch} />
            
            {loading && <p>Loading...</p>}
            
            <div className="jobs-list">
                {jobs.map(job => (
                    <JobCard key={job.id} job={job} />
                ))}
            </div>
            
            <p>Total: {total}</p>
            {jobs.length > 0 && (
                <button onClick={handleNextPage}>Next Page</button>
            )}
        </div>
    );
}

export default App;
```

---

## Best Practices

### 1. Error Handling

```python
from requests.exceptions import Timeout, ConnectionError

def safe_api_call(func, *args, **kwargs):
    """Safely call API with error handling."""
    try:
        return func(*args, **kwargs)
    except Timeout:
        print("API request timed out")
    except ConnectionError:
        print("Cannot connect to API - is it running?")
    except Exception as e:
        print(f"API error: {e}")
    return None
```

### 2. Caching

```python
from functools import lru_cache
import time

class CachedCrawler:
    """Crawler with simple caching."""
    def __init__(self, cache_ttl=300):
        self.crawler = CrawlerAPIClient()
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def get_jobs(self, page=1, limit=10):
        key = f"jobs_{page}_{limit}"
        now = time.time()
        
        if key in self.cache:
            data, timestamp = self.cache[key]
            if now - timestamp < self.cache_ttl:
                return data
        
        data = self.crawler.get_jobs(page, limit)
        self.cache[key] = (data, now)
        return data
```

### 3. Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_jobs_with_retry():
    crawler = CrawlerAPIClient()
    return crawler.get_jobs()
```

### 4. Rate Limiting

```python
from time import sleep

class RateLimitedCrawler:
    def __init__(self, requests_per_second=10):
        self.crawler = CrawlerAPIClient()
        self.rate_limit = 1.0 / requests_per_second
        self.last_request = 0
    
    def api_call(self, func, *args, **kwargs):
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            sleep(self.rate_limit - elapsed)
        
        self.last_request = time.time()
        return func(*args, **kwargs)
```

---

## Troubleshooting

### Issue: Connection Refused

**Error:** `ConnectionError: Connection refused`

**Solution:**
```bash
# Verify API is running
curl http://localhost:8000/api/status

# If not running, start it:
cd /path/to/job-crawler
python run_api.py
```

### Issue: Timeout Errors

**Error:** `RequestException: Timeout`

**Solution:**
```python
# Increase timeout
crawler = CrawlerAPIClient(timeout=30)

# Add retry logic (see Best Practices)
```

### Issue: Empty Results

**Solution:**
```python
# Check database stats
stats = crawler.get_stats()
print(f"Total jobs: {stats['total_jobs']}")

# If zero, run crawler first:
# python run_crawler.py crawl
```

### Issue: CORS Errors (Browser/Frontend)

**Solution:** API already allows CORS. If issues persist:
```python
# In src/api/app.py, modify:
allow_origins=["http://localhost:3000", "https://yourdomain.com"]
```

---

## Summary

To use the Job Portal Crawler API in your main project:

1. **Start the API:** `python run_api.py`
2. **Install client library:** `pip install requests` (Python) or `npm install axios` (Node.js)
3. **Import the client:** Use provided `CrawlerAPIClient` class
4. **Make requests:** Call methods like `get_jobs()`, `search_jobs()`, etc.
5. **Handle responses:** Check status codes and parse JSON
6. **Cache results:** Implement caching for better performance
7. **Monitor errors:** Add proper error handling and logging

The API provides real-time access to crawled job data with full search and filtering capabilities.

---

**Next Steps:**
- [ ] Copy `crawler_client.py` to your project
- [ ] Test API connectivity
- [ ] Implement in your views/routes
- [ ] Add error handling and caching
- [ ] Deploy API for production use

Good luck! 🚀
