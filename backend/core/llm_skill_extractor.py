import json
from typing import Set, Optional, List
from openai import OpenAI


SYSTEM = """You extract professional skills from text.
Return ONLY valid JSON. No markdown. No commentary.
"""

USER_TEMPLATE = """Extract a clean, deduplicated list of skills from the text below.

Rules:
- Include technical skills, tools, frameworks, cloud platforms, methodologies, and relevant soft skills.
- Keep skills short (1-4 words).
- Prefer canonical forms (e.g., "machine learning" not "ML" unless only "ML" is present).
- Do NOT include generic phrases like "team player", "good communication" unless explicitly emphasized.
- Return JSON exactly in this schema:
{{
  "skills": ["skill1", "skill2", ...]
}}

TEXT:
{TEXT}
"""


class LLMSkillExtractor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract_skills(self, text: str) -> Set[str]:
        if not text or not text.strip():
            return set()

        prompt = USER_TEMPLATE.replace("{TEXT}", text)

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        raw = resp.choices[0].message.content.strip()

        # Robust parse (LLMs sometimes add whitespace)
        data = json.loads(raw)
        skills = data.get("skills", [])
        return {s.strip().lower() for s in skills if isinstance(s, str) and s.strip()}
