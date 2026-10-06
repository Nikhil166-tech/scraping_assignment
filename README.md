# Multi-Source Web Scraping & Data Consolidation Pipeline

> **Junior Developer Technical Assessment Submission**  
> **Candidate Project:** Realisieren Technologies Web Scraping Interview Assignment  
> **Python Version:** Python 3.10+ (Developed and tested on Python 3.13)

---

## 📌 1. Assignment & Project Overview

This project implements a robust, modular Python-based web scraping and data processing pipeline. It collects information from two distinct public web sources with different HTML structures, cleans and standardizes the data into a unified schema, performs strict data validation, detects and suppresses duplicates using content hashing, and outputs a consolidated dataset along with an execution summary report and detailed logs.

### Target Sources:
- **Source 1 – Books to Scrape (`https://books.toscrape.com/`)**: 1,000 book records across 50 paginated catalog pages.
- **Source 2 – Quotes to Scrape (`https://quotes.toscrape.com/`)**: 100 quotes across 10 paginated pages.

### High-Level Workflow:
```
Books to Scrape  ─┐
                  ├─> Scraping ─> Cleaning ─> Validation ─> Deduplication ─> Consolidation ─> Final Dataset
Quotes to Scrape ─┘
```

### Stage 1: Website Exploration & DOM Observations
Per Stage 1 of the assignment guide, inspecting both websites reveals the following selectors:

| Item | Books to Scrape | Quotes to Scrape |
| :--- | :--- | :--- |
| **One record** | `article.product_pod` | `div.quote` |
| **Main text** | `h3 > a` (full title in `title` attribute) | `span.text` (wrapped in curly quotes) |
| **Price** | `p.price_color` (e.g. `£51.77`) | None |
| **Rating** | class on `p.star-rating` (e.g. `Three`) | None |
| **Author** | None | `small.author` |
| **Tags** | None | `a.tag` (zero or more) |
| **Link** | `h3 > a[href]` (relative path) | `a[href^="/author/"]` (author page) |
| **Next page** | `li.next > a` | `li.next > a` |

---

## 🐍 2. Python Version & Dependencies

- **Python Version:** Python 3.10+ (Tested on Python 3.13.5).
- **Core Dependencies (`requirements.txt`):**
  - `requests`: HTTP client library for network requests.
  - `beautifulsoup4`: HTML DOM parsing and CSS selector extraction.
  - `lxml`: High-performance HTML parsing engine.
  - `pytest`: Automated test runner for unit tests.

---

## 💻 3. Installation & Setup Instructions

### Step 1: Clone or open the project directory
```bash
cd scraping_assignment
```

### Step 2: Set up a virtual environment (Recommended)
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install pinned dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 4. How to Run the Scraper

Run the main pipeline orchestrator from your terminal:
```bash
python main.py
```
*(On Windows using the Python Launcher, you can also run `py main.py`)*

### Configurable CLI Flags
- `--delay <seconds>`: Set custom polite throttling delay between HTTP requests (default: `0.5`s).
  ```bash
  python main.py --delay 0.5
  ```
- `--max-pages <number>`: Limit the number of pages scraped per source (useful for fast smoke testing).
  ```bash
  python main.py --max-pages 2
  ```

---

## 🔄 5. How Pagination Works

Rather than hardcoding page counts or URLs (`page-1.html ... page-50.html`), both crawlers implement **dynamic pagination**:
1. The scraper starts at the source root URL.
2. After extracting items on the current page, it queries the DOM for the next page link (`soup.select_one("li.next a")`).
3. If found, the relative URL is converted to an absolute URL using `urllib.parse.urljoin(current_url, next_href)`.
4. The loop continues (`while current_url:`) until `li.next a` is no longer found in the DOM, at which point it terminates gracefully.

---

## 📊 6. Unified Data Model

The pipeline consolidates disparate structures into the standardized 9-column schema required by the assignment specification:

| Field Name | Type | Books to Scrape | Quotes to Scrape | Notes & Formatting |
| :--- | :--- | :--- | :--- | :--- |
| `source` | `string` | `"Books to Scrape"` | `"Quotes to Scrape"` | Required. Exactly one of the two exact source names. |
| `name_or_title` | `string` | Book title | First 50 chars of quote | Required. Whitespace-trimmed string. |
| `category` | `string` | `None` / empty | `None` / empty | Optional field. Left empty when not available. |
| `price` | `float` | Book price (e.g., `51.77`) | `None` / empty | Float $\ge 0.0$ for Books. Quotes leave empty. |
| `rating` | `integer` | Star rating (`1` to `5`) | `None` / empty | Integer $1 \le \text{rating} \le 5$ for Books. |
| `author` | `string` | `None` / empty | Author name | Required for Quotes. Books leave empty. |
| `tags` | `string` | `None` / empty | Pipe-separated tags | Lowercase, pipe-separated (`tag1 \| tag2`). |
| `source_url` | `string` | Book detail URL | Page URL | Full absolute URL starting with `http://` or `https://`. |
| `scraped_at` | `string` | UTC ISO-8601 | UTC ISO-8601 | Standard timestamp: `YYYY-MM-DDTHH:MM:SSZ`. |

---

## 🧹 7. Cleaning Approach (`processing/cleaning.py`)

Cleaning functions are written as **pure, side-effect-free functions**:
- **Text Normalization (`clean_text`)**: Converts unicode/curly quotes (`“`, `”`, `‘`, `’`) to standard ASCII quotes, collapses multiple spaces/newlines/tabs into a single space, and strips whitespace.
- **Price Conversion (`clean_price`)**: Strips currency symbols (`£`, `$`, `€`) using regular expressions (`\d+(?:\.\d+)?`) and converts the price into a standard two-decimal `float`.
- **Rating Standardization (`clean_rating`)**: Converts word-based ratings (`"One"` $\to$ `1`, `"Five"` $\to$ `5`) and digit strings to integers between `1` and `5`.
- **Tag Normalization (`clean_tags`)**: Converts tag collections into lowercase, trims extra spaces, removes duplicate tags while preserving order, and joins them using `" | "`.
- **Missing Value Handling**: Inapplicable fields are consistently mapped to `None` in Python and output as empty strings in CSV.

---

## 🛡️ 8. Validation Approach (`processing/validation.py`)

Validation runs on every cleaned record prior to deduplication:
- `validate_record(record)` checks all schema constraints and returns a list of error codes (e.g. `["missing_name_or_title", "invalid_price"]`).
- If errors exist, the record is rejected, a warning is logged, and the `records_rejected` metric is incremented.
- Enforced rules:
  - Source must be either `"Books to Scrape"` or `"Quotes to Scrape"`.
  - `name_or_title` must be non-empty.
  - `source_url` must be a valid HTTP/HTTPS URL.
  - Books must have numeric price $\ge 0.0$ and ratings between $1$ and $5$.
  - Quotes must not contain prices or ratings, and must have an author.
  - `scraped_at` must conform to ISO-8601 UTC.

---

## 🔍 9. Deduplication Approach (`processing/deduplication.py`)

To detect duplicate or equivalent items across pages and runs:
1. **Fingerprint Normalization**:
   - The key text fields are lowercased.
   - All punctuation and symbols are stripped (`re.sub(r'[^\w\s]', '', text)`).
   - Internal whitespace is collapsed into single spaces.
2. **Deterministic Composite Key**:
   - Books: `f"Books to Scrape:{normalized(title)}"`
   - Quotes: `f"Quotes to Scrape:{normalized(author)}:{normalized(first_50_chars_quote)}"`
3. **Cryptographic SHA-256 Hashing**:
   - A SHA-256 hash is computed over the composite key.
   - The stateful `Deduplicator` tracks seen hashes in an in-memory set ($O(1)$ lookup time).
   - If a hash has already been seen, the record is flagged/dropped as duplicate and counted under `records_duplicate`.

---

## ⚙️ 10. Error Handling & Network Resilience

- **Retry Adapter with Exponential Backoff**: The `BaseScraper` mounts an `HTTPAdapter` with `urllib3.util.Retry(total=3, backoff_factor=1.0)` that automatically retries transient errors (`429, 500, 502, 503, 504`).
- **Defensive Timeouts**: All requests have an explicit 10-second timeout to prevent hanging.
- **Polite Rate Limiting**: A configurable pause (`time.sleep(self.delay)`) is observed before every request.
- **Missing Element Safety**: HTML elements are retrieved defensively using `.select_one()`, returning `None` if absent without raising `AttributeError`.
- **Source Fault Isolation**: Books and Quotes scrapers run inside isolated `try/except` blocks in `main.py`. A network or parsing crash in one source will never abort the other.
- **Dual-Destination Logging**: Logs are simultaneously streamed to the console (stdout) and appended to `logs/scraper.log`.

---

## 📁 11. Output Deliverables Description

1. **`output/final_dataset.csv`**:
   - UTF-8 encoded CSV containing all consolidated records under the 9 standardized columns.
2. **`output/summary_report.json`**:
   - Execution metrics breakdown per source:
     - `records_scraped`
     - `records_cleaned`
     - `records_rejected`
     - `records_duplicate`
     - `records_final`
   - Total pipeline aggregates, execution start/end timestamps, and duration.
   - **Count Reconciliation**: Enforces $\text{scraped} - \text{rejected} - \text{duplicate} = \text{final}$.
3. **`logs/scraper.log`**:
   - Complete record of all `INFO`, `WARNING`, and `ERROR` events during scraping.

---

## 🧪 12. Automated Unit Tests

A comprehensive suite of 19 offline unit tests is located in `tests/`:
- `tests/test_cleaning.py`: Tests text stripping, smart quote handling, price parsing, rating word conversions, and tag formatting.
- `tests/test_validation.py`: Tests valid records, bad URLs, invalid prices, missing authors, and incorrect sources.
- `tests/test_deduplication.py`: Tests synthetic duplicate suppression with variations in capitalization, whitespace, and punctuation.

Run tests:
```bash
pytest tests/ -v
```

---

---

## 🎁 14. Bonus Features Implemented (Section 14)

To demonstrate practical production-readiness from a junior developer perspective, the following optional bonus features were implemented:

1. **Embedded Relational Database Integration (`SQLite`)**:
   - Stores all 1,099 consolidated records in `output/scraped_data.db`.
   - Creates the `consolidated_records` table with primary keys and an index on `source_url`.
   - Easily queryable with standard SQL tools (or disable via `--no-db`).

2. **Automated Data-Quality Report (`output/data_quality_report.json`)**:
   - Computes completeness percentages and missing counts for each of the 9 columns.
   - Calculates price statistics for Books (min, max, mean, median).
   - Tallies the 5-tier star rating distribution.
   - Summarizes top authors and most frequent tags.

3. **Checkpoint & Resume Support (`--resume`)**:
   - Maintains page-level scraping progress in `output/checkpoint.json`.
   - Enables interrupted runs to resume seamlessly without re-downloading previously processed pages.

4. **Docker Containerization (`Dockerfile` & `.dockerignore`)**:
   - Complete container recipe using `python:3.11-slim` for one-command reproducible runs:
     ```bash
     docker build -t scraping-app .
     docker run -v ${PWD}/output:/app/output scraping-app
     ```

5. **Centralized Configuration (`config.py`)**:
   - Consolidates delays, timeouts, retries, and output paths into a clean configuration module.

6. **Comprehensive Unit Test Suite**:
   - 21 automated unit tests in `tests/` covering cleaning, validation, deduplication, and bonus features (`pytest tests/`).

---

## 📝 15. Assumptions

1. **Catalog vs. Detail Page Trade-off**: Books are extracted directly from the 50 catalog pages. This captures all 1,000 books with title, URL, price, and star rating in ~35 seconds, without making 1,000 extra individual detail-page HTTP requests.
2. **Quotes Identifier**: Per Section 5.2 and schema specifications, the first 50 characters of a quote serve as the `name_or_title` identifier.
3. **Price Currency**: Prices on Books to Scrape are in British Pounds (`£`) and are converted to clean floating-point numbers without currency symbols.

---

## ⚠️ 16. Known Limitations & Production Roadmap

- **Category extraction for Books**: Currently `category` is empty for Books because it is not displayed on the catalog cards. A detail-page crawler mode could be enabled if category extraction is strictly demanded.
- **Scalability**: For very large catalogs (>100,000 pages), an asynchronous framework (`aiohttp` / `asyncio`) or distributed queue (Celery + Redis) would provide higher throughput.

---

## 🤖 17. AI Usage Summary

Full details of AI assistance are documented in [`AI_USAGE.md`](AI_USAGE.md).  
In brief: An AI coding assistant was used to scaffold initial boilerplate, verify regular expression edge cases, and assist with unit test generation. All code was reviewed, debugged, and verified through manual inspections and automated test suites.
