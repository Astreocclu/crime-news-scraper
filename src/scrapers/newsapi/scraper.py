"""
NewsAPI scraper implementation.

This module provides a scraper for the NewsAPI service, searching for jewelry theft 
incidents and related information across multiple news sources.
"""

import time
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..base import BaseScraper, Article
from .config import NEWSAPI_CONFIG, MONITORED_LOCATIONS
from .utils import detect_location, extract_keywords, is_business_related, standardize_date
from src.utils.logger import get_logger
from src.utils.exceptions import ScraperNetworkError, ScraperParsingError

# Get a logger for this module
logger = get_logger(__name__)

class NewsAPIScraper(BaseScraper):
    """NewsAPI-based scraper implementation"""
    
    def __init__(self):
        super().__init__(NEWSAPI_CONFIG["name"], NEWSAPI_CONFIG["base_url"])
        self.config = NEWSAPI_CONFIG
        self.monitored_locations = MONITORED_LOCATIONS
        self.api_key = self.config["api_key"]
        self.session = requests.Session()
    
    def search_articles(self, query: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
        """
        Search for articles using the NewsAPI
        
        Parameters:
        -----------
        query : str
            Search query string
        from_date : Optional[str]
            Start date for search (YYYY-MM-DD format)
        to_date : Optional[str]
            End date for search (YYYY-MM-DD format)
            
        Returns:
        --------
        Dict
            JSON response from the API
        """
        # Default to last 30 days if no date range specified
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
            
        # Build endpoint and params
        endpoint = f"{self.url}everything"
        params = self.config["default_params"].copy()
        params.update({
            "q": query,
            "from": from_date,
            "to": to_date,
            "apiKey": self.api_key
        })
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Searching NewsAPI for: {query} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(endpoint, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "ok":
                        logger.info(f"Found {data.get('totalResults', 0)} results for query: {query}")
                        return data
                    else:
                        error_message = data.get("message", "Unknown API error")
                        logger.error(f"API error: {error_message}")
                        raise ScraperNetworkError(f"NewsAPI error: {error_message}")
                
                elif response.status_code == 429:
                    # Rate limit exceeded
                    logger.warning("API rate limit exceeded. Waiting before retry.")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
                else:
                    logger.error(f"API request failed with status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    raise ScraperNetworkError(f"NewsAPI request failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise ScraperNetworkError(f"Failed to connect to NewsAPI: {str(e)}")
                
        return {"status": "error", "articles": []}
    
    def process_article(self, article_data: Dict) -> Optional[Dict]:
        """
        Process a single article from NewsAPI response
        
        Parameters:
        -----------
        article_data : Dict
            Article data from NewsAPI
            
        Returns:
        --------
        Optional[Dict]
            Processed article data or None if not relevant
        """
        try:
            # Extract basic info
            title = article_data.get("title", "")
            description = article_data.get("description", "")
            content = article_data.get("content", "")
            url = article_data.get("url", "")
            date = article_data.get("publishedAt", "")
            source_name = article_data.get("source", {}).get("name", self.name)
            
            # Combine text for analysis
            content_to_check = f"{title} {description} {content}".lower()
            
            # Extract keywords and check if business related
            keywords = extract_keywords(content_to_check)
            business_related = is_business_related(content_to_check)
            
            # If no theft keywords found or not business related, skip
            if not keywords or not business_related:
                return None
                
            # Detect location - ONLY keep articles in our target regions
            location = detect_location(content_to_check)
            if not location or location not in self.monitored_locations:
                # Only process articles from our monitored locations
                if location:
                    logger.debug(f"Article location '{location}' not in monitored locations")
                return None
                
            # Create article object
            return {
                "title": title,
                "url": url,
                "date": standardize_date(date),
                "excerpt": description if description else content[:200] + "...",
                "source": source_name,
                "keywords": keywords,
                "is_theft_related": True,
                "is_business_related": business_related,
                "store_type": self._detect_store_type(content_to_check)
            }
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None
            
    def _detect_store_type(self, content: str) -> str:
        """
        Detect the type of store mentioned in the content
        
        Parameters:
        -----------
        content : str
            Content to analyze
            
        Returns:
        --------
        str
            Detected store type or empty string if none detected
        """
        # Keywords for different store types
        store_types = {
            "Jewelry Store": ["jewelry store", "jeweler", "jewellers", "jewelers", "jewelry shop"],
            "Watch Store": ["watch store", "watch shop", "rolex dealer"],
            "Sports Memorabilia": ["sports memorabilia", "sports collectibles", "sports cards", "sports merchandise"],
            "Luxury Retail": ["luxury store", "luxury boutique", "high-end retail", "luxury goods"]
        }
        
        content = content.lower()
        
        # Check each store type
        for store_type, keywords in store_types.items():
            if any(keyword in content for keyword in keywords):
                return store_type
                
        # Default to jewelry store if no specific type detected but contains jewelry terms
        if any(term in content for term in ["jewelry", "jewellery", "diamond", "gold", "necklace", "bracelet"]):
            return "Jewelry Store"
            
        return "High-Value Retail"
    
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
        logger.info("Starting NewsAPI scraper...")
        
        # Dictionary to store articles by location
        location_articles = {}
        for location in self.monitored_locations:
            location_articles[location] = []
        
        # Also track unclassified articles
        location_articles["Other"] = []
        
        # Search for each term
        for search_term in self.config["search_terms"]:
            try:
                if self._stop_requested:
                    logger.info("Stopping scraper as requested")
                    break
                    
                # Search for articles
                response = self.search_articles(search_term)
                
                if response.get("status") != "ok":
                    logger.warning(f"Search failed for term: {search_term}")
                    continue
                
                articles = response.get("articles", [])
                logger.info(f"Processing {len(articles)} articles for search term: {search_term}")
                
                # Process each article
                for article_data in articles:
                    if self._stop_requested:
                        break
                        
                    processed_article = self.process_article(article_data)
                    
                    if processed_article:
                        location = detect_location(processed_article["title"] + " " + processed_article["excerpt"])
                        if location in location_articles:
                            location_articles[location].append(processed_article)
                        else:
                            location_articles["Other"].append(processed_article)
                
                # Add a small delay between searches to be nice to the API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching for term '{search_term}': {e}")
                continue
        
        # Log summary
        total_articles = sum(len(articles) for articles in location_articles.values())
        logger.info(f"NewsAPI scraper found {total_articles} relevant articles")
        
        return location_articles

def main():
    """Run the NewsAPI scraper directly"""
    import csv
    from src.utils.logger import get_logger, log_execution_time, get_dated_log_filename
    
    # Get a dedicated logger for the main function
    main_logger = get_logger("newsapi_scraper_main")
    
    @log_execution_time(main_logger, "NewsAPI Scraper: ")
    def run_scraper():
        scraper = NewsAPIScraper()
        return scraper.scrape()
    
    # Run the scraper with execution time logging
    main_logger.info("Starting NewsAPI scraper run")
    results = run_scraper()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'newsapi_articles_{timestamp}.csv')
    
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