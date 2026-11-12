#!/usr/bin/env python3
"""
Test script to check job search functionality and available jobs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'backend'))

from app.adzuna_client import search_jobs

def run_search(query: str):
    print(f"\n{'='*60}")
    print(f"Searching for: '{query}'")
    print('='*60)

    result = search_jobs(country='de', page=1, what=query, where=None, results_per_page=50)

    print(f"\nTotal jobs found: {result['count']}")
    print(f"Sources: {result['sources']}")

    if result['results']:
        print(f"\nJob titles:")
        for i, job in enumerate(result['results'][:15], 1):
            print(f"  {i}. {job['title']} - {job['company']['display_name']} ({job['source']})")
    else:
        print("\nNo jobs found for this query.")

    return result['count']

if __name__ == "__main__":
    # Test various search terms
    queries = [
        "engineer",
        "developer",
        "data",
        "python",
        "software",
    ]

    print("\n" + "="*60)
    print("JOB SEARCH TEST - Testing multiple queries")
    print("="*60)

    results = {}
    for query in queries:
        count = run_search(query)
        results[query] = count

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for query, count in results.items():
        print(f"  '{query}': {count} jobs")

    print("\n💡 TIP: Use broader terms like 'engineer' or 'developer' for more results.")
    print("   The free job APIs have limited listings, especially for specific roles.")


def test_arbeitnow_filters_before_limit(monkeypatch):
    from datetime import datetime, timezone
    from unittest.mock import Mock
    import backend.app.adzuna_client as client

    today = datetime.now(timezone.utc).isoformat()

    arbeitnow_jobs = [
        {
            "title": "Data Analyst",
            "company_name": "Munich Company",
            "location": "Munich",
            "description": "Data analysis",
            "url": "https://example.com/munich",
            "created_at": today,
        },
        {
            "title": "Data Analyst",
            "company_name": "Berlin Company",
            "location": "Berlin",
            "description": "Python and SQL",
            "url": "https://example.com/berlin",
            "created_at": today,
        },
    ]

    def fake_get(url, **kwargs):
        response = Mock()
        response.raise_for_status.return_value = None

        if "arbeitnow.com" in url:
            response.json.return_value = {"data": arbeitnow_jobs}
        elif "remotive.com" in url:
            response.json.return_value = {"jobs": []}
        else:
            response.json.return_value = {"results": []}

        return response

    monkeypatch.setattr(client.requests, "get", fake_get)
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    result = client.search_jobs(
        country="de",
        page=1,
        what="Data Analyst",
        where="Berlin",
        results_per_page=1,
        max_days_old=30,
    )

    arbeitnow_results = [
        job for job in result["results"]
        if job.get("source") == "Arbeitnow"
    ]

    assert len(arbeitnow_results) == 1
    assert arbeitnow_results[0]["company"]["display_name"] == "Berlin Company"
