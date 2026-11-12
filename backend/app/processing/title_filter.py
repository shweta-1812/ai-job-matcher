
def match_score(query: str, text: str) -> float:
    """
    Calculate job-title relevance.

    Exact phrase: 1.0
    All query words present: 0.8
    First query word present: 0.6
    Any query word present: 0.4
    No match: 0.0
    """
    query_lower = query.lower().strip()
    text_lower = (text or "").lower()

    if not query_lower:
        return 0.0

    if query_lower in text_lower:
        return 1.0

    query_words = [
        word for word in query_lower.split()
        if len(word) > 2
    ]

    if not query_words:
        return 0.0

    if len(query_words) > 1:
        if all(word in text_lower for word in query_words):
            return 0.8

        if query_words[0] in text_lower:
            return 0.6

    if any(word in text_lower for word in query_words):
        return 0.4

    return 0.0


def filter_jobs_by_title(
    jobs: list[dict],
    query: str,
    min_score: float = 0.4,
) -> list[dict]:
    """Keep jobs meeting the minimum title relevance score."""
    if not query or not query.strip():
        return jobs

    return [
        job for job in jobs
        if match_score(query, job.get("title", "")) >= min_score
    ]
