
from backend.app.processing.title_filter import (
    match_score,
    filter_jobs_by_title,
)


def test_exact_phrase():
    assert match_score("Data Analyst", "Senior Data Analyst") == 1.0


def test_all_words():
    assert match_score("Data Analyst", "Analyst - Data Operations") == 0.8


def test_partial_match():
    assert match_score("Data Analyst", "Data Engineer") == 0.6


def test_no_match():
    assert match_score("Data Analyst", "Software Developer") == 0.0


def test_filter_jobs():
    jobs = [
        {"title": "Data Analyst"},
        {"title": "Data Engineer"},
        {"title": "Software Developer"},
    ]

    filtered = filter_jobs_by_title(
        jobs,
        query="Data Analyst",
        min_score=0.6,
    )

    assert len(filtered) == 2
