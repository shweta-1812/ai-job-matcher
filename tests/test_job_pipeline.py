
from backend.app.pipelines import job_pipeline


def test_collect_jobs(monkeypatch):
    sample_jobs = [
        {
            "title": "Python Developer",
            "company": {"display_name": "Acme"},
            "location": {"display_name": "Berlin"},
            "description": "English required",
            "redirect_url": "https://example.com/1",
        },
        {
            "title": "Python Developer",
            "company": {"display_name": "Acme"},
            "location": {"display_name": "Berlin"},
            "description": "English required",
            "redirect_url": "https://example.com/1",
        },
        {
            "title": "Data Analyst",
            "company": {"display_name": "Other"},
            "location": {"display_name": "Berlin"},
            "description": "Deutsch erforderlich",
            "redirect_url": "https://example.com/2",
        },
    ]

    def fake_search_jobs(**kwargs):
        return {
            "results": sample_jobs,
            "sources": {"mock": 3},
        }

    # Mock ATS results
    monkeypatch.setattr(
        job_pipeline,
        "search_jobs",
        fake_search_jobs,
    )

    monkeypatch.setattr(
        job_pipeline,
        "enrich_descriptions",
        lambda jobs: None,
    )

    monkeypatch.setattr(
        job_pipeline,
        "fetch_ats_jobs",
        lambda **kwargs: [],
    )

    results = job_pipeline.collect_jobs(
        job_title="Developer",
        country="de",
        city="Berlin",
        pages=1,
        results_per_page=50,
        max_days_old=None,
        language="English",
    )

    assert len(results) == 1
    assert results[0]["title"] == "Python Developer"


def test_collect_jobs_includes_ats(monkeypatch):
    ats_job = {
        "title": "Data Analyst",
        "company": {"display_name": "Example Company"},
        "location": {"display_name": "Berlin"},
        "description": "English required. Python and SQL.",
        "redirect_url": "https://example.com/ats/1",
        "source": "greenhouse",
    }

    # No jobs returned by Adzuna, Remotive or Arbeitnow
    monkeypatch.setattr(
        job_pipeline,
        "search_jobs",
        lambda **kwargs: {"results": [], "sources": {}},
    )

    # ATS returns one Greenhouse job
    monkeypatch.setattr(
        job_pipeline,
        "fetch_ats_jobs",
        lambda **kwargs: [ats_job],
    )

    monkeypatch.setattr(
        job_pipeline,
        "enrich_descriptions",
        lambda jobs: None,
    )

    results = job_pipeline.collect_jobs(
        job_title="Data Analyst",
        country="de",
        city="Berlin",
        pages=1,
        results_per_page=50,
        max_days_old=None,
        language="English",
    )

    assert len(results) == 1
    assert results[0]["title"] == "Data Analyst"
    assert results[0]["source"] == "greenhouse"
