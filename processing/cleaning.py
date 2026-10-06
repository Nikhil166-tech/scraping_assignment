"""Data cleaning module with pure functions.

Transforms raw scraped fields into normalized, consistent formats (Stage 5).
"""

import re
from typing import Any, Dict, List, Optional, Union

# Word-to-numeric rating map (from Snippet 5.4)
RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def clean_text(value: Optional[Any]) -> Optional[str]:
    """Remove extra spaces, tabs, newlines, and non-breaking spaces (\xa0).

    Snippet 5.4: Collapse all whitespace. Empty string becomes None.
    """
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(text: Optional[str]) -> Optional[str]:
    """Remove surrounding curly or standard quotation marks from text."""
    if not text:
        return None
    t = text.strip()
    # Strip smart/curly quotes as well as standard quotes
    t = t.strip('“"”\'‘’) ')
    return t or None


def clean_price(raw: Optional[Any]) -> Optional[float]:
    """Turn currency string (e.g. '£51.77') into a float (Snippet 5.4)."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return round(float(raw), 2) if raw >= 0 else None
    raw_str = str(raw).strip()
    if not raw_str:
        return None
    match = re.search(r"\d+(?:\.\d+)?", raw_str.replace(",", ""))
    return round(float(match.group()), 2) if match else None


def clean_rating(raw: Optional[Any]) -> Optional[int]:
    """Convert rating words ('star-rating Three') or numbers to integer 1..5 (Snippet 5.4)."""
    if raw is None:
        return None
    if isinstance(raw, int) and 1 <= raw <= 5:
        return raw

    # Search for rating word in string
    for word in str(raw).lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
        if word.isdigit() and 1 <= int(word) <= 5:
            return int(word)
    return None


def clean_tags(tags: Optional[Union[List[str], str]]) -> Optional[str]:
    """Lowercase, sort, and join tags with ';' (Stage 5 specification)."""
    if not tags:
        return None

    if isinstance(tags, str):
        parts = [p.strip().lower() for p in re.split(r"[,;\|]", tags)]
    elif isinstance(tags, list):
        parts = [str(p).strip().lower() for p in tags]
    else:
        return None

    # Lowercase, deduplicate, and sort
    cleaned = sorted(list(set(p for p in parts if p)))
    return ";".join(cleaned) if cleaned else None


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Ensure URL is clean and starts with http:// or https://."""
    if not url:
        return None
    cleaned = str(url).strip()
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    return None


def clean_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """Apply cleaning functions to all fields of a raw scraped record."""
    source = clean_text(raw_record.get("source"))
    title_raw = raw_record.get("name_or_title")

    # If it's a quote, strip surrounding curly quotes first
    if source == "Quotes to Scrape" and title_raw:
        title = clean_text(strip_quotes(str(title_raw)))
    else:
        title = clean_text(title_raw)

    return {
        "source": source,
        "name_or_title": title,
        "category": clean_text(raw_record.get("category")),
        "price": clean_price(raw_record.get("price")),
        "rating": clean_rating(raw_record.get("rating")),
        "author": clean_text(raw_record.get("author")),
        "tags": clean_tags(raw_record.get("tags")),
        "source_url": clean_text(raw_record.get("source_url")),
        "scraped_at": clean_text(raw_record.get("scraped_at")),
    }
