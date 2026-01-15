#!/usr/bin/env python3
"""
Fetch the top-most job from the live API and export it to a TXT file.

Usage:
  python scripts/export_top_job_from_api.py \
    --base https://job-crawler-api-0885.onrender.com \
    --output outputs/top_job_api.txt

Defaults:
  base: https://job-crawler-api-0885.onrender.com
  output: outputs/top_job_api.txt

The script:
- Calls GET /api/jobs?limit=1 to get the first job
- If needed, calls GET /api/jobs/{job_id}/details to enrich the description
- Writes a well-formatted text file with title, meta, and full description

Note: On Render free tier, first request after idle can take ~30s. The script retries a few times.
"""
from __future__ import annotations
import argparse
import time
from pathlib import Path
from textwrap import fill
from typing import Any, Dict

import requests

DEFAULT_BASE = "https://job-crawler-api-0885.onrender.com"


def fetch_json(url: str, *, timeout: int = 30, retries: int = 3, backoff: float = 2.0) -> Any:
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            # Some endpoints may not return JSON on occasional cold starts; try again if so
            if "application/json" in r.headers.get("Content-Type", ""):
                return r.json()
            last_err = RuntimeError(f"Non-JSON response from {url}: {r.text[:200]}")
        except Exception as e:
            last_err = e
        if i < retries - 1:
            time.sleep(backoff * (i + 1))
    raise last_err  # type: ignore[misc]


def get_top_job(base: str) -> Dict[str, Any]:
    # Fetch first page with a single item
    data = fetch_json(f"{base}/api/jobs?limit=1")
    items = []
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        items = data["items"]
    elif isinstance(data, list):
        items = data
    if not items:
        raise SystemExit("No jobs available from API")

    job = items[0]

    # Ensure detailed info if possible
    job_id = job.get("id")
    has_full = bool((job.get("detailed_info") or {}).get("full_description"))
    if job_id and not has_full:
        try:
            details = fetch_json(f"{base}/api/jobs/{job_id}/details")
            # Merge if structure matches expectation
            if isinstance(details, dict):
                # Details endpoint may wrap response; try common patterns
                if "detailed_info" in details:
                    job["detailed_info"] = details["detailed_info"]
                else:
                    # Fallback: if details looks like a job object, update fields
                    for k in ("detailed_info", "details_crawled"):
                        if k in details:
                            job[k] = details[k]
        except Exception:
            # Non-fatal: continue with whatever we have
            pass

    return job


def format_job(job: Dict[str, Any]) -> str:
    title = job.get("title") or "(No Title)"
    url = job.get("url") or ""
    portal = job.get("portal") or ""
    posted = job.get("posted_date") or ""
    scraped_at = job.get("scraped_at") or ""
    job_id = job.get("id") or ""

    detailed = job.get("detailed_info") or {}
    full_description = detailed.get("full_description") or detailed.get("description") or ""

    lines = []
    lines.append(title)
    lines.append("=" * max(8, min(len(title), 120)))
    lines.append("")

    meta = [
        ("ID", job_id),
        ("URL", url),
        ("Portal", portal),
        ("Posted", posted),
        ("Scraped", scraped_at),
    ]
    for k, v in meta:
        if v:
            lines.append(f"{k}: {v}")
    lines.append("")

    lines.append("Description:")
    lines.append("-" * 11)
    if full_description:
        for para in full_description.splitlines():
            if para.strip() == "":
                lines.append("")
            else:
                lines.append(fill(para, width=100))
    else:
        lines.append("(No detailed description available)")

    return "\n".join(lines).rstrip() + "\n"


def export_top_job_from_api(base: str, output_path: Path) -> Path:
    job = get_top_job(base)
    content = format_job(job)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export top-most job from live API to TXT")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Base API URL")
    parser.add_argument("--output", default="outputs/top_job_api.txt", help="Output TXT path")
    args = parser.parse_args()

    out = export_top_job_from_api(args.base, Path(args.output))
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
