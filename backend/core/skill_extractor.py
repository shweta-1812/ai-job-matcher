import re
from typing import Optional, Set, Tuple, List

from keybert import KeyBERT
from sklearn.feature_extraction.text import CountVectorizer


class SkillExtractor:
    """
    KeyBERT + constrained candidate phrases for skill extraction.

    Key idea:
    - Use CountVectorizer to generate candidate skill-like phrases.
    - Then KeyBERT ranks those candidates by relevance.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        top_n: int = 35,
        ngram_range: Tuple[int, int] = (1, 3),
    ):
        self.kw_model = KeyBERT(model_name)
        self.top_n = top_n
        self.ngram_range = ngram_range

        # Strong "JD fluff" / action verbs / generic words
        self.bad_words = {
            "we", "you", "our", "their", "team", "teams", "company", "companies",
            "role", "opportunity", "opportunities", "responsibilities", "requirements", "required",
            "looking", "seeking", "join", "work", "works", "working", "deliver", "delivering",
            "ensure", "ensuring", "support", "supporting", "build", "built", "develop", "developed",
            "friendly", "global", "dedicated", "focused", "dear", "currently", "different",
            "clients", "countries", "sector", "sectors", "expert", "experts",
            "experience", "skills", "ability", "knowledge", "understanding", "strong",
            "good", "excellent", "great", "best", "new", "years", "year", "day", "days",
            "time", "times", "way", "ways", "need", "needs", "want", "wants",
            "help", "helps", "helping", "make", "makes", "making", "use", "using", "used",
            "including", "include", "includes", "such", "like", "well", "also", "plus",
            "related", "relevant", "similar", "various", "multiple", "several",
            "level", "levels", "senior", "junior", "mid", "entry", "lead",
            "position", "positions", "candidate", "candidates", "applicant", "applicants",
            "project", "projects", "product", "products", "service", "services",
            "business", "management", "manager", "development", "engineering",
            "software", "application", "applications", "system", "systems",
            "design", "designing", "implementation", "implementing", "integration",
            "solution", "solutions", "platform", "platforms", "technology", "technologies",
            "data", "analysis", "analytics", "reporting", "reports",
            "communication", "collaboration", "problem", "solving", "thinking",
            "learning", "training", "mentoring", "coaching", "leadership",
            "agile", "scrum", "kanban", "waterfall", "methodology", "methodologies",
            "process", "processes", "procedure", "procedures", "workflow", "workflows",
            "quality", "testing", "debugging", "troubleshooting", "optimization",
            "performance", "scalability", "reliability", "availability", "security",
            "documentation", "documenting", "writing", "reading", "reviewing"
        }

        # Canonical mappings
        self.normalize_map = {
            "scikit learn": "scikit-learn",
            "sklearn": "scikit-learn",
            "fast api": "fastapi",
        }

        # Small universal tool list to always keep if present (not huge)
        self.core_tools = {
            "python", "java", "javascript", "typescript", "c++", "csharp", "ruby", "php", "go", "rust", "scala", "kotlin",
            "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "cassandra",
            "git", "github", "gitlab", "bitbucket", "svn",
            "aws", "azure", "gcp", "heroku", "digitalocean",
            "docker", "kubernetes", "jenkins", "circleci", "travis",
            "pytorch", "tensorflow", "keras", "scikit-learn", "opencv", "nltk", "spacy",
            "spark", "hadoop", "airflow", "kafka", "flink",
            "fastapi", "django", "flask", "express", "spring", "rails",
            "react", "angular", "vue", "svelte", "nextjs",
            "pandas", "numpy", "matplotlib", "seaborn", "plotly",
            "tableau", "power bi", "looker", "metabase",
            "linux", "unix", "bash", "powershell",
            "rest", "graphql", "grpc", "soap",
            "html", "css", "sass", "less", "tailwind",
            "webpack", "vite", "rollup", "parcel",
            "jest", "pytest", "junit", "mocha", "cypress",
            "terraform", "ansible", "puppet", "chef",
            "nginx", "apache", "tomcat", "iis"
        }

        # Candidate generator: only allow alphabetic words + hyphen
        # Stopwords will be handled via stop_words list
        self.vectorizer = CountVectorizer(
            ngram_range=self.ngram_range,
            stop_words="english",
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]+\b"
        )

    def _clean(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize(self, phrase: str) -> str:
        p = phrase.strip().lower()
        p = re.sub(r"\s+", " ", p)
        if p in self.normalize_map:
            return self.normalize_map[p]
        p = p.replace("scikit learn", "scikit-learn").replace("fast api", "fastapi")
        return p

    def _is_noise_phrase(self, phrase: str) -> bool:
        words = phrase.split()
        if len(words) == 0:
            return True
        if len(words) > 3:
            return True
        if len(phrase) < 2:
            return True
        
        # Filter out phrases with bad words
        if any(w in self.bad_words for w in words):
            return True
        
        # Filter out purely numeric or too short
        if phrase.isdigit() or len(phrase) <= 2:
            return True
        
        # Filter out phrases that are just adjectives/adverbs
        adjectives = {"good", "great", "best", "strong", "excellent", "high", "low", "new", "old"}
        if phrase in adjectives:
            return True
        
        return False

    def extract_skills(self, text: str, extra_stopwords: Optional[Set[str]] = None) -> Set[str]:
        if not text or not text.strip():
            return set()

        cleaned = self._clean(text)
        extra_sw = set((extra_stopwords or set()))

        # 1) Always capture core tools if present (fast + reliable)
        skills: Set[str] = set()
        for tool in self.core_tools:
            if re.search(rf"\b{re.escape(tool)}\b", cleaned):
                skills.add(tool)

        # 2) KeyBERT with constrained candidate phrases
        #    candidates come from CountVectorizer, which reduces junk a lot.
        keywords = self.kw_model.extract_keywords(
            cleaned,
            vectorizer=self.vectorizer,
            top_n=self.top_n,
            use_mmr=True,
            diversity=0.7,  # Increased diversity to get more varied skills
        )

        for phrase, score in keywords:
            # Lower threshold to capture more skills (was 0.3)
            if score < 0.2:
                continue
            
            p = self._normalize(phrase)
            if p in extra_sw:
                continue
            if self._is_noise_phrase(p):
                continue
            
            # Skip if already in core tools (avoid duplicates)
            if p in self.core_tools:
                continue
            
            # Skip if it's a combination of multiple core tools (e.g., "python aws docker")
            words = p.split()
            if len(words) > 1:
                core_tool_count = sum(1 for w in words if w in self.core_tools)
                if core_tool_count > 1:
                    continue  # Skip multi-tool combinations
            
            # Only add if it looks like a real technical term
            # (contains numbers, hyphens, or is a known pattern)
            if self._looks_like_technical_term(p):
                skills.add(p)

        return skills
    
    def _looks_like_technical_term(self, phrase: str) -> bool:
        """Check if phrase looks like a real technical term."""
        # Allow if it has numbers (e.g., "python3", "c++", "vue3")
        if re.search(r'\d', phrase):
            return True
        
        # Allow if it has special chars like + or # (e.g., "c++", "c#")
        if re.search(r'[+#]', phrase):
            return True
        
        # Allow if it's a compound word with hyphen (e.g., "machine-learning")
        if '-' in phrase and len(phrase) > 5:
            return True
        
        # Allow if it's an acronym (all caps, 2-5 letters)
        if phrase.isupper() and 2 <= len(phrase) <= 5:
            return True
        
        # Allow if it ends with common tech suffixes
        tech_suffixes = ['js', 'py', 'sql', 'api', 'db', 'ml', 'ai', 'ui', 'ux', 'ci', 'cd']
        if any(phrase.endswith(suffix) for suffix in tech_suffixes):
            return True
        
        # Allow if it's in a list of known technical domains/skills
        tech_domains = {
            'devops', 'mlops', 'devsecops', 'frontend', 'backend', 'fullstack',
            'microservices', 'serverless', 'containerization', 'orchestration',
            'cicd', 'etl', 'elt', 'olap', 'oltp', 'nosql', 'rdbms',
            'nlp', 'cv', 'rl', 'gan', 'cnn', 'rnn', 'lstm', 'bert', 'gpt',
            'restful', 'graphql', 'grpc', 'websocket', 'mqtt',
            'oauth', 'jwt', 'saml', 'ldap', 'ssl', 'tls', 'https',
            'agile', 'scrum', 'kanban', 'jira', 'confluence',
            # Add more common technical terms
            'api', 'sdk', 'cli', 'gui', 'ide', 'orm', 'mvc', 'mvvm',
            'json', 'xml', 'yaml', 'csv', 'pdf', 'http', 'ftp', 'ssh',
            'cloud', 'saas', 'paas', 'iaas', 'cdn', 'dns', 'vpc',
            'machine learning', 'deep learning', 'neural network', 'computer vision',
            'natural language', 'data science', 'big data', 'data warehouse',
            'web development', 'mobile development', 'app development',
            'version control', 'code review', 'unit testing', 'integration testing',
            'continuous integration', 'continuous deployment', 'continuous delivery',
            'load balancing', 'caching', 'monitoring', 'logging', 'debugging',
            'refactoring', 'optimization', 'automation', 'scripting',
            'database design', 'schema design', 'query optimization',
            'responsive design', 'cross-browser', 'accessibility',
            'authentication', 'authorization', 'encryption', 'hashing',
            'algorithms', 'data structures', 'object-oriented', 'functional programming'
        }
        if phrase in tech_domains:
            return True
        
        # Allow multi-word technical phrases (2-3 words)
        words = phrase.split()
        if len(words) >= 2:
            # Check if it contains at least one core tool or tech domain word
            tech_words = {'learning', 'network', 'language', 'science', 'warehouse', 
                         'development', 'testing', 'integration', 'deployment', 'delivery',
                         'balancing', 'design', 'programming', 'structures', 'oriented'}
            if any(word in tech_words for word in words):
                return True
        
        # Allow if it's a single technical-sounding word (>= 4 chars, not in bad_words)
        if len(phrase) >= 4 and phrase not in self.bad_words:
            # Check if it looks like a technical term (contains common tech patterns)
            tech_patterns = ['tech', 'dev', 'eng', 'ops', 'sys', 'net', 'web', 'app', 
                           'data', 'base', 'ware', 'soft', 'hard', 'script', 'code',
                           'test', 'debug', 'deploy', 'build', 'compile', 'run']
            if any(pattern in phrase for pattern in tech_patterns):
                return True
        
        # Reject everything else (too generic)
        return False
