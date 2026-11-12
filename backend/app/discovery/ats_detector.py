from urllib.parse import urlparse

HOSTS = {
    'greenhouse': {'job-boards.greenhouse.io', 'boards.greenhouse.io'},
    'lever': {'jobs.lever.co'},
    'ashby': {'jobs.ashbyhq.com'},
}

def detect_ats(url: str):
    """Return (provider, board_token) for a recognized public ATS URL, else None."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or '').lower().rstrip('.')
        if parsed.scheme not in ('http', 'https'):
            return None
        parts = [p for p in parsed.path.split('/') if p]
        if not parts:
            return None
        for provider, hosts in HOSTS.items():
            if host in hosts:
                token = parts[0]
                if token and token not in ('.', '..'):
                    return provider, token
    except (ValueError, TypeError):
        pass
    return None
