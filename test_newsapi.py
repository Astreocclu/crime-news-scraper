"""Test script to run NewsAPI scraper for jewelry store break-ins in Las Vegas."""

import os
import csv
from datetime import datetime, timedelta
from src.scrapers.newsapi.scraper import NewsAPIScraper
from src.scrapers.newsapi.utils import detect_location
from src.utils.logger import get_logger

# Configure logging
logger = get_logger('newsapi_test')

def run_custom_newsapi_search():
    """Run a custom NewsAPI search for Las Vegas jewelry store break-ins in the last year."""
    
    # Create scraper instance
    scraper = NewsAPIScraper()
    
    # Set up date range for the last month (free tier limitation)
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = '2025-03-02'  # One day after the API limit to avoid errors
    
    print(f"Searching for news from {from_date} to {to_date}")
    
    # Search for theft at specific store types in our target states
    custom_query = '(Nevada OR California OR Arizona OR Texas OR "Las Vegas" OR "Los Angeles" OR "San Francisco" OR "Phoenix" OR "Dallas" OR "Houston" OR "Austin") AND ("jewelry store" OR jeweler OR "luxury store" OR "sports memorabilia" OR "watch store" OR "high-end retail") AND (theft OR robbery OR burglary OR "smash and grab" OR heist OR stolen)'
    
    response = scraper.search_articles(custom_query, from_date, to_date)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'output/target_states_luxury_theft_{timestamp}.csv'
    
    # Process results
    articles = response.get('articles', [])
    processed_articles = []
    
    print(f"Found {len(articles)} articles matching the search criteria")
    
    for article in articles:
        processed = scraper.process_article(article)
        if processed:
            processed_articles.append(processed)
    
    print(f"Processed {len(processed_articles)} relevant articles")
    
    # Write results to CSV
    if processed_articles:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'title', 'date', 'url', 'excerpt', 'source', 
                'keywords', 'is_theft_related', 'is_business_related',
                'store_type', 'location'
            ])
            writer.writeheader()
            
            for article in processed_articles:
                # Get location from processed article
                content_check = article['title'] + ' ' + article['excerpt']
                location = detect_location(content_check)
                
                row = {
                    'title': article['title'],
                    'date': article['date'],
                    'url': article['url'],
                    'excerpt': article['excerpt'],
                    'source': article['source'],
                    'keywords': ','.join(article['keywords']),
                    'is_theft_related': article['is_theft_related'],
                    'is_business_related': article['is_business_related'],
                    'store_type': article.get('store_type', 'Jewelry Store'),
                    'location': location if location else 'Other'
                }
                writer.writerow(row)
        
        print(f"Results saved to {output_file}")
    else:
        print("No relevant articles found")
    
    return processed_articles

if __name__ == "__main__":
    articles = run_custom_newsapi_search()
    
    # Display article titles
    if articles:
        print("\nFound articles:")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']} ({article['date']})")
    else:
        print("No relevant articles found")