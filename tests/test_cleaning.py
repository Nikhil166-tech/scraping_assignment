"""Unit tests for processing/cleaning.py.

Directly tests Stage 5 functions and Snippet 5.4.
"""

import unittest
from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_record,
    clean_tags,
    clean_text,
    strip_quotes,
)


class TestCleaning(unittest.TestCase):
    """Test suite for data cleaning utilities."""

    def test_snippet_5_4_quick_checks(self):
        """Snippet 5.4: exact examples from the reference document."""
        self.assertEqual(clean_price("£51.77"), 51.77)
        self.assertEqual(clean_rating("star-rating Three"), 3)
        self.assertEqual(clean_text(" Hello \n World "), "Hello World")

    def test_clean_text_handles_whitespace_and_empty(self):
        """clean_text should collapse spaces, replace non-breaking spaces, and map empty to None."""
        self.assertEqual(clean_text("  Title   with \xa0 spaces  "), "Title with spaces")
        self.assertIsNone(clean_text(None))
        self.assertIsNone(clean_text(""))
        self.assertIsNone(clean_text("    "))

    def test_strip_quotes(self):
        """strip_quotes should remove surrounding curly and straight quotes."""
        self.assertEqual(strip_quotes('“A beautiful quote.”'), "A beautiful quote.")
        self.assertEqual(strip_quotes('"Standard quotes"'), "Standard quotes")
        self.assertIsNone(strip_quotes(""))
        self.assertIsNone(strip_quotes(None))

    def test_clean_price_handles_currencies_and_floats(self):
        """clean_price should strip currency symbols, commas, and handle floats."""
        self.assertEqual(clean_price("£1,234.56"), 1234.56)
        self.assertEqual(clean_price("$19.99"), 19.99)
        self.assertEqual(clean_price(51.77), 51.77)
        self.assertIsNone(clean_price(None))
        self.assertIsNone(clean_price("Free"))
        self.assertIsNone(clean_price(""))

    def test_clean_rating_handles_words_and_numbers(self):
        """clean_rating should convert rating words One..Five to 1..5."""
        self.assertEqual(clean_rating("star-rating One"), 1)
        self.assertEqual(clean_rating("Two"), 2)
        self.assertEqual(clean_rating("Three"), 3)
        self.assertEqual(clean_rating("Four"), 4)
        self.assertEqual(clean_rating("Five"), 5)
        self.assertEqual(clean_rating(4), 4)
        self.assertIsNone(clean_rating("Zero"))
        self.assertIsNone(clean_rating(None))

    def test_clean_tags_sorting_and_semicolon(self):
        """clean_tags: lowercase, sort, and join tags with ';' (Stage 5 specification)."""
        tags_list = ["Books", "  Fiction ", "books", "Young Adult"]
        self.assertEqual(clean_tags(tags_list), "books;fiction;young adult")

        # Delimited string input
        self.assertEqual(clean_tags("humor, inspirational, humor"), "humor;inspirational")
        self.assertIsNone(clean_tags([]))
        self.assertIsNone(clean_tags(None))

    def test_clean_record(self):
        """clean_record should normalize a complete dictionary into standard schema."""
        raw_book = {
            "source": " Books to Scrape ",
            "source_url": "https://books.toscrape.com/catalogue/test_1/index.html ",
            "name_or_title": " A Light in the Attic ",
            "category": " Poetry ",
            "price": "£51.77",
            "rating": "star-rating Three",
            "author": None,
            "tags": None,
            "scraped_at": " 2026-10-06T12:00:00Z ",
        }
        cleaned = clean_record(raw_book)
        self.assertEqual(cleaned["source"], "Books to Scrape")
        self.assertEqual(cleaned["name_or_title"], "A Light in the Attic")
        self.assertEqual(cleaned["category"], "Poetry")
        self.assertEqual(cleaned["price"], 51.77)
        self.assertEqual(cleaned["rating"], 3)
        self.assertIsNone(cleaned["author"])
        self.assertIsNone(cleaned["tags"])
        self.assertEqual(cleaned["scraped_at"], "2026-10-06T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
