"""
Test script to verify the improved matching system.
"""
import sys
sys.path.insert(0, ".")

from backend.core.resume_parser_v2 import ResumeParser
from backend.core.jd_analyzer import JDAnalyzer
from backend.core.semantic_scorer import SemanticScorer

# Sample resume text
SAMPLE_RESUME = """
John Doe
Senior Software Engineer

EXPERIENCE:
Senior Software Engineer at Tech Corp (2019 - Present)
- Led development of microservices using Python, FastAPI, and Docker
- Implemented CI/CD pipelines with GitHub Actions
- Managed PostgreSQL databases and optimized queries
- Worked with AWS (EC2, S3, Lambda) for cloud infrastructure

Software Engineer at StartupXYZ (2017 - 2019)
- Built REST APIs using Python and Flask
- Developed frontend with React and TypeScript
- Used Git for version control

SKILLS:
Python, FastAPI, Flask, Docker, Kubernetes, PostgreSQL, AWS, React, TypeScript, Git
"""

# Sample job description
SAMPLE_JD = """
Senior Backend Engineer

We're looking for a Senior Backend Engineer with 5+ years of experience.

Requirements:
- Strong Python experience
- Experience with FastAPI or similar frameworks
- Docker and Kubernetes knowledge
- Cloud experience (AWS preferred)
- PostgreSQL or similar databases
- Git version control

Nice to have:
- React knowledge
- CI/CD experience
"""

def test_resume_parser():
    print("=" * 60)
    print("Testing Resume Parser")
    print("=" * 60)
    
    parser = ResumeParser()
    result = parser.parse(SAMPLE_RESUME)
    
    print(f"\nExtracted Skills ({len(result['skills'])}):")
    print(", ".join(sorted(result['skills'])))
    
    print(f"\nExperience Level: {result['experience_level']}")
    print(f"Years of Experience: {result['years_of_experience']}")
    print()

def test_jd_analyzer():
    print("=" * 60)
    print("Testing JD Analyzer")
    print("=" * 60)
    
    analyzer = JDAnalyzer()
    result = analyzer.analyze(SAMPLE_JD)
    
    print(f"\nExtracted Skills ({len(result['skills'])}):")
    print(", ".join(sorted(result['skills'])))
    
    print(f"\nRequired Experience Level: {result['experience_level']}")
    print(f"Min Years: {result['min_years']}")
    print(f"Max Years: {result['max_years']}")
    print()

def test_semantic_scorer():
    print("=" * 60)
    print("Testing Semantic Scorer")
    print("=" * 60)
    
    scorer = SemanticScorer()
    score = scorer.score(SAMPLE_RESUME, SAMPLE_JD)
    
    print(f"\nSemantic Similarity Score: {score:.2f}/100")
    print()

def test_skill_overlap():
    print("=" * 60)
    print("Testing Skill Overlap")
    print("=" * 60)
    
    parser = ResumeParser()
    analyzer = JDAnalyzer()
    
    resume_data = parser.parse(SAMPLE_RESUME)
    jd_data = analyzer.analyze(SAMPLE_JD)
    
    resume_skills = resume_data['skills']
    jd_skills = jd_data['skills']
    
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    
    print(f"\nMatched Skills ({len(matched)}):")
    print(", ".join(sorted(matched)))
    
    print(f"\nMissing Skills ({len(missing)}):")
    print(", ".join(sorted(missing)))
    
    overlap_pct = len(matched) / len(jd_skills) * 100 if jd_skills else 0
    print(f"\nSkill Overlap: {overlap_pct:.1f}%")
    print()

if __name__ == "__main__":
    print("\n🚀 Testing Improved Job Matching System\n")
    
    try:
        test_resume_parser()
        test_jd_analyzer()
        test_semantic_scorer()
        test_skill_overlap()
        
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
