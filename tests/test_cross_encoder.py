import time
from sentence_transformers import CrossEncoder

MODEL_NAME = "BAAI/bge-reranker-v2-m3"

print("Loading reranker...")
model = CrossEncoder(MODEL_NAME, max_length=512)

resume = """
Business Analyst and Product Owner with experience in
Agile, Scrum, SAP, SQL, Python, FastAPI and AI projects.
"""

jobs = [
    "Product Owner requiring Agile, Scrum, SAP and SQL",

    "AI Engineer requiring Python, FastAPI and machine learning",

    "Produktmanager mit Erfahrung in Agile, Scrum, SAP und SQL",

    "KI-Entwickler mit Erfahrung in Python, FastAPI und Machine Learning",

    "Senior Java Entwickler mit Spring Boot und Kubernetes",

    "Marketing Manager mit Erfahrung in SEO und Werbung",
]

pairs = [(resume, job) for job in jobs]

print(f"Testing {len(pairs)} jobs...")

start = time.perf_counter()

scores = model.predict(pairs, batch_size=4)

elapsed = time.perf_counter() - start
print(f"\nReranking time: {elapsed:.2f} seconds")

ranked = sorted(
    zip(jobs, scores),
    key=lambda item: float(item[1]),
    reverse=True
)

for job, score in ranked:
    print(f"{float(score):.4f} | {job}")
