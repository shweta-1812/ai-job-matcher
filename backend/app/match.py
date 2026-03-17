# backend/app/match.py

from __future__ import annotations

import re
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.semantic_scorer import SemanticScorer
from core.resume_parser_v2 import ResumeParser
from core.jd_analyzer import JDAnalyzer


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text

# Initialize shared instances
semantic_scorer = SemanticScorer()
resume_parser = ResumeParser()
jd_analyzer = JDAnalyzer()

EXPERIENCE_LEVEL_ORDER = {
    "Entry": 1,
    "Mid": 2,
    "Senior": 3,
    "Lead": 4,
    "Any": 0,
    "Unknown": 0
}


def is_remote_like(title: str, desc: str, location: str) -> bool:
    """
    Check if job is remote/hybrid based on title and location only.
    Don't check description to avoid false positives.
    """
    # Check title and location (not description to avoid false positives)
    title_lower = (title or "").lower()
    location_lower = (location or "").lower()
    
    # Strong remote indicators in title or location
    remote_keywords = ["remote", "home office", "work from home", "distributed", "fully remote", "100% remote"]
    hybrid_keywords = ["hybrid"]
    
    # Check if location explicitly says remote/hybrid
    for keyword in remote_keywords + hybrid_keywords:
        if keyword in location_lower:
            return True
    
    # Check if title explicitly mentions remote/hybrid
    for keyword in remote_keywords + hybrid_keywords:
        if keyword in title_lower:
            return True
    
    return False


def skill_overlap(resume_skills: set[str], job_skills: set[str]) -> float:
    """Calculate skill overlap score."""
    if not job_skills:
        return 0.0
    matched = len(resume_skills & job_skills)
    return matched / len(job_skills)


def experience_level_match(resume_level: str, job_level: str) -> float:
    """
    Calculate experience level match score.
    Returns 1.0 for perfect match, 0.8 for close match, 0.5 for acceptable, 0.3 for mismatch.
    """
    if job_level == "Any" or resume_level == "Unknown":
        return 1.0
    
    resume_rank = EXPERIENCE_LEVEL_ORDER.get(resume_level, 0)
    job_rank = EXPERIENCE_LEVEL_ORDER.get(job_level, 0)
    
    if resume_rank == job_rank:
        return 1.0
    elif abs(resume_rank - job_rank) == 1:
        return 0.8  # One level off (e.g., Mid applying for Senior)
    elif resume_rank > job_rank:
        return 0.9  # Overqualified (usually acceptable)
    else:
        return 0.5  # Underqualified


def _job_text_for_scoring(job: dict) -> str:
    """
    Get job text for scoring - now all descriptions are full from API
    """
    title = job.get("title", "") or ""
    desc = job.get("description") or ""
    loc = (job.get("location") or {}).get("display_name", "") or ""
    company = (job.get("company") or {}).get("display_name", "") or ""
    return f"{title}\n{company}\n{loc}\n{desc}"


def rank_jobs(
    resume_text: str, 
    jobs: list[dict], 
    work_mode: str,
    experience_level_filter: str | None = None
):
    """
    Returns:
      ranked: list[tuple[score, idx]] sorted desc
      resume_data: dict with parsed resume info
      job_analyses: list[dict] aligned to jobs
      remote_flags: list[bool] aligned to jobs
    """

    # ---- guards ----
    if not jobs:
        return [], {}, [], []

    resume_text = resume_text or ""
    
    # Parse resume once
    resume_data = resume_parser.parse(resume_text)
    resume_skills = resume_data["skills"]
    resume_level = resume_data["experience_level"]

    job_texts: list[str] = []
    job_analyses: list[dict] = []
    remote_flags: list[bool] = []

    for j in jobs:
        title = j.get("title", "") or ""
        desc = j.get("description") or ""
        loc = (j.get("location") or {}).get("display_name", "") or ""

        text = _job_text_for_scoring(j)
        job_texts.append(text)

        # Analyze JD
        analysis = jd_analyzer.analyze(text)
        job_analyses.append(analysis)

        remote_flags.append(is_remote_like(title, desc, loc))

    scored: list[tuple[float, int]] = []
    
    # Batch encode all job descriptions at once (much faster)
    job_texts_for_scoring = [_job_text_for_scoring(jobs[idx]) for idx in range(len(jobs))]
    semantic_scores = semantic_scorer.batch_score(resume_text, job_texts_for_scoring)
    
    for idx, j in enumerate(jobs):
        job_analysis = job_analyses[idx]
        job_skills = job_analysis["skills"]
        job_level = job_analysis["experience_level"]
        
        # Apply experience level filter if specified
        if experience_level_filter and experience_level_filter != "Any":
            if job_level != "Any" and job_level != experience_level_filter:
                # Skip jobs that don't match the filter
                # Allow one level flexibility (e.g., Mid can see Senior)
                filter_rank = EXPERIENCE_LEVEL_ORDER.get(experience_level_filter, 0)
                job_rank = EXPERIENCE_LEVEL_ORDER.get(job_level, 0)
                if abs(filter_rank - job_rank) > 1:
                    continue
        
        # Semantic similarity (0-100 scale, already computed in batch)
        sem_score = float(semantic_scores[idx]) / 100.0 if idx < len(semantic_scores) else 0.0
        
        # Skill overlap (0-1 scale)
        skill_score = skill_overlap(resume_skills, job_skills)
        
        # Experience level match (0-1 scale)
        exp_match = experience_level_match(resume_level, job_level)
        
        # Calculate number of matched skills (absolute count matters)
        matched_skills_count = len(resume_skills & job_skills)
        
        # Skill match bonus: reward jobs where you have many of the required skills
        skill_match_bonus = min(matched_skills_count / 10.0, 0.3)  # Up to 30% bonus for 10+ matched skills
        
        # Improved hybrid score with adjusted weights
        # 35% semantic, 45% skills, 20% experience level
        # Skills are now more important than semantic similarity
        base_score = 0.35 * sem_score + 0.45 * skill_score + 0.20 * exp_match
        
        # Add skill match bonus
        score = base_score + skill_match_bonus
        
        # Minimum threshold: if skill overlap is too low, penalize heavily
        if skill_score < 0.2 and matched_skills_count < 3:
            score *= 0.5  # Poor skill match, reduce score significantly

        # Apply work mode preference penalty (not a hard filter)
        if work_mode == "Remote" and not remote_flags[idx]:
            score *= 0.9
        elif work_mode == "On-site" and remote_flags[idx]:
            score *= 0.9

        scored.append((score, idx))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored, resume_data, job_analyses, remote_flags
