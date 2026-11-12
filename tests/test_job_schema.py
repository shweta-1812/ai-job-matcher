
from backend.app.job_sources.job_schema import normalize_job

examples = [
    ("Software Engineer", "Technology"),
    ("Registered Nurse", "Healthcare"),
    ("Accountant", "Finance"),
    ("Primary School Teacher", "Education"),
    ("Sales Manager", "Sales"),
]

for title, category in examples:
    job = normalize_job(
        title=title,
        company="Example Employer",
        location="Berlin, Germany",
        description=f"Open position for {title}",
        url="https://example.com/jobs",
        source="Test",
        category=category,
    )

    assert job["title"] == title
    assert job["category"] == category
    assert job["company"]["display_name"] == "Example Employer"

    print(f"PASS: {title} ({category})")

print("All job schema tests passed!")
