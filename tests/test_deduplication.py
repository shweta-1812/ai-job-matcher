
from backend.app.job_sources.deduplication import deduplicate_jobs


def make_job(company, title, description, url, location="Berlin"):
    return {
        "company": {"display_name": company},
        "title": title,
        "description": description,
        "redirect_url": url,
        "location": {"display_name": location},
    }


def test_duplicate_url():
    jobs = [
        make_job("Acme", "Data Engineer", "Build pipelines", "https://example.com/1"),
        make_job("Acme", "Data Engineer", "Different text", "https://example.com/1"),
    ]
    assert len(deduplicate_jobs(jobs)) == 1


def test_cross_board_duplicate():
    jobs = [
        make_job("artefact", "Data Consultant", "Data strategy", "https://example.com/1"),
        make_job("artefactlinkedin", "Data Consultant", "Data strategy", "https://example.com/2"),
    ]
    assert len(deduplicate_jobs(jobs)) == 1


def test_distinct_vacancies():
    jobs = [
        make_job("Acme", "Software Engineer", "Backend APIs", "https://example.com/1"),
        make_job("Acme", "Software Engineer", "Frontend React", "https://example.com/2"),
    ]
    assert len(deduplicate_jobs(jobs)) == 2
