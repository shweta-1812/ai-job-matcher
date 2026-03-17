import os
import requests
import logging
from typing import List, Dict, Any
from urllib.parse import urlencode
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)


def _match_score(query: str, text: str) -> float:
    """
    Calculate match score for ranking:
    - Exact phrase: 1.0
    - All words present: 0.8
    - First word present (for 2-word queries): 0.6
    - Any word present: 0.4
    """
    query_lower = query.lower().strip()
    text_lower = text.lower()
    
    # Exact phrase match
    if query_lower in text_lower:
        return 1.0
    
    query_words = [w for w in query_lower.split() if len(w) > 2]
    if not query_words:
        return 0.0
    
    # All words present
    if len(query_words) > 1:
        all_present = all(word in text_lower for word in query_words)
        if all_present:
            return 0.8
        
        # First word present (specialization)
        if query_words[0] in text_lower:
            return 0.6
    
    # Any word present
    if any(word in text_lower for word in query_words):
        return 0.4
    
    return 0.0


def _flexible_match(query: str, text: str) -> bool:
    """
    Strict matching for multi-word queries:
    - For "AI engineer", REQUIRES "AI" to be present
    - For single words, just checks if present
    """
    query_lower = query.lower().strip()
    text_lower = text.lower()
    
    # Exact phrase match
    if query_lower in text_lower:
        return True
    
    # Split into words (filter out short words like "a", "an", "the")
    query_words = [w for w in query_lower.split() if len(w) > 2]
    if not query_words:
        return False
    
    # For multi-word queries, REQUIRE the first word (specialization)
    if len(query_words) > 1:
        # First word MUST be present
        return query_words[0] in text_lower
    
    # For single-word queries, just check if it's present
    return query_words[0] in text_lower


def _simple_location_match(city: str, location: str) -> bool:
    """
    Simple case-insensitive location matching.
    """
    if not city or not location:
        return True
    
    city_lower = city.lower().strip()
    location_lower = location.lower().strip()
    
    # Check if city name appears anywhere in location
    return city_lower in location_lower


def _is_germany_eu_location(location: str) -> bool:
    """
    Check if location is in Germany or EU.
    """
    if not location:
        return True  # If no location specified, include it
    
    location_lower = location.lower()
    
    # Germany cities and regions
    german_keywords = [
        "germany", "deutschland", "berlin", "munich", "münchen", "hamburg", 
        "frankfurt", "cologne", "köln", "stuttgart", "düsseldorf", "dortmund",
        "essen", "leipzig", "bremen", "dresden", "hannover", "nuremberg", "nürnberg",
        "duisburg", "bochum", "wuppertal", "bonn", "bielefeld", "mannheim", "karlsruhe",
        "remote", "anywhere", "europe", "eu", "dach"
    ]
    
    # EU countries
    eu_countries = [
        "austria", "österreich", "belgium", "bulgaria", "croatia", "cyprus",
        "czech", "denmark", "estonia", "finland", "france", "greece", "hungary",
        "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta",
        "netherlands", "poland", "portugal", "romania", "slovakia", "slovenia",
        "spain", "sweden", "switzerland", "schweiz"
    ]
    
    all_keywords = german_keywords + eu_countries
    
    # Check if any keyword is in location
    return any(keyword in location_lower for keyword in all_keywords)


def search_jobs(country: str, page: int, what: str, where: str | None, results_per_page: int = 50) -> Dict[str, Any]:
    """
    Multi-source job search with Adzuna as primary source.
    
    Returns:
        {
            "results": List[Dict],
            "count": int,
            "sources": Dict[str, int]  # source name -> job count
        }
    """
    all_jobs = []
    sources = {}
    
    # Source 1: Adzuna (PRIMARY - best coverage and quality)
    adzuna_app_id = os.getenv("ADZUNA_APP_ID")
    adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
    
    if adzuna_app_id and adzuna_app_key:
        try:
            logger.info("Fetching from Adzuna API...")
            
            # Adzuna API endpoint for Germany
            base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
            
            params = {
                "app_id": adzuna_app_id,
                "app_key": adzuna_app_key,
                "results_per_page": results_per_page,
                "what": what,
                "content-type": "application/json"
            }
            
            if where:
                params["where"] = where
            
            r = requests.get(base_url, params=params, timeout=30)
            r.raise_for_status()
            
            data = r.json()
            jobs = data.get("results", [])
            
            count = 0
            for job in jobs:
                location = job.get("location", {}).get("display_name", "")
                
                # Filter by Germany/EU location
                if not _is_germany_eu_location(location):
                    continue
                
                # Calculate relevance score
                title = job.get("title", "")
                score = _match_score(what, title)
                
                # For multi-word queries, filter out low-relevance results
                query_words = [w for w in what.lower().split() if len(w) > 2]
                if len(query_words) > 1 and score < 0.6:
                    # Skip jobs that don't have the specialization word
                    continue
                
                all_jobs.append({
                    "title": title,
                    "company": {"display_name": job.get("company", {}).get("display_name", "")},
                    "location": {"display_name": location},
                    "description": job.get("description", ""),
                    "redirect_url": job.get("redirect_url", ""),
                    "created": job.get("created", ""),
                    "source": "Adzuna",
                    "_relevance_score": score
                })
                count += 1
            
            sources["Adzuna"] = count
            logger.info(f"Fetched {count} jobs from Adzuna")
            
        except requests.RequestException as e:
            logger.error(f"Adzuna API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching from Adzuna: {e}")
    else:
        logger.warning("Adzuna API credentials not found in environment")
    
    # Source 2: Remotive (remote jobs, full descriptions)
    try:
        logger.info("Fetching from Remotive API...")
        r = requests.get("https://remotive.com/api/remote-jobs", timeout=30)
        r.raise_for_status()
        
        jobs = r.json().get("jobs", [])
        
        # Score and filter jobs
        scored_jobs = []
        for j in jobs:
            title = j.get("title", "")
            category = j.get("category", "")
            score = max(_match_score(what, title), _match_score(what, category))
            
            # For multi-word queries, require minimum score
            query_words = [w for w in what.lower().split() if len(w) > 2]
            if len(query_words) > 1 and score < 0.6:
                continue
            
            if score > 0:
                scored_jobs.append((score, j))
        
        # Sort by score and take top results
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        count = 0
        for score, job in scored_jobs[:results_per_page]:
            location = job.get("candidate_required_location", "Remote")
            
            # Filter by Germany/EU location
            if not _is_germany_eu_location(location):
                continue
            
            all_jobs.append({
                "title": job.get("title", ""),
                "company": {"display_name": job.get("company_name", "")},
                "location": {"display_name": location},
                "description": job.get("description", ""),
                "redirect_url": job.get("url", ""),
                "created": job.get("publication_date", ""),
                "source": "Remotive",
                "_relevance_score": score
            })
            count += 1
        
        sources["Remotive"] = count
        logger.info(f"Fetched {count} jobs from Remotive")
        
    except requests.RequestException as e:
        logger.error(f"Remotive API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching from Remotive: {e}")
    
    # Source 3: Arbeitnow (EU jobs, full descriptions)
    try:
        logger.info("Fetching from Arbeitnow API...")
        r = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=30)
        r.raise_for_status()
        
        jobs = r.json().get("data", [])
        
        # Score and filter jobs
        scored_jobs = []
        for j in jobs:
            title = j.get("title", "")
            score = _match_score(what, title)
            
            # For multi-word queries, require minimum score
            query_words = [w for w in what.lower().split() if len(w) > 2]
            if len(query_words) > 1 and score < 0.6:
                continue
            
            if score > 0:
                # Apply location filter early (simple match)
                location = j.get("location", "Remote")
                if where and not _simple_location_match(where, location):
                    continue
                scored_jobs.append((score, j))
        
        # Sort by score and take top results
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        count = 0
        for score, job in scored_jobs[:results_per_page]:
            location = job.get("location", "Remote")
            
            # Filter by Germany/EU location
            if not _is_germany_eu_location(location):
                continue
            
            all_jobs.append({
                "title": job.get("title", ""),
                "company": {"display_name": job.get("company_name", "")},
                "location": {"display_name": location},
                "description": job.get("description", ""),
                "redirect_url": job.get("url", ""),
                "created": job.get("created_at", ""),
                "source": "Arbeitnow",
                "_relevance_score": score
            })
            count += 1
        
        sources["Arbeitnow"] = count
        logger.info(f"Fetched {count} jobs from Arbeitnow")
        
    except requests.RequestException as e:
        logger.error(f"Arbeitnow API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching from Arbeitnow: {e}")
    
    # Sort all jobs by relevance score before returning
    all_jobs.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
    
    logger.info(f"Total jobs fetched: {len(all_jobs)} from {len(sources)} sources")
    
    return {
        "results": all_jobs,
        "count": len(all_jobs),
        "sources": sources
    }
