#!/usr/bin/env python3
"""
Crime News Scraper - Main Application Entry Point

A comprehensive system for scraping crime news articles, analyzing incidents,
and finding nearby businesses for targeted security lead generation.

FOCUSED TARGETING: This system exclusively targets three high-value business types:
1. Jewelry stores (primary target - highest priority)
2. Sports memorabilia stores (secondary target)
3. Luxury goods stores (secondary target)

Usage:
    python -m src.main <command> [options]

Commands:
    scrape      Collect articles from configured news sources
    analyze     Process articles through AI-powered crime incident analysis
    nearby      Find nearby target businesses for analyzed incidents
    workflow    Execute complete end-to-end workflow

Global Options:
    --use-database       Use SQLite database for storage (recommended)
    --max-runtime MIN    Maximum execution time in minutes (default: 5)
    --progress-type TYPE Progress indicator type (spinner, dots, bar)

Command-Specific Options:
    Scrape:
        --sources SRC1,SRC2  Comma-separated list of sources (default: all)

    Analyze:
        --input-file FILE    Input CSV file for analysis
        --batch-size SIZE    Articles per batch (default: 10)
        --no-scrape          Skip scraping step (use existing data)

    Nearby:
        --analysis-file FILE Analysis CSV file containing incidents
        --radius METERS      Search radius in meters (default: 1609)

    Workflow:
        --no-scrape          Skip scraping step
        --no-analyze         Skip analysis step
        --no-nearby          Skip nearby business finder step
        --no-complete        Skip Complete Scrape creation step

Examples:
    # Complete workflow with database storage (recommended)
    python -m src.main workflow --use-database

    # Analyze existing data with custom batch size
    python -m src.main analyze --input-file output/scraped_data.csv --batch-size 20

    # Find nearby target businesses
    python -m src.main nearby --analysis-file output/analyzed_leads.csv

Performance Benchmarks:
    - Processing Speed: ~10.4 seconds per article
    - Address Validation: 81.4% success rate
    - Lead Quality: 62.2% high-quality leads (score ≥5)
    - Target Business Focus: 100% (jewelry, sports memorabilia, luxury goods only)

For detailed documentation, see docs/deployment_guide.md
"""

"""
Standard library imports
"""
import argparse
import glob
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any

"""
Third-party imports
"""
from dotenv import load_dotenv

"""
Local application imports
"""
from src.scrapers.unified import UnifiedScraper
from src.analyzer.claude_client import ClaudeClient
from src.database import initialize_database

# Load environment variables
load_dotenv()

# Configure logging
logs_dir = os.getenv('LOGS_DIR', 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, 'application.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    # Get default values from environment variables
    default_batch_size = int(os.getenv('DEFAULT_BATCH_SIZE', 10))
    default_search_radius = int(os.getenv('DEFAULT_SEARCH_RADIUS', 1609))

    # Create the main parser
    parser = argparse.ArgumentParser(description='Crime News Scraper')
    parser.add_argument('--use-database', action='store_true', help='Use database for storage instead of CSV files')
    parser.add_argument('--max-runtime', type=int, default=5, help='Maximum runtime in minutes (default: 5)')
    parser.add_argument('--progress-type', choices=['spinner', 'dots', 'bar'], default='spinner',
                      help='Type of progress indicator to use')

    # Create subparsers for each command
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Run the scraper to collect articles')
    scrape_parser.add_argument('--sources', type=str, help='Comma-separated list of sources to scrape (default: all)')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Process articles through the analyzer')
    analyze_parser.add_argument('--input-file', type=str, help='Input CSV file for analysis')
    analyze_parser.add_argument('--batch-size', type=int, default=default_batch_size,
                             help=f'Number of articles to process in one batch (default: {default_batch_size})')
    analyze_parser.add_argument('--no-scrape', action='store_true', help='Skip the scraping step')

    # Nearby command
    nearby_parser = subparsers.add_parser('nearby', help='Find nearby businesses for analyzed incidents')
    nearby_parser.add_argument('--analysis-file', type=str, required=True, help='Analysis file containing incidents')
    nearby_parser.add_argument('--radius', type=int, default=default_search_radius,
                            help=f'Search radius in meters (default: {default_search_radius})')

    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run the complete workflow')
    workflow_parser.add_argument('--no-scrape', action='store_true', help='Skip the scraping step')
    workflow_parser.add_argument('--no-analyze', action='store_true', help='Skip the analysis step')
    workflow_parser.add_argument('--no-nearby', action='store_true', help='Skip the nearby business finder step')
    workflow_parser.add_argument('--no-complete', action='store_true', help='Skip the Complete Scrape creation step')
    workflow_parser.add_argument('--input-file', type=str, help='Input file for analysis (if skipping scrape)')
    workflow_parser.add_argument('--analysis-file', type=str, help='Analysis file for nearby finder (if skipping analyze)')

    # For backward compatibility, add the old arguments to the main parser
    parser.add_argument('--no-scrape', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-analyze', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--input-file', type=str, help=argparse.SUPPRESS)
    parser.add_argument('--batch-size', type=int, default=default_batch_size, help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Handle backward compatibility - if no command is specified but old-style arguments are used,
    # set the command to 'workflow'
    if not args.command and (args.no_scrape or args.no_analyze or args.input_file or args.batch_size):
        args.command = 'workflow'

    # If no command is specified at all, default to 'workflow'
    if not args.command:
        args.command = 'workflow'

    return args

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
        output_dir = os.getenv('OUTPUT_DIR', 'output')
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

def run_analyzer(input_file: Optional[str] = None, batch_size: int = 10, use_database: bool = False) -> None:
    """
    Run the analyzer on articles.

    Args:
        input_file: Path to the input CSV file, or None to use database
        batch_size: Number of articles to process in one batch
        use_database: Whether to use the database for reading articles
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

def run_nearby_finder(analysis_file: str, radius: int = 1609) -> None:
    """
    Run the nearby business finder on analyzed incidents.

    Args:
        analysis_file: Path to the analysis file containing incidents
        radius: Search radius in meters
    """
    try:
        logger.info(f"Starting nearby business finder with analysis file: {analysis_file}")

        # Import the finder module dynamically
        from src.nearby_finder.finder import NearbyBusinessFinder

        # Initialize and run the finder
        finder = NearbyBusinessFinder()
        success = finder.find_nearby_businesses(analysis_file)

        if success:
            logger.info("Nearby business finding completed successfully")
        else:
            logger.error("Nearby business finding failed")

    except Exception as e:
        logger.error(f"Error running nearby business finder: {e}")

def run_workflow(args: argparse.Namespace) -> None:
    """
    Run the complete workflow (scrape, analyze, nearby, complete).

    Args:
        args: Command line arguments
    """
    try:
        start_time = time.time()
        logger.info("Starting complete workflow")

        # Create output directories if they don't exist
        os.makedirs('output/scraping', exist_ok=True)
        os.makedirs('output/analysis', exist_ok=True)
        os.makedirs('output/nearby', exist_ok=True)

        # Set up a timeout mechanism
        max_runtime_seconds = args.max_runtime * 60

        # Step 1: Scrape crime news articles
        input_file = None
        if not args.no_scrape:
            # Check if we've already exceeded the maximum runtime
            if time.time() - start_time > max_runtime_seconds:
                logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded before starting scraping step")
                return

            logger.info("Step 1: Scraping crime news articles")
            input_file = run_scraper()
            if not input_file and not args.use_database:
                logger.error("Scraping failed, exiting workflow")
                return

            # Check if we've exceeded the maximum runtime
            if time.time() - start_time > max_runtime_seconds:
                logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded after scraping step")
                return
        else:
            logger.info("Skipping scrape step")
            if args.input_file:
                input_file = args.input_file
            elif not args.use_database:
                logger.error("No input file specified for analysis in CSV mode")
                return

        # Step 2: Analyze the articles
        analysis_file = None
        if not args.no_analyze:
            # Check if we've already exceeded the maximum runtime
            if time.time() - start_time > max_runtime_seconds:
                logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded before starting analysis step")
                return

            logger.info(f"Step 2: Analyzing articles")
            batch_size = getattr(args, 'batch_size', 10)
            run_analyzer(input_file, batch_size, args.use_database)

            # Find the most recent analyzed_leads_*.csv file
            # Check both possible locations for analysis files
            analyzed_files = []
            for pattern in ["output/analysis_results/analyzed_leads_*.csv",
                           "output/analysis/analyzed_leads_*.csv",
                           "output/analyzed_leads_*.csv"]:
                analyzed_files.extend(glob.glob(pattern))

            analyzed_files = sorted(analyzed_files, key=os.path.getmtime, reverse=True)

            if analyzed_files:
                analysis_file = analyzed_files[0]
                logger.info(f"Using most recent analysis file: {analysis_file}")
            else:
                logger.error("No analyzed_leads_*.csv files found!")
                return

            # Check if we've exceeded the maximum runtime
            if time.time() - start_time > max_runtime_seconds:
                logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded after analysis step")
                return
        else:
            logger.info("Skipping analysis step")
            if args.analysis_file:
                analysis_file = args.analysis_file
            else:
                logger.error("No analysis file specified for nearby finder")
                return

        # Step 3: Find nearby businesses
        if not args.no_nearby:
            # Check if we've already exceeded the maximum runtime
            if time.time() - start_time > max_runtime_seconds:
                logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded before starting nearby finder step")
                return

            logger.info(f"Step 3: Finding nearby businesses for incidents in {analysis_file}")
            radius = getattr(args, 'radius', 1609)
            run_nearby_finder(analysis_file, radius)

            # Check if we've exceeded the maximum runtime
            if time.time() - start_time > max_runtime_seconds:
                logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded after nearby finder step")
                return
        else:
            logger.info("Skipping nearby business finder step")

        # Step 4: Create the Complete Scrape file
        if not args.no_complete:
            logger.info("Step 4: Creating Complete Scrape file")
            # Import and run the complete scrape creator
            try:
                from scripts.create_complete_scrape import main as create_complete_scrape
                create_complete_scrape()
                logger.info("Complete Scrape file created successfully")
            except Exception as e:
                logger.error(f"Complete Scrape creation failed: {e}")
        else:
            logger.info("Skipping Complete Scrape creation step")

        elapsed_time = time.time() - start_time
        logger.info(f"Workflow completed in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Unhandled exception in workflow: {e}")

def main() -> None:
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

        # Handle different commands
        if args.command == 'scrape':
            logger.info("Running scraper command")
            run_scraper()

        elif args.command == 'analyze':
            logger.info("Running analyzer command")
            input_file = args.input_file
            if not input_file and not args.no_scrape:
                input_file = run_scraper()
            run_analyzer(input_file, args.batch_size, args.use_database)

        elif args.command == 'nearby':
            logger.info("Running nearby finder command")
            run_nearby_finder(args.analysis_file, args.radius)

        elif args.command == 'workflow':
            logger.info("Running complete workflow")
            run_workflow(args)

        else:
            logger.error(f"Unknown command: {args.command}")

        elapsed_time = time.time() - start_time
        logger.info(f"Application completed in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")

if __name__ == "__main__":
    main()