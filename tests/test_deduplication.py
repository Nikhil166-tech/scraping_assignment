"""Unit tests for processing/deduplication.py.

Directly implements tests from Stage 7 and Snippet 5.6.
"""

import unittest
from processing.deduplication import (
    Deduplicator,
    find_duplicates,
    make_fingerprint,
)


class TestDeduplication(unittest.TestCase):
    """Test suite for fingerprint hashing and deduplication."""

    def test_duplicates_ignore_case_and_spaces(self):
        """Snippet 5.6 exact test: verify duplicates are found ignoring case and spaces."""
        base = {"source": "Books to Scrape", "author": None}
        records = [
            {**base, "name_or_title": "Example Book Title"},
            {**base, "name_or_title": " Example Book Title "},
            {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
        ]
        unique, dupes = find_duplicates(records)
        self.assertEqual(len(unique), 1)
        self.assertEqual(len(dupes), 2)

    def test_synthetic_duplicates_generate_identical_fingerprint(self):
        """Variations in punctuation, whitespace, and case must yield identical hashes."""
        book1 = {
            "source": "Books to Scrape",
            "name_or_title": "A Light in the Attic",
        }
        book2 = {
            "source": "Books to Scrape",
            "name_or_title": "  a light in the attic!  ",
        }
        book3 = {
            "source": "Books to Scrape",
            "name_or_title": "A   LIGHT   IN   THE   ATTIC",
        }

        fp1 = make_fingerprint(book1)
        fp2 = make_fingerprint(book2)
        fp3 = make_fingerprint(book3)

        self.assertEqual(fp1, fp2)
        self.assertEqual(fp2, fp3)

    def test_distinct_records_generate_different_fingerprints(self):
        """Different titles or sources should produce different hashes."""
        book1 = {"source": "Books to Scrape", "name_or_title": "Book Alpha"}
        book2 = {"source": "Books to Scrape", "name_or_title": "Book Beta"}
        self.assertNotEqual(make_fingerprint(book1), make_fingerprint(book2))

    def test_deduplicator_tracks_seen_records(self):
        """Deduplicator class should return False for first appearance and True for repeats."""
        dedup = Deduplicator()
        record = {
            "source": "Books to Scrape",
            "name_or_title": "The Grand Design",
        }

        # First encounter -> Not a duplicate
        self.assertFalse(dedup.is_duplicate(record))

        # Second encounter -> Duplicate detected
        self.assertTrue(dedup.is_duplicate(record))

        # Third encounter with different formatting -> Duplicate detected
        record_variant = {
            "source": "Books to Scrape",
            "name_or_title": "  THE GRAND DESIGN!! ",
        }
        self.assertTrue(dedup.is_duplicate(record_variant))

    def test_quotes_incorporate_author_in_fingerprint(self):
        """Quotes with same text but different authors must produce distinct hashes."""
        quote1 = {
            "source": "Quotes to Scrape",
            "author": "Albert Einstein",
            "name_or_title": "Life is like riding a bicycle.",
        }
        quote2 = {
            "source": "Quotes to Scrape",
            "author": "Unknown",
            "name_or_title": "Life is like riding a bicycle.",
        }
        self.assertNotEqual(make_fingerprint(quote1), make_fingerprint(quote2))


if __name__ == "__main__":
    unittest.main()
