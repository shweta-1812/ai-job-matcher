"""Discover employer ATS boards from job listings (no search API required)."""
from .ats_detector import detect_ats
from .board_validator import validate_board
from .url_resolver import resolve_ats_urls
from urllib.parse import urlparse
from backend.app.services.employer_registry import save_board


def candidate_urls_from_jobs(jobs):
    for job in jobs:
        for key in ('redirect_url', 'url', 'apply_url'):
            value = job.get(key)
            if isinstance(value, str) and value.startswith(('https://', 'http://')):
                yield value


def discover_from_urls(urls, conn, source, validator=validate_board):
    """Validate and persist boards. Unreachable endpoints are marked unknown."""
    seen = set()
    counts = {'valid': 0, 'invalid': 0, 'unknown': 0}
    for url in urls:
        found = detect_ats(url)
        if not found or found in seen:
            continue
        seen.add(found)
        provider, token = found
        status = validator(provider, token)
        save_board(conn, provider, token, status, source)
        counts[status] += 1
    return counts


def discover_from_jobs(
    jobs,
    conn,
    validator=validate_board,
    resolve_links=False,
    resolver=resolve_ats_urls,
    max_pages=15,
):
    """Discover ATS boards, prioritizing accessible job sources."""

    urls = list(candidate_urls_from_jobs(jobs))

    if resolve_links and max_pages > 0:
        unique_urls = list(dict.fromkeys(urls))

        arbeitnow_urls = []
        remotive_urls = []
        other_urls = []
        adzuna_urls = []

        for url in unique_urls:
            host = (urlparse(url).hostname or "").lower()

            if host in ("arbeitnow.com", "www.arbeitnow.com") or host.endswith(".arbeitnow.com"):
                arbeitnow_urls.append(url)

            elif host in ("remotive.com", "www.remotive.com") or host.endswith(".remotive.com"):
                remotive_urls.append(url)

            elif host in ("adzuna.de", "www.adzuna.de") or host.endswith(".adzuna.de"):
                adzuna_urls.append(url)

            else:
                other_urls.append(url)

        # Prioritize accessible sources.
        selected_urls = (
            arbeitnow_urls
            + remotive_urls
            + other_urls
        )[:max_pages]

        print(
            "Discovery inspection:",
            f"Arbeitnow={len(arbeitnow_urls)},",
            f"Remotive={len(remotive_urls)},",
            f"Other={len(other_urls)},",
            f"Adzuna skipped={len(adzuna_urls)},",
            f"Selected={len(selected_urls)}",
        )

        for url in selected_urls:
            if not detect_ats(url):
                urls.extend(resolver(url))

    return discover_from_urls(
        urls,
        conn,
        "job_sources",
        validator,
    )
