
import logging
import re
from html import unescape

import requests

from .job_schema import normalize_job

logger = logging.getLogger(__name__)


def clean_html(value: str) -> str:
    """Convert HTML descriptions to plain text."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def fetch_lever_jobs(
    board_token: str,
    company_name: str,
) -> list[dict]:
    """Fetch and normalize jobs from a public Lever board."""

    url = f"https://api.lever.co/v0/postings/{board_token}"

    try:
        response = requests.get(
            url,
            params={"mode": "json"},
            timeout=20,
        )
        response.raise_for_status()
        raw_jobs = response.json()

        if not isinstance(raw_jobs, list):
            logger.warning(
                "Unexpected Lever response for %s",
                board_token,
            )
            return []

    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            "Lever fetch failed for %s: %s",
            board_token,
            exc,
        )
        return []

    normalized_jobs = []

    for job in raw_jobs:
        categories = job.get("categories") or {}

        location = categories.get("location", "")
        department = categories.get("department", "")

        description = (
            job.get("descriptionPlain")
            or clean_html(job.get("description", ""))
        )

        additional = job.get("additionalPlain", "")

        if additional:
            description = f"{description}\n{additional}".strip()

        normalized_jobs.append(
            normalize_job(
                job_id=f"lever-{board_token}-{job.get('id', '')}",
                title=job.get("text", ""),
                company=company_name,
                location=location,
                description=description,
                url=job.get("hostedUrl", ""),
                source="Lever",
                created="",
                category=department,
            )
        )

    logger.info(
        "Fetched %s jobs from Lever board %s",
        len(normalized_jobs),
        board_token,
    )

    return normalized_jobs
