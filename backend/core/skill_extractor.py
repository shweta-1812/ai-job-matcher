import re
import json
import os
import time
import hashlib
from typing import Optional, Set

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Groq free tier: 30 RPM for llama-3.1-8b-instant
_MIN_INTERVAL = 60.0 / 30  # 2.0 seconds between calls


class SkillExtractor:
    """
    Two-mode skill extractor:
    - use_llm=False  → fast regex scan (bulk job ranking pass)
    - use_llm=True   → Groq LLM (resume + top 30 jobs)
    """

    def __init__(self, top_n: int = 35, **kwargs):
        self._groq_client = None
        self._cache: dict = {}
        self._last_call_time: float = 0
        self._init_groq()

        self.core_tools = {
            # Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "csharp", "ruby", "php",
            "go", "golang", "rust", "scala", "kotlin", "swift", "r", "matlab", "perl",
            # Databases
            "sql", "nosql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
            "cassandra", "dynamodb", "neo4j", "mariadb", "sqlite", "oracle", "mssql",
            "bigquery", "snowflake", "redshift", "databricks",
            # Vector DBs
            "pinecone", "weaviate", "qdrant", "chroma", "milvus", "faiss", "pgvector",
            # Version Control
            "git", "github", "gitlab", "bitbucket",
            # Cloud
            "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean",
            # DevOps
            "docker", "kubernetes", "k8s", "jenkins", "circleci", "terraform", "ansible", "helm",
            # AI/ML
            "pytorch", "tensorflow", "keras", "scikit-learn", "opencv", "nltk", "spacy",
            "huggingface", "transformers", "langchain", "llamaindex", "openai",
            "llm", "rag", "fine-tuning", "prompt engineering", "embeddings",
            "nlp", "computer vision", "deep learning", "machine learning",
            "mlflow", "wandb", "mlops",
            # Data
            "spark", "hadoop", "airflow", "kafka", "flink", "hive",
            "etl", "informatica", "talend", "aws glue", "dbt", "fivetran",
            # Web
            "fastapi", "django", "flask", "express", "spring", "spring boot", "rails",
            "react", "angular", "vue", "nextjs",
            "pandas", "numpy", "matplotlib", "scipy",
            # BI
            "tableau", "power bi", "looker", "looker studio", "grafana", "kibana",
            # Tools & Methods
            "jira", "confluence", "slack", "notion",
            "agile", "scrum", "kanban", "devops", "cicd",
            "rest", "restful", "graphql", "grpc",
            "linux", "bash",
            "prometheus", "datadog", "splunk",
        }

        self.normalize_map = {
            "scikit learn": "scikit-learn",
            "sklearn": "scikit-learn",
            "fast api": "fastapi",
            "gcp": "google cloud",
            "google cloud platform": "google cloud",
            "google cloud run": "google cloud",
            "google cloud functions": "google cloud",
            "k8s": "kubernetes",
            "llms": "llm",
            "large language model": "llm",
            "large language models": "llm",
            "retrieval augmented generation": "rag",
            "ci/cd": "cicd",
            "ci cd": "cicd",
        }

    def _init_groq(self):
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self._groq_client = Groq(api_key=api_key)
        except Exception as e:
            print(f"Groq init failed: {e}")

    def _normalize(self, phrase: str) -> str:
        p = phrase.strip().lower()
        p = re.sub(r"\s+", " ", p)
        return self.normalize_map.get(p, p)

    def _call_groq(self, text: str) -> Optional[Set[str]]:
        """Single rate-limited Groq call."""
        if not self._groq_client:
            return None
        try:
            elapsed = time.time() - self._last_call_time
            if elapsed < _MIN_INTERVAL:
                time.sleep(_MIN_INTERVAL - elapsed)

            prompt = f"""Extract all technical skills, tools, technologies, frameworks, programming languages,
methodologies, and platforms mentioned in the following text.

Rules:
- Return ONLY a JSON array of strings, nothing else
- Each item should be a specific skill/tool name (e.g. "Python", "AWS", "RAG", "LLM", "Docker")
- Normalize: "Google Cloud Run" -> "Google Cloud", "LLMs" -> "LLM", "APIs" -> "API"
- Include methodologies if explicit (e.g. "Agile", "Scrum")
- Do NOT include job titles/roles, generic words like "experience"/"team", or vague concepts
- Keep names concise and canonical

Text:
{text[:3000]}

Return only the JSON array:"""

            self._last_call_time = time.time()
            response = self._groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )

            raw = response.choices[0].message.content.strip()
            m = re.search(r'\[.*?\]', raw, re.DOTALL)
            if not m:
                return None

            skills = set()
            for item in json.loads(m.group()):
                if isinstance(item, str) and item.strip():
                    n = self._normalize(item)
                    if len(n) >= 2:
                        skills.add(n)
            return skills

        except Exception as e:
            print(f"Groq call failed: {e}")
            return None

    def _extract_with_regex(self, text: str) -> Set[str]:
        """Fast regex scan — used for bulk job ranking."""
        cleaned = re.sub(r"\s+", " ", text.lower())
        skills = set()
        for tool in self.core_tools:
            if re.search(rf"\b{re.escape(tool)}\b", cleaned):
                skills.add(self._normalize(tool))
        return skills

    def extract_skills(self, text: str, extra_stopwords=None, use_llm: bool = False) -> Set[str]:
        """
        Extract skills from text.
        use_llm=True  → Groq LLM (resume + top jobs)
        use_llm=False → regex (bulk ranking pass, no API calls)
        """
        if not text or not text.strip():
            return set()

        cache_key = hashlib.md5((text + str(use_llm)).encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        skills = self._call_groq(text) if use_llm else None
        if skills is None:
            skills = self._extract_with_regex(text)

        self._cache[cache_key] = skills
        return skills

    def extract_skills_batch_llm(self, texts: list, top_n: int = 30) -> list:
        """
        Run Groq on up to top_n texts with rate limiting.
        Returns list of skill sets aligned to input.
        """
        results = []
        limit = min(len(texts), top_n)
        for i, text in enumerate(texts[:limit]):
            print(f"  LLM skill analysis {i+1}/{limit}...")
            results.append(self.extract_skills(text, use_llm=True))
        return results
