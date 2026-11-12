
import pytest
from pydantic import ValidationError

from backend.core.schemas.job_requirements import JobRequirements


def test_default_values():
    job = JobRequirements(job_title="Junior AI Engineer")

    assert job.job_title == "Junior AI Engineer"
    assert job.required_skills == []
    assert job.preferred_skills == []
    assert job.experience_level == "Any"
    assert job.work_arrangement == "Unknown"


def test_valid_job_requirements():
    job = JobRequirements(
        job_title="AI Engineer",
        required_skills=["Python", "SQL"],
        preferred_skills=["Azure"],
        experience_level="Mid",
        min_years=2,
        max_years=5,
        work_arrangement="Hybrid",
        eligible_countries=["Germany"],
        required_languages=["English"],
    )

    assert job.required_skills == ["Python", "SQL"]
    assert job.min_years == 2
    assert job.max_years == 5


def test_invalid_experience_range():
    with pytest.raises(ValidationError):
        JobRequirements(min_years=5, max_years=2)


def test_negative_experience():
    with pytest.raises(ValidationError):
        JobRequirements(min_years=-1)


def test_invalid_experience_level():
    with pytest.raises(ValidationError):
        JobRequirements(experience_level="Expert")


def test_independent_skill_lists():
    first = JobRequirements()
    second = JobRequirements()

    first.required_skills.append("Python")

    assert second.required_skills == []
