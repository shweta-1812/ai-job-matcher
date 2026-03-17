"""
Enhanced resume parser that extracts structured information including skills and experience level.
"""
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_extractor import SkillExtractor


class ResumeParser:
    """Parse resume to extract skills, experience level, and structured data."""
    
    def __init__(self):
        self.skill_extractor = SkillExtractor(top_n=40)
    
    def parse(self, resume_text: str) -> Dict:
        """
        Parse resume and return structured data.
        
        Returns:
            {
                "raw_text": str,
                "skills": Set[str],
                "experience_level": str,  # "Entry", "Mid", "Senior", "Lead", "Unknown"
                "years_of_experience": Optional[int]
            }
        """
        if not resume_text or not resume_text.strip():
            return {
                "raw_text": "",
                "skills": set(),
                "experience_level": "Unknown",
                "years_of_experience": None
            }
        
        skills = self.skill_extractor.extract_skills(resume_text, use_llm=True)
        years = self._extract_years_of_experience(resume_text)
        level = self._determine_experience_level(resume_text, years)
        
        return {
            "raw_text": resume_text,
            "skills": skills,
            "experience_level": level,
            "years_of_experience": years
        }
    
    def _extract_years_of_experience(self, text: str) -> Optional[int]:
        """Extract total years of experience from resume."""
        text_lower = text.lower()
        
        # Pattern 1: "X years of experience"
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+(?:in|as|with)',
        ]
        
        years_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years_found.append(int(match))
                except ValueError:
                    continue
        
        # Pattern 2: Calculate from work history dates (YYYY - YYYY)
        date_pattern = r'(20\d{2}|19\d{2})\s*[-–—]\s*(20\d{2}|19\d{2}|present|current)'
        date_matches = re.findall(date_pattern, text_lower, re.IGNORECASE)
        
        total_years = 0
        for start, end in date_matches:
            try:
                start_year = int(start)
                if end.lower() in ('present', 'current'):
                    end_year = 2024  # Current year
                else:
                    end_year = int(end)
                total_years += max(0, end_year - start_year)
            except ValueError:
                continue
        
        if total_years > 0:
            years_found.append(total_years)
        
        # Return the maximum found (most conservative estimate)
        return max(years_found) if years_found else None
    
    def _determine_experience_level(self, text: str, years: Optional[int]) -> str:
        """
        Determine experience level from text and years.
        
        Levels:
        - Entry: 0-2 years or junior keywords
        - Mid: 2-5 years or mid-level keywords
        - Senior: 5-8 years or senior keywords
        - Lead: 8+ years or lead/principal/staff keywords
        """
        text_lower = text.lower()
        
        # Explicit level keywords (highest priority)
        if any(kw in text_lower for kw in ['principal engineer', 'staff engineer', 'engineering manager', 'tech lead', 'lead engineer']):
            return "Lead"
        
        if any(kw in text_lower for kw in ['senior engineer', 'senior developer', 'senior software', 'sr. engineer', 'sr engineer']):
            return "Senior"
        
        if any(kw in text_lower for kw in ['mid-level', 'mid level', 'intermediate']):
            return "Mid"
        
        if any(kw in text_lower for kw in ['junior', 'entry level', 'entry-level', 'graduate', 'intern']):
            return "Entry"
        
        # Use years if available
        if years is not None:
            if years >= 8:
                return "Lead"
            elif years >= 5:
                return "Senior"
            elif years >= 2:
                return "Mid"
            else:
                return "Entry"
        
        return "Unknown"
