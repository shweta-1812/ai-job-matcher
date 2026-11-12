
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class JobRequirements(BaseModel):
    """Structured requirements extracted from a job posting."""

    job_title: str = ""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)

    experience_level: Literal[
        "Entry", "Mid", "Senior", "Lead", "Any"
    ] = "Any"

    min_years: int | None = Field(default=None, ge=0)
    max_years: int | None = Field(default=None, ge=0)

    work_arrangement: Literal[
        "Remote", "Hybrid", "On-site", "Unknown"
    ] = "Unknown"

    eligible_countries: list[str] = Field(default_factory=list)
    required_languages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_experience_range(self):
        if (
            self.min_years is not None
            and self.max_years is not None
            and self.min_years > self.max_years
        ):
            raise ValueError(
                "min_years cannot exceed max_years"
            )
        return self
