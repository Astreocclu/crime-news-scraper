"""Unified scraper that orchestrates different scraper modules."""

import logging
import os
import csv
from datetime import datetime
from typing import Dict, List
from .jsa.scraper import JSAScraper
from .wfaa.scraper import WFAAScraper
from .reviewjournal.scraper import ReviewJournalScraper
from .eightnews.scraper import EightNewsScraper
from .nevadacurrent.scraper import NevadaCurrentScraper
from .newsapi.scraper import NewsAPIScraper
from ..database import get_db_connection

logger = logging.getLogger(__name__)

class UnifiedScraper:
    """Main orchestrator for all scrapers"""
    
    def __init__(self):
        self.scrapers = {
            "jsa": JSAScraper(),
            "wfaa": WFAAScraper(),
            "reviewjournal": ReviewJournalScraper(),
            "eightnews": EightNewsScraper(),
            "nevadacurrent": NevadaCurrentScraper(),
            "newsapi": NewsAPIScraper()
        }
    
    def scrape_all(self, deep_check: bool = True, max_deep_check: int = 20) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Run all configured scrapers
        
        Parameters:
        -----------
        deep_check : bool
            Whether to perform deep checking
        max_deep_check : int
            Maximum number of articles to deep check
            
        Returns:
        --------
        Dict[str, Dict[str, List[Dict]]]
            Dictionary with scraper names as keys and their results as values
        """
        results = {}
        
        for name, scraper in self.scrapers.items():
            logger.info(f"Starting {name} scraper...")
            try:
                results[name] = scraper.scrape(deep_check=deep_check, max_deep_check=max_deep_check)
            except Exception as e:
                logger.error(f"Error in {name} scraper: {e}")
                results[name] = {}
        
        # Save results to CSV files
        self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict[str, Dict[str, List[Dict]]]):
        """Save results to the SQLite database."""
        # Create output directory if it doesn't exist (for logs/other files)
        os.makedirs('output', exist_ok=True)
        
        # Generate timestamp for records
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Track number of articles saved for logging
        articles_saved = 0
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for scraper_name, location_articles in results.items():
                    if not location_articles:
                        continue
                    
                    for location, articles in location_articles.items():
                        for article in articles:
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
                            articles_saved += 1
                
                # Commit all insertions at once
                conn.commit()
                
            logger.info(f"Saved {articles_saved} articles to database")
            
            # Also save to CSV for backward compatibility - can be removed later
            self._save_results_to_csv(results)
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            # Fall back to CSV in case of database error
            self._save_results_to_csv(results)
            
    def _save_results_to_csv(self, results: Dict[str, Dict[str, List[Dict]]]):
        """Legacy method to save results to CSV files."""
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for scraper_name, location_articles in results.items():
            if not location_articles:
                continue
                
            # Create CSV file for this scraper
            output_file = f'output/{scraper_name}_articles_{timestamp}.csv'
            
            # Write results to CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'location', 'title', 'date', 'url', 'excerpt',
                    'source', 'keywords', 'is_theft_related', 'is_business_related',
                    'store_type', 'business_name', 'detailed_location'
                ])
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
            
            logger.info(f"Results also saved to CSV: {output_file}")

def main():
    """Main function to run the unified scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scraper = UnifiedScraper()
    results = scraper.scrape_all(deep_check=False)
    
    # Print results
    for scraper_name, location_articles in results.items():
        print(f"\nResults from {scraper_name}:")
        for location, articles in location_articles.items():
            print(f"\n{location}:")
            for article in articles:
                print(f"- {article['title']} ({article['date']})")
                print(f"  URL: {article['url']}")
                print(f"  Keywords: {', '.join(article['keywords'])}")

if __name__ == "__main__":
    main() 