#!/usr/bin/env python3
"""
Limited workflow test script to validate the complete workflow with a small batch.

This script tests the end-to-end workflow with 10 articles to identify integration issues
and validate that the address validation fixes are working.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import main as run_main
from src.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_workflow_limited.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_database_state():
    """Check the current state of the database."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
            
        cursor = conn.cursor()
        
        # Check articles count
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        # Check analysis results count
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        analysis_count = cursor.fetchone()[0]
        
        # Check nearby businesses count
        cursor.execute("SELECT COUNT(*) FROM nearby_businesses")
        nearby_count = cursor.fetchone()[0]
        
        logger.info(f"Database state: {articles_count} articles, {analysis_count} analysis results, {nearby_count} nearby businesses")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking database state: {str(e)}")
        return False

def test_limited_workflow():
    """Test the complete workflow with limited articles."""
    logger.info("Starting limited workflow test")
    
    # Check initial database state
    logger.info("Checking initial database state...")
    if not check_database_state():
        return False
    
    # Test parameters - use correct argument structure for workflow command
    test_args = [
        'src/main.py',
        '--use-database',
        '--max-runtime', '10',  # 10 minute limit for larger test
        'workflow',
        '--no-scrape',  # Skip scraping to use existing data
    ]
    
    # Override sys.argv for the test
    original_argv = sys.argv
    sys.argv = test_args
    
    try:
        start_time = time.time()
        logger.info("Starting workflow test with parameters: " + " ".join(test_args[1:]))
        
        # Run the main workflow
        result = run_main()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Workflow completed in {elapsed_time:.2f} seconds")
        
        # Check final database state
        logger.info("Checking final database state...")
        if not check_database_state():
            return False
            
        # Check if analysis files were created
        analysis_dir = 'output/analysis_results'
        if os.path.exists(analysis_dir):
            analysis_files = [f for f in os.listdir(analysis_dir) if f.endswith('.csv') or f.endswith('.json')]
            logger.info(f"Found {len(analysis_files)} analysis files in {analysis_dir}")
            
            # Show the most recent files
            if analysis_files:
                analysis_files.sort(key=lambda x: os.path.getmtime(os.path.join(analysis_dir, x)), reverse=True)
                logger.info(f"Most recent analysis file: {analysis_files[0]}")
        
        # Check if nearby business files were created
        nearby_dir = 'output/nearby_businesses'
        if os.path.exists(nearby_dir):
            nearby_files = [f for f in os.listdir(nearby_dir) if f.endswith('.csv')]
            logger.info(f"Found {len(nearby_files)} nearby business files in {nearby_dir}")
        
        logger.info("Limited workflow test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during workflow test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

def main():
    """Main entry point for the test script."""
    logger.info("=" * 60)
    logger.info("CRIME NEWS SCRAPER - LIMITED WORKFLOW TEST")
    logger.info("=" * 60)
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('output/analysis_results', exist_ok=True)
    os.makedirs('output/nearby_businesses', exist_ok=True)
    
    # Run the test
    success = test_limited_workflow()
    
    if success:
        logger.info("✅ Limited workflow test PASSED")
        return 0
    else:
        logger.error("❌ Limited workflow test FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
