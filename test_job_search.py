#!/usr/bin/env python3
"""
Test script to check job search functionality and available jobs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'backend'))

from app.adzuna_client import search_jobs

def test_search(query: str):
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
        count = test_search(query)
        results[query] = count
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for query, count in results.items():
        print(f"  '{query}': {count} jobs")
    
    print("\n💡 TIP: Use broader terms like 'engineer' or 'developer' for more results.")
    print("   The free job APIs have limited listings, especially for specific roles.")
