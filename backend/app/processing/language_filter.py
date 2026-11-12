
import re


GERMAN_PATTERNS = [
    r"\bgerman\b",
    r"\bdeutsch\w*\b",
    r"\bverhandlungssicher(es)?\s+deutsch\w*\b",
    r"\bsehr gute\s+deutschkenntnisse\b",
]

ENGLISH_PATTERNS = [
    r"\benglish\w*\b",
    r"\benglisch\w*\b",
    r"\bbusiness english\b",
    r"\bverhandlungssicher(es)?\s+englisch\w*\b",
]

CEFR_PATTERN = r"\b(a1|a2|b1|b2|c1|c2)\b"


def detect_languages(text: str) -> dict:
    """Detect mentions of German and English in job text."""
    t = (text or "").lower()

    has_german = any(re.search(p, t) for p in GERMAN_PATTERNS)
    has_english = any(re.search(p, t) for p in ENGLISH_PATTERNS)

    german_cefr = bool(
        re.search(
            rf"\b(german|deutsch\w*)\b.{{0,40}}{CEFR_PATTERN}",
            t,
        )
    )
    english_cefr = bool(
        re.search(
            rf"\b(english\w*|englisch\w*)\b.{{0,40}}{CEFR_PATTERN}",
            t,
        )
    )

    return {
        "german": has_german or german_cefr,
        "english": has_english or english_cefr,
    }


def language_tag_for(text: str) -> str:
    """Return the language tag used by the existing API."""
    langs = detect_languages(text)

    if langs["english"] and langs["german"]:
        return "English & German"
    if langs["english"]:
        return "English"
    if langs["german"]:
        return "German"
    return "Unspecified"


def filter_jobs_by_language(
    jobs: list[dict],
    language: str,
) -> list[dict]:
    """Apply the existing language-filtering behavior."""
    if language == "Any":
        return jobs

    filtered = []

    for job in jobs:
        title = job.get("title", "")
        description = job.get("description", "")
        tag = language_tag_for(f"{title} {description}")

        if language == "German" and tag in (
            "German",
            "English & German",
            "Unspecified",
        ):
            filtered.append(job)

        elif language == "English" and tag in (
            "English",
            "Unspecified",
        ):
            filtered.append(job)

    return filtered
