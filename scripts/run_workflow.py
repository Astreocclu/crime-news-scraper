#!/usr/bin/env python3
"""
Run the complete crime news scraper workflow.

This script runs the complete workflow:
1. Scrape crime news articles
2. Analyze the articles to identify victim businesses
3. Find nearby businesses in target industries
4. Generate a CSV with qualified leads
"""
import os
import sys
import argparse
import subprocess
import datetime
import logging
import glob
import pandas as pd
import time
import threading
import itertools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('workflow')

class ProgressIndicator:
    """A simple progress indicator that shows activity while a process is running."""

    def __init__(self, description, indicator_type='spinner'):
        """Initialize the progress indicator.

        Args:
            description: Description of the process being run
            indicator_type: Type of indicator ('spinner', 'dots', or 'bar')
        """
        self.description = description
        self.indicator_type = indicator_type
        self.is_running = False
        self.thread = None
        self.start_time = None
        self.counter = 0

    def _spinner_task(self):
        """Display a spinner, elapsed time, and description."""
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.start_time = time.time()

        while self.is_running:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            timestr = f"{mins:02d}:{secs:02d}"

            sys.stdout.write(f"\r{next(spinner)} {self.description} (elapsed: {timestr}) ")
            sys.stdout.flush()
            time.sleep(0.1)

        # Clear the line when done
        sys.stdout.write("\r" + " " * (len(self.description) + 30) + "\r")
        sys.stdout.flush()

    def _dots_task(self):
        """Display dots and elapsed time."""
        self.start_time = time.time()

        while self.is_running:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            timestr = f"{mins:02d}:{secs:02d}"

            self.counter += 1
            dots = "." * (self.counter % 4)
            sys.stdout.write(f"\r{self.description}{dots.ljust(4)} (elapsed: {timestr}) ")
            sys.stdout.flush()
            time.sleep(1.0)

        # Clear the line when done
        sys.stdout.write("\r" + " " * (len(self.description) + 30) + "\r")
        sys.stdout.flush()

    def _bar_task(self):
        """Display a simple animated bar and elapsed time."""
        self.start_time = time.time()
        bar_length = 20

        while self.is_running:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            timestr = f"{mins:02d}:{secs:02d}"

            # Animate the bar
            pos = self.counter % (bar_length * 2)
            if pos > bar_length:
                pos = bar_length * 2 - pos

            bar = "█" * pos + "░" * (bar_length - pos)
            sys.stdout.write(f"\r{self.description} [{bar}] (elapsed: {timestr}) ")
            sys.stdout.flush()

            self.counter += 1
            time.sleep(0.1)

        # Clear the line when done
        sys.stdout.write("\r" + " " * (len(self.description) + bar_length + 30) + "\r")
        sys.stdout.flush()

    def start(self):
        """Start the progress indicator."""
        self.is_running = True

        if self.indicator_type == 'spinner':
            self.thread = threading.Thread(target=self._spinner_task)
        elif self.indicator_type == 'dots':
            self.thread = threading.Thread(target=self._dots_task)
        else:  # default to bar
            self.thread = threading.Thread(target=self._bar_task)

        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the progress indicator."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

        # Calculate and return elapsed time
        if self.start_time:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            return f"{mins:02d}:{secs:02d}"
        return "00:00"

# Global variable to store the progress indicator type
progress_indicator_type = 'spinner'

def run_command(command, description):
    """Run a command and log the output with a progress indicator."""
    logger.info(f"Running {description}...")

    # Start progress indicator
    progress = ProgressIndicator(f"Running {description}", indicator_type=progress_indicator_type)
    progress.start()

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        elapsed = progress.stop()
        logger.info(f"{description} completed successfully in {elapsed}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        elapsed = progress.stop()
        logger.error(f"{description} failed after {elapsed}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None

def main():
    """Run the complete workflow."""
    parser = argparse.ArgumentParser(description='Run the complete crime news scraper workflow')
    parser.add_argument('--no-scrape', action='store_true', help='Skip the scraping step')
    parser.add_argument('--no-analyze', action='store_true', help='Skip the analysis step')
    parser.add_argument('--no-nearby', action='store_true', help='Skip the nearby business finder step')
    parser.add_argument('--no-complete', action='store_true', help='Skip the Complete Scrape creation step')
    parser.add_argument('--input-file', help='Input file for analysis (if skipping scrape)')
    parser.add_argument('--analysis-file', help='Analysis file for nearby finder (if skipping analyze)')
    parser.add_argument('--progress-type', choices=['spinner', 'dots', 'bar'], default='spinner',
                      help='Type of progress indicator to use')
    parser.add_argument('--max-runtime', type=int, default=5,
                      help='Maximum runtime in minutes (default: 5)')
    args = parser.parse_args()

    # Set the global progress indicator type
    global progress_indicator_type
    progress_indicator_type = args.progress_type

    # Create timestamp for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting workflow at {timestamp}")
    print(f"\nStarting workflow with {args.progress_type} progress indicator...")
    print(f"Maximum runtime set to {args.max_runtime} minutes\n")

    # Create an overall progress indicator for the workflow
    overall_progress = ProgressIndicator("Overall workflow progress", indicator_type='bar')
    overall_progress.start()

    # Set up a timeout mechanism
    start_time = time.time()
    max_runtime_seconds = args.max_runtime * 60

    # Step 1: Scrape crime news articles
    if not args.no_scrape:
        # Check if we've already exceeded the maximum runtime
        if time.time() - start_time > max_runtime_seconds:
            logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded before starting scraping step")
            print(f"\nMaximum runtime of {args.max_runtime} minutes exceeded before starting scraping step\n")
            overall_progress.stop()
            return 0

        logger.info("Step 1: Scraping crime news articles")
        scrape_output = run_command(
            ["python3", "-m", "src.main", "--no-analyze"],
            "Scraper"
        )
        if not scrape_output:
            logger.error("Scraping failed, exiting workflow")
            overall_progress.stop()
            return 1

        # Find the most recent JSA articles file
        import glob
        jsa_files = sorted(glob.glob("output/jsa_articles_*.csv"), key=os.path.getmtime, reverse=True)
        if not jsa_files:
            logger.error("No JSA articles files found!")
            overall_progress.stop()
            return 1
        input_file = jsa_files[0]
        logger.info(f"Using most recent JSA file: {input_file}")

        # Check if we've exceeded the maximum runtime
        if time.time() - start_time > max_runtime_seconds:
            logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded after scraping step")
            print(f"\nMaximum runtime of {args.max_runtime} minutes exceeded after scraping step\n")
            overall_progress.stop()
            return 0
    else:
        logger.info("Skipping scrape step")
        if args.input_file:
            input_file = args.input_file
        else:
            logger.error("No input file specified for analysis")
            overall_progress.stop()
            return 1

    # Step 2: Analyze the articles
    if not args.no_analyze:
        # Check if we've already exceeded the maximum runtime
        if time.time() - start_time > max_runtime_seconds:
            logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded before starting analysis step")
            print(f"\nMaximum runtime of {args.max_runtime} minutes exceeded before starting analysis step\n")
            overall_progress.stop()
            return 0

        logger.info(f"Step 2: Analyzing articles from {input_file}")
        analyze_output = run_command(
            ["python3", "-m", "src.main", "--no-scrape", "--input-file", input_file],
            "Analyzer"
        )
        if not analyze_output:
            logger.error("Analysis failed, exiting workflow")
            overall_progress.stop()
            return 1

        # Find the most recent analyzed_leads_*.csv file
        # Look in both output/ and output/analyzed/ directories
        analyzed_files = sorted(glob.glob("output/analyzed_leads_*.csv") +
                               glob.glob("output/analyzed/analyzed_leads_*.csv"),
                               key=os.path.getmtime, reverse=True)

        if not analyzed_files:
            logger.error("No analyzed_leads_*.csv files found!")
            overall_progress.stop()
            return 1

        analysis_file = analyzed_files[0]
        logger.info(f"Using most recent analysis file: {analysis_file}")

        # Check if we've exceeded the maximum runtime
        if time.time() - start_time > max_runtime_seconds:
            logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded after analysis step")
            print(f"\nMaximum runtime of {args.max_runtime} minutes exceeded after analysis step\n")
            overall_progress.stop()
            return 0
    else:
        logger.info("Skipping analysis step")
        if args.analysis_file:
            analysis_file = args.analysis_file
        else:
            logger.error("No analysis file specified for nearby finder")
            overall_progress.stop()
            return 1

    # Step 3: Find nearby businesses
    if not args.no_nearby:
        logger.info(f"Step 3: Finding nearby businesses for incidents in {analysis_file}")

        # Debug logging - verify the analysis file exists and has content
        if os.path.exists(analysis_file):
            try:
                df = pd.read_csv(analysis_file)
                logger.info(f"Analysis file contains {len(df)} rows and {len(df.columns)} columns")
                logger.info(f"Columns: {', '.join(df.columns)}")
                if 'extracted_incident_address' in df.columns:
                    extracted_count = df['extracted_incident_address'].notna().sum()
                    logger.info(f"Found {extracted_count} rows with extracted_incident_address")
            except Exception as e:
                logger.warning(f"Could not read analysis file: {e}")
        else:
            logger.error(f"Analysis file does not exist: {analysis_file}")

        # Use the real nearby finder with the analysis file
        nearby_output = run_command(
            ["python3", "-m", "src.nearby_finder.finder", "--input-file", analysis_file],
            "Nearby Business Finder"
        )

        if not nearby_output:
            logger.error("Nearby business finding failed, exiting workflow")
            overall_progress.stop()
            return 1

        # Check if we've exceeded the maximum runtime
        if time.time() - start_time > max_runtime_seconds:
            logger.warning(f"Maximum runtime of {args.max_runtime} minutes exceeded after nearby finder step")
            print(f"\nMaximum runtime of {args.max_runtime} minutes exceeded after nearby finder step\n")
            overall_progress.stop()
            return 0

        # Extract the output file from the nearby finder output
        # This is a simplification - in reality you'd need to parse the output
        nearby_file = f"output/nearby/nearby_businesses_{timestamp}.csv"
    else:
        logger.info("Skipping nearby business finder step")

    # Step 4: Create the Complete Scrape file
    if not args.no_complete:
        logger.info("Step 4: Creating Complete Scrape file")
        complete_scrape_output = run_command(
            ["python3", "create_complete_scrape.py"],
            "Complete Scrape Creator"
        )

        if not complete_scrape_output:
            logger.error("Complete Scrape creation failed, but continuing workflow")
            print("\nWarning: Complete Scrape creation failed, but continuing workflow\n")
        else:
            logger.info("Complete Scrape file created successfully")
    else:
        logger.info("Skipping Complete Scrape creation step")

    # Stop the overall progress indicator
    elapsed = overall_progress.stop()

    logger.info(f"Workflow completed successfully in {elapsed}")
    print(f"\nWorkflow completed successfully in {elapsed}\n")
    return 0

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    sys.exit(main())
