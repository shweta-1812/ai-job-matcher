"""
Job description analyzer to extract requirements, skills, and experience level.
"""
import re
import sys
from pathlib import Path
from typing import Dict, Set, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_extractor import SkillExtractor


class JDAnalyzer:
    """Analyze job descriptions to extract structured requirements."""
    
    def __init__(self):
        self.skill_extractor = SkillExtractor(top_n=40)
    
    def analyze(self, jd_text: str) -> Dict:
        """
        Analyze job description and return structured data.
        
        Returns:
            {
                "skills": Set[str],
                "experience_level": str,  # "Entry", "Mid", "Senior", "Lead", "Any"
                "min_years": Optional[int],
                "max_years": Optional[int]
            }
        """
        if not jd_text or not jd_text.strip():
            return {
                "skills": set(),
                "experience_level": "Any",
                "min_years": None,
                "max_years": None
            }
        
        skills = self.skill_extractor.extract_skills(jd_text)
        min_years, max_years = self._extract_years_requirement(jd_text)
        level = self._determine_required_level(jd_text, min_years)
        
        return {
            "skills": skills,
            "experience_level": level,
            "min_years": min_years,
            "max_years": max_years
        }
    
    def _extract_years_requirement(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract required years of experience from JD."""
        text_lower = text.lower()
        
        # Pattern: "X+ years", "X-Y years", "minimum X years"
        patterns = [
            r'(\d+)\+\s*years?',
            r'(\d+)\s*[-–—to]\s*(\d+)\s*years?',
            r'minimum\s+(\d+)\s*years?',
            r'at least\s+(\d+)\s*years?',
            r'(\d+)\s*years?\s+(?:of\s+)?(?:experience|exp)',
        ]
        
        min_years = None
        max_years = None
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    # Range pattern (X-Y years)
                    try:
                        nums = [int(m) for m in match if m]
                        if len(nums) == 2:
                            min_years = min(nums)
                            max_years = max(nums)
                        elif len(nums) == 1:
                            min_years = nums[0]
                    except ValueError:
                        continue
                else:
                    # Single number pattern
                    try:
                        min_years = int(match)
                    except ValueError:
                        continue
        
        return min_years, max_years
    
    def _determine_required_level(self, text: str, min_years: Optional[int]) -> str:
        """Determine required experience level from JD."""
        text_lower = text.lower()
        
        # Explicit level keywords
        if any(kw in text_lower for kw in ['principal', 'staff', 'lead', 'head of', 'director', 'vp']):
            return "Lead"
        
        if any(kw in text_lower for kw in ['senior', 'sr.', 'sr ']):
            return "Senior"
        
        if any(kw in text_lower for kw in ['mid-level', 'mid level', 'intermediate']):
            return "Mid"
        
        if any(kw in text_lower for kw in ['junior', 'entry level', 'entry-level', 'graduate', 'intern']):
            return "Entry"
        
        # Use years requirement if available
        if min_years is not None:
            if min_years >= 8:
                return "Lead"
            elif min_years >= 5:
                return "Senior"
            elif min_years >= 2:
                return "Mid"
            elif min_years >= 0:
                return "Entry"
        
        return "Any"
