
from typing import Any


def normalize_job(
    *,
    title: str,
    company: str,
    location: str,
    description: str,
    url: str,
    source: str,
    created: str = "",
    job_id: str = "",
    category: str = "",
) -> dict[str, Any]:
    """
    Standard job format for every provider and industry.

    Compatible with the existing AI Job Matcher.
    """
    return {
        "id": str(job_id),
        "title": title.strip(),
        "company": {
            "display_name": company.strip()
        },
        "location": {
            "display_name": location.strip()
        },
        "description": description or "",
        "redirect_url": url,
        "created": created or "",
        "source": source,
        "category": category or "Uncategorized",
        "_relevance_score": 0.0,
    }
