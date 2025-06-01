"""
Crime News Scraper - Unified Scraper Module

This module orchestrates multiple news source scrapers to collect crime-related
articles for targeted lead generation. It manages scraping from various sources
and stores results in both database and CSV formats.

The unified scraper coordinates:
- JSA (Jewelers Security Alliance) - Primary jewelry industry source
- WFAA - Dallas/Fort Worth news source
- Review Journal - Las Vegas news source
- 8News - Virginia news source
- Nevada Current - Nevada news source
- NewsAPI - General news aggregation

Author: Augment Agent
Version: 2.0.0
"""

"""
Standard library imports
"""
import logging
import os
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional

"""
Local application imports
"""
from .jsa.scraper import JSAScraper
from .wfaa.scraper import WFAAScraper
from .reviewjournal.scraper import ReviewJournalScraper
from .eightnews.scraper import EightNewsScraper
from .nevadacurrent.scraper import NevadaCurrentScraper
from .newsapi.scraper import NewsAPIScraper
from ..database import get_db_connection

logger = logging.getLogger(__name__)

class UnifiedScraper:
    """
    Main orchestrator for all news source scrapers.

    This class coordinates multiple scraper modules to collect crime-related
    articles from various news sources. It manages the scraping process,
    handles results aggregation, and stores data in both database and CSV formats.

    Supported News Sources:
        - JSA (Jewelers Security Alliance): Primary jewelry industry source
        - WFAA: Dallas/Fort Worth news source
        - Review Journal: Las Vegas news source
        - 8News: Virginia news source
        - Nevada Current: Nevada news source
        - NewsAPI: General news aggregation

    The scraper focuses on identifying incidents involving our three target
    business types: jewelry stores, sports memorabilia stores, and luxury goods stores.
    """

    def __init__(self) -> None:
        """Initialize the unified scraper with all configured scrapers."""
        self.scrapers = {
            "jsa": JSAScraper(),
            "wfaa": WFAAScraper(),
            "reviewjournal": ReviewJournalScraper(),
            "eightnews": EightNewsScraper(),
            "nevadacurrent": NevadaCurrentScraper(),
            "newsapi": NewsAPIScraper()
        }
    
    def scrape_all(self, deep_check: bool = True, max_deep_check: int = 20) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Run all configured scrapers to collect crime-related articles.

        Args:
            deep_check: Whether to perform deep content validation on articles
            max_deep_check: Maximum number of articles to deep check per scraper

        Returns:
            Dict containing scraper names as keys and their results as values.
            Structure: {scraper_name: {location: [articles]}}
        """
        results = {}

        for name, scraper in self.scrapers.items():
            logger.info(f"Starting {name} scraper...")
            try:
                results[name] = scraper.scrape(deep_check=deep_check, max_deep_check=max_deep_check)
            except Exception as e:
                logger.error(f"Error in {name} scraper: {e}")
                results[name] = {}

        # Save results to database and CSV files
        self._save_results(results)

        return results
    
    def _save_results(self, results: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> None:
        """
        Save scraping results to both database and CSV files.

        Args:
            results: Dictionary containing scraper results organized by scraper name and location
        """
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)

        # Try to save to database first
        database_success = self._save_to_database(results)

        # Always save to CSV for backward compatibility
        self._save_results_to_csv(results)

        if not database_success:
            logger.warning("Database save failed, but CSV backup was created")

    def _save_to_database(self, results: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> bool:
        """
        Save results to the SQLite database.

        Args:
            results: Dictionary containing scraper results

        Returns:
            bool: True if save was successful, False otherwise
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        articles_saved = 0

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                for scraper_name, location_articles in results.items():
                    if not location_articles:
                        continue

                    for location, articles in location_articles.items():
                        for article in articles:
                            success = self._insert_article(cursor, scraper_name, location, article, timestamp)
                            if success:
                                articles_saved += 1

                # Commit all insertions at once
                conn.commit()

            logger.info(f"Saved {articles_saved} articles to database")
            return True

        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False

    def _insert_article(self, cursor: Any, scraper_name: str, location: str,
                       article: Dict[str, Any], timestamp: str) -> bool:
        """
        Insert a single article into the database.

        Args:
            cursor: Database cursor
            scraper_name: Name of the scraper that found this article
            location: Location associated with the article
            article: Article data dictionary
            timestamp: Timestamp for the record

        Returns:
            bool: True if insertion was successful, False otherwise
        """
        try:
            # Convert boolean flags to integers for SQLite
            is_theft_related = 1 if article['is_theft_related'] else 0
            is_business_related = 1 if article['is_business_related'] else 0

            # Prepare article data for insertion
            article_data = (
                scraper_name,
                location,
                article['title'],
                article['date'],  # Should be in ISO format YYYY-MM-DD
                article['url'],
                article['excerpt'],
                article['source'],
                ','.join(article['keywords']),
                is_theft_related,
                is_business_related,
                article.get('store_type', ''),
                article.get('business_name', ''),
                article.get('detailed_location', ''),
                timestamp
            )

            # SQL statement with OR IGNORE to handle duplicates based on URL
            sql = '''
            INSERT OR IGNORE INTO articles
            (scraper_name, location, title, article_date, url, excerpt,
             source, keywords, is_theft_related, is_business_related,
             store_type, business_name, detailed_location, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            cursor.execute(sql, article_data)
            return True

        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            return False
            
    def _save_results_to_csv(self, results: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> None:
        """
        Save results to CSV files for backward compatibility.

        Args:
            results: Dictionary containing scraper results
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for scraper_name, location_articles in results.items():
            if not location_articles:
                continue

            # Create CSV file for this scraper
            output_file = f'output/{scraper_name}_articles_{timestamp}.csv'

            try:
                self._write_csv_file(output_file, location_articles)
                logger.info(f"Results saved to CSV: {output_file}")
            except Exception as e:
                logger.error(f"Error saving CSV file {output_file}: {e}")

    def _write_csv_file(self, output_file: str, location_articles: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Write articles to a CSV file.

        Args:
            output_file: Path to the output CSV file
            location_articles: Dictionary of articles organized by location
        """
        fieldnames = [
            'location', 'title', 'date', 'url', 'excerpt',
            'source', 'keywords', 'is_theft_related', 'is_business_related',
            'store_type', 'business_name', 'detailed_location'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for location, articles in location_articles.items():
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
                        'store_type': article.get('store_type', ''),
                        'business_name': article.get('business_name', ''),
                        'detailed_location': article.get('detailed_location', '')
                    }
                    writer.writerow(row)

def main() -> None:
    """
    Main function to run the unified scraper.

    Configures logging, initializes the unified scraper, runs all scrapers,
    and displays a summary of results.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Crime News Scraper - Unified Mode")

    try:
        # Initialize and run the unified scraper
        scraper = UnifiedScraper()
        results = scraper.scrape_all(deep_check=False)

        # Display results summary
        _display_results_summary(results)

        logger.info("Unified scraping completed successfully")

    except Exception as e:
        logger.error(f"Error in unified scraper: {e}")
        raise


def _display_results_summary(results: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> None:
    """
    Display a summary of scraping results.

    Args:
        results: Dictionary containing scraper results
    """
    total_articles = 0

    for scraper_name, location_articles in results.items():
        scraper_total = sum(len(articles) for articles in location_articles.values())
        total_articles += scraper_total

        print(f"\n📰 Results from {scraper_name}: {scraper_total} articles")

        for location, articles in location_articles.items():
            if articles:  # Only show locations with articles
                print(f"\n  📍 {location} ({len(articles)} articles):")
                for article in articles[:3]:  # Show first 3 articles
                    print(f"    • {article['title']} ({article['date']})")
                    print(f"      🔗 {article['url']}")
                    if article['keywords']:
                        print(f"      🏷️  Keywords: {', '.join(article['keywords'])}")

                if len(articles) > 3:
                    print(f"    ... and {len(articles) - 3} more articles")

    print(f"\n🎯 Total articles collected: {total_articles}")
    print("📊 Results saved to database and CSV files in output/ directory")


if __name__ == "__main__":
    main()