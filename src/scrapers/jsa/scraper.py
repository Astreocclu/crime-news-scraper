"""
JSA scraper implementation.

This module provides a Selenium-based scraper for the Jewelers Security Alliance (JSA)
website, extracting jewelry theft incidents and related information.
"""

import time
import re
import requests
import os
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Import from base package
from ..base import BaseScraper, Article
from .config import JSA_CONFIG, MONITORED_LOCATIONS
from .utils import detect_location, extract_keywords, is_business_related, standardize_date
from ...utils.logger import get_logger
from ...utils.exceptions import ScraperNetworkError, ScraperParsingError

# Get a logger for this module
logger = get_logger(__name__)

class JSAScraper(BaseScraper):
    """Selenium-based JSA scraper implementation"""

    def __init__(self):
        super().__init__(JSA_CONFIG["name"], JSA_CONFIG["url"])
        self.config = JSA_CONFIG
        self.monitored_locations = MONITORED_LOCATIONS
        self.driver = None

    def setup_driver(self):
        """Set up and return a configured Chrome/Chromium WebDriver"""
        chrome_options = Options()

        # Basic options for headless mode
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # Additional options to help with running in CI/CD or environments without Chrome
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')

        # Create the driver with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to create WebDriver (attempt {attempt + 1}/{max_retries})")

                # Try to use Chromium directly (if installed)
                try:
                    logger.info("Attempting to use Chromium directly")
                    chrome_options.binary_location = "/usr/bin/chromium-browser"  # Location of Chromium on this system
                    # Add a unique user data directory to avoid conflicts
                    import tempfile
                    import os
                    import uuid
                    temp_dir = tempfile.mkdtemp(prefix="chromium_data_")
                    # Add a UUID to ensure unique user data directory
                    unique_id = str(uuid.uuid4())
                    user_data_dir = os.path.join(temp_dir, unique_id)
                    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
                    logger.info(f"Using temporary user data directory: {user_data_dir}")
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.set_page_load_timeout(30)
                    return self.driver
                except Exception as chromium_error:
                    logger.warning(f"Could not use Chromium directly: {str(chromium_error)}")

                    # Fall back to webdriver_manager approach
                    logger.info("Falling back to webdriver_manager")
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.driver.set_page_load_timeout(30)
                    return self.driver

            except Exception as e:
                logger.error(f"Error creating WebDriver (attempt {attempt + 1}): {str(e)}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue

        logger.error("Failed to create WebDriver after all retries")
        return None

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with retry logic and better timeout handling"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch page with Selenium (attempt {attempt + 1}/{max_retries}): {url}")

                # Ensure we have a driver
                if not self.driver:
                    self.setup_driver()

                # If still no driver, use requests as fallback
                if not self.driver:
                    return self._fetch_with_requests(url)

                # Set a shorter timeout for initial page load
                self.driver.set_page_load_timeout(15)

                # Add a timeout for script execution
                self.driver.set_script_timeout(15)

                # Navigate to the page
                self.driver.get(url)

                # Wait for the body to be present with a shorter timeout
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except TimeoutException:
                    logger.warning("Timeout waiting for body element")
                    continue

                # Get the page source
                page_source = self.driver.page_source

                if not page_source or len(page_source.strip()) < 100:
                    logger.warning("Page source is empty or too short")
                    continue

                return page_source

            except TimeoutException as e:
                logger.error(f"Timeout error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Short delay before retry
                continue

            except Exception as e:
                logger.error(f"Error fetching page (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Short delay before retry
                continue

        # If Selenium fails completely, try with requests as a fallback
        logger.info("Selenium failed, trying with requests as fallback")
        return self._fetch_with_requests(url)

    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """Fallback method to fetch page with requests if Selenium fails"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch page with requests (attempt {attempt + 1}/{max_retries}): {url}")

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }

                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    page_content = response.text

                    if not page_content or len(page_content.strip()) < 100:
                        logger.warning("Page content from requests is empty or too short")
                        continue

                    return page_content
                else:
                    logger.error(f"Failed to fetch page with requests. Status code: {response.status_code}")

            except Exception as e:
                logger.error(f"Error fetching page with requests (attempt {attempt + 1}): {str(e)}")

            if attempt < max_retries - 1:
                time.sleep(2)  # Short delay before retry

        logger.error("Failed to fetch page with both Selenium and requests")
        return None

    def find_element(self, container, selectors):
        """Try multiple selectors to find an element"""
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            if selector.startswith('.'):
                # Class selector
                element = container.find(class_=selector[1:])
            else:
                # Tag selector
                element = container.find(selector)
            if element:
                return element
        return None

    def get_last_page_number(self, soup: BeautifulSoup) -> int:
        """Get the last page number from pagination"""
        try:
            # Find all page number elements that are links (not current page or dots)
            page_numbers = []
            for elem in soup.find_all('a', class_='page-numbers'):
                if elem.get_text().strip().isdigit():
                    page_numbers.append(int(elem.get_text().strip()))

            if not page_numbers:
                # Check if we're on the only page (current page span)
                current = soup.find('span', class_='page-numbers current')
                if current and current.get_text().strip().isdigit():
                    return int(current.get_text().strip())
                return 1

            # Get the highest page number
            last_page = max(page_numbers)
            logger.info(f"Found {last_page} pages")
            return last_page

        except Exception as e:
            logger.error(f"Error getting last page number: {e}")
            return 1

    def scrape_crimes_category(self, max_pages: int = None) -> Dict[str, List[Dict]]:
        """
        Scrape all pages from the crimes category

        Parameters:
        -----------
        max_pages : int, optional
            Maximum number of pages to scrape. If None, scrape all pages.

        Returns:
        --------
        Dict[str, List[Dict]]
            Dictionary with locations as keys and lists of article dictionaries as values
        """
        logger.info("Starting JSA crimes category scraper...")

        # Dictionary to store articles by location
        location_articles = {}
        for location in self.monitored_locations:
            location_articles[location] = []

        # Also track unclassified articles
        location_articles["Other"] = []

        try:
            # Set up the driver
            self.setup_driver()

            # Get the first page
            current_url = self.config["crimes_url"]
            page_content = self.fetch_page(current_url)

            if not page_content:
                logger.error("Failed to get first page")
                return location_articles

            soup = BeautifulSoup(page_content, 'html.parser')

            # Get total number of pages
            total_pages = self.get_last_page_number(soup)
            if max_pages:
                total_pages = min(total_pages, max_pages)

            logger.info(f"Will scrape {total_pages} pages")

            # Process each page
            for page_num in range(1, total_pages + 1):
                logger.info(f"Processing page {page_num}/{total_pages}")

                # Get page content
                if page_num > 1:
                    page_url = f"{current_url}page/{page_num}/"
                    page_content = self.fetch_page(page_url)
                    if not page_content:
                        logger.error(f"Failed to get page {page_num}")
                        continue
                    soup = BeautifulSoup(page_content, 'html.parser')

                # Find all post sections
                posts = []
                for selector in self.config["selectors"]["posts"]:
                    if selector.startswith('.'):
                        # Class selector
                        posts.extend(soup.find_all(class_=selector[1:]))
                    else:
                        # Tag selector
                        posts.extend(soup.find_all(selector))

                if not posts:
                    logger.warning(f"No post sections found on page {page_num}")
                    continue

                # Process each post section
                for post in posts:
                    try:
                        # Get title
                        title_elem = self.find_element(post, self.config["selectors"]["title"])
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)

                        # Get URL if it's in a link
                        url = ""
                        link = title_elem.find("a")
                        if link:
                            url = link.get("href", "")
                            if not url.startswith("http"):
                                url = f"https://{url.lstrip('/')}"

                        # Get date if available
                        date = ""
                        date_elem = self.find_element(post, self.config["selectors"]["date"])
                        if date_elem:
                            date = standardize_date(date_elem.get_text(strip=True))
                            logger.info(f"Found article date: {date}")
                        else:
                            # Try to find date in the article content
                            excerpt_elem = self.find_element(post, self.config["selectors"]["excerpt"])
                            if excerpt_elem:
                                excerpt_text = excerpt_elem.get_text(strip=True)
                                # Look for dates in common formats
                                date_patterns = [
                                    r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                                    r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
                                    r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                                    r'occurred\s+(?:on|during|at)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                                    r'occurred\s+(?:on|during|at)\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
                                    r'occurred\s+(?:on|during|at)\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                                    r'(?:in|during)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
                                    r'(?:in|during)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
                                    r'(?:published|posted|written)\s+(?:on|at)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                                    r'(?:published|posted|written)\s+(?:on|at)\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
                                    r'(?:published|posted|written)\s+(?:on|at)\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                                    r'(\d{1,2}/\d{1,2}/\d{2,4})',  # Fallback for any date in MM/DD/YYYY format
                                    r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',  # Fallback for any date with month name
                                ]

                                for pattern in date_patterns:
                                    match = re.search(pattern, excerpt_text, re.IGNORECASE)
                                    if match:
                                        date = standardize_date(match.group(1))
                                        logger.info(f"Found date in excerpt: {date}")
                                        break

                        # Get excerpt if available
                        excerpt = ""
                        excerpt_elem = self.find_element(post, self.config["selectors"]["excerpt"])
                        if excerpt_elem:
                            excerpt = excerpt_elem.get_text(strip=True)

                        # Combine text for analysis
                        content_to_check = f"{title} {excerpt}".lower()

                        # Extract keywords and check if business related
                        keywords = extract_keywords(content_to_check)
                        business_related = is_business_related(content_to_check)

                        # Create article object
                        article_obj = {
                            "title": title,
                            "url": url,
                            "date": date,
                            "excerpt": excerpt,
                            "source": self.name,
                            "keywords": keywords,
                            "is_theft_related": bool(keywords),
                            "is_business_related": business_related
                        }

                        # Detect location and add to appropriate list
                        location = detect_location(content_to_check)
                        if location in location_articles:
                            location_articles[location].append(article_obj)
                        else:
                            location_articles["Other"].append(article_obj)

                    except Exception as e:
                        logger.error(f"Error processing article: {e}")
                        continue

                # Log progress
                total_articles = sum(len(articles) for articles in location_articles.values())
                logger.info(f"Total articles found so far: {total_articles}")

                # Add a small delay between pages
                time.sleep(2)

            return location_articles

        except Exception as e:
            logger.error(f"Error in scraper: {e}")
            return location_articles

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

    def scrape(self, deep_check: bool = True, max_deep_check: int = 20) -> Dict[str, List[Dict]]:
        """
        Implementation of the abstract scrape method from BaseScraper.
        This method is kept for compatibility but delegates to scrape_crimes_category.

        Parameters:
        -----------
        deep_check : bool
            Whether to perform deep checking (not used in this implementation)
        max_deep_check : int
            Maximum number of articles to deep check (not used in this implementation)

        Returns:
        --------
        Dict[str, List[Dict]]
            Dictionary with locations as keys and lists of article dictionaries as values
        """
        return self.scrape_crimes_category()

def main():
    """Run the JSA scraper directly"""
    import csv
    from datetime import datetime
    from ...utils.logger import get_logger, log_execution_time, get_dated_log_filename

    # Get a dedicated logger for the main function
    main_logger = get_logger("jsa_scraper_main")

    @log_execution_time(main_logger, "JSA Scraper: ")
    def run_scraper():
        scraper = JSAScraper()
        return scraper.scrape_crimes_category()  # No max_pages specified means scrape all pages

    # Run the scraper with execution time logging
    main_logger.info("Starting JSA scraper run")
    results = run_scraper()

    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'jsa_articles_{timestamp}.csv')

    # Count total articles
    total_articles = sum(len(articles) for articles in results.values())
    main_logger.info(f"Found {total_articles} articles across {len(results)} locations")

    # Write results to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'location', 'title', 'date', 'url', 'excerpt',
                'source', 'keywords', 'is_theft_related', 'is_business_related'
            ])
            writer.writeheader()

            for location, articles in results.items():
                for article in articles:
                    row = {
                        'location': location,
                        'title': article['title'],
                        'date': article['date'],
                        'url': article['url'],
                        'excerpt': article['excerpt'],
                        'source': article['source'],
                        'keywords': ','.join(article['keywords']),
                        'is_theft_related': article['is_theft_related'],
                        'is_business_related': article['is_business_related']
                    }
                    writer.writerow(row)

        main_logger.info(f"Results saved to {output_file}")

        # Generate summary by location
        location_counts = {loc: len(articles) for loc, articles in results.items()}
        for location, count in location_counts.items():
            main_logger.info(f"Location '{location}': {count} articles")

        # Print summary to console for user feedback
        print(f"\nScraper completed successfully:")
        print(f"- Total articles: {total_articles}")
        print(f"- Output saved to: {output_file}")
        print(f"- Check logs for details: logs/scrapers.log")

        return output_file

    except Exception as e:
        main_logger.exception(f"Error saving results: {str(e)}")
        print(f"Error saving results: {str(e)}")
        return None

if __name__ == "__main__":
    main()