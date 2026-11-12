
import logging
import re
from html import unescape

import requests

from .job_schema import normalize_job

logger = logging.getLogger(__name__)


def clean_html(value: str) -> str:
    """Convert HTML job descriptions to plain text."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def fetch_greenhouse_jobs(
    board_token: str,
    company_name: str,
) -> list[dict]:
    """Fetch and normalize jobs from a Greenhouse board."""

    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        f"{board_token}/jobs"
    )

    try:
        response = requests.get(
            url,
            params={"content": "true"},
            timeout=20,
        )
        response.raise_for_status()
        raw_jobs = response.json().get("jobs", [])

    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            "Greenhouse fetch failed for %s: %s",
            board_token,
            exc,
        )
        return []

    normalized_jobs = []

    for job in raw_jobs:
        normalized_jobs.append(
            normalize_job(
                job_id=f"greenhouse-{board_token}-{job.get('id')}",
                title=job.get("title", ""),
                company=company_name,
                location=(job.get("location") or {}).get("name", ""),
                description=clean_html(job.get("content", "")),
                url=job.get("absolute_url", ""),
                source="Greenhouse",
                # updated_at is not the original posting date.
                created="",
            )
        )

    logger.info(
        "Fetched %s jobs from %s",
        len(normalized_jobs),
        company_name,
    )

    return normalized_jobs
