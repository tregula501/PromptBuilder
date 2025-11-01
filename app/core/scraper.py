"""
Web scraping module for fetching betting data from sportsbook websites.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.core.config import get_config
from app.core.models import Game, OddsData, ScrapingRule, APIResponse, DataSource

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for web scraping."""

    def __init__(self):
        self.config = get_config()
        self.delay = self.config.scraping_delay
        self.timeout = self.config.request_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_html(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            time.sleep(self.delay)  # Rate limiting

            req_headers = self.session.headers.copy()
            if headers:
                req_headers.update(headers)

            response = self.session.get(url, headers=req_headers, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Successfully fetched: {url}")
            return response.text

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """Parse HTML content."""
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return None


class SeleniumScraper:
    """Scraper using Selenium for dynamic content."""

    def __init__(self):
        self.config = get_config()
        self.delay = self.config.scraping_delay
        self.driver: Optional[webdriver.Chrome] = None

    def init_driver(self, headless: bool = True):
        """Initialize Chrome WebDriver."""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )

            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium driver initialized")

        except Exception as e:
            logger.error(f"Error initializing Selenium driver: {e}")
            self.driver = None

    def fetch_page(self, url: str, wait_for_selector: Optional[str] = None) -> Optional[str]:
        """Fetch page content using Selenium."""
        if not self.driver:
            self.init_driver()

        if not self.driver:
            return None

        try:
            time.sleep(self.delay)
            self.driver.get(url)

            # Wait for specific element if provided
            if wait_for_selector:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )

            time.sleep(2)  # Additional wait for dynamic content
            return self.driver.page_source

        except Exception as e:
            logger.error(f"Error fetching page with Selenium: {e}")
            return None

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium driver closed")


class CustomScraper(BaseScraper):
    """Custom scraper using user-defined rules."""

    def __init__(self, rule: ScrapingRule):
        super().__init__()
        self.rule = rule

    def scrape(self) -> APIResponse:
        """Scrape data using the configured rule."""
        if not self.rule.enabled:
            return APIResponse(
                success=False,
                error="Scraping rule is disabled",
                source=DataSource.WEB_SCRAPING
            )

        try:
            # Add custom headers if provided
            headers = self.rule.headers or {}

            html = self.fetch_html(self.rule.url, headers)
            if not html:
                return APIResponse(
                    success=False,
                    error="Failed to fetch HTML",
                    source=DataSource.WEB_SCRAPING
                )

            soup = self.parse_html(html)
            if not soup:
                return APIResponse(
                    success=False,
                    error="Failed to parse HTML",
                    source=DataSource.WEB_SCRAPING
                )

            # Extract data using selectors
            data = self._extract_data(soup)

            return APIResponse(
                success=True,
                data=data,
                source=DataSource.WEB_SCRAPING
            )

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return APIResponse(
                success=False,
                error=str(e),
                source=DataSource.WEB_SCRAPING
            )

    def _extract_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data using CSS selectors from the rule."""
        extracted = {}

        for field, selector in self.rule.selectors.items():
            try:
                # Try CSS selector first
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        extracted[field] = elements[0].get_text(strip=True)
                    else:
                        extracted[field] = [elem.get_text(strip=True) for elem in elements]
                else:
                    extracted[field] = None

            except Exception as e:
                logger.warning(f"Error extracting {field}: {e}")
                extracted[field] = None

        return extracted


class DraftKingsScraper(BaseScraper):
    """Specialized scraper for DraftKings (example implementation)."""

    BASE_URL = "https://sportsbook.draftkings.com"

    def scrape_odds(self, sport: str) -> APIResponse:
        """
        Scrape odds from DraftKings.

        Note: This is a placeholder implementation. Actual implementation
        would require analyzing DraftKings' page structure and potentially
        using their API if available.
        """
        try:
            # Placeholder - would need actual implementation
            logger.warning("DraftKings scraper not fully implemented")

            return APIResponse(
                success=False,
                error="DraftKings scraper requires implementation",
                source=DataSource.WEB_SCRAPING
            )

        except Exception as e:
            return APIResponse(
                success=False,
                error=str(e),
                source=DataSource.WEB_SCRAPING
            )


class FanDuelScraper(BaseScraper):
    """Specialized scraper for FanDuel (example implementation)."""

    BASE_URL = "https://sportsbook.fanduel.com"

    def scrape_odds(self, sport: str) -> APIResponse:
        """
        Scrape odds from FanDuel.

        Note: This is a placeholder implementation.
        """
        try:
            logger.warning("FanDuel scraper not fully implemented")

            return APIResponse(
                success=False,
                error="FanDuel scraper requires implementation",
                source=DataSource.WEB_SCRAPING
            )

        except Exception as e:
            return APIResponse(
                success=False,
                error=str(e),
                source=DataSource.WEB_SCRAPING
            )


class ScraperManager:
    """Manager for coordinating different scrapers."""

    def __init__(self):
        self.config = get_config()
        self.custom_scrapers: Dict[str, CustomScraper] = {}
        self.selenium_scraper: Optional[SeleniumScraper] = None

    def add_custom_scraper(self, name: str, rule: ScrapingRule):
        """Add a custom scraper with specified rules."""
        self.custom_scrapers[name] = CustomScraper(rule)
        logger.info(f"Added custom scraper: {name}")

    def scrape_with_custom(self, name: str) -> APIResponse:
        """Execute a custom scraper by name."""
        if name not in self.custom_scrapers:
            return APIResponse(
                success=False,
                error=f"Scraper '{name}' not found",
                source=DataSource.WEB_SCRAPING
            )

        return self.custom_scrapers[name].scrape()

    def scrape_with_selenium(self, url: str, wait_selector: Optional[str] = None) -> Optional[str]:
        """Scrape a page using Selenium."""
        if not self.selenium_scraper:
            self.selenium_scraper = SeleniumScraper()

        return self.selenium_scraper.fetch_page(url, wait_selector)

    def close_all(self):
        """Close all active scrapers."""
        if self.selenium_scraper:
            self.selenium_scraper.close()
        logger.info("All scrapers closed")


# Singleton instance
_scraper_manager: Optional[ScraperManager] = None


def get_scraper_manager() -> ScraperManager:
    """Get the scraper manager singleton."""
    global _scraper_manager
    if _scraper_manager is None:
        _scraper_manager = ScraperManager()
    return _scraper_manager
