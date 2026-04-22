"""
Scraper for Avito.ma — immobilier listings.
Collects ONLY non-personal, publicly visible real-estate data.
No names, phone numbers, or emails are ever scraped.
Polite crawling: random delay 2–4s between requests.
"""

import re
import time
import json
import os
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from src.utils.logger import get_logger

logger = get_logger("scraper")

# 🔴 FIX 1: BASE_URL corrected to Avito.ma (was books.toscrape.com)
BASE_URL   = "https://www.avito.ma/fr/maroc/immobilier"
MAX_PAGES  = 1
DELAY_MIN  = 3
DELAY_MAX  = 7
BRONZE_DIR = os.path.join(os.path.dirname(__file__), "../../data/bronze")


# ── Driver ────────────────────────────────────────────────────────────────────

def _build_driver() -> webdriver.Chrome:
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()

    
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    # Headless config (stable version)
    options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_text(driver, css: str, default: str = "") -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, css).text.strip()
    except NoSuchElementException:
        return default


def _get_listing_urls(driver, page_url: str) -> list[str]:
    urls = []
    try:
        driver.get(page_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/annonces/']"))
        )
        seen = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/annonces/']"):
            href = a.get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                urls.append(href)
        logger.info(f"Page {page_url} → {len(urls)} listings found.")
    except TimeoutException:
        logger.warning(f"Timeout on results page: {page_url}")
    except Exception as e:
        logger.error(f"Error fetching results page {page_url}: {e}")
    return urls


def _scrape_listing(driver, url: str) -> dict:
    record = {
        "titre":              "",
        "prix":               "",
        "ville":              "",
        "quartier":           "",
        "surface":            "",
        "nb_chambres":        "",
        "nb_salles_bain":     "",
        "etage":              "",
        "annee_construction": "",
        "lien":               url,
        "scraped_at":         datetime.utcnow().isoformat(),
        # 🔴 FIX 2: error field added to track timeout/failures clearly
        "error":              None,
    }
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )

        record["titre"] = _safe_text(driver, "h1")
        record["prix"]  = _safe_text(
            driver, "[class*='price'] span, [data-testid='price']"
        )

        # Location from breadcrumb
        loc_els = driver.find_elements(
            By.CSS_SELECTOR,
            "[class*='breadcrumb'] a, [class*='location'] span",
        )
        if len(loc_els) >= 2:
            record["ville"]    = loc_els[-2].text.strip()
            record["quartier"] = loc_els[-1].text.strip()
        elif len(loc_els) == 1:
            record["ville"] = loc_els[0].text.strip()

        # Attribute items (surface, rooms, floor, year …)
        for item in driver.find_elements(
            By.CSS_SELECTOR,
            "[class*='attribute'], [class*='detail'] li, [class*='param'] li",
        ):
            txt = item.text.lower()
            if "surface" in txt or "m²" in txt or "m2" in txt:
                record["surface"] = item.text.strip()
            elif "chambre" in txt or "pièce" in txt:
                record["nb_chambres"] = item.text.strip()
            elif "bain" in txt or "salle" in txt:
                record["nb_salles_bain"] = item.text.strip()
            elif "étage" in txt or "etage" in txt:
                record["etage"] = item.text.strip()
            elif "année" in txt or "construction" in txt:
                record["annee_construction"] = item.text.strip()

        logger.debug(f"Scraped: {record['titre'][:60]}")

    except TimeoutException:
        logger.warning(f"Timeout on listing: {url}")
        record["error"] = "timeout"  # 🔴 FIX 2: mark clearly instead of silent fail

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        record["error"] = str(e)  # 🔴 FIX 2: capture the error message

    return record


# ── Bronze persistence ────────────────────────────────────────────────────────

def _save_bronze(records: list[dict], page_num: int) -> str:
    today = datetime.utcnow()

    # 🔴 FIX 3: use BRONZE_DIR consistently (was hardcoded "data/bronze/...")
    path = os.path.join(
        BRONZE_DIR,
        f"{today.year}/{today.month:02d}/{today.day:02d}"
    )
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, f"page_{page_num}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logger.info(f"Bronze saved → {file_path} ({len(records)} records)")
    return file_path


# ── Validation ────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = ["titre", "prix", "lien"]


def check_schema(record: dict) -> bool:
    return all(field in record for field in REQUIRED_FIELDS)


def check_content(record: dict) -> bool:
    # 🔴 FIX 5: named exception instead of bare except
    try:
        if not record.get("titre") or len(record["titre"]) < 5:
            return False
        if not record.get("prix"):
            return False
        if not record.get("lien"):
            return False
        return True
    except Exception as e:
        logger.error(f"check_content error: {e}")
        return False


def check_business_rules(record: dict) -> bool:
    # 🔴 FIX 4: stricter price validation using regex (min 3 digits)
    # 🔴 FIX 5: named exception instead of bare except
    try:
        prix = str(record.get("prix", ""))
        if not re.search(r'\d{3,}', prix):
            return False
        return True
    except Exception as e:
        logger.error(f"check_business_rules error: {e}")
        return False


def is_valid_record(record: dict) -> bool:
    return (
        check_schema(record)
        and check_content(record)
        and check_business_rules(record)
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def run_scraper(max_pages: int = MAX_PAGES) -> list[dict]:  # 🔴 FIX 6: will now return data
    logger.info("=== Scraper started ===")
    driver = _build_driver()

    total_records  = 0
    valid_records  = 0
    invalid_records = 0
    all_records    = []  # 🔴 FIX 6: collect all pages to return at the end

    try:
        for page_num in range(1, max_pages + 1):
            page_url = f"{BASE_URL}?o={page_num}"  # Avito uses ?o= for pagination
            logger.info(f"── Page {page_num}/{max_pages}")

            listing_urls = _get_listing_urls(driver, page_url)

            if not listing_urls:
                logger.warning("No listings found — stopping pagination.")
                break

            page_records = []  # reset per page

            for url in listing_urls:
                record = _scrape_listing(driver, url)  # create first
                total_records += 1

                if is_valid_record(record):              # then validate
                    page_records.append(record)
                    valid_records += 1
                else:
                    invalid_records += 1
                    logger.warning(f"❌ Invalid record skipped: {record.get('lien')}")

                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

            logger.info(
                f"\n📊 PAGE {page_num} STATS:\n"
                f"--------------------------------\n"
                f"Total records:   {total_records}\n"
                f"Valid records:   {valid_records}\n"
                f"Invalid records: {invalid_records}\n"
                f"--------------------------------"
            )

            _save_bronze(page_records, page_num)        # save after each page
            all_records.extend(page_records)            # 🔴 FIX 6: accumulate

    except WebDriverException as e:
        logger.error(f"WebDriver fatal error: {e}")

    finally:
        driver.quit()
        logger.info("WebDriver closed.")

    logger.info("=== Scraper finished ===")
    return all_records  # 🔴 FIX 6: actually return the collected data