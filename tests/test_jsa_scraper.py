"""Test script for the JSA scraper."""

import logging
import sys
from src.scrapers.jsa.scraper import JSAScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('output/jsa_scraper.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        # Run the scraper with deep_check=False
        logger.info("Starting JSA scraper test (headlines only)...")
        scraper = JSAScraper()
        articles = scraper.scrape(deep_check=False, max_deep_check=0)
        
        # Print results
        if articles:
            print("\nResults by location:")
            total_articles = 0
            for location, location_articles in articles.items():
                if location_articles:
                    total_articles += len(location_articles)
                    print(f"\n=== {location} ({len(location_articles)} articles) ===")
                    for article in location_articles:
                        print(f"\nTitle: {article['title']}")
                        print(f"URL: {article['url']}")
                        print(f"Date: {article['date']}")
                        print(f"Keywords: {', '.join(article['keywords'])}")
                        print("-" * 80)
            print(f"\nTotal articles found: {total_articles}")
        else:
            logger.warning("No articles found")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 