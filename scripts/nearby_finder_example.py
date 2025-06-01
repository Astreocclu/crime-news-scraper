"""
Example script demonstrating how to use the Nearby Business Finder module.
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.nearby_finder.finder import NearbyBusinessFinder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run an example of finding nearby businesses."""
    # Sample input file - should be an analyzed leads CSV
    input_file = '/home/astreocclu/projects/crime-news-scraper/output/jsa_articles_20250402_091600.csv'
    
    # Check if the file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        # Find an alternative file in the output directory
        output_dir = os.path.join('output')
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.csv') and 'analyzed' in file:
                    input_file = os.path.join(root, file)
                    logger.info(f"Using alternative input file: {input_file}")
                    break
            if os.path.exists(input_file):
                break
    
    if not os.path.exists(input_file):
        logger.error("No suitable input file found in the output directory")
        return
    
    # Initialize the finder
    finder = NearbyBusinessFinder()
    
    # Process the file
    output_file = finder.find_nearby_businesses(input_file)
    
    logger.info(f"Example completed. Results saved to: {output_file}")
    logger.info("The CSV contains both original incidents and nearby businesses with 'record_type' column")

if __name__ == "__main__":
    main()