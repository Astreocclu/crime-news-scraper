"""Unified scraper that orchestrates different scraper modules."""

import logging
import os
import csv
from datetime import datetime
from typing import Dict, List
from .jsa.scraper import JSAScraper

logger = logging.getLogger(__name__)

class UnifiedScraper:
    """Main orchestrator for all scrapers"""
    
    def __init__(self):
        self.scrapers = {
            "jsa": JSAScraper()
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
        """Save results to CSV files."""
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
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
            
            logger.info(f"Results saved to {output_file}")

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