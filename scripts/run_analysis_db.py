#!/usr/bin/env python
"""
Run analysis on unanalyzed articles from the database and save results back to the database.

This script fetches unanalyzed articles from the database, performs analysis using the LLM,
and saves the structured results back into the analysis_results table.

Usage:
    python run_analysis_db.py [--batch-size SIZE]

Options:
    --batch-size    Number of articles to process in one batch (default: 10)
"""

import argparse
import logging
import os
import sys
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# Import database functions
from src.database import initialize_database, get_db_connection
from src.analyzer.analyzer import get_unanalyzed_articles, save_analysis_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyzer_db.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run analyzer on unanalyzed articles from the database')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of articles to process in one batch')
    return parser.parse_args()

def create_analysis_prompt(article):
    """Create a prompt for analyzing a single article."""
    # Handle keywords as a comma-separated string
    keywords = article.get('keywords', '')
    keywords_str = keywords if keywords else 'None'

    # Get excerpt
    excerpt = article.get('excerpt', 'No excerpt available')

    prompt = f"""
    Please analyze this crime article and extract key information:

    Title: {article.get('title', '')}
    Location: {article.get('location', '')}
    Date: {article.get('date', 'Not available')}
    Keywords: {keywords_str}
    Excerpt: {excerpt}
    Source: {article.get('source', '')}
    Is Theft Related: {article.get('is_theft_related', '')}
    Is Business Related: {article.get('is_business_related', '')}

    Please provide:
    1. Type of crime (e.g., robbery, burglary, theft)
    2. Method used (e.g., smash and grab, armed robbery)
    3. Target (e.g., jewelry store, individual)
    4. Store type (e.g., retail jewelry store, pawn shop, luxury boutique)
    5. Business name of the victimized store
    6. Detailed location information (address, city, state, landmarks)
    7. Estimated value of items (if mentioned)
    8. Number of suspects involved
    9. Any unique characteristics or patterns
    10. Date of the incident (if mentioned in the article or can be inferred)
    11. Date of article (when the article was published)
    12. A brief summary of the incident
    13. Lead quality score (1-10) based on:
        - Value score (1-5): Higher for more valuable items
        - Recency score (1-5): Higher for more recent incidents
    14. Method of entry used by criminals

    Format the response as a JSON object with these fields:
    {{
        "crimeType": "type of crime",
        "method": "method used",
        "target": "target of the crime",
        "storeType": "type of store",
        "businessName": "name of the business",
        "detailedLocation": "detailed location information",
        "estimatedValue": "estimated value",
        "numSuspects": "number of suspects",
        "characteristics": "unique characteristics",
        "incidentDate": "date of the incident",
        "dateOfArticle": "when the article was published",
        "summary": "brief summary of the incident",
        "valueScore": "score from 1-5 based on value",
        "recencyScore": "score from 1-5 based on recency",
        "totalScore": "total score from 1-10",
        "entryMethod": "method used to enter premises"
    }}
    """
    return prompt

def extract_json_from_response(response_text):
    """Extract JSON from the LLM response."""
    # Try different patterns to extract JSON
    for pattern in [r'```json\s*({.*?})\s*```', r'{.*}']:
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
    return None

def analyze_articles_from_db(batch_size=10):
    """
    Fetch unanalyzed articles from the database, perform analysis, and save results.
    
    Parameters:
    -----------
    batch_size : int, optional
        Number of articles to process in one batch (default: 10)
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        # Step 1.1: Initialize Database
        logger.info("Initializing database...")
        if not initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        # Step 1.2: Connect to Database
        logger.info("Connecting to database...")
        db_conn = get_db_connection()
        if not db_conn:
            logger.error("Failed to connect to database")
            return False
        
        try:
            # Step 1.3: Fetch Unanalyzed Articles
            logger.info(f"Fetching up to {batch_size} unanalyzed articles...")
            articles = get_unanalyzed_articles(db_conn, limit=batch_size)
            
            if not articles:
                logger.info("No unanalyzed articles found in the database")
                return True
            
            logger.info(f"Found {len(articles)} unanalyzed articles")
            
            # Load API key from environment variable
            load_dotenv()
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.error("ANTHROPIC_API_KEY environment variable not set")
                return False
            
            # Initialize Claude client
            client = anthropic.Anthropic(api_key=api_key)
            
            # Step 1.4: Perform Analysis on Articles
            results = []
            for idx, article in enumerate(articles):
                try:
                    logger.info(f"\nAnalyzing article {idx + 1}/{len(articles)}: {article['title']}")
                    
                    # Create the analysis prompt
                    prompt = create_analysis_prompt(article)
                    
                    # Get analysis from Claude
                    try:
                        response = client.messages.create(
                            model="claude-3-7-sonnet-20250219",
                            max_tokens=4000,
                            temperature=0.7,
                            messages=[{"role": "user", "content": prompt}],
                            timeout=30  # 30 second timeout
                        )
                        
                        # Extract the analysis
                        analysis_text = response.content[0].text
                        logger.info(f"Received response from Claude")
                        
                        # Extract JSON from the response
                        analysis = extract_json_from_response(analysis_text)
                        
                        if analysis:
                            # Add article ID and timestamp
                            analysis['article_id'] = article['id']
                            analysis['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            results.append(analysis)
                            logger.info(f"Successfully analyzed article {idx + 1}")
                        else:
                            logger.warning(f"Could not extract JSON from Claude response for article {idx + 1}")
                            
                    except Exception as e:
                        logger.error(f"Error calling Claude API for article {idx + 1}: {str(e)}")
                        
                except Exception as e:
                    logger.error(f"Error processing article {idx + 1}: {str(e)}")
            
            # Step 1.5: Save Analysis Results
            if results:
                logger.info(f"Saving {len(results)} analysis results to database...")
                if save_analysis_results(db_conn, results):
                    logger.info("Successfully saved analysis results to database")
                else:
                    logger.error("Failed to save analysis results to database")
                    return False
            else:
                logger.warning("No analysis results to save")
            
            return True
            
        finally:
            # Step 1.6: Close Database Connection
            if db_conn:
                db_conn.close()
                logger.info("Database connection closed")
    
    except Exception as e:
        logger.error(f"Error analyzing articles from database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point for the script."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Run the analyzer
        logger.info(f"Running analyzer on database with batch size {args.batch_size}")
        success = analyze_articles_from_db(args.batch_size)
        
        if success:
            logger.info("Analysis completed successfully")
        else:
            logger.error("Analysis failed")
            
    except Exception as e:
        logger.error(f"Error running analyzer: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
