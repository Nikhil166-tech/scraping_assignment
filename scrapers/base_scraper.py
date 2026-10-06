"""Base Scraper Module.

Provides a robust HTTP client session with retry logic, polite rate limiting,
custom user-agent headers, and defensive error handling.
"""

import logging
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper providing common HTTP networking capabilities.

    Attributes:
        delay (float): Seconds to pause between consecutive requests.
        timeout (int): Request timeout in seconds.
        session (requests.Session): Persistent HTTP session with retries.
    """

    def __init__(
        self,
        delay: float = 0.5,
        timeout: int = 10,
        user_agent: Optional[str] = None,
    ):
        """Initialize base scraper with polite rate limiting and retry adapter.

        Args:
            delay: Pause time in seconds between network requests.
            timeout: HTTP request timeout in seconds.
            user_agent: Optional custom User-Agent string.
        """
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()

        # Set standard descriptive User-Agent header
        ua = user_agent or (
            "RealisierenScraperBot/1.0 "
            "(Educational/TakeHomeAssessment; contact: junior-dev@example.com)"
        )
        self.session.headers.update({"User-Agent": ua})

        # Configure exponential backoff retry strategy for transient errors
        retries = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch the HTML content of a URL with rate-limiting and error handling.

        Args:
            url: The absolute target URL to fetch.

        Returns:
            The raw HTML string if successful, or None if the request failed.
        """
        # Respect polite delay before request
        if self.delay > 0:
            time.sleep(self.delay)

        try:
            logger.info("Fetching URL: %s", url)
            response = self.session.get(url, timeout=self.timeout)

            # Check HTTP status
            if response.status_code != 200:
                logger.warning(
                    "Unexpected HTTP status %d for URL: %s",
                    response.status_code,
                    url,
                )
                return None

            # Explicitly force UTF-8 to prevent character encoding issues
            response.encoding = "utf-8"
            return response.text

        except requests.exceptions.Timeout:
            logger.error("Request timed out for URL: %s", url)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("HTTP error fetching %s: %s", url, e)
            return None

    def close(self) -> None:
        """Close the underlying requests session."""
        self.session.close()
