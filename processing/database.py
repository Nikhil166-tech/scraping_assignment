"""SQLite Database storage module (Bonus Feature).

Stores consolidated records in a relational database using Python's built-in sqlite3.
No external database server or installation is required.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


def save_to_sqlite(records: List[Dict[str, Any]], db_path: Path) -> int:
    """Store consolidated records in an SQLite database table.

    Args:
        records: List of normalized records to insert.
        db_path: Path to the SQLite .db file.

    Returns:
        Number of rows successfully inserted.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table schema
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS consolidated_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            name_or_title TEXT NOT NULL,
            category TEXT,
            price REAL,
            rating INTEGER,
            author TEXT,
            tags TEXT,
            source_url TEXT NOT NULL,
            scraped_at TEXT NOT NULL
        )
        """
    )

    # Create index for fast lookups by URL
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_source_url ON consolidated_records (source_url)"
    )

    # Clear previous run data to prevent duplicate inserts on re-runs
    cursor.execute("DELETE FROM consolidated_records")

    insert_query = """
        INSERT INTO consolidated_records (
            source, name_or_title, category, price, rating, author, tags, source_url, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    rows_to_insert = [
        (
            r.get("source"),
            r.get("name_or_title"),
            r.get("category"),
            r.get("price"),
            r.get("rating"),
            r.get("author"),
            r.get("tags"),
            r.get("source_url"),
            r.get("scraped_at"),
        )
        for r in records
    ]

    cursor.executemany(insert_query, rows_to_insert)
    conn.commit()
    inserted_count = cursor.rowcount
    conn.close()

    return inserted_count
