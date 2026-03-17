from pydantic import BaseModel
from typing import Optional, List, Literal, Dict, Any

WorkMode = Literal["Remote", "On-site"]
ExperienceLevel = Literal["Any", "Entry", "Mid", "Senior", "Lead"]

class MatchRequest(BaseModel):
    job_title: str
    where: Optional[str] = None
    country: str = "de"
    pages: int = 2
    results_per_page: int = 50
    work_mode: WorkMode = "Remote"
    experience_level: ExperienceLevel = "Any"

class ResumeAnalysis(BaseModel):
    skills: List[str]
    experience_level: str
    years_of_experience: Optional[int]
    skill_count: int

class JobMatch(BaseModel):
    match_percentage: float
    title: str
    company: str
    location: str
    url: str
    remote_like: bool
    matched_skills: List[str]
    missing_skills: List[str]
    language_tag: str
    experience_level: str
    salary: Optional[str] = None
    source: Optional[str] = None
    raw: Dict[str, Any]
