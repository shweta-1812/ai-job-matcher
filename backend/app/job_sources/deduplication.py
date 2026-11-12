
import re
from urllib.parse import urlsplit, urlunsplit


COMPANY_ALIASES = {
    "artefactlinkedin": "artefact",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").casefold()).strip()


def canonical_company(job: dict) -> str:
    company = job.get("company") or {}
    name = (
        company.get("display_name", "")
        if isinstance(company, dict)
        else str(company)
    )
    normalized = normalize_text(name)
    return COMPANY_ALIASES.get(normalized, normalized)


def normalized_url(job: dict) -> str:
    url = (job.get("redirect_url") or "").strip()
    if not url:
        return ""

    parsed = urlsplit(url)
    return urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        "",
        "",
    ))


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """Remove confirmed duplicate URLs and matching job records."""
    seen_urls = set()
    seen_records = set()
    unique_jobs = []

    for job in jobs:
        company = canonical_company(job)
        title = normalize_text(job.get("title", ""))
        location = normalize_text(
            (job.get("location") or {}).get("display_name", "")
        )
        description = normalize_text(job.get("description", ""))
        url = normalized_url(job)

        record_key = (company, title, location, description)

        if url and url in seen_urls:
            continue

        # Avoid merging distinct vacancies based only on title.
        if description and record_key in seen_records:
            continue

        if url:
            seen_urls.add(url)

        if description:
            seen_records.add(record_key)

        unique_jobs.append(job)

    return unique_jobs
