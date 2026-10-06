"""Unit tests for bonus features: Data Quality Report and SQLite Database."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from processing.database import save_to_sqlite
from processing.quality_report import generate_data_quality_report


class TestBonusFeatures(unittest.TestCase):
    """Test suite for bonus features."""

    def setUp(self):
        self.sample_records = [
            {
                "source": "Books to Scrape",
                "name_or_title": "Book Alpha",
                "category": None,
                "price": 10.0,
                "rating": 5,
                "author": None,
                "tags": None,
                "source_url": "https://books.toscrape.com/1",
                "scraped_at": "2026-10-06T12:00:00Z",
            },
            {
                "source": "Books to Scrape",
                "name_or_title": "Book Beta",
                "category": None,
                "price": 20.0,
                "rating": 3,
                "author": None,
                "tags": None,
                "source_url": "https://books.toscrape.com/2",
                "scraped_at": "2026-10-06T12:00:00Z",
            },
            {
                "source": "Quotes to Scrape",
                "name_or_title": "A wise quote about life",
                "category": None,
                "price": None,
                "rating": None,
                "author": "Albert Einstein",
                "tags": "life;wisdom",
                "source_url": "https://quotes.toscrape.com/1",
                "scraped_at": "2026-10-06T12:00:00Z",
            },
        ]

    def test_data_quality_report_metrics(self):
        """Should calculate completeness, price analytics, ratings, and authors correctly."""
        report = generate_data_quality_report(self.sample_records)
        self.assertEqual(report["total_records_analyzed"], 3)

        # Completeness checks
        comp = report["column_completeness"]
        self.assertEqual(comp["source"]["completeness_pct"], 100.0)
        self.assertEqual(comp["name_or_title"]["completeness_pct"], 100.0)
        self.assertEqual(comp["category"]["completeness_pct"], 0.0)

        # Price analytics
        price_stats = report["price_analytics"]
        self.assertEqual(price_stats["min_price"], 10.0)
        self.assertEqual(price_stats["max_price"], 20.0)
        self.assertEqual(price_stats["mean_price"], 15.0)

        # Rating distribution
        rating_dist = report["rating_distribution"]
        self.assertEqual(rating_dist["5_star"], 1)
        self.assertEqual(rating_dist["3_star"], 1)
        self.assertEqual(rating_dist["1_star"], 0)

        # Top author
        self.assertIn("Albert Einstein", report["top_authors"])

    def test_sqlite_storage(self):
        """Should insert rows and create index in SQLite database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_data.db"
            inserted = save_to_sqlite(self.sample_records, db_path)
            self.assertEqual(inserted, 3)

            # Query back from SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM consolidated_records")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 3)

            cursor.execute("SELECT name_or_title, price FROM consolidated_records WHERE rating = 5")
            row = cursor.fetchone()
            self.assertEqual(row[0], "Book Alpha")
            self.assertEqual(row[1], 10.0)
            conn.close()


if __name__ == "__main__":
    unittest.main()
