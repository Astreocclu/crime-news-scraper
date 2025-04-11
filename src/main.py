#!/usr/bin/env python
"""
Main entry point for the Crime News Scraper application.

This script orchestrates the entire workflow:
1. Runs the unified scraper to collect articles from configured sources
2. Processes the scraped articles through the analyzer
3. Generates analysis reports and summaries

Usage:
    python -m src.main [--no-scrape] [--no-analyze] [--input-file FILE] [--batch-size SIZE]

Options:
    --no-scrape     Skip the scraping step and use existing data
    --no-analyze    Skip the analysis step
    --input-file    Specify an input CSV file for analysis (ignores scraping)
    --batch-size    Number of articles to process in one batch (default: 10)
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from src.scrapers.unified import UnifiedScraper
from src.analyzer.claude_client import ClaudeClient
from src.database import initialize_database

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
    parser.add_argument('--batch-size', type=int, default=10, help='Number of articles to process in one batch')
    parser.add_argument('--use-database', action='store_true', help='Use database for storage instead of CSV files')
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

def run_analyzer(input_file: Optional[str] = None, batch_size: int = 10, use_database: bool = False):
    """
    Run the analyzer on articles.

    Parameters:
    -----------
    input_file : Optional[str]
        Path to the input CSV file, or None to use database
    batch_size : int
        Number of articles to process in one batch
    use_database : bool
        Whether to use the database for reading articles
    """
    try:
        if input_file:
            logger.info(f"Starting analyzer with input file: {input_file}")
        else:
            logger.info(f"Starting analyzer with database (batch size: {batch_size})")

        # Load API key from environment variable
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            return

        # Import analyzer module dynamically to avoid circular imports
        from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer

        # Initialize and run the analyzer
        # SingleBatchAnalyzer now loads API key from environment variables
        analyzer = SingleBatchAnalyzer()

        # If using database, pass None as input_file
        file_arg = None if use_database else input_file
        success = analyzer.process_single_batch(file_arg, batch_size=batch_size)

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

        # Initialize the database
        initialize_database()
        logger.info("Database initialized")

        # Determine if we're using CSV or database mode
        use_database = args.use_database

        # Handle scraping step
        input_file = None
        if args.input_file:
            input_file = args.input_file
            logger.info(f"Using specified input file: {input_file}")
            use_database = False  # Override to use CSV if input file is specified
        elif not args.no_scrape:
            logger.info("Running scraper to collect articles")
            # If using database, we don't need the returned CSV file
            input_file = run_scraper()
            if not input_file and not use_database:
                logger.error("Scraping failed, no input file available for analysis")
                return
        elif not use_database:
            logger.error("No input file specified and scraping is disabled (in CSV mode)")
            return

        # Run analyzer if not disabled
        if not args.no_analyze:
            logger.info("Running analyzer")
            batch_size = args.batch_size
            run_analyzer(input_file, batch_size, use_database)
        else:
            logger.info("Analysis step skipped")

        elapsed_time = time.time() - start_time
        logger.info(f"Application completed in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")

if __name__ == "__main__":
    main()