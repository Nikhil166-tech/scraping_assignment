"""Data processing package containing cleaning, validation, and deduplication modules."""
from processing.cleaning import (
    clean_record,
    clean_text,
    clean_price,
    clean_rating,
    clean_tags,
    strip_quotes,
    normalize_url,
)
from processing.validation import validate_record
from processing.deduplication import Deduplicator, make_fingerprint, find_duplicates

# Alias for backward compatibility
compute_record_hash = make_fingerprint

__all__ = [
    "clean_record",
    "clean_text",
    "clean_price",
    "clean_rating",
    "clean_tags",
    "strip_quotes",
    "normalize_url",
    "validate_record",
    "Deduplicator",
    "make_fingerprint",
    "compute_record_hash",
    "find_duplicates",
]
