"""
Scraper for Avito.ma — immobilier listings.
Collects ONLY non-personal, publicly visible real-estate data.
No names, phone numbers, or emails are ever scraped.
Polite crawling: random delay 2–4s between requests.
"""

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

BASE_URL   = "https://www.avito.ma/fr/maroc/immobilier"
MAX_PAGES  = 10
DELAY_MIN  = 2.0
DELAY_MAX  = 4.0
BRONZE_DIR = os.path.join(os.path.dirname(__file__), "../../data/bronze")


# ── Driver ────────────────────────────────────────────────────────────────────

def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    chromium_bin = "/usr/bin/chromium"
    if os.path.exists(chromium_bin):
        options.binary_location = chromium_bin
        driver = webdriver.Chrome(
            service=Service("/usr/bin/chromedriver"), options=options
        )
    else:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
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
        "titre":             "",
        "prix":              "",
        "ville":             "",
        "quartier":          "",
        "surface":           "",
        "nb_chambres":       "",
        "nb_salles_bain":    "",
        "etage":             "",
        "annee_construction":"",
        "lien":              url,
        "scraped_at":        datetime.utcnow().isoformat(),
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
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")

    return record


# ── Bronze persistence ────────────────────────────────────────────────────────

def _save_bronze(records: list[dict]) -> str:
    os.makedirs(BRONZE_DIR, exist_ok=True)
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BRONZE_DIR, f"avito_raw_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info(f"Bronze saved → {path}  ({len(records)} records)")
    return path


# ── Entry point ───────────────────────────────────────────────────────────────

def run_scraper(max_pages: int = MAX_PAGES) -> list[dict]:
    logger.info("=== Scraper started ===")
    driver      = _build_driver()
    all_records = []

    try:
        for page_num in range(1, max_pages + 1):
            page_url = f"{BASE_URL}?page={page_num}"
            logger.info(f"── Results page {page_num}/{max_pages}")

            # Retry getting listing URLs up to 3 times
            listing_urls = []
            for attempt in range(3):
                listing_urls = _get_listing_urls(driver, page_url)
                if listing_urls:
                    break
                logger.warning(f"Attempt {attempt + 1}: no URLs found, retrying…")
                time.sleep(5)

            if not listing_urls:
                logger.warning("No listings found — stopping pagination.")
                break

            for url in listing_urls:
                record = _scrape_listing(driver, url)
                all_records.append(record)
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    except WebDriverException as e:
        logger.error(f"WebDriver fatal error: {e}")
    finally:
        driver.quit()
        logger.info("WebDriver closed.")

    _save_bronze(all_records)
    logger.info(f"=== Scraper finished — {len(all_records)} records ===")
    return all_records
