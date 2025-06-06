"""
Crime News Scraper - JSA (Jewelers Security Alliance) Scraper Module

This module provides a comprehensive Selenium-based scraper for the Jewelers Security
Alliance (JSA) website, which is our PRIMARY source for jewelry industry crime incidents.

The JSA scraper is critical to our focused targeting approach as it provides:
- High-quality jewelry store theft incidents
- Detailed incident descriptions with business names and locations
- Geographic coverage across multiple monitored locations
- Direct relevance to our primary target business type (jewelry stores)

This scraper uses both Selenium WebDriver and requests as fallback to ensure
reliable data collection from the JSA crimes category pages.

Author: Augment Agent
Version: 2.0.0
"""

"""
Standard library imports
"""
import time
import re
import requests
import os
from typing import Dict, List, Optional, Any, Tuple

"""
Third-party imports
"""
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

"""
Local application imports
"""

# Import from base package
from ..base import BaseScraper, Article
from .config import JSA_CONFIG, MONITORED_LOCATIONS
from .utils import detect_location, extract_keywords, is_business_related, standardize_date
from ...utils.logger import get_logger
from ...utils.exceptions import ScraperNetworkError, ScraperParsingError

# Get a logger for this module
logger = get_logger(__name__)

class JSAScraper(BaseScraper):
    """
    Selenium-based JSA (Jewelers Security Alliance) scraper implementation.

    This scraper is our PRIMARY source for jewelry industry crime incidents,
    providing high-quality data directly relevant to our target business type.

    Features:
        - Selenium WebDriver for dynamic content handling
        - Requests fallback for reliability
        - Multi-page scraping with pagination support
        - Geographic location detection and filtering
        - Comprehensive error handling and retry logic

    The scraper focuses on the JSA crimes category pages, extracting:
        - Incident titles and descriptions
        - Dates and locations
        - Business names and types
        - Keywords for theft-related content
    """

    def __init__(self) -> None:
        """Initialize the JSA scraper with configuration and monitoring settings."""
        super().__init__(JSA_CONFIG["name"], JSA_CONFIG["url"])
        self.config = JSA_CONFIG
        self.monitored_locations = MONITORED_LOCATIONS
        self.driver: Optional[webdriver.Chrome] = None

    def setup_driver(self) -> Optional[webdriver.Chrome]:
        """
        Set up and return a configured Chrome/Chromium WebDriver.

        Returns:
            Optional[webdriver.Chrome]: Configured WebDriver instance or None if setup fails
        """
        chrome_options = self._configure_chrome_options()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to create WebDriver (attempt {attempt + 1}/{max_retries})")

                # Try Chromium first, then fall back to webdriver_manager
                driver = self._try_chromium_driver(chrome_options) or self._try_webdriver_manager(chrome_options)

                if driver:
                    driver.set_page_load_timeout(30)
                    self.driver = driver
                    return driver

            except Exception as e:
                logger.error(f"Error creating WebDriver (attempt {attempt + 1}): {str(e)}")
                self._cleanup_driver()
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue

        logger.error("Failed to create WebDriver after all retries")
        return None

    def _configure_chrome_options(self) -> Options:
        """Configure Chrome options for headless operation."""
        chrome_options = Options()

        # Basic options for headless mode
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Additional options for CI/CD environments
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')

        return chrome_options

    def _try_chromium_driver(self, chrome_options: Options) -> Optional[webdriver.Chrome]:
        """
        Try to create a WebDriver using Chromium directly.

        Args:
            chrome_options: Configured Chrome options

        Returns:
            Optional[webdriver.Chrome]: WebDriver instance or None if failed
        """
        try:
            logger.info("Attempting to use Chromium directly")
            chrome_options.binary_location = "/usr/bin/chromium-browser"

            # Create unique user data directory
            user_data_dir = self._create_temp_user_data_dir()
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            logger.info(f"Using temporary user data directory: {user_data_dir}")

            return webdriver.Chrome(options=chrome_options)

        except Exception as chromium_error:
            logger.warning(f"Could not use Chromium directly: {str(chromium_error)}")
            return None

    def _try_webdriver_manager(self, chrome_options: Options) -> Optional[webdriver.Chrome]:
        """
        Try to create a WebDriver using webdriver_manager.

        Args:
            chrome_options: Configured Chrome options

        Returns:
            Optional[webdriver.Chrome]: WebDriver instance or None if failed
        """
        try:
            logger.info("Falling back to webdriver_manager")
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)

        except Exception as e:
            logger.error(f"webdriver_manager approach failed: {str(e)}")
            return None

    def _create_temp_user_data_dir(self) -> str:
        """Create a unique temporary user data directory."""
        import tempfile
        import uuid

        temp_dir = tempfile.mkdtemp(prefix="chromium_data_")
        unique_id = str(uuid.uuid4())
        return os.path.join(temp_dir, unique_id)

    def _cleanup_driver(self) -> None:
        """Clean up the current driver instance."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

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

    def scrape_crimes_category(self, max_pages: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape all pages from the JSA crimes category.

        This is the main entry point for scraping jewelry industry crime incidents
        from the JSA website, our primary source for target business incidents.

        Args:
            max_pages: Maximum number of pages to scrape. If None, scrape all pages.

        Returns:
            Dictionary with locations as keys and lists of article dictionaries as values
        """
        logger.info("Starting JSA crimes category scraper...")

        # Initialize location-based article storage
        location_articles = self._initialize_location_storage()

        try:
            # Set up the driver and get initial page
            soup, total_pages = self._setup_scraping_session(max_pages)
            if not soup:
                return location_articles

            # Process all pages
            self._process_all_pages(soup, total_pages, location_articles)

            return location_articles

        except Exception as e:
            logger.error(f"Error in scraper: {e}")
            return location_articles

        finally:
            self._cleanup_driver()

    def _initialize_location_storage(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize the location-based article storage dictionary."""
        location_articles = {}
        for location in self.monitored_locations:
            location_articles[location] = []

        # Also track unclassified articles
        location_articles["Other"] = []
        return location_articles

    def _setup_scraping_session(self, max_pages: Optional[int]) -> Tuple[Optional[BeautifulSoup], int]:
        """
        Set up the scraping session and get initial page information.

        Args:
            max_pages: Maximum number of pages to scrape

        Returns:
            Tuple of (BeautifulSoup object, total_pages) or (None, 0) if failed
        """
        # Set up the driver
        self.setup_driver()

        # Get the first page
        current_url = self.config["crimes_url"]
        page_content = self.fetch_page(current_url)

        if not page_content:
            logger.error("Failed to get first page")
            return None, 0

        soup = BeautifulSoup(page_content, 'html.parser')

        # Get total number of pages
        total_pages = self.get_last_page_number(soup)
        if max_pages:
            total_pages = min(total_pages, max_pages)

        logger.info(f"Will scrape {total_pages} pages")
        return soup, total_pages

    def _process_all_pages(self, initial_soup: BeautifulSoup, total_pages: int,
                          location_articles: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Process all pages in the crimes category.

        Args:
            initial_soup: BeautifulSoup object for the first page
            total_pages: Total number of pages to process
            location_articles: Dictionary to store articles by location
        """
        current_url = self.config["crimes_url"]

        for page_num in range(1, total_pages + 1):
            logger.info(f"Processing page {page_num}/{total_pages}")

            # Get page content (use initial_soup for first page)
            if page_num == 1:
                soup = initial_soup
            else:
                soup = self._fetch_page_soup(current_url, page_num)
                if not soup:
                    continue

            # Process posts on this page
            self._process_page_posts(soup, page_num, location_articles)

            # Log progress and add delay
            self._log_progress_and_delay(location_articles)

    def _fetch_page_soup(self, base_url: str, page_num: int) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a specific page.

        Args:
            base_url: Base URL for the crimes category
            page_num: Page number to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        page_url = f"{base_url}page/{page_num}/"
        page_content = self.fetch_page(page_url)

        if not page_content:
            logger.error(f"Failed to get page {page_num}")
            return None

        return BeautifulSoup(page_content, 'html.parser')

    def _process_page_posts(self, soup: BeautifulSoup, page_num: int,
                           location_articles: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Process all posts on a single page.

        Args:
            soup: BeautifulSoup object for the page
            page_num: Current page number
            location_articles: Dictionary to store articles by location
        """
        # Find all post sections
        posts = self._find_posts(soup)

        if not posts:
            logger.warning(f"No post sections found on page {page_num}")
            return

        # Process each post
        for post in posts:
            try:
                article = self._extract_article_data(post)
                if article:
                    self._categorize_and_store_article(article, location_articles)

            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue

    def _find_posts(self, soup: BeautifulSoup) -> List[Any]:
        """Find all post sections on a page."""
        posts = []
        for selector in self.config["selectors"]["posts"]:
            if selector.startswith('.'):
                # Class selector
                posts.extend(soup.find_all(class_=selector[1:]))
            else:
                # Tag selector
                posts.extend(soup.find_all(selector))
        return posts

    def _log_progress_and_delay(self, location_articles: Dict[str, List[Dict[str, Any]]]) -> None:
        """Log current progress and add delay between pages."""
        total_articles = sum(len(articles) for articles in location_articles.values())
        logger.info(f"Total articles found so far: {total_articles}")
        time.sleep(2)  # Small delay between pages

    def _extract_article_data(self, post: Any) -> Optional[Dict[str, Any]]:
        """
        Extract article data from a post element.

        Args:
            post: BeautifulSoup post element

        Returns:
            Article dictionary or None if extraction failed
        """
        # Get title
        title_elem = self.find_element(post, self.config["selectors"]["title"])
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # Get URL if it's in a link
        url = self._extract_article_url(title_elem)

        # Get date
        date = self._extract_article_date(post)

        # Get excerpt
        excerpt = self._extract_article_excerpt(post)

        # Combine text for analysis
        content_to_check = f"{title} {excerpt}".lower()

        # Extract keywords and check if business related
        keywords = extract_keywords(content_to_check)
        business_related = is_business_related(content_to_check)

        return {
            "title": title,
            "url": url,
            "date": date,
            "excerpt": excerpt,
            "source": self.name,
            "keywords": keywords,
            "is_theft_related": bool(keywords),
            "is_business_related": business_related
        }

    def _extract_article_url(self, title_elem: Any) -> str:
        """Extract URL from title element."""
        url = ""
        link = title_elem.find("a")
        if link:
            url = link.get("href", "")
            if not url.startswith("http"):
                url = f"https://{url.lstrip('/')}"
        return url

    def _extract_article_date(self, post: Any) -> str:
        """
        Extract date from post element.

        Args:
            post: BeautifulSoup post element

        Returns:
            Standardized date string or empty string if not found
        """
        # Try to get date from date element first
        date_elem = self.find_element(post, self.config["selectors"]["date"])
        if date_elem:
            date = standardize_date(date_elem.get_text(strip=True))
            logger.info(f"Found article date: {date}")
            return date

        # Try to find date in the article content
        excerpt_elem = self.find_element(post, self.config["selectors"]["excerpt"])
        if excerpt_elem:
            excerpt_text = excerpt_elem.get_text(strip=True)
            return self._extract_date_from_text(excerpt_text)

        return ""

    def _extract_date_from_text(self, text: str) -> str:
        """
        Extract date from text using regex patterns.

        Args:
            text: Text to search for dates

        Returns:
            Standardized date string or empty string if not found
        """
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
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date = standardize_date(match.group(1))
                logger.info(f"Found date in excerpt: {date}")
                return date

        return ""

    def _extract_article_excerpt(self, post: Any) -> str:
        """Extract excerpt from post element."""
        excerpt_elem = self.find_element(post, self.config["selectors"]["excerpt"])
        if excerpt_elem:
            return excerpt_elem.get_text(strip=True)
        return ""

    def _categorize_and_store_article(self, article: Dict[str, Any],
                                    location_articles: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Categorize article by location and store it.

        Args:
            article: Article dictionary
            location_articles: Dictionary to store articles by location
        """
        content_to_check = f"{article['title']} {article['excerpt']}".lower()
        location = detect_location(content_to_check)

        if location in location_articles:
            location_articles[location].append(article)
        else:
            location_articles["Other"].append(article)

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