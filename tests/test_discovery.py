import tempfile
import unittest
from pathlib import Path
from backend.app.discovery.ats_detector import detect_ats
from backend.app.discovery.employer_discovery import discover_from_jobs, discover_from_urls
from backend.app.services.employer_registry import connect_registry, get_boards

class DiscoveryTests(unittest.TestCase):
    def test_detector(self):
        self.assertEqual(detect_ats('https://job-boards.greenhouse.io/stripe/jobs/123'), ('greenhouse', 'stripe'))
        self.assertEqual(detect_ats('https://jobs.lever.co/example/123'), ('lever', 'example'))
        self.assertEqual(detect_ats('https://jobs.ashbyhq.com/example/123'), ('ashby', 'example'))
        self.assertIsNone(detect_ats('https://evil.com/jobs.lever.co/example'))

    def test_job_sources_and_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            conn = connect_registry(Path(d) / 'registry.sqlite3')
            jobs = [{'source': 'Adzuna', 'redirect_url': 'https://job-boards.greenhouse.io/stripe/jobs/1'},
                    {'source': 'Remotive', 'url': 'https://job-boards.greenhouse.io/stripe/jobs/2'},
                    {'source': 'Arbeitnow', 'redirect_url': 'https://jobs.lever.co/example/3'}]
            fake_validator = lambda provider, token: 'valid'
            result = discover_from_jobs(jobs, conn, fake_validator)
            self.assertEqual(result['valid'], 2)
            self.assertEqual(len(get_boards(conn)), 2)
            discover_from_urls(['https://jobs.lever.co/example/4'], conn, 'search_api', fake_validator)
            self.assertEqual(len(get_boards(conn)), 2)
            conn.close()

if __name__ == '__main__':
    unittest.main()
