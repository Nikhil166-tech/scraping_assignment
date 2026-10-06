"""Quotes to Scrape scraper module.

Extracts quotes, authors, and tags with dynamic pagination from https://quotes.toscrape.com/.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    """Scraper for https://quotes.toscrape.com/."""

    BASE_URL = "https://quotes.toscrape.com/"
    START_URL = "https://quotes.toscrape.com/"
    SOURCE_NAME = "Quotes to Scrape"

    def scrape_all(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrape all available quote pages dynamically.

        Args:
            max_pages: Optional cap on pages to crawl.

        Returns:
            List of raw extracted quote dictionaries.
        """
        current_url: Optional[str] = self.START_URL
        all_quotes: List[Dict] = []
        page_count = 0

        logger.info("Starting scrape of '%s' at %s", self.SOURCE_NAME, self.START_URL)

        while current_url:
            page_count += 1
            logger.info("Scraping Quotes page %d: %s", page_count, current_url)
            html = self.fetch_page(current_url)
            if not html:
                logger.warning("Failed to fetch page %s, stopping pagination.", current_url)
                break

            soup = BeautifulSoup(html, "html.parser")
            quote_divs = soup.select("div.quote")

            if not quote_divs:
                logger.warning("No quote cards found on page %s.", current_url)

            for quote_div in quote_divs:
                raw_quote = self._extract_quote_card(quote_div, current_url)
                if raw_quote:
                    all_quotes.append(raw_quote)

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
            len(all_quotes),
            page_count,
        )
        return all_quotes

    def _extract_quote_card(self, card: BeautifulSoup, page_url: str) -> Optional[Dict]:
        """Safely extract quote attributes from a single div.quote element."""
        try:
            # 1. Quote text
            text_tag = card.select_one("span.text")
            raw_text = text_tag.get_text(strip=True) if text_tag else ""

            # Per schema: name_or_title is first 50 chars of quote
            name_or_title = raw_text[:50] if raw_text else ""

            # 2. Author
            author_tag = card.select_one("small.author")
            author = author_tag.get_text(strip=True) if author_tag else None

            # 3. Tags
            tag_elements = card.select("div.tags a.tag")
            raw_tags = [t.get_text(strip=True) for t in tag_elements if t.get_text(strip=True)]

            # Current UTC timestamp in ISO-8601 format
            scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            return {
                "source": self.SOURCE_NAME,
                "source_url": page_url,
                "name_or_title": name_or_title,
                "category": None,     # Quotes do not have category
                "price": None,        # Quotes do not have price
                "rating": None,       # Quotes do not have rating
                "author": author,
                "tags": raw_tags,
                "scraped_at": scraped_at,
            }

        except Exception as e:
            logger.error("Error parsing quote card: %s", e)
            return None
