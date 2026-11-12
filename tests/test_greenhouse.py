
from backend.app.job_sources.greenhouse import fetch_greenhouse_jobs

jobs = fetch_greenhouse_jobs(
    board_token="stripe",
    company_name="Stripe",
)

print(f"Total Greenhouse jobs: {len(jobs)}")

for job in jobs[:5]:
    print(
        job["title"],
        "|",
        job["company"]["display_name"],
        "|",
        job["location"]["display_name"],
    )

if jobs:
    assert all(job["source"] == "Greenhouse" for job in jobs)
    assert all(job["redirect_url"] for job in jobs)
    print("Greenhouse integration test passed!")
else:
    print("No jobs returned. Check the board token or API response.")


from collections import Counter

print("\nTop 15 job locations:")
locations = Counter(
    job["location"]["display_name"]
    for job in jobs
)

for location, count in locations.most_common(15):
    print(f"{count:4} | {location}")

print("\nGermany-related jobs:")
germany_jobs = [
    job for job in jobs
    if any(
        term in job["location"]["display_name"].lower()
        for term in [
            "germany",
            "deutschland",
            "berlin",
            "munich",
            "münchen",
            "hamburg",
            "frankfurt",
        ]
    )
]

print(f"Germany-related: {len(germany_jobs)}")

for job in germany_jobs[:10]:
    print(
        job["title"],
        "|",
        job["location"]["display_name"],
    )
