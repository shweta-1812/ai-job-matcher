
import logging

from ..adzuna_client import search_jobs, enrich_descriptions
from ..job_sources.deduplication import deduplicate_jobs
from ..processing.language_filter import filter_jobs_by_language
from ..job_sources.ats_aggregator import fetch_ats_jobs

logger = logging.getLogger(__name__)


def collect_jobs(
    job_title: str,
    country: str,
    city: str | None,
    pages: int,
    results_per_page: int,
    max_days_old: int | None,
    language: str = "Any",
) -> list[dict]:
    """Collect and process jobs using the existing search sources."""

    jobs = []

    # Stage 1: Fetch Adzuna, Remotive and Arbeitnow jobs
    for page in range(1, pages + 1):
        try:
            response = search_jobs(
                country=country,
                page=page,
                what=job_title,
                where=city,
                results_per_page=results_per_page,
                max_days_old=max_days_old,
            )

            page_jobs = response.get("results", [])
            jobs.extend(page_jobs)

            logger.info(
                "Page %s: fetched %s jobs from %s",
                page,
                len(page_jobs),
                response.get("sources", {}),
            )

        except Exception:
            logger.exception(
                "Failed to fetch jobs for page %s",
                page,
            )

    # Stage 2: Fetch Greenhouse, Lever and Ashby jobs
    try:
        ats_jobs = fetch_ats_jobs(
            country=country,
            city=city,
            job_title=job_title,
        )

        jobs.extend(ats_jobs)

        logger.info(
            "Added %s ATS jobs",
            len(ats_jobs),
        )

    except Exception:
        logger.exception("Failed to fetch ATS jobs")

    # Stage 3: Check whether any jobs were found
    if not jobs:
        return []

    logger.info("Jobs before deduplication: %s", len(jobs))
    jobs = deduplicate_jobs(jobs)
    logger.info("Jobs after deduplication: %s", len(jobs))

    enrich_descriptions(jobs)

    jobs = filter_jobs_by_language(jobs, language)

    logger.info(
        "Jobs after language filtering (%s): %s",
        language,
        len(jobs),
    )

    return jobs
