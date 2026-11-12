"""Run from project root: python run_discovery.py --country de --query 'data analyst' --city Berlin"""
import argparse
from backend.app.adzuna_client import search_jobs
from backend.app.discovery.employer_discovery import discover_from_jobs
from backend.app.services.employer_registry import connect_registry, get_boards


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', default='de')
    parser.add_argument('--query', default='data analyst')
    parser.add_argument('--city', default='Berlin')
    parser.add_argument('--pages', type=int, default=1)
    parser.add_argument('--inspect-links', type=int, default=10,
                        help='Max number of aggregator pages to inspect per results page (0 disables)')
    args = parser.parse_args()
    if args.pages < 1 or args.inspect_links < 0:
        parser.error('--pages must be >= 1 and --inspect-links must be >= 0')
    conn = connect_registry()
    try:
        for page in range(1, args.pages + 1):
            response = search_jobs(country=args.country, page=page, what=args.query,
                                   where=args.city, results_per_page=50)
            jobs = response.get('results', [])
            result = discover_from_jobs(jobs, conn, resolve_links=args.inspect_links > 0,
                                        max_pages=args.inspect_links)
            print(f'Page {page}: {len(jobs)} jobs; board validation: {result}')
        print('Total verified boards:', len(get_boards(conn)))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
