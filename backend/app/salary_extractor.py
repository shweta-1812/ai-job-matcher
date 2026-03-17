"""
Extract salary information from job descriptions.
"""
import re
from typing import Optional, Dict


def extract_salary(text: str) -> Optional[Dict[str, any]]:
    """
    Extract salary information from job description text.
    
    Returns:
        {
            "min": int,
            "max": int,
            "currency": str,
            "period": str,  # "year", "month", "hour"
            "raw": str
        }
        or None if no salary found
    """
    if not text:
        return None
    
    text = text.replace(",", "").replace(".", "")  # Normalize numbers
    
    # Patterns for different salary formats
    patterns = [
        # €50,000 - €70,000 per year
        r'[€$£]\s*(\d+)[\s,]*k?\s*[-–—to]\s*[€$£]?\s*(\d+)[\s,]*k?\s*(?:per\s+)?(year|annum|annually|yr|pa)',
        # 50k - 70k EUR
        r'(\d+)[\s,]*k\s*[-–—to]\s*(\d+)[\s,]*k\s*(eur|usd|gbp|euro|dollar|pound)',
        # €50000 - €70000
        r'[€$£]\s*(\d{4,6})\s*[-–—to]\s*[€$£]?\s*(\d{4,6})',
        # 50000 - 70000 EUR/year
        r'(\d{4,6})\s*[-–—to]\s*(\d{4,6})\s*(eur|usd|gbp|euro|dollar|pound)?\s*(?:/|per)?\s*(year|month|hour|yr|mo|hr)?',
        # Up to €70,000
        r'up\s+to\s+[€$£]\s*(\d+)[\s,]*k?',
        # €70,000+
        r'[€$£]\s*(\d+)[\s,]*k?\s*\+',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            # Determine currency
            currency = "EUR"  # Default
            for g in groups:
                if g and g.lower() in ["usd", "dollar"]:
                    currency = "USD"
                elif g and g.lower() in ["gbp", "pound"]:
                    currency = "GBP"
                elif g and g.lower() in ["eur", "euro"]:
                    currency = "EUR"
            
            # Determine period
            period = "year"  # Default
            for g in groups:
                if g and g.lower() in ["month", "mo"]:
                    period = "month"
                elif g and g.lower() in ["hour", "hr"]:
                    period = "hour"
            
            # Extract min/max
            try:
                if len(groups) >= 2 and groups[0] and groups[1]:
                    min_sal = int(groups[0])
                    max_sal = int(groups[1])
                    
                    # Handle 'k' notation (50k = 50000)
                    if "k" in match.group(0).lower():
                        min_sal *= 1000
                        max_sal *= 1000
                    
                    return {
                        "min": min_sal,
                        "max": max_sal,
                        "currency": currency,
                        "period": period,
                        "raw": match.group(0)
                    }
                elif groups[0]:
                    # Single value (up to X or X+)
                    sal = int(groups[0])
                    if "k" in match.group(0).lower():
                        sal *= 1000
                    
                    if "up to" in match.group(0).lower():
                        return {
                            "min": None,
                            "max": sal,
                            "currency": currency,
                            "period": period,
                            "raw": match.group(0)
                        }
                    else:  # X+
                        return {
                            "min": sal,
                            "max": None,
                            "currency": currency,
                            "period": period,
                            "raw": match.group(0)
                        }
            except (ValueError, IndexError):
                continue
    
    return None


def format_salary(salary_info: Optional[Dict]) -> str:
    """Format salary info for display."""
    if not salary_info:
        return "Not specified"
    
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£"
    }
    
    symbol = currency_symbols.get(salary_info["currency"], salary_info["currency"])
    period = salary_info["period"]
    
    if salary_info["min"] and salary_info["max"]:
        return f"{symbol}{salary_info['min']:,} - {symbol}{salary_info['max']:,}/{period}"
    elif salary_info["max"]:
        return f"Up to {symbol}{salary_info['max']:,}/{period}"
    elif salary_info["min"]:
        return f"{symbol}{salary_info['min']:,}+/{period}"
    
    return "Not specified"
