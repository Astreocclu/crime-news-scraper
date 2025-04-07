"""
WFAA scraper implementation.

This module provides a Selenium-based scraper for the WFAA crime news section,
extracting theft incidents and related information.
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
from .config import WFAA_CONFIG, MONITORED_LOCATIONS
from .utils import detect_location, extract_keywords, is_business_related, standardize_date, extract_location_details
from src.utils.logger import get_logger
from src.utils.exceptions import ScraperNetworkError, ScraperParsingError

# Get a logger for this module
logger = get_logger(__name__)

class WFAAScraper(BaseScraper):
    """Selenium-based WFAA scraper implementation"""
    
    def __init__(self):
        super().__init__(WFAA_CONFIG["name"], WFAA_CONFIG["url"])
        self.config = WFAA_CONFIG
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
    
    def find_element(self, container, selectors):
        """Try multiple selectors to find an element"""
        if isinstance(selectors, str):
            selectors = [selectors]
            
        for selector in selectors:
            try:
                if selector.startswith('.'):
                    # Class selector
                    element = container.find(class_=selector[1:])
                elif selector.startswith('[') and selector.endswith(']'):
                    # Attribute selector like [data-module]
                    attr_name = selector[1:-1]
                    elements = container.find_all(attrs={attr_name: True})
                    element = elements[0] if elements else None
                else:
                    # Tag selector
                    element = container.find(selector)
                if element:
                    return element
            except Exception as e:
                logger.debug(f"Error finding element with selector {selector}: {str(e)}")
                continue
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
    
    def scrape_crime_news(self, max_scrolls: int = 5) -> Dict[str, List[Dict]]:
        """
        Scrape crime news from WFAA
        
        Parameters:
        -----------
        max_scrolls : int
            Maximum number of scrolls to perform for loading more content
            
        Returns:
        --------
        Dict[str, List[Dict]]
            Dictionary with locations as keys and lists of article dictionaries as values
        """
        logger.info("Starting WFAA crime news scraper...")
        
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
            current_url = self.config["url"]
            page_content = self.fetch_page(current_url)
            
            if not page_content:
                logger.error("Failed to get the crime page")
                
                # Try the section crime URL as fallback
                logger.info("Trying alternative crime section URL")
                current_url = "https://www.wfaa.com/section/crime"
                page_content = self.fetch_page(current_url)
                
                if not page_content:
                    logger.error("Failed to get the crime section page")
                    return location_articles
                
            # Use Selenium to scroll and load more content if dynamic loading is detected
            self.scroll_to_load_more(max_scrolls=max_scrolls)
            
            # Get the updated page content after scrolling
            page_content = self.driver.page_source
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Find all post/article sections using multiple selectors
            posts = []
            for selector in self.config["selectors"]["posts"]:
                if selector.startswith('.'):
                    # Class selector
                    posts.extend(soup.find_all(class_=selector[1:]))
                else:
                    # Tag selector
                    posts.extend(soup.find_all(selector))
            
            if not posts:
                logger.warning("No post sections found on the page")
                return location_articles
            
            logger.info(f"Found {len(posts)} potential article elements")
            
            # Process each post/article
            article_count = 0
            for post in posts:
                try:
                    # Get title - first try finding the link heading then the title element
                    title = ""
                    link_heading = post.select_one(".grid__module-heading a")
                    if link_heading:
                        title = link_heading.get_text(strip=True)
                        
                    # If no link heading with title, try the regular title selectors
                    if not title:
                        title_elem = self.find_element(post, self.config["selectors"]["title"])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                    
                    # Skip if no title found
                    if not title:
                        continue
                    
                    # Log the title for debugging
                    logger.info(f"Found article title: {title}")
                        
                    # Get URL - first try the heading link, then any link
                    url = ""
                    if link_heading and link_heading.has_attr('href'):
                        url = link_heading['href']
                    
                    # If no URL from heading link, try any link in the post
                    if not url:
                        link_elem = post.find("a")
                        if link_elem and link_elem.has_attr('href'):
                            url = link_elem['href']
                    
                    # Handle relative URLs
                    if url and not url.startswith('http'):
                        if url.startswith('/'):
                            url = f"https://www.wfaa.com{url}"
                        else:
                            url = f"https://www.wfaa.com/{url}"
                    
                    # Get date if available
                    date = ""
                    date_elem = self.find_element(post, self.config["selectors"]["date"])
                    if date_elem:
                        date = standardize_date(date_elem.get_text(strip=True))
                    
                    # Get excerpt if available
                    excerpt = ""
                    excerpt_elem = self.find_element(post, self.config["selectors"]["excerpt"])
                    if excerpt_elem:
                        excerpt = excerpt_elem.get_text(strip=True)
                    
                    # If no excerpt, try to use the title as content
                    content_to_check = f"{title} {excerpt}".lower() if excerpt else title.lower()
                    
                    # Extract keywords and check if business related
                    keywords = extract_keywords(content_to_check)
                    business_related = is_business_related(content_to_check)
                    
                    # Log details for monitoring
                    logger.info(f"Article keywords: {keywords}")
                    logger.info(f"Business related: {business_related}")
                    
                    # Only include articles that are theft-related or business-related
                    if not keywords and not business_related:
                        continue
                        
                    # Try to extract more detailed location
                    detailed_location = extract_location_details(content_to_check)
                    
                    # Create article object
                    article_obj = {
                        "title": title,
                        "url": url,
                        "date": date,
                        "excerpt": excerpt,
                        "source": self.name,
                        "keywords": keywords,
                        "is_theft_related": bool(keywords),
                        "is_business_related": business_related,
                        "detailed_location": detailed_location
                    }
                    
                    # Detect location and add to appropriate list
                    location = detect_location(content_to_check)
                    if location in location_articles:
                        location_articles[location].append(article_obj)
                        article_count += 1
                    else:
                        location_articles["Other"].append(article_obj)
                        article_count += 1
                        
                    logger.info(f"Processed article: {title}")
                        
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
            
            logger.info(f"Successfully processed {article_count} relevant articles")
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
        return self.scrape_crime_news(max_scrolls=5)

def main():
    """Run the WFAA scraper directly"""
    import csv
    from datetime import datetime
    from src.utils.logger import get_logger, log_execution_time, get_dated_log_filename
    
    # Get a dedicated logger for the main function
    main_logger = get_logger("wfaa_scraper_main")
    
    @log_execution_time(main_logger, "WFAA Scraper: ")
    def run_scraper():
        scraper = WFAAScraper()
        return scraper.scrape_crime_news()
    
    # Run the scraper with execution time logging
    main_logger.info("Starting WFAA scraper run")
    results = run_scraper()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'wfaa_articles_{timestamp}.csv')
    
    # Count total articles
    total_articles = sum(len(articles) for articles in results.values())
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