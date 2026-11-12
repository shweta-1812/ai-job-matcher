
import logging
import time

from .greenhouse import fetch_greenhouse_jobs
from .lever import fetch_lever_jobs
from .ashby import fetch_ashby_jobs
from .location_filter import location_matches
from ..processing.title_filter import filter_jobs_by_title
from .deduplication import deduplicate_jobs
from ..services.employer_registry import (connect_registry,get_boards,)

logger = logging.getLogger(__name__)

FETCHERS = {
    "greenhouse": fetch_greenhouse_jobs,
    "lever": fetch_lever_jobs,
    "ashby": fetch_ashby_jobs,
}


def fetch_ats_jobs(
    country: str,
    city: str | None = None,
    job_title: str | None = None,
) -> list[dict]:
    """Fetch ATS jobs, filter by location, and log metrics."""

    pipeline_start = time.perf_counter()

    conn = connect_registry()

    try:
        boards = get_boards(conn, status="valid")
    finally:
        conn.close()

    logger.info("Found %s verified ATS boards", len(boards))

    jobs = []

    total_fetched = 0
    total_location_matched = 0
    total_title_matched = 0
    total_fetch_time = 0.0
    total_filter_time = 0.0
    successful_boards = 0
    failed_boards = 0

    for provider, token in boards:
        fetcher = FETCHERS.get(provider)

        if fetcher is None:
            logger.warning("Unsupported ATS provider: %s", provider)
            continue

        try:
            # Stage 1: Fetch jobs
            fetch_start = time.perf_counter()

            board_jobs = fetcher(
                board_token=token,
                company_name=token,
            )

            fetch_time = time.perf_counter() - fetch_start

            total_fetch_time += fetch_time
            total_fetched += len(board_jobs)

            # Stage 2: Location filtering
            filter_start = time.perf_counter()

            matching_jobs = [
                job
                for job in board_jobs
                if location_matches(
                    location=job.get("location", {}).get(
                        "display_name", ""
                    ),
                    country=country,
                    city=city,
                    include_unknown=False,
                )
            ]

            filter_time = time.perf_counter() - filter_start

            total_filter_time += filter_time
            total_location_matched += len(matching_jobs)

            # Stage 3: Filter by job-title relevance
            title_matched_jobs = filter_jobs_by_title(
                matching_jobs,
                query=job_title or "",
                min_score=0.4,
            )

            total_title_matched += len(title_matched_jobs)

            jobs.extend(title_matched_jobs)
            successful_boards += 1

            logger.info(
                "%s/%s: fetched=%s, matched=%s, "
                "fetch_time=%.3fs, filter_time=%.3fs",
                provider,
                token,
                len(board_jobs),
                len(matching_jobs),
                fetch_time,
                filter_time,
            )

        except Exception:
            failed_boards += 1
            logger.exception(
                "Unexpected error fetching ATS board %s/%s",
                provider,
                token,
            )

    # Stage 4: Remove duplicate jobs across ATS boards
    before_dedup = len(jobs)
    jobs = deduplicate_jobs(jobs)
    duplicates_removed = before_dedup - len(jobs)

    total_time = time.perf_counter() - pipeline_start

    removed_by_location = (
        total_fetched - total_location_matched
    )

    reduction_pct = (
        removed_by_location / total_fetched * 100
        if total_fetched else 0
    )

    logger.info("========== ATS PIPELINE METRICS ==========")
    logger.info("Verified boards: %s", len(boards))
    logger.info("Successful boards: %s", successful_boards)
    logger.info("Failed boards: %s", failed_boards)
    logger.info("Jobs fetched: %s", total_fetched)
    logger.info("Location-matched jobs: %s", total_location_matched)
    logger.info("Title-matched jobs: %s", total_title_matched)
    logger.info("Duplicates removed: %s", duplicates_removed)
    logger.info("Final unique ATS jobs: %s", len(jobs))
    logger.info("Jobs excluded by location: %s", removed_by_location)
    logger.info("Location reduction: %.2f%%", reduction_pct)
    logger.info("Total fetch time: %.3fs", total_fetch_time)
    logger.info("Total filter time: %.3fs", total_filter_time)
    logger.info("End-to-end time: %.3fs", total_time)
    logger.info("==========================================")

    return jobs
