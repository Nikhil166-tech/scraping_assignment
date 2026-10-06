"""Main entry point for the Multi-Source Web Scraping & Data Pipeline.

Orchestrates scraping, data cleaning, validation, deduplication, and export.
Includes bonus features: SQLite database export, Data Quality Report,
checkpoint/resume support, and centralized configuration.
"""

import argparse
import csv
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import config
from processing.checkpoint import CheckpointManager
from processing.cleaning import clean_record
from processing.database import save_to_sqlite
from processing.deduplication import Deduplicator
from processing.quality_report import generate_data_quality_report
from processing.validation import validate_record
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

CSV_FIELDS = [
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


def setup_logging(log_dir: Path) -> logging.Logger:
    """Configure dual-destination logging to both stdout and logs/scraper.log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scraper.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler
    file_handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def process_scraped_data(
    raw_records: List[Dict[str, Any]],
    deduplicator: Deduplicator,
    source_name: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Clean, validate, and deduplicate a list of raw records from a single source."""
    logger = logging.getLogger(__name__)

    rejection_reasons: Counter = Counter()
    metrics = {
        "records_scraped": len(raw_records),
        "records_cleaned": 0,
        "records_rejected": 0,
        "records_duplicate": 0,
        "records_final": 0,
        "rejected_by_reason": {},
    }

    final_records: List[Dict[str, Any]] = []

    for raw in raw_records:
        # Step 1: Cleaning
        cleaned = clean_record(raw)
        metrics["records_cleaned"] += 1

        # Step 2: Validation
        problems = validate_record(cleaned)
        if problems:
            for prob in problems:
                rejection_reasons[prob] += 1
            logger.warning(
                "Record rejected from %s [%s]: %s",
                source_name,
                (cleaned.get("name_or_title") or "Unknown")[:30],
                ", ".join(problems),
            )
            metrics["records_rejected"] += 1
            continue

        # Step 3: Deduplication
        if deduplicator.is_duplicate(cleaned):
            logger.info(
                "Duplicate detected and dropped from %s: '%s'",
                source_name,
                (cleaned.get("name_or_title") or "")[:40],
            )
            metrics["records_duplicate"] += 1
            continue

        # Valid, unique record
        final_records.append(cleaned)
        metrics["records_final"] += 1

    metrics["rejected_by_reason"] = dict(rejection_reasons)

    expected_final = (
        metrics["records_scraped"]
        - metrics["records_rejected"]
        - metrics["records_duplicate"]
    )
    if metrics["records_final"] != expected_final:
        logger.error(
            "Count reconciliation mismatch in %s: %d != %d",
            source_name,
            metrics["records_final"],
            expected_final,
        )

    return final_records, metrics


def save_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Save consolidated records to CSV file using standard 9-column schema."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in records:
            row = {k: ("" if r.get(k) is None else r.get(k)) for k in CSV_FIELDS}
            writer.writerow(row)


def save_json(data: Dict[str, Any], output_path: Path) -> None:
    """Save data dictionary to a formatted JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def main():
    """Main pipeline execution routine."""
    parser = argparse.ArgumentParser(
        description="Multi-Source Web Scraping & Data Consolidation Pipeline"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=config.DEFAULT_DELAY,
        help=f"Polite delay in seconds between HTTP requests (default: {config.DEFAULT_DELAY}s)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional maximum number of pages to scrape per source (for testing)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume scraping using checkpoint file if available",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip saving output records to SQLite database",
    )
    args = parser.parse_args()

    # 1. Setup logging
    logger = setup_logging(config.LOGS_DIR)
    logger.info("==================================================")
    logger.info("Starting Multi-Source Web Scraping Pipeline")
    logger.info("Configuration: delay=%.2fs, max_pages=%s, resume=%s", args.delay, args.max_pages, args.resume)
    logger.info("==================================================")

    start_dt = datetime.now(timezone.utc)
    execution_start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    checkpoint_mgr = CheckpointManager(config.CHECKPOINT_PATH)
    deduplicator = Deduplicator()
    all_final_records: List[Dict[str, Any]] = []
    source_metrics: Dict[str, Dict[str, Any]] = {}
    aggregated_rejected_reasons: Counter = Counter()

    # 2. Scrape Books to Scrape
    try:
        logger.info("Initializing Books to Scrape crawler...")
        books_crawler = BooksScraper(delay=args.delay)
        raw_books = books_crawler.scrape_all(max_pages=args.max_pages)
        books_crawler.close()

        valid_books, b_metrics = process_scraped_data(
            raw_books, deduplicator, "Books to Scrape"
        )
        all_final_records.extend(valid_books)
        source_metrics["Books to Scrape"] = b_metrics
        for reason, count in b_metrics.get("rejected_by_reason", {}).items():
            aggregated_rejected_reasons[reason] += count

        logger.info(
            "Books processing complete: %d scraped, %d rejected, %d duplicate, %d final.",
            b_metrics["records_scraped"],
            b_metrics["records_rejected"],
            b_metrics["records_duplicate"],
            b_metrics["records_final"],
        )
    except Exception as e:
        logger.exception("Unexpected failure during Books scraping: %s", e)
        source_metrics["Books to Scrape"] = {
            "records_scraped": 0,
            "records_cleaned": 0,
            "records_rejected": 0,
            "records_duplicate": 0,
            "records_final": 0,
            "error": str(e),
        }

    # 3. Scrape Quotes to Scrape
    try:
        logger.info("Initializing Quotes to Scrape crawler...")
        quotes_crawler = QuotesScraper(delay=args.delay)
        raw_quotes = quotes_crawler.scrape_all(max_pages=args.max_pages)
        quotes_crawler.close()

        valid_quotes, q_metrics = process_scraped_data(
            raw_quotes, deduplicator, "Quotes to Scrape"
        )
        all_final_records.extend(valid_quotes)
        source_metrics["Quotes to Scrape"] = q_metrics
        for reason, count in q_metrics.get("rejected_by_reason", {}).items():
            aggregated_rejected_reasons[reason] += count

        logger.info(
            "Quotes processing complete: %d scraped, %d rejected, %d duplicate, %d final.",
            q_metrics["records_scraped"],
            q_metrics["records_rejected"],
            q_metrics["records_duplicate"],
            q_metrics["records_final"],
        )
    except Exception as e:
        logger.exception("Unexpected failure during Quotes scraping: %s", e)
        source_metrics["Quotes to Scrape"] = {
            "records_scraped": 0,
            "records_cleaned": 0,
            "records_rejected": 0,
            "records_duplicate": 0,
            "records_final": 0,
            "error": str(e),
        }

    # 4. Final Aggregations & Reconciliation
    end_dt = datetime.now(timezone.utc)
    execution_end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    duration_seconds = round((end_dt - start_dt).total_seconds(), 2)

    total_scraped = sum(m.get("records_scraped", 0) for m in source_metrics.values())
    total_cleaned = sum(m.get("records_cleaned", 0) for m in source_metrics.values())
    total_rejected = sum(m.get("records_rejected", 0) for m in source_metrics.values())
    total_duplicate = sum(m.get("records_duplicate", 0) for m in source_metrics.values())
    total_final = len(all_final_records)

    reconciliation_passed = (
        total_scraped - total_rejected - total_duplicate == total_final
    )

    summary_report = {
        "collected_per_source": {
            k: v.get("records_scraped", 0) for k, v in source_metrics.items()
        },
        "cleaned_per_source": {
            k: v.get("records_cleaned", 0) for k, v in source_metrics.items()
        },
        "rejected_by_reason": dict(aggregated_rejected_reasons),
        "duplicates_detected": total_duplicate,
        "final_record_count": total_final,
        "duration_seconds": duration_seconds,
        "execution_start": execution_start_iso,
        "execution_end": execution_end_iso,
        "reconciliation_passed": reconciliation_passed,
        "detailed_sources": source_metrics,
    }

    # 5. Export Deliverables
    logger.info("Exporting consolidated dataset to %s...", config.CSV_OUTPUT_PATH)
    save_csv(all_final_records, config.CSV_OUTPUT_PATH)

    logger.info("Exporting summary metrics report to %s...", config.SUMMARY_REPORT_PATH)
    save_json(summary_report, config.SUMMARY_REPORT_PATH)

    # 6. Bonus Feature: Data Quality Report
    logger.info("Generating Data Quality Report (Bonus Feature) to %s...", config.DATA_QUALITY_REPORT_PATH)
    quality_report = generate_data_quality_report(all_final_records)
    save_json(quality_report, config.DATA_QUALITY_REPORT_PATH)

    # 7. Bonus Feature: SQLite Database Storage
    if not args.no_db:
        logger.info("Storing records in SQLite database (Bonus Feature) at %s...", config.SQLITE_DB_PATH)
        inserted_rows = save_to_sqlite(all_final_records, config.SQLITE_DB_PATH)
        logger.info("Successfully inserted %d rows into SQLite table 'consolidated_records'.", inserted_rows)

    # Clean up checkpoint on clean completion
    checkpoint_mgr.clear()

    logger.info("==================================================")
    logger.info("Pipeline Execution Summary:")
    logger.info("  Duration:             %.2f seconds", duration_seconds)
    logger.info("  Total Scraped:        %d", total_scraped)
    logger.info("  Total Cleaned:        %d", total_cleaned)
    logger.info("  Total Rejected:       %d", total_rejected)
    logger.info("  Total Duplicate:      %d", total_duplicate)
    logger.info("  Total Final Saved:    %d", total_final)
    logger.info("  Reconciliation Check: %s", "PASSED" if reconciliation_passed else "FAILED")
    logger.info("  Output CSV:           %s", config.CSV_OUTPUT_PATH)
    logger.info("  Summary JSON:         %s", config.SUMMARY_REPORT_PATH)
    logger.info("  Quality Report JSON:  %s", config.DATA_QUALITY_REPORT_PATH)
    if not args.no_db:
        logger.info("  SQLite Database:      %s", config.SQLITE_DB_PATH)
    logger.info("  Log File:             %s", config.LOG_FILE_PATH)
    logger.info("==================================================")


if __name__ == "__main__":
    main()
