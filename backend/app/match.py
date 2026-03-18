# backend/app/match.py

from __future__ import annotations

import re
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.semantic_scorer import SemanticScorer
from core.resume_parser_v2 import ResumeParser
from core.jd_analyzer import JDAnalyzer
from core.skill_extractor import SkillExtractor

semantic_scorer = SemanticScorer()
resume_parser = ResumeParser()
jd_analyzer = JDAnalyzer()
skill_extractor = SkillExtractor()  # shared instance (shared cache + rate limiter)

TOP_N_LLM = 30  # re-analyze top N jobs with Groq

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
    Two-pass ranking:
    Pass 1 — regex skill extraction on all jobs → fast initial ranking
    Pass 2 — Groq LLM re-extraction on top 30 → accurate matched/missing skills
    """
    if not jobs:
        return [], {}, [], []

    resume_text = resume_text or ""

    # Parse resume with Groq (once)
    resume_data = resume_parser.parse(resume_text)
    resume_skills = resume_data["skills"]
    resume_level = resume_data["experience_level"]

    # --- Pass 1: regex extraction on all jobs ---
    job_texts: list[str] = []
    job_analyses: list[dict] = []
    remote_flags: list[bool] = []

    for j in jobs:
        title = j.get("title", "") or ""
        desc = j.get("description") or ""
        loc = (j.get("location") or {}).get("display_name", "") or ""
        text = _job_text_for_scoring(j)
        job_texts.append(text)
        job_analyses.append(jd_analyzer.analyze(text))
        remote_flags.append(is_remote_like(title, desc, loc))

    semantic_scores = semantic_scorer.batch_score(resume_text, job_texts)

    scored: list[tuple[float, int]] = []
    for idx, j in enumerate(jobs):
        job_analysis = job_analyses[idx]
        job_skills = job_analysis["skills"]
        job_level = job_analysis["experience_level"]

        if experience_level_filter and experience_level_filter != "Any":
            if job_level != "Any" and job_level != experience_level_filter:
                filter_rank = EXPERIENCE_LEVEL_ORDER.get(experience_level_filter, 0)
                job_rank = EXPERIENCE_LEVEL_ORDER.get(job_level, 0)
                if abs(filter_rank - job_rank) > 1:
                    continue

        # Filter by work mode strictly
        if work_mode == "Remote" and not remote_flags[idx]:
            continue
        if work_mode == "On-site" and remote_flags[idx]:
            continue

        sem_score = float(semantic_scores[idx]) / 100.0 if idx < len(semantic_scores) else 0.0
        skill_score = skill_overlap(resume_skills, job_skills)
        exp_match = experience_level_match(resume_level, job_level)
        matched_count = len(resume_skills & job_skills)
        job_skills_count = len(job_skills)

        # 25% semantic, 55% skills, 20% experience — weights sum to 1.0, max score = 1.0
        score = 0.25 * sem_score + 0.55 * skill_score + 0.20 * exp_match

        if matched_count < 3:
            score = min(score, 0.6)
        elif matched_count < 5 and job_skills_count > 5:
            score *= 0.7
        elif skill_score < 0.3:
            score *= 0.75

        scored.append((min(score, 1.0), idx))

    scored.sort(key=lambda x: x[0], reverse=True)

    # --- Pass 2: Groq LLM re-extraction on top 30 ---
    top_indices = [idx for _, idx in scored[:TOP_N_LLM]]
    top_texts = [job_texts[idx] for idx in top_indices]

    print(f"Running Groq LLM analysis on top {len(top_indices)} jobs...")
    llm_skills_list = skill_extractor.extract_skills_batch_llm(top_texts, top_n=TOP_N_LLM)

    # Update job_analyses AND recalculate scores with LLM skills
    score_map = {idx: score for score, idx in scored}

    for job_idx, llm_skills in zip(top_indices, llm_skills_list):
        job_analyses[job_idx]["skills"] = llm_skills

        # Recalculate score with accurate LLM skills
        job_level = job_analyses[job_idx]["experience_level"]
        matched_count = len(resume_skills & llm_skills)
        job_skills_count = len(llm_skills)
        skill_score = matched_count / job_skills_count if job_skills_count else 0.0
        sem_score = float(semantic_scores[job_idx]) / 100.0
        exp_match = experience_level_match(resume_level, job_level)

        score = 0.25 * sem_score + 0.55 * skill_score + 0.20 * exp_match

        if matched_count < 3:
            score = min(score, 0.6)
        elif matched_count < 5 and job_skills_count > 5:
            score *= 0.7
        elif skill_score < 0.3:
            score *= 0.75

        score_map[job_idx] = min(score, 1.0)

    # Re-sort with updated scores
    scored = sorted([(score_map[idx], idx) for _, idx in scored], key=lambda x: x[0], reverse=True)

    return scored, resume_data, job_analyses, remote_flags
