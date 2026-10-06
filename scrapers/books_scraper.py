"""Books to Scrape scraper module.

Extracts book catalog records with dynamic pagination from https://books.toscrape.com/.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    """Scraper for https://books.toscrape.com/ catalog."""

    BASE_URL = "https://books.toscrape.com/"
    START_URL = "https://books.toscrape.com/catalogue/page-1.html"
    SOURCE_NAME = "Books to Scrape"

    def scrape_all(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrape all available book catalog pages dynamically.

        Args:
            max_pages: Optional cap on pages to crawl (useful for testing).

        Returns:
            List of raw extracted book dictionaries before cleaning.
        """
        current_url: Optional[str] = self.START_URL
        all_books: List[Dict] = []
        page_count = 0

        logger.info("Starting scrape of '%s' at %s", self.SOURCE_NAME, self.START_URL)

        while current_url:
            page_count += 1
            logger.info("Scraping Books page %d: %s", page_count, current_url)
            html = self.fetch_page(current_url)
            if not html:
                logger.warning("Failed to fetch page %s, stopping pagination.", current_url)
                break

            soup = BeautifulSoup(html, "html.parser")
            pods = soup.select("article.product_pod")

            if not pods:
                logger.warning("No product pods found on page %s.", current_url)

            for pod in pods:
                raw_book = self._extract_book_card(pod, current_url)
                if raw_book:
                    all_books.append(raw_book)

            # Check if page cap reached
            if max_pages and page_count >= max_pages:
                logger.info("Reached maximum page limit of %d. Stopping.", max_pages)
                break

            # Follow dynamic pagination: next page link inside li.next > a
            next_tag = soup.select_one("li.next a")
            if next_tag and next_tag.get("href"):
                current_url = urljoin(current_url, next_tag.get("href"))
            else:
                logger.info("No next page link found. Reached end of pagination.")
                current_url = None

        logger.info(
            "Completed '%s' scrape: extracted %d total raw records across %d pages.",
            self.SOURCE_NAME,
            len(all_books),
            page_count,
        )
        return all_books

    def _extract_book_card(self, pod: BeautifulSoup, page_url: str) -> Optional[Dict]:
        """Safely extract book attributes from a single product pod element."""
        try:
            # 1. Title & URL
            link_tag = pod.select_one("h3 a")
            if not link_tag:
                return None

            title = link_tag.get("title") or link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            source_url = urljoin(page_url, href)

            # 2. Price
            price_tag = pod.select_one("p.price_color")
            price_raw = price_tag.get_text(strip=True) if price_tag else None

            # 3. Rating class (e.g., class=['star-rating', 'Three'])
            rating_tag = pod.select_one("p.star-rating")
            rating_raw = None
            if rating_tag and rating_tag.get("class"):
                classes = rating_tag.get("class")
                # Look for class name that represents rating word (One, Two, Three, Four, Five)
                for cls in classes:
                    if cls.lower() in ["one", "two", "three", "four", "five"]:
                        rating_raw = cls
                        break

            # Current UTC timestamp in ISO-8601 format
            scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            return {
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "name_or_title": title,
                "category": None,    # Optional field per Section 5.2/8; empty when scraping catalog pod
                "price": price_raw,
                "rating": rating_raw,
                "author": None,      # Books do not have author in this source
                "tags": None,        # Catalog pod does not include category tags
                "scraped_at": scraped_at,
            }

        except Exception as e:
            logger.error("Error parsing book card: %s", e)
            return None
