from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import MatchRequest, JobMatch, ResumeAnalysis
from .resume_extract import extract_resume_text
from .adzuna_client import search_jobs
from .match import rank_jobs
from .salary_extractor import extract_salary, format_salary
from fastapi import HTTPException
import re, hashlib
import logging

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Job Matcher API", version="0.1")

def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _n(s: str) -> str:
    return (s or "").strip().lower()

def _strip_city_suffix(title: str) -> str:
    # Remove common " - City" / " – City" patterns and Remote-location tags
    t = _norm(title)
    t = re.sub(r"\s*[-–—]\s*(remote|hybrid)\s*[-–—]\s*.*$", r" \1", t)  # "Remote - Nürnberg" -> "Remote"
    t = re.sub(r"\s*[-–—]\s*[a-zäöüß .()]+$", "", t)  # remove trailing city-ish part
    return t

def dedupe_jobs(jobs: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for j in jobs:
        company = _norm((j.get("company") or {}).get("display_name", ""))
        title_base = _strip_city_suffix(j.get("title", ""))
        desc = _norm(j.get("description", ""))
        desc_sig = hashlib.md5(desc.encode("utf-8")).hexdigest()  # stable fingerprint

        key = f"{company}|{title_base}|{desc_sig}"
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out

def norm_company(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def base_job_title(title: str) -> str:
    """
    Convert:
      'Data Analytics Engineer (w/m/d) Remote - Mainz' -> 'data analytics engineer (w/m/d) remote'
      'Data Analytics Engineer (w/m/d) - Weimar'      -> 'data analytics engineer (w/m/d)'
      '... remote - würzburg'                         -> '... remote'
    """
    t = re.sub(r"\s+", " ", (title or "").strip().lower())

    # Normalize common separators
    t = t.replace("–", "-").replace("—", "-")

    # If title contains 'remote' or 'hybrid', keep that as part of base title but drop city after it
    t = re.sub(r"\s*-\s*(remote|hybrid)\s*-\s*.*$", r" \1", t)

    # Drop trailing " - <city/region>" if present
    t = re.sub(r"\s*-\s*[^-]{2,}$", "", t)

    # Final whitespace cleanup
    t = re.sub(r"\s+", " ", t).strip()
    return t

def dedupe_by_company_base_title(jobs: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for j in jobs:
        company = norm_company((j.get("company") or {}).get("display_name", ""))
        title = base_job_title(j.get("title", ""))
        key = f"{company}|{title}"
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out

def detect_languages(text: str) -> dict:
    t = (text or "").lower()

    GERMAN_PATTERNS = [
    r"\bgerman\b", r"\bdeutsch\b", r"\bdeutschkenntnisse\b",
    r"\bverhandlungssicher(es)?\s+deutsch\b",
    r"\bsehr gute\s+deutschkenntnisse\b",
    ]

    ENGLISH_PATTERNS = [
    r"\benglish\b", r"\benglisch\b",
    r"\bbusiness english\b",
    r"\bverhandlungssicher(es)?\s+englisch\b",
    ]

    # CEFR levels like C1, B2, etc. Often appear near a language word.
    CEFR_PATTERN = r"\b(a1|a2|b1|b2|c1|c2)\b"


    has_german_word = any(re.search(p, t) for p in GERMAN_PATTERNS)
    has_english_word = any(re.search(p, t) for p in ENGLISH_PATTERNS)

    # Catch cases like "German (at least C1)" or "English skills (B2)"
    german_cefr = bool(re.search(rf"\b(german|deutsch)\b.{0,40}{CEFR_PATTERN}", t))
    english_cefr = bool(re.search(rf"\b(english|englisch)\b.{0,40}{CEFR_PATTERN}", t))

    return {
        "german": has_german_word or german_cefr,
        "english": has_english_word or english_cefr,
    }


def language_tag_for(text: str) -> str:
    langs = detect_languages(text)
    if langs["english"] and langs["german"]:
        return "English & German"
    if langs["english"]:
        return "English"
    if langs["german"]:
        return "German"
    return "Unspecified"

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
    work_mode: str = Form("Remote"),
    language: str = Form("Any"),
    experience_level: str = Form("Any"),
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

    jobs = []
    for p in range(1, pages + 1):
        try:
            resp = search_jobs(country=country, page=p, what=job_title, where=city, results_per_page=results_per_page)
            jobs.extend(resp.get("results", []))
            logger.info(f"Page {p}: fetched {len(resp.get('results', []))} jobs from {resp.get('sources', {})}")
        except Exception as e:
            logger.error(f"Error fetching jobs page {p}: {e}")
            # Continue with other pages

    if not jobs:
        raise HTTPException(
            status_code=404,
            detail="No jobs found for the given job_title/city. Try broader terms."
    )

    logger.info(f"Total jobs before deduplication: {len(jobs)}")
    jobs = dedupe_jobs(jobs)
    jobs = dedupe_by_company_base_title(jobs)
    logger.info(f"Total jobs after deduplication: {len(jobs)}")

    # Filter jobs by language
    if language != "Any":
        filtered = []
        for j in jobs:
            title = j.get("title", "")
            desc = j.get("description", "")
            tag = language_tag_for(f"{title} {desc}")

            if language == "German" and tag in ("German", "English & German","Unspecified"):
                filtered.append(j)
            elif language == "English" and tag in ("English", "English & German","Unspecified"):
                filtered.append(j)

        jobs = filtered
        logger.info(f"Jobs after language filter ({language}): {len(jobs)}")

        if not jobs:
            raise HTTPException(
                status_code=404,
                detail=f"No jobs matched language filter '{language}'. Try 'Any' or broaden your search."
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
        logger.error(f"Error ranking jobs: {e}")
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
        
        # Extract salary
        salary_info = extract_salary(desc)
        salary_str = format_salary(salary_info)
        
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
            salary=salary_str,
            source=source,
            raw=j
        ))
    
    logger.info(f"Returning {len(results)} job matches")
    return results
