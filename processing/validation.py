"""Validation module for enforcing schema and business rules on scraped records.

Directly implements Stage 6 and Snippet 5.5 validation rules and failure codes.
"""

from typing import Any, Dict, List

VALID_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(rec: Dict[str, Any]) -> List[str]:
    """Check one cleaned record and return a list of problems (Snippet 5.5).

    An empty list indicates the record is valid.
    """
    problems: List[str] = []

    # 1. Source check
    if rec.get("source") not in VALID_SOURCES:
        problems.append("unknown_source")

    # 2. Name or Title check
    if not rec.get("name_or_title"):
        problems.append("missing_name")

    # 3. Source URL check
    if not str(rec.get("source_url") or "").startswith(("http://", "https://")):
        problems.append("invalid_url")

    # 4. Price check (if present, must be numeric >= 0)
    price = rec.get("price")
    if price is not None and (not isinstance(price, (int, float)) or price < 0):
        problems.append("invalid_price")

    # 5. Rating check (if present, must be integer 1 to 5)
    rating = rec.get("rating")
    if rating is not None and rating not in (1, 2, 3, 4, 5):
        problems.append("invalid_rating")

    # 6. Source-specific expectations
    if rec.get("source") == "Quotes to Scrape":
        if not rec.get("author"):
            problems.append("missing_author")
        if price is not None:
            problems.append("unexpected_price")

    return problems
