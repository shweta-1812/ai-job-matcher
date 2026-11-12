import tempfile
import unittest
from pathlib import Path
from backend.app.discovery.employer_discovery import discover_from_jobs
from backend.app.discovery.url_resolver import is_public_url, resolve_ats_urls
from backend.app.services.employer_registry import connect_registry, get_boards


class _Response:
    def __init__(self, status, headers=None, body=b''):
        self.status_code = status
        self.headers = headers or {}
        self.encoding = 'utf-8'
        self.body = body

    def iter_content(self, chunk_size):
        yield self.body

    def close(self):
        pass


class _Session:
    def get(self, url, **kwargs):
        return _Response(200, {'Content-Type': 'text/html'},
                         b'<a href="https://jobs.lever.co/example/123">Apply</a>')


class NoBraveTests(unittest.TestCase):
    def test_reject_private_ips(self):
        def resolver(host, port, **kwargs):
            return [(None, None, None, None, ('127.0.0.1', port))]
        self.assertFalse(is_public_url('http://localhost/', resolver=resolver))
        self.assertFalse(is_public_url('http://example.com/', resolver=resolver))

    def test_public_page_link(self):
        from unittest.mock import patch
        with patch('backend.app.discovery.url_resolver.is_public_url', return_value=True):
            self.assertEqual(resolve_ats_urls('https://example.com/job', session=_Session()),
                             ['https://jobs.lever.co/example/123'])

    def test_discovery_resolves_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = connect_registry(Path(folder) / 'boards.sqlite3')
            jobs = [{'redirect_url': 'https://aggregator.example/job1'},
                    {'redirect_url': 'https://aggregator.example/job2'}]
            resolver = lambda url: ['https://jobs.lever.co/example/123']
            result = discover_from_jobs(jobs, conn, validator=lambda p, t: 'valid',
                                        resolve_links=True, resolver=resolver)
            self.assertEqual(result['valid'], 1)
            self.assertEqual(len(get_boards(conn)), 1)
            conn.close()


if __name__ == '__main__':
    unittest.main()
