#!/usr/bin/env python3
"""
Wrapper script for running the scraper.

This script is a convenience wrapper around the 'scrape' command of src/main.py.
It allows users to run the scraper without having to remember the full command syntax.

Usage:
    python scripts/scrape.py [options]

Options:
    --sources SRC1,SRC2  Comma-separated list of sources to scrape (default: all)
    --use-database       Use database for storage instead of CSV files
    --max-runtime MIN    Maximum runtime in minutes (default: 5)
    --progress-type TYPE Type of progress indicator (spinner, dots, bar)
"""

import sys
import os
import subprocess

def main():
    """Run the scraper command."""
    # Get the path to the main.py script
    main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'main.py')
    
    # Build the command
    cmd = [sys.executable, main_script, 'scrape']
    
    # Add any additional arguments
    cmd.extend(sys.argv[1:])
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running scraper: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
