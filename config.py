"""Project configuration file.

Contains default settings for networking, file paths, and database storage.
Can be overridden via command-line arguments.
"""

from pathlib import Path

# Networking & Rate Limiting
DEFAULT_DELAY = 0.5       # Polite pause in seconds between HTTP requests
REQUEST_TIMEOUT = 10      # Seconds before a network request times out
MAX_RETRIES = 3           # Number of retry attempts on network errors
RETRY_BACKOFF = 1.0       # Exponential backoff factor

# Directories
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# Output File Paths
CSV_OUTPUT_PATH = OUTPUT_DIR / "final_dataset.csv"
SUMMARY_REPORT_PATH = OUTPUT_DIR / "summary_report.json"
DATA_QUALITY_REPORT_PATH = OUTPUT_DIR / "data_quality_report.json"
SQLITE_DB_PATH = OUTPUT_DIR / "scraped_data.db"
CHECKPOINT_PATH = OUTPUT_DIR / "checkpoint.json"
LOG_FILE_PATH = LOGS_DIR / "scraper.log"

# Target Source URLs
BOOKS_START_URL = "https://books.toscrape.com/catalogue/page-1.html"
QUOTES_START_URL = "https://quotes.toscrape.com/"
