from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .processing.language_filter import (language_tag_for,)
from .pipelines.job_pipeline import collect_jobs
from .models import JobMatch, ResumeAnalysis
from .resume_extract import extract_resume_text
from .match import rank_jobs
import logging

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Job Matcher API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze-resume", response_model=ResumeAnalysis)
async def analyze_resume(resume_upload: UploadFile = File(...)):
    """
    Analyze resume and return extracted information.
    Useful for users to see what the system detected before searching.
    """
    try:
        data = await resume_upload.read()
        resume_text = extract_resume_text(resume_upload.filename, data)

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Resume text is too short or could not be extracted. Please check the file."
            )

        # Import here to avoid circular dependency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from core.resume_parser_v2 import ResumeParser
        parser = ResumeParser()
        resume_data = parser.parse(resume_text)

        return ResumeAnalysis(
            skills=sorted(list(resume_data["skills"]))[:50],  # Limit to top 50
            experience_level=resume_data["experience_level"],
            years_of_experience=resume_data["years_of_experience"],
            skill_count=len(resume_data["skills"])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

@app.post("/match", response_model=list[JobMatch])
async def match_jobs(
    resume_upload: UploadFile = File(...),
    job_title: str = Form(...),
    country: str = Form("de"),
    city: str | None = Form(None),
    pages: int = Form(2),
    results_per_page: int = Form(50),
    work_mode: str = Form("Any"),
    language: str = Form("Any"),
    experience_level: str = Form("Any"),
    date_posted: str = Form("Any time"),
):
    if pages < 1 or pages > 10:
        raise HTTPException(status_code=400, detail="pages must be 1..10")
    if results_per_page < 10 or results_per_page > 100:
        raise HTTPException(status_code=400, detail="results_per_page must be 10..100")

    try:
        data = await resume_upload.read()
        resume_text = extract_resume_text(resume_upload.filename, data)

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Resume text is too short or could not be extracted."
            )
    except Exception as e:
        logger.error(f"Error extracting resume: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading resume: {str(e)}")

    # Map date_posted label to max_days_old
    date_to_days = {
        "Past 24 hours": 1,
        "Past week": 7,
        "Past month": 30,
        "Any time": None,
    }
    max_days_old = date_to_days.get(date_posted, None)


    # Fetch, deduplicate, enrich and filter jobs
    jobs = collect_jobs(
        job_title=job_title,
        country=country,
        city=city,
        pages=pages,
        results_per_page=results_per_page,
        max_days_old=max_days_old,
        language=language,
    )

    if not jobs:
        raise HTTPException(
            status_code=404,
            detail="No jobs matched the search criteria. Try broader filters.",
        )

    try:
        ranked, resume_data, job_analyses, remote_flags = rank_jobs(
            resume_text,
            jobs,
            work_mode,
            experience_level_filter=experience_level if experience_level != "Any" else None
        )
        logger.info(f"Ranked {len(ranked)} jobs")
    except Exception as e:
        import traceback
        logger.error(f"Error ranking jobs: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error ranking jobs: {str(e)}")

    results: list[JobMatch] = []
    for score, idx in ranked[:50]:
        j = jobs[idx]
        job_analysis = job_analyses[idx]

        title = j.get("title","")
        company = (j.get("company") or {}).get("display_name","")
        loc = (j.get("location") or {}).get("display_name","")
        url = j.get("redirect_url","")
        source = j.get("source", "Unknown")

        resume_skills = resume_data["skills"]
        job_skills = job_analysis["skills"]

        matched = sorted(list(resume_skills & job_skills))
        missing = sorted(list(job_skills - resume_skills))[:15]

        desc = j.get("description") or ""
        text_for_lang = f"{title} {desc}"
        lang_tag = language_tag_for(text_for_lang)

        results.append(JobMatch(
            match_percentage=float(score * 100),
            title=title,
            company=company,
            location=loc,
            url=url,
            remote_like=bool(remote_flags[idx]),
            matched_skills=matched,
            missing_skills=missing,
            language_tag=lang_tag,
            experience_level=job_analysis["experience_level"],
            source=source,
            raw=j
        ))

    logger.info(f"Returning {len(results)} job matches")
    return results
