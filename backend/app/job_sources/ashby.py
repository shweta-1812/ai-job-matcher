
import logging
import re
from html import unescape

import requests

from .job_schema import normalize_job

logger = logging.getLogger(__name__)


def clean_html(value: str) -> str:
    """Convert HTML descriptions into plain text."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def fetch_ashby_jobs(
    board_token: str,
    company_name: str,
) -> list[dict]:
    """Fetch and normalize jobs from a public Ashby board."""

    url = (
        "https://api.ashbyhq.com/posting-api/job-board/"
        f"{board_token}"
    )

    try:
        response = requests.get(
            url,
            timeout=20,
        )
        response.raise_for_status()

        raw_jobs = response.json().get("jobs", [])

        if not isinstance(raw_jobs, list):
            logger.warning(
                "Unexpected Ashby response for %s",
                board_token,
            )
            return []

    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            "Ashby fetch failed for %s: %s",
            board_token,
            exc,
        )
        return []

    normalized_jobs = []

    for job in raw_jobs:
        # Exclude unpublished job postings.
        if job.get("isListed") is False:
            continue

        description = (
            job.get("descriptionPlain")
            or clean_html(job.get("descriptionHtml", ""))
        )

        location = job.get("location", "")

        normalized_jobs.append(
            normalize_job(
                job_id=f"ashby-{board_token}-{job.get('id', '')}",
                title=job.get("title", ""),
                company=company_name,
                location=location,
                description=description,
                url=job.get("jobUrl", ""),
                source="Ashby",
                created=job.get("publishedAt") or "",
                category=job.get("department", ""),
            )
        )

    logger.info(
        "Fetched %s jobs from Ashby board %s",
        len(normalized_jobs),
        board_token,
    )

    return normalized_jobs
