
from backend.app.processing.language_filter import (
    detect_languages,
    language_tag_for,
    filter_jobs_by_language,
)


def test_detect_german():
    assert detect_languages("Sehr gute Deutschkenntnisse")["german"]


def test_detect_english():
    assert detect_languages("Fluent English required")["english"]


def test_language_tags():
    assert language_tag_for("English and German required") == "English & German"
    assert language_tag_for("Python developer") == "Unspecified"


def test_filter_english():
    jobs = [
        {"title": "Developer", "description": "English required"},
        {"title": "Analyst", "description": "Deutsch erforderlich"},
        {"title": "Engineer", "description": "Python and SQL"},
    ]

    filtered = filter_jobs_by_language(jobs, "English")

    assert len(filtered) == 2
    assert [job["title"] for job in filtered] == [
        "Developer",
        "Engineer",
    ]


def test_filter_german():
    jobs = [
        {"title": "Developer", "description": "English required"},
        {"title": "Analyst", "description": "Deutsch erforderlich"},
        {"title": "Engineer", "description": "Python and SQL"},
    ]

    filtered = filter_jobs_by_language(jobs, "German")

    assert len(filtered) == 2
    assert [job["title"] for job in filtered] == [
        "Analyst",
        "Engineer",
    ]
