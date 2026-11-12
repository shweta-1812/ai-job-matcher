"""Best-effort, bounded discovery of ATS links from public job pages.

Only public HTTP(S) destinations are allowed. No login, bypass, or JavaScript.
"""
import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse
import requests

from .ats_detector import detect_ats

ALLOWED_PORTS = {None, 80, 443}
MAX_HTML_BYTES = 350_000
MAX_REDIRECTS = 4
ATS_HOST_FRAGMENTS = ('greenhouse.io', 'lever.co', 'ashbyhq.com')


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("a", "link"):
            return

        values = dict(attrs)
        href = values.get("href")

        if href:
            self.urls.append(href)


def is_public_url(url, resolver=socket.getaddrinfo):
    """Reject local, private, reserved and non-HTTP(S) destinations."""
    try:
        p = urlparse(url)
        if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
            return False
        if p.port not in ALLOWED_PORTS:
            return False
        host = p.hostname.rstrip('.').lower()
        if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
            return False
        records = resolver(host, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        ips = [ipaddress.ip_address(item[4][0]) for item in records]
        return bool(ips) and all(ip.is_global for ip in ips)
    except (ValueError, OSError, TypeError):
        return False


def resolve_ats_urls(url, session=None, max_redirects=MAX_REDIRECTS):
    """Discover ATS links through public job pages and application redirects."""
    client = session or requests.Session()
    discovered = []
    visited = set()
    queue = [(url, 0)]

    while queue and len(visited) < 20:
        current, depth = queue.pop(0)

        if current in visited:
            continue

        visited.add(current)

        found = detect_ats(current)
        if found:
            discovered.append(current)
            continue

        if depth > max_redirects or not is_public_url(current):
            continue

        try:
            response = client.get(
                current,
                allow_redirects=False,
                timeout=(3, 8),
                headers={"User-Agent": "CareerJobBoardDiscovery/0.1"},
                stream=True,
            )

            try:
                if response.status_code in (301, 302, 303, 307, 308):
                    target = urljoin(
                        current,
                        response.headers.get("Location", ""),
                    )
                    queue.append((target, depth + 1))
                    continue

                if response.status_code != 200:
                    continue

                if "html" not in response.headers.get(
                    "Content-Type", ""
                ).lower():
                    continue

                chunks = []
                total = 0

                for chunk in response.iter_content(chunk_size=16384):
                    total += len(chunk)

                    if total > MAX_HTML_BYTES:
                        break

                    chunks.append(chunk)

                html = b"".join(chunks).decode(
                    response.encoding or "utf-8",
                    errors="replace",
                )

                parser = _Links()
                parser.feed(html)

                for href in parser.urls:
                    candidate = urljoin(current, href)

                    if detect_ats(candidate):
                        discovered.append(candidate)

                    elif (
                        urlparse(candidate).hostname
                        == urlparse(current).hostname
                        and urlparse(candidate).path.rstrip("/").endswith("/apply")
                    ):
                        queue.append((candidate, depth + 1))

            finally:
                response.close()

        except (requests.RequestException, ValueError, UnicodeError):
            continue

    return list(dict.fromkeys(discovered))[:25]
