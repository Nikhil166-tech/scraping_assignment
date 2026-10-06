"""Deduplication module using content fingerprinting and SHA-256 hashing.

Directly implements Stage 7 and Snippet 5.6.
"""

import hashlib
import re
from typing import Any, Dict, List, Set, Tuple


def make_fingerprint(rec: Dict[str, Any]) -> str:
    """Build a fingerprint hash for a record (Snippet 5.6).

    Rules:
    - Books:  source + title
    - Quotes: source + author + first 50 chars of quote
    - Lowercase, drop punctuation, collapse spaces, SHA-256 hash.
    """
    source = rec.get("source", "")
    title = str(rec.get("name_or_title") or "")

    if source == "Books to Scrape":
        key = f"{source} {title}"
    else:  # quotes
        author = str(rec.get("author") or "")
        key = f"{source} {author} {title[:50]}"

    key = re.sub(r"[^\w\s]", "", key.lower())  # lowercase, drop punctuation
    key = " ".join(key.split())                 # collapse spaces
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Separate records into unique and duplicate lists (Snippet 5.6)."""
    seen: Set[str] = set()
    unique: List[Dict[str, Any]] = []
    dupes: List[Dict[str, Any]] = []

    for rec in records:
        fp = make_fingerprint(rec)
        if fp in seen:
            dupes.append(rec)
        else:
            unique.append(rec)
            seen.add(fp)

    return unique, dupes


class Deduplicator:
    """Stateful duplicate detector maintaining seen cryptographic hashes."""

    def __init__(self):
        self.seen_hashes: Set[str] = set()

    def is_duplicate(self, record: Dict[str, Any]) -> bool:
        """Check if record has already been seen; marks it seen if not."""
        fp = make_fingerprint(record)
        if fp in self.seen_hashes:
            return True
        self.seen_hashes.add(fp)
        return False

    def reset(self) -> None:
        """Clear set of seen hashes."""
        self.seen_hashes.clear()
