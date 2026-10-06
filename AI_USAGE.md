# AI Usage & Transparency Log

> **Document Requirement:** Section 11 of the Technical Assessment ("AI_USAGE.md – Required").  
> **Purpose:** Transparent disclosure of AI tools utilized, specific workflows assisted, prompts used, human reviews, corrections, and validation methods.

---

## 1. AI Tools Used

- **Primary Tool:** Antigravity AI Coding Assistant (powered by Google Gemini)
- **Role:** Architectural advisor, boilerplate scaffolder, test case generator, and pair-programming assistant.

---

## 2. What the Tool Was Used For

- **Understanding & Analysis:** Parsing assignment instructions and breaking down the 11 pipeline stages.
- **Scaffolding Modular Architecture:** Generating initial folder structures and boilerplate for `scrapers/`, `processing/`, and `tests/`.
- **Regex & String Patterns:** Crafting regular expressions for currency stripping and punctuation normalization.
- **Unit Test Case Generation:** Writing mock test inputs for edge-case coverage in `test_cleaning.py`, `test_validation.py`, and `test_deduplication.py`.
- **Documentation Structuring:** Drafting technical documentation sections in `README.md`.

---

## 3. Representative Prompts Used

Below are authentic sample prompts used during development:

1. **Prompt 1 (Analysis & Architecture):**
   > *"Analyze this assignment document. What are the target websites, required schema fields, deduplication logic, and required deliverables?"*

2. **Prompt 2 (Modular Data Cleaning):**
   > *"Write pure Python functions in `processing/cleaning.py` to clean whitespace, convert prices (e.g. '£51.77' -> 51.77 float), convert ratings ('Three' -> 3 int), and format tags into lowercase pipe-separated strings."*

3. **Prompt 3 (Deduplication & Content Hashing):**
   > *"How do we implement duplicate detection that ignores differences in capitalization, extra whitespace, and punctuation using SHA-256 content hashing?"*

4. **Prompt 4 (Resilient Base Scraper):**
   > *"Create a BaseScraper class using requests.Session, urllib3.util.Retry with exponential backoff on 429, 500, 502, 503, 504, 10s timeouts, and polite delay throttling."*

---

## 4. Which Parts of the Code Were AI-Assisted

- **`scrapers/base_scraper.py`**: Retry adapter configuration and session mounting.
- **`processing/cleaning.py`**: Dictionary mapping for rating words (`RATING_MAP`) and regex float extraction.
- **`processing/deduplication.py`**: Punctuation stripping regex (`re.sub(r'[^\w\s]', '', text)`) and SHA-256 hashing composite key logic.
- **`tests/*.py`**: Test case definitions and assertions for mock raw records.

---

## 5. Important Changes Made After Reviewing AI Output

1. **Pagination Off-by-One Loop Logic**:
   - *AI Output:* Initially, the AI proposed checking `page_count > max_pages` at the start of the while loop after incrementing, which resulted in fetching one additional page during smoke testing.
   - *Correction:* Refactored to check `if max_pages and page_count >= max_pages: break` immediately after processing the current page's items.
2. **Catalog vs. Detail Page Strategy**:
   - *AI Output:* The AI initially considered making 1,000 individual detail-page HTTP requests to retrieve book categories.
   - *Correction:* Recognized that making 1,000 extra requests with a 0.5s polite throttle would take ~10 minutes and create unnecessary server load. Decided to extract title, price, star rating, and product URL directly from the 50 catalog pages (~35s), leaving `category` as `None` in accordance with Section 5.2 ("Not every field will exist for every source. Use appropriate null/empty values when a field does not apply. Do not invent data").
3. **Double-Quotation Mark Artifacts**:
   - *AI Output:* Replacing curly quotes (`“`, `”`) with standard ASCII quotes (`"`) caused the CSV writer to escape them as doubled quotes (`""`).
   - *Correction:* Kept the core quote text clean and ensured unit tests explicitly verified consistent normalization without breaking string comparisons.

---

## 6. Incorrect or Incomplete AI-Generated Suggestions Discovered

- **Selector Fragility:** An initial AI snippet suggested using `.product_pod .price_color` without verifying if `.product_pod` existed. This was modified to use safe `.select_one()` calls with explicit fallback checks (`price_tag.get_text(strip=True) if price_tag else None`) to prevent `AttributeError: 'NoneType' object has no attribute 'get_text'`.
- **Character Encoding Default:** The AI did not initially set `response.encoding = "utf-8"`, which on some Windows systems defaulted to Windows-1252, corrupting the British Pound currency symbol `£` into `Â£`. Explicitly adding `response.encoding = "utf-8"` solved this.

---

## 7. How the Final Solution Was Tested and Verified

1. **Unit Testing (`pytest tests/`)**:
   - 19 automated tests executed offline, covering all cleaning edge cases, schema validation rejections, and hash stability under formatting variations.
2. **Smoke Testing (`--max-pages 2`)**:
   - Tested pipeline execution on 2 pages per source to verify console logging, file creation, and rate-limiting behavior.
3. **Full Live Verification**:
   - Crawled all 50 catalog pages of *Books to Scrape* (1,000 items) and all 10 pages of *Quotes to Scrape* (100 items).
   - Confirmed duplicate detection dropped 1 natural duplicate on *Books to Scrape* (`'The Star-Touched Queen'`).
   - Mathematically verified the reconciliation formula:
     $$\text{Total Scraped (1100)} - \text{Rejected (0)} - \text{Duplicate (1)} = \text{Final Records (1099)}$$
   - Checked CSV formatting in `output/final_dataset.csv` and metrics in `output/summary_report.json`.
