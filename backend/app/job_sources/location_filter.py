
"""Shared location filtering for all job providers."""

import re
from typing import Literal

Eligibility = Literal["eligible", "ineligible", "unknown"]

# Country codes used by Adzuna and our other job providers.
COUNTRY_ALIASES = {
    "de": ("germany", "deutschland"),
    "gb": ("united kingdom", "great britain", "uk"),
    "us": ("united states", "usa", "u.s.", "us"),
    "fr": ("france",),
    "nl": ("netherlands",),
    "at": ("austria", "österreich"),
    "ch": ("switzerland", "schweiz"),
    "ie": ("ireland",),
    "es": ("spain",),
    "it": ("italy",),
    "pl": ("poland",),
    "se": ("sweden",),
    "dk": ("denmark",),
    "be": ("belgium",),
    "pt": ("portugal",),
    "fi": ("finland",),
}

# Expand this registry as we add more countries.
CITY_COUNTRIES = {
    "berlin": "de",
    "munich": "de",
    "münchen": "de",
    "hamburg": "de",
    "frankfurt": "de",
    "cologne": "de",
    "köln": "de",
    "stuttgart": "de",
    "düsseldorf": "de",
    "dortmund": "de",
    "essen": "de",
    "leipzig": "de",
    "bremen": "de",
    "dresden": "de",
    "hannover": "de",
    "nuremberg": "de",
    "nürnberg": "de",
    "duisburg": "de",
    "bochum": "de",
    "wuppertal": "de",
    "bonn": "de",
    "bielefeld": "de",
    "mannheim": "de",
    "karlsruhe": "de",
    "london": "gb",
    "dublin": "ie",
    "paris": "fr",
    "amsterdam": "nl",
    "vienna": "at",
    "wien": "at",
    "zurich": "ch",
    "zürich": "ch",
    "madrid": "es",
    "milan": "it",
    "milano": "it",
    "warsaw": "pl",
    "stockholm": "se",
    "copenhagen": "dk",
    "brussels": "be",
    "lisbon": "pt",
    "helsinki": "fi",
    "new york": "us",
    "san francisco": "us",
    "seattle": "us",
    "chicago": "us",
}

EU_COUNTRIES = {
    "de", "fr", "nl", "at", "ie", "es", "it",
    "pl", "se", "dk", "be", "pt", "fi",
}

UNKNOWN_LOCATIONS = {
    "", "n/a", "unknown", "not specified", "unspecified"
}


def _contains(text: str, term: str) -> bool:
    """Match whole words/phrases, not partial substrings."""
    return bool(
        re.search(
            rf"(?<!\w){re.escape(term)}(?!\w)",
            text,
            re.IGNORECASE,
        )
    )


def _mentioned_countries(location: str) -> set[str]:
    """Find known countries mentioned directly or via city names."""
    found = set()

    for code, aliases in COUNTRY_ALIASES.items():
        if any(_contains(location, alias) for alias in aliases):
            found.add(code)

    for city, code in CITY_COUNTRIES.items():
        if _contains(location, city):
            found.add(code)

    return found


def location_eligibility(
    location: str,
    country: str,
    city: str | None = None,
) -> Eligibility:
    """
    Classify whether a job location matches a target country/city.

    'eligible' means a location match, not confirmed work authorization.
    'unknown' means insufficient information.
    """
    text = (location or "").strip().lower()
    country = (country or "").strip().lower()
    city = (city or "").strip().lower()

    if text in UNKNOWN_LOCATIONS:
        return "unknown"

    if country not in COUNTRY_ALIASES:
        return "unknown"

    mentioned = _mentioned_countries(text)

    # Remote roles can be limited to a country or region.
    is_remote = any(
        _contains(text, word)
        for word in ("remote", "work from anywhere", "wfh")
    )

    # An explicit city match is strongest.
    if city and _contains(text, city):
        return "eligible"

    # A remote job explicitly open to the target country.
    if is_remote and country in mentioned:
        return "eligible"

    # Regional remote eligibility.
    if is_remote:
        if _contains(text, "dach") and country in {"de", "at", "ch"}:
            return "eligible"

        if (
            (_contains(text, "eu") or
             _contains(text, "european union"))
            and country in EU_COUNTRIES
        ):
            return "eligible"

        # Europe is ambiguous: not every Europe-wide listing
        # has the same employment eligibility rules.
        if _contains(text, "europe"):
            return "unknown"

        if mentioned and country not in mentioned:
            return "ineligible"

        return "unknown"

    # A city-specific search should not automatically accept
    # every onsite job in the same country.
    if city:
        if mentioned and country not in mentioned:
            return "ineligible"
        return "unknown"

    if country in mentioned:
        return "eligible"

    if mentioned:
        return "ineligible"

    return "unknown"


def location_matches(
    location: str,
    country: str,
    city: str | None = None,
    include_unknown: bool = True,
) -> bool:
    """
    Boolean filter for provider integrations.

    Unknown jobs can be retained for further review.
    """
    result = location_eligibility(location, country, city)

    return (
        result == "eligible"
        or (include_unknown and result == "unknown")
    )
