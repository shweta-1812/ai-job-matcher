
from backend.app.job_sources.location_filter import (
    location_eligibility,
    location_matches,
)

cases = [
    ("Berlin, Germany", "de", None, "eligible"),
    ("Germany", "de", None, "eligible"),
    ("Munich", "de", None, "eligible"),
    ("Remote - Germany", "de", None, "eligible"),
    ("Remote from the US", "de", None, "ineligible"),
    ("US-Remote", "de", None, "ineligible"),
    ("Remote - EU", "de", None, "eligible"),
    ("Remote - Europe", "de", None, "unknown"),
    ("London", "de", None, "ineligible"),
    ("Dublin or Germany (Berlin or Remote)", "de", None, "eligible"),
    ("London OR Paris OR Germany", "de", None, "eligible"),
    ("N/A", "de", None, "unknown"),
    ("Berlin", "de", "Berlin", "eligible"),
    ("Munich", "de", "Berlin", "unknown"),
    ("Remote - US", "de", "Berlin", "ineligible"),
]

for location, country, city, expected in cases:
    result = location_eligibility(location, country, city)

    assert result == expected, (
        f"{location}: expected {expected}, got {result}"
    )

    print(f"PASS: {location} -> {result}")

assert location_matches("Remote from the US", "de") is False
assert location_matches("N/A", "de") is True

print("\nAll location filter tests passed!")
