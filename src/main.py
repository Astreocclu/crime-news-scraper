#!/usr/bin/env python
"""
Main entry point for the Crime News Scraper application.

This script orchestrates the entire workflow:
1. Runs the unified scraper to collect articles from configured sources
2. Processes the scraped articles through the analyzer
3. Generates analysis reports and summaries

Usage:
    python -m src.main [--no-scrape] [--no-analyze] [--input-file FILE]

Options:
    --no-scrape     Skip the scraping step and use existing data
    --no-analyze    Skip the analysis step
    --input-file    Specify an input CSV file for analysis (ignores scraping)
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from scrapers.unified import UnifiedScraper
from analyzer.claude_client import ClaudeClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('application.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Crime News Scraper')
    parser.add_argument('--no-scrape', action='store_true', help='Skip the scraping step')
    parser.add_argument('--no-analyze', action='store_true', help='Skip the analysis step')
    parser.add_argument('--input-file', type=str, help='Input CSV file for analysis')
    return parser.parse_args()

def run_scraper() -> Optional[str]:
    """Run the unified scraper to collect articles.
    
    Returns:
    --------
    Optional[str]
        Path to the generated CSV file, or None if scraping failed
    """
    try:
        logger.info("Starting the unified scraper...")
        scraper = UnifiedScraper()
        results = scraper.scrape_all(deep_check=False)
        
        # Find the most recent CSV file in the output directory
        output_dir = 'output'
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        if not csv_files:
            logger.error("No CSV files found in output directory")
            return None
            
        # Sort by modification time (most recent first)
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
        most_recent_csv = os.path.join(output_dir, csv_files[0])
        logger.info(f"Most recent CSV file: {most_recent_csv}")
        return most_recent_csv
        
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        return None

def run_analyzer(input_file: str):
    """Run the analyzer on the input file.
    
    Parameters:
    -----------
    input_file : str
        Path to the input CSV file
    """
    try:
        logger.info(f"Starting analyzer with input file: {input_file}")
        
        # Load API key from environment variable
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            return
            
        # Import analyzer module dynamically to avoid circular imports
        from analyzer.test_analyzer_single_batch2 import TestAnalyzerSingleBatch
        
        # Initialize and run the analyzer
        analyzer = TestAnalyzerSingleBatch()
        success = analyzer.process_single_batch(input_file)
        
        if success:
            logger.info("Analysis completed successfully")
        else:
            logger.error("Analysis failed")
            
    except Exception as e:
        logger.error(f"Error running analyzer: {e}")

def main():
    """Main entry point for the application."""
    try:
        start_time = time.time()
        logger.info("Starting Crime News Scraper application")
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # Determine input file
        input_file = None
        if args.input_file:
            input_file = args.input_file
            logger.info(f"Using specified input file: {input_file}")
        elif not args.no_scrape:
            logger.info("Running scraper to collect articles")
            input_file = run_scraper()
            if not input_file:
                logger.error("Scraping failed, no input file available for analysis")
                return
        else:
            logger.error("No input file specified and scraping is disabled")
            return
        
        # Run analyzer if not disabled
        if not args.no_analyze:
            logger.info("Running analyzer")
            run_analyzer(input_file)
        else:
            logger.info("Analysis step skipped")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Application completed in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        
if __name__ == "__main__":
    main()