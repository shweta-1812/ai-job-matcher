# AI Job Matcher 🎯

AI-powered job matching platform that analyzes your resume and finds the best-fit jobs in Germany/EU. Uses LLM-based skill extraction, semantic similarity, and experience matching to rank jobs by relevance.

## Features ✨

- **LLM-Powered Skill Extraction**: Uses Groq (llama-3.1-8b) to accurately extract skills from resumes and job descriptions — handles any writing style, not just keyword lists
- **Two-Pass Matching**: Fast regex scan ranks all jobs, then Groq re-analyzes the top 30 for accurate skill matching
- **Smart Resume Analysis**: Extracts skills, experience level, and years of experience from your resume
- **Intelligent Matching**: Ranks jobs using a weighted score (capped at 100%):
  - 55% Skill overlap
  - 25% Semantic similarity
  - 20% Experience level match
- **Accurate Skill Sections**: Shows exactly which skills matched and which to develop, powered by LLM extraction
- **Advanced Filtering**: Filter by location, experience level, language requirements, and work mode
- **Salary Extraction**: Automatically extracts and displays salary information from job descriptions
- **Germany/EU Focus**: Filters jobs specifically for German and EU markets
- **Deduplication**: Removes duplicate job listings across sources

## Tech Stack 🛠️

**Backend:**
- FastAPI
- Groq API (llama-3.1-8b-instant) — LLM skill extraction
- Sentence Transformers — semantic similarity
- Python 3.11+

**Frontend:**
- Streamlit

**APIs:**
- Adzuna API (job listings)
- Groq API (skill extraction)

## Installation 📦

### Prerequisites
- Python 3.11+
- Adzuna API credentials — free at https://developer.adzuna.com/
- Groq API key — free at https://console.groq.com/

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-job-matcher.git
cd ai-job-matcher
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd backend && pip install -r requirements.txt
cd ../frontend && pip install -r requirements.txt
```

4. Configure environment variables in `backend/.env`:
```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
GROQ_API_KEY=your_groq_key
```

## Usage 🚀

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
streamlit run app.py --server.port 8501
```

Open http://localhost:8501 in your browser.

## How It Works 🔍

1. **Upload Resume** — PDF, DOCX, or TXT
2. **Analyze Resume** (optional) — preview detected skills and experience level
3. **Search Jobs** — enter job title and filters
4. **Get Matches** — view ranked results with match %, matched skills, skills to develop, salary, and experience level

## Matching Algorithm 📊

```
Score = (25% × Semantic Similarity) + (55% × Skill Overlap) + (20% × Experience Match)
```

**Penalties applied when:**
- Fewer than 3 skills matched → capped at 60%
- Fewer than 5 skills matched (job requires 5+) → 30% penalty
- Less than 30% skill overlap → 25% penalty
- Work mode mismatch → 10% penalty

Score is always capped at 100%.

**Two-pass skill extraction:**
- Pass 1: regex scan on all jobs (fast, no API calls) → initial ranking
- Pass 2: Groq LLM on top 30 jobs → accurate skill matching, score recalculated

## Project Structure 📁

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & endpoints
│   │   ├── match.py             # Two-pass matching & scoring
│   │   ├── adzuna_client.py     # Job search API client
│   │   ├── models.py            # Pydantic models
│   │   ├── resume_extract.py    # Resume file parsing
│   │   └── salary_extractor.py  # Salary extraction
│   ├── core/
│   │   ├── skill_extractor.py   # Groq LLM + regex skill extraction
│   │   ├── resume_parser_v2.py  # Resume analysis (uses LLM)
│   │   ├── jd_analyzer.py       # Job description analysis (uses regex)
│   │   └── semantic_scorer.py   # Sentence transformer scoring
│   └── requirements.txt
├── frontend/
│   ├── app.py                   # Streamlit UI
│   └── requirements.txt
└── README.md
```

## API Endpoints 🔌

### POST /analyze-resume
```json
// Response
{
  "skills": ["python", "aws", "docker"],
  "experience_level": "Senior",
  "years_of_experience": 5,
  "skill_count": 12
}
```

### POST /match
```json
// Response
[
  {
    "match_percentage": 78.5,
    "title": "Senior AI Engineer",
    "company": "Company Name",
    "location": "Berlin, Germany",
    "url": "https://...",
    "remote_like": true,
    "matched_skills": ["python", "docker", "aws"],
    "missing_skills": ["llm", "rag", "vector database"],
    "language_tag": "English & German",
    "experience_level": "Senior",
    "salary": "€70,000 - €90,000",
    "source": "Adzuna"
  }
]
```

## Environment Variables ⚙️

| Variable | Description |
|---|---|
| `ADZUNA_APP_ID` | Adzuna application ID |
| `ADZUNA_APP_KEY` | Adzuna API key |
| `GROQ_API_KEY` | Groq API key (free tier: 30 req/min, 14,400/day) |
| `BACKEND_URL` | Backend URL (default: http://localhost:8000) |

## Future Improvements 🚀

- [ ] Saved searches and job alerts
- [ ] Export results to CSV/PDF
- [ ] More job sources
- [ ] Company information integration
- [ ] Analytics dashboard
