#!/usr/bin/env python
"""
Export analysis results from the database to CSV.

This script queries the analysis_results table from the database and writes the contents to a new CSV file.

Usage:
    python export_analysis_to_csv.py [--output-dir DIR]

Options:
    --output-dir    Directory to save the CSV file (default: output/analysis)
"""

import argparse
import logging
import os
import sys
import pandas as pd
from datetime import datetime

# Import database functions
from src.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('export_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Export analysis results from database to CSV')
    parser.add_argument('--output-dir', type=str, default='output/analysis', 
                        help='Directory to save the CSV file (default: output/analysis)')
    return parser.parse_args()

def export_analysis_to_csv(output_dir='output/analysis'):
    """
    Query analysis results from the database and export to CSV.
    
    Parameters:
    -----------
    output_dir : str, optional
        Directory to save the CSV file (default: output/analysis)
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        # Step 2.1: Connect to Database
        logger.info("Connecting to database...")
        db_conn = get_db_connection()
        if not db_conn:
            logger.error("Failed to connect to database")
            return False
        
        try:
            # Step 2.2: Query Analysis Results
            logger.info("Querying analysis results from database...")
            cursor = db_conn.cursor()
            
            # Join with articles table to get article information
            query = """
            SELECT ar.*, a.title as article_title, a.url as article_url, a.location as article_location
            FROM analysis_results ar
            JOIN articles a ON ar.article_id = a.id
            """
            
            cursor.execute(query)
            
            # Step 2.3: Fetch Query Results
            logger.info("Fetching query results...")
            rows = cursor.fetchall()
            
            if not rows:
                logger.info("No analysis results found in the database")
                return True
            
            logger.info(f"Found {len(rows)} analysis results")
            
            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]
            
            # Step 2.4: Write Results to CSV
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Define output file path
            output_file = os.path.join(output_dir, f'analysis_export_{timestamp}.csv')
            
            # Convert to DataFrame and save to CSV
            df = pd.DataFrame(results)
            df.to_csv(output_file, index=False)
            
            logger.info(f"Successfully exported {len(results)} analysis results to {output_file}")
            
            return True
            
        finally:
            # Step 2.5: Close Database Connection
            if db_conn:
                db_conn.close()
                logger.info("Database connection closed")
    
    except Exception as e:
        logger.error(f"Error exporting analysis results: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point for the script."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Run the export
        logger.info(f"Exporting analysis results to {args.output_dir}")
        success = export_analysis_to_csv(args.output_dir)
        
        if success:
            logger.info("Export completed successfully")
        else:
            logger.error("Export failed")
            
    except Exception as e:
        logger.error(f"Error running export: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
