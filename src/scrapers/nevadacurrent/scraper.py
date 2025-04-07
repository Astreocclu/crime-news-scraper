"""
Nevada Current scraper implementation.

This module provides a Selenium-based scraper for the Nevada Current justice section,
extracting theft incidents and related information with a focus on Nevada businesses.
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

from ..base import BaseScraper, Article
from .config import NEVADACURRENT_CONFIG, MONITORED_LOCATIONS
from .utils import detect_location, extract_keywords, is_business_related, standardize_date, extract_location_details
from src.utils.logger import get_logger
from src.utils.exceptions import ScraperNetworkError, ScraperParsingError

# Get a logger for this module
logger = get_logger(__name__)

class NevadaCurrentScraper(BaseScraper):
    """Selenium-based Nevada Current scraper implementation"""
    
    def __init__(self):
        super().__init__(NEVADACURRENT_CONFIG["name"], NEVADACURRENT_CONFIG["url"])
        self.config = NEVADACURRENT_CONFIG
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
                    chrome_options.binary_location = "/usr/bin/chromium-browser"
                    # Add a unique user data directory to avoid conflicts
                    import tempfile
                    import uuid
                    temp_dir = tempfile.mkdtemp(prefix="chromium_data_")
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
    
    def scroll_to_load_more(self, max_scrolls=10):
        """
        Scroll down the page to load more dynamically loaded content
        
        Parameters:
        -----------
        max_scrolls : int
            Maximum number of scroll operations to perform
        """
        try:
            if not self.driver:
                logger.warning("No driver available for scrolling")
                return
                
            logger.info(f"Starting scroll operation to load more content (max: {max_scrolls})")
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(max_scrolls):
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for content to load
                time.sleep(2)
                
                # Calculate new scroll height and compare to last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == initial_height:
                    # No new content loaded, stop scrolling
                    logger.info(f"No new content after scroll {i+1}, stopping")
                    break
                    
                initial_height = new_height
                logger.info(f"Completed scroll {i+1}/{max_scrolls}, new height: {new_height}")
                
        except Exception as e:
            logger.error(f"Error during scroll operation: {str(e)}")
    
    def get_pagination_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract pagination links from the page
        
        Parameters:
        -----------
        soup : BeautifulSoup
            Parsed HTML of the page
            
        Returns:
        --------
        List[str]
            List of pagination URLs
        """
        pagination_links = []
        try:
            # Look for pagination elements
            pagination = soup.select('.navigation a, .pagination a')
            if pagination:
                for link in pagination:
                    if link.has_attr('href') and 'page' in link['href']:
                        pagination_links.append(link['href'])
                        
            logger.info(f"Found {len(pagination_links)} pagination links")
            return pagination_links
        except Exception as e:
            logger.error(f"Error getting pagination links: {e}")
            return []
    
    def extract_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract articles from the soup object
        
        Parameters:
        -----------
        soup : BeautifulSoup
            Parsed HTML of the page
            
        Returns:
        --------
        List[Dict]
            List of article dictionaries
        """
        articles = []
        
        # Process post elements
        for selector in self.config["selectors"]["posts"]:
            post_elements = []
            
            if selector.startswith('.'):
                # Class selector
                post_elements = soup.select(selector)
            else:
                # Tag selector
                post_elements = soup.find_all(selector)
                
            logger.info(f"Found {len(post_elements)} post elements with selector '{selector}'")
            
            # Process each post
            for post in post_elements:
                try:
                    # Extract title
                    title = ""
                    title_elem = None
                    
                    # Try title selectors
                    for title_selector in self.config["selectors"]["title"]:
                        if title_selector.startswith('.'):
                            title_elem = post.select_one(title_selector)
                        else:
                            title_elem = post.find(title_selector)
                            
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            break
                            
                    # If no title found, skip this post
                    if not title:
                        continue
                        
                    # Extract URL
                    url = ""
                    
                    # First try to get URL from title element
                    if title_elem and title_elem.find('a'):
                        url = title_elem.find('a').get('href', '')
                    else:
                        # Try link selectors
                        for link_selector in self.config["selectors"]["link"]:
                            link_elem = None
                            
                            if link_selector.startswith('.'):
                                link_elem = post.select_one(link_selector)
                            else:
                                link_elem = post.find(link_selector)
                                
                            if link_elem and link_elem.get('href'):
                                url = link_elem.get('href')
                                break
                    
                    # Ensure URL is absolute
                    if url and not url.startswith('http'):
                        url = f"https://nevadacurrent.com{url}" if url.startswith('/') else f"https://nevadacurrent.com/{url}"
                        
                    # Extract date
                    date = ""
                    for date_selector in self.config["selectors"]["date"]:
                        date_elem = None
                        
                        if date_selector.startswith('.'):
                            date_elem = post.select_one(date_selector)
                        else:
                            date_elem = post.find(date_selector)
                            
                        if date_elem:
                            date = standardize_date(date_elem.get_text(strip=True))
                            break
                            
                    # Extract excerpt
                    excerpt = ""
                    for excerpt_selector in self.config["selectors"]["excerpt"]:
                        excerpt_elem = None
                        
                        if excerpt_selector.startswith('.'):
                            excerpt_elem = post.select_one(excerpt_selector)
                        else:
                            excerpt_elem = post.find(excerpt_selector)
                            
                        if excerpt_elem:
                            excerpt = excerpt_elem.get_text(strip=True)
                            break
                    
                    # Create article object and check relevance
                    content_to_check = f"{title} {excerpt}".lower() if excerpt else title.lower()
                    
                    # Extract keywords and check if business related
                    keywords = extract_keywords(content_to_check)
                    business_related = is_business_related(content_to_check)
                    
                    logger.info(f"Article: {title}")
                    logger.info(f"Keywords: {keywords}")
                    logger.info(f"Business related: {business_related}")
                    
                    # Only include articles that are theft-related or business-related
                    if not keywords and not business_related:
                        continue
                        
                    article = {
                        "title": title,
                        "url": url,
                        "date": date,
                        "excerpt": excerpt,
                        "source": self.name,
                        "keywords": keywords,
                        "is_theft_related": bool(keywords),
                        "is_business_related": business_related,
                        "detailed_location": extract_location_details(content_to_check)
                    }
                    
                    articles.append(article)
                    logger.info(f"Added article: {title}")
                    
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
                    
        return articles
    
    def scrape_justice_news(self, max_pages: int = None) -> Dict[str, List[Dict]]:
        """
        Scrape justice news from Nevada Current
        
        Parameters:
        -----------
        max_pages : int
            Maximum number of pages to scrape
            
        Returns:
        --------
        Dict[str, List[Dict]]
            Dictionary with locations as keys and lists of article dictionaries as values
        """
        logger.info("Starting Nevada Current justice news scraper...")
        
        # Dictionary to store articles by location
        location_articles = {}
        for location in self.monitored_locations:
            location_articles[location] = []
        
        # Also track unclassified articles
        location_articles["Other"] = []
        
        try:
            # Set up the driver
            self.setup_driver()
            
            # Get the justice page
            current_url = self.config["url"]
            page_content = self.fetch_page(current_url)
            
            if not page_content:
                logger.error("Failed to get the justice page")
                return location_articles
                
            # Use Selenium to scroll and load more content
            self.scroll_to_load_more(max_scrolls=5)
            
            # Get the updated page content after scrolling
            page_content = self.driver.page_source
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Get pagination links
            pagination_links = self.get_pagination_links(soup)
            
            # Limit pages if specified
            if max_pages and pagination_links:
                pagination_links = pagination_links[:max_pages-1]  # -1 because we already have the first page
            
            # Process first page
            articles = self.extract_articles(soup)
            
            # Process articles and add to appropriate location bucket
            for article in articles:
                # Detect location
                content_to_check = f"{article['title']} {article['excerpt']}".lower()
                location = detect_location(content_to_check)
                
                if location in location_articles:
                    location_articles[location].append(article)
                else:
                    location_articles["Other"].append(article)
            
            # Process additional pages
            for i, page_url in enumerate(pagination_links):
                logger.info(f"Processing page {i+2}/{len(pagination_links)+1}")
                
                page_content = self.fetch_page(page_url)
                if not page_content:
                    logger.error(f"Failed to get page {page_url}")
                    continue
                    
                soup = BeautifulSoup(page_content, 'html.parser')
                
                # Extract articles
                page_articles = self.extract_articles(soup)
                
                # Process articles and add to appropriate location bucket
                for article in page_articles:
                    # Detect location
                    content_to_check = f"{article['title']} {article['excerpt']}".lower()
                    location = detect_location(content_to_check)
                    
                    if location in location_articles:
                        location_articles[location].append(article)
                    else:
                        location_articles["Other"].append(article)
                
                # Small delay between pages
                time.sleep(2)
            
            # Count total articles
            total_articles = sum(len(articles) for articles in location_articles.values() if articles)
            logger.info(f"Successfully processed {total_articles} relevant articles")
            
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
        return self.scrape_justice_news(max_pages=3)  # Limit to 3 pages for efficiency

def main():
    """Run the Nevada Current scraper directly"""
    import csv
    from datetime import datetime
    from src.utils.logger import get_logger, log_execution_time, get_dated_log_filename
    
    # Get a dedicated logger for the main function
    main_logger = get_logger("nevadacurrent_scraper_main")
    
    @log_execution_time(main_logger, "Nevada Current Scraper: ")
    def run_scraper():
        scraper = NevadaCurrentScraper()
        return scraper.scrape_justice_news(max_pages=3)  # Limit to 3 pages for testing
    
    # Run the scraper with execution time logging
    main_logger.info("Starting Nevada Current scraper run")
    results = run_scraper()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'nevadacurrent_articles_{timestamp}.csv')
    
    # Count total articles
    total_articles = sum(len(articles) for articles in results.values() if articles)
    main_logger.info(f"Found {total_articles} articles across {len(results)} locations")
    
    # Write results to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'location', 'title', 'date', 'url', 'excerpt',
                'source', 'keywords', 'is_theft_related', 'is_business_related',
                'detailed_location'
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
                        'is_business_related': article['is_business_related'],
                        'detailed_location': article.get('detailed_location', '')
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