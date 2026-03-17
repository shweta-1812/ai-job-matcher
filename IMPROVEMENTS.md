# Job Matcher Improvements

## Summary of Changes

This update significantly improves the job matching system with better semantic understanding, skill extraction, and experience level filtering.

## Key Improvements

### 1. Enhanced Semantic Matching
- **Before**: Used TF-IDF (basic keyword matching)
- **After**: Uses sentence-transformers (`all-MiniLM-L6-v2`) for deep semantic understanding
- **Benefit**: Catches synonyms and contextual meaning (e.g., "ML" = "Machine Learning", "React" = "React.js")

### 2. Better Skill Extraction
- **Before**: Limited to ~25 hardcoded skills
- **After**: Uses KeyBERT with smart candidate generation to extract 35+ skills dynamically
- **Benefit**: Identifies domain-specific skills, frameworks, and tools automatically

### 3. Experience Level Filtering (NEW)
- **Feature**: Optional filter for Entry/Mid/Senior/Lead positions
- **Smart Matching**: Allows one-level flexibility (e.g., Mid-level candidates see Senior roles)
- **Resume Analysis**: Automatically detects candidate's experience level from resume
- **JD Analysis**: Extracts required experience level from job descriptions

### 4. Improved Scoring Algorithm
- **New Weights**:
  - 50% Semantic similarity (deep understanding)
  - 30% Skill overlap (specific requirements)
  - 20% Experience level match (career stage alignment)
- **Before**: 65% TF-IDF + 35% keyword overlap

### 5. Structured Resume Parsing
- Extracts years of experience from dates and explicit mentions
- Identifies experience level (Entry/Mid/Senior/Lead)
- Better skill extraction with noise filtering

### 6. Structured JD Analysis
- Extracts required skills using KeyBERT
- Identifies required experience level
- Parses min/max years requirements

## New Files

1. `core/resume_parser_v2.py` - Enhanced resume parser
2. `core/jd_analyzer.py` - Job description analyzer
3. `test_improvements.py` - Test script to verify improvements
4. `IMPROVEMENTS.md` - This documentation

## Modified Files

1. `backend/app/match.py` - Updated matching logic
2. `backend/app/main.py` - Added experience_level parameter
3. `backend/app/models.py` - Added ExperienceLevel type and field
4. `frontend/app.py` - Added experience level dropdown
5. `backend/requirements.txt` - Added sentence-transformers and keybert

## Usage

### Frontend Changes
Users now see an "Experience level" dropdown with options:
- Any (default - shows all levels)
- Entry
- Mid
- Senior
- Lead

### API Changes
New optional parameter in `/match` endpoint:
```python
experience_level: str = Form("Any")  # "Any", "Entry", "Mid", "Senior", "Lead"
```

### Response Changes
JobMatch now includes:
```python
experience_level: str  # The detected level for each job
```

## Installation

Update backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

First run will download the sentence-transformer model (~80MB).

## Testing

Run the test script to verify everything works:
```bash
python test_improvements.py
```

## Performance Notes

- First request will be slower (~5-10s) due to model loading
- Subsequent requests are fast (~1-2s for 50 jobs)
- Models are cached in memory after first load
- Consider using GPU for faster inference (optional)

## Future Enhancements

1. Cache embeddings for job descriptions
2. Add salary range filtering
3. Implement user feedback loop
4. Add "must-have" vs "nice-to-have" skill distinction
5. Extract and match certifications
6. Add company size preference
