# AI Job Matcher 🎯

AI-powered job matching platform that analyzes your resume and finds the best-fit jobs in Germany/EU. Uses semantic similarity, skill extraction, and experience matching to rank jobs by relevance.

## Features ✨

- **Smart Resume Analysis**: Extracts skills, experience level, and years of experience from your resume
- **Multi-Source Job Search**: Integrates Adzuna, Remotive, and Arbeitnow APIs for comprehensive job listings
- **Intelligent Matching**: Ranks jobs using:
  - 45% Skill overlap
  - 35% Semantic similarity (AI-powered)
  - 20% Experience level match
- **Advanced Filtering**: Filter by location, experience level, language requirements, and work mode
- **Salary Extraction**: Automatically extracts and displays salary information from job descriptions
- **Germany/EU Focus**: Filters jobs specifically for German and EU markets

## Tech Stack 🛠️

**Backend:**
- FastAPI - Modern Python web framework
- Sentence Transformers - Semantic similarity matching
- KeyBERT - Skill extraction
- Python 3.11+

**Frontend:**
- Streamlit - Interactive web interface

**APIs:**
- Adzuna API (primary source)
- Remotive API (remote jobs)
- Arbeitnow API (EU jobs)

## Installation 📦

### Prerequisites
- Python 3.11 or higher
- Adzuna API credentials (get free at https://developer.adzuna.com/)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-job-matcher.git
cd ai-job-matcher
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd ../frontend
pip install -r requirements.txt
```

5. Configure environment variables:
Create `backend/.env` file:
```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

## Usage 🚀

### Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
streamlit run app.py --server.port 8501
```

### Access the Application
Open your browser and go to: http://localhost:8501

## How It Works 🔍

1. **Upload Resume**: Upload your resume (PDF, DOCX, or TXT)
2. **Analyze Resume** (Optional): See what skills and experience level the system detected
3. **Search Jobs**: Enter job title and preferences
4. **Get Matches**: View ranked job matches with:
   - Match percentage
   - Matched skills
   - Skills to develop
   - Salary information
   - Experience level
   - Remote/On-site indicator

## Matching Algorithm 📊

The match percentage is calculated using:

```
Base Score = (35% × Semantic Similarity) + (45% × Skill Overlap) + (20% × Experience Match)
Skill Bonus = min(Matched Skills / 10, 0.3)  # Up to 30% bonus
Final Score = (Base Score + Bonus) × Penalties
```

**Penalties:**
- Poor skill match (<20% overlap, <3 skills): 50% penalty
- Work mode mismatch: 10% penalty

## Project Structure 📁

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── match.py             # Matching logic
│   │   ├── adzuna_client.py     # Job fetching
│   │   ├── models.py            # Pydantic models
│   │   ├── resume_extract.py    # Resume parsing
│   │   └── salary_extractor.py  # Salary extraction
│   ├── core/
│   │   ├── semantic_scorer.py   # Semantic matching
│   │   ├── skill_extractor.py   # Skill extraction
│   │   ├── resume_parser_v2.py  # Resume analysis
│   │   └── jd_analyzer.py       # Job description analysis
│   └── requirements.txt
├── frontend/
│   ├── app.py                   # Streamlit UI
│   └── requirements.txt
└── README.md
```

## API Endpoints 🔌

### POST /analyze-resume
Analyze resume and extract skills, experience level, and years of experience.

**Request:**
- `resume_upload`: File (PDF/DOCX/TXT)

**Response:**
```json
{
  "skills": ["python", "aws", "docker", ...],
  "experience_level": "Senior",
  "years_of_experience": 5,
  "skill_count": 25
}
```

### POST /match
Search and rank jobs based on resume.

**Request:**
- `resume_upload`: File
- `job_title`: string
- `country`: string (default: "de")
- `city`: string (optional)
- `pages`: int (1-10)
- `results_per_page`: int (10-100)
- `work_mode`: "Remote" | "On-site"
- `language`: "Any" | "English" | "German"
- `experience_level`: "Any" | "Entry" | "Mid" | "Senior" | "Lead"

**Response:**
```json
[
  {
    "match_percentage": 78.5,
    "title": "Senior AI Engineer",
    "company": "Company Name",
    "location": "Berlin, Germany",
    "url": "https://...",
    "remote_like": true,
    "matched_skills": ["python", "tensorflow", ...],
    "missing_skills": ["kubernetes", ...],
    "language_tag": "English & German",
    "experience_level": "Senior",
    "salary": "€70,000 - €90,000",
    "source": "Adzuna"
  }
]
```

## Configuration ⚙️

### Environment Variables
- `ADZUNA_APP_ID`: Your Adzuna application ID
- `ADZUNA_APP_KEY`: Your Adzuna API key
- `BACKEND_URL`: Backend URL (default: http://localhost:8000)

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the MIT License.

## Acknowledgments 🙏

- Adzuna API for job listings
- Remotive for remote job data
- Arbeitnow for EU job data
- Sentence Transformers for semantic matching
- KeyBERT for skill extraction

## Future Improvements 🚀

- [ ] Caching for job results
- [ ] User authentication and saved searches
- [ ] Job alerts and notifications
- [ ] More job sources
- [ ] Company information integration
- [ ] Export results to CSV/PDF
- [ ] Advanced analytics dashboard

---

