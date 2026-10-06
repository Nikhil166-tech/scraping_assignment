"""Unit tests for processing/validation.py.

Directly tests Stage 6 and Snippet 5.5 validation rules.
"""

import unittest
from processing.validation import validate_record


class TestValidation(unittest.TestCase):
    """Test suite for record schema validation."""

    def setUp(self):
        self.valid_book = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            "name_or_title": "A Light in the Attic",
            "category": None,
            "price": 51.77,
            "rating": 3,
            "author": None,
            "tags": None,
            "scraped_at": "2026-10-06T12:00:00Z",
        }

        self.valid_quote = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/",
            "name_or_title": "The world as we have created it is a process of ou",
            "category": None,
            "price": None,
            "rating": None,
            "author": "Albert Einstein",
            "tags": "change;deep-thoughts;thinking;world",
            "scraped_at": "2026-10-06T12:00:00Z",
        }

    def test_valid_book_passes_validation(self):
        """Valid book record should return empty list of problems."""
        self.assertEqual(validate_record(self.valid_book), [])

    def test_valid_quote_passes_validation(self):
        """Valid quote record should return empty list of problems."""
        self.assertEqual(validate_record(self.valid_quote), [])

    def test_unknown_source_rejected(self):
        """Records with unknown source names must report 'unknown_source'."""
        rec = dict(self.valid_book)
        rec["source"] = "Random Site"
        self.assertIn("unknown_source", validate_record(rec))

    def test_missing_name_rejected(self):
        """Records with missing or empty name must report 'missing_name'."""
        rec = dict(self.valid_book)
        rec["name_or_title"] = None
        self.assertIn("missing_name", validate_record(rec))

        rec["name_or_title"] = ""
        self.assertIn("missing_name", validate_record(rec))

    def test_invalid_url_rejected(self):
        """URLs not starting with http:// or https:// must report 'invalid_url'."""
        rec = dict(self.valid_book)
        rec["source_url"] = "ftp://invalid-url.com"
        self.assertIn("invalid_url", validate_record(rec))

        rec["source_url"] = None
        self.assertIn("invalid_url", validate_record(rec))

    def test_invalid_price_rejected(self):
        """Prices that are negative or non-numeric must report 'invalid_price'."""
        rec = dict(self.valid_book)
        rec["price"] = -5.00
        self.assertIn("invalid_price", validate_record(rec))

        rec["price"] = "not-a-number"
        self.assertIn("invalid_price", validate_record(rec))

    def test_invalid_rating_rejected(self):
        """Ratings outside 1..5 must report 'invalid_rating'."""
        rec = dict(self.valid_book)
        rec["rating"] = 6
        self.assertIn("invalid_rating", validate_record(rec))

        rec["rating"] = 0
        self.assertIn("invalid_rating", validate_record(rec))


if __name__ == "__main__":
    unittest.main()
