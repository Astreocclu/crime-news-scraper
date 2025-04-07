"""Test script to run the Review Journal scraper specifically for jewelry theft incidents."""

import os
import csv
from datetime import datetime
from src.scrapers.reviewjournal.scraper import ReviewJournalScraper
from src.utils.logger import get_logger

# Configure logging
logger = get_logger('reviewjournal_test')

def run_reviewjournal_scraper():
    """Run the Review Journal scraper and filter for jewelry and luxury store thefts."""
    
    logger.info("Starting Review Journal scraper test")
    
    # Create scraper instance
    scraper = ReviewJournalScraper()
    
    # Run the scraper
    results = scraper.scrape()
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'output/reviewjournal_jewelry_theft_{timestamp}.csv'
    
    # Post-process results to further filter for jewelry and luxury store thefts
    jewelry_theft_articles = []
    
    for location, articles in results.items():
        for article in articles:
            # Check for jewelry or luxury store keywords
            title_and_excerpt = (article['title'] + ' ' + article['excerpt']).lower()
            
            # Look for jewelry or luxury store related keywords
            jewelry_keywords = ['jewelry', 'jeweler', 'jewellery', 'diamond', 'gold', 'silver', 
                               'watch', 'rolex', 'luxury', 'high-end', 'boutique']
            
            # Check if any jewelry keywords are in the title or excerpt
            is_jewelry_related = any(keyword in title_and_excerpt for keyword in jewelry_keywords)
            
            # Only keep articles that are theft-related, business-related, and jewelry-related
            if article['is_theft_related'] and article['is_business_related'] and is_jewelry_related:
                jewelry_theft_articles.append(article)
    
    # Write filtered results to CSV
    if jewelry_theft_articles:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'location', 'title', 'date', 'url', 'excerpt',
                'source', 'keywords', 'is_theft_related', 'is_business_related',
                'detailed_location'
            ])
            writer.writeheader()
            
            for article in jewelry_theft_articles:
                row = {
                    'location': 'Nevada',  # Review Journal is Nevada-focused
                    'title': article['title'],
                    'date': article['date'],
                    'url': article['url'],
                    'excerpt': article['excerpt'],
                    'source': article['source'],
                    'keywords': ','.join(article['keywords']),
                    'is_theft_related': article['is_theft_related'],
                    'is_business_related': article['is_business_related'],
                    'detailed_location': article.get('detailed_location', 'Las Vegas area')
                }
                writer.writerow(row)
        
        print(f"Results saved to {output_file}")
        print(f"Found {len(jewelry_theft_articles)} jewelry/luxury theft articles")
    else:
        print("No jewelry or luxury theft articles found")
    
    return jewelry_theft_articles

if __name__ == "__main__":
    articles = run_reviewjournal_scraper()
    
    # Display article titles
    if articles:
        print("\nFound articles:")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']} ({article['date']})")
    else:
        print("No relevant articles found")