import requests

ENDPOINTS = {
    'greenhouse': 'https://boards-api.greenhouse.io/v1/boards/{token}/jobs',
    'lever': 'https://api.lever.co/v0/postings/{token}?mode=json',
    'ashby': 'https://api.ashbyhq.com/posting-api/job-board/{token}',
}

def validate_board(provider: str, token: str, session=None) -> str:
    """Return valid, invalid, or unknown (network/rate-limit/server issue)."""
    if provider not in ENDPOINTS or not token or '/' in token:
        return 'invalid'
    client = session or requests
    try:
        response = client.get(ENDPOINTS[provider].format(token=token), timeout=12)
        if response.status_code in (404, 410):
            return 'invalid'
        if response.status_code != 200:
            return 'unknown'
        payload = response.json()
        if provider == 'greenhouse':
            ok = isinstance(payload, dict) and isinstance(payload.get('jobs'), list)
        elif provider == 'lever':
            ok = isinstance(payload, list)
        else:
            ok = isinstance(payload, dict) and isinstance(payload.get('jobs'), list)
        return 'valid' if ok else 'unknown'
    except (requests.RequestException, ValueError):
        return 'unknown'
