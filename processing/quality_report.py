"""Data Quality Report generator (Bonus Feature).

Analyzes the consolidated records to produce metrics on field completeness,
price distributions, rating breakdowns, and top entities.
"""

from collections import Counter
import statistics
from typing import Any, Dict, List


def generate_data_quality_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze consolidated records and generate a comprehensive data quality report.

    Args:
        records: List of cleaned, validated, and deduplicated records.

    Returns:
        Dictionary containing completeness percentages, price stats, rating counts, etc.
    """
    total_records = len(records)
    if total_records == 0:
        return {"total_records": 0, "message": "No records to analyze"}

    # 1. Field Completeness Analytics
    columns = [
        "source",
        "name_or_title",
        "category",
        "price",
        "rating",
        "author",
        "tags",
        "source_url",
        "scraped_at",
    ]

    completeness: Dict[str, Dict[str, Any]] = {}
    for col in columns:
        present_count = sum(1 for r in records if r.get(col) is not None and str(r.get(col)).strip() != "")
        missing_count = total_records - present_count
        pct = round((present_count / total_records) * 100, 2)
        completeness[col] = {
            "present_count": present_count,
            "missing_count": missing_count,
            "completeness_pct": pct,
        }

    # 2. Price Distribution (for Books)
    prices = [float(r["price"]) for r in records if r.get("price") is not None]
    price_stats: Dict[str, Any] = {}
    if prices:
        price_stats = {
            "total_items_with_price": len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "mean_price": round(statistics.mean(prices), 2),
            "median_price": round(statistics.median(prices), 2),
        }

    # 3. Star Rating Distribution (1 to 5)
    ratings = [r["rating"] for r in records if r.get("rating") is not None]
    rating_counts = dict(Counter(ratings))
    # Format with star labels
    rating_distribution = {
        f"{star}_star": rating_counts.get(star, 0) for star in range(1, 6)
    }

    # 4. Author Breakdown (for Quotes)
    authors = [r["author"] for r in records if r.get("author")]
    top_authors = dict(Counter(authors).most_common(5))

    # 5. Tag Breakdown
    all_tags: List[str] = []
    for r in records:
        if r.get("tags"):
            # Split semicolon-delimited tags
            all_tags.extend(tag.strip() for tag in str(r["tags"]).split(";") if tag.strip())
    top_tags = dict(Counter(all_tags).most_common(10))

    return {
        "total_records_analyzed": total_records,
        "column_completeness": completeness,
        "price_analytics": price_stats,
        "rating_distribution": rating_distribution,
        "top_authors": top_authors,
        "top_tags": top_tags,
    }
