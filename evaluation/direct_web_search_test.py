#!/usr/bin/env python3
"""
Test the web-search function directly from the environment.
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_search_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Test the web-search function directly."""
    logger.info("Testing web-search function directly")
    
    try:
        # Try to import the web-search function from the environment
        from web_search import web_search
        logger.info("Successfully imported web_search function")
        
        # Test the function with a simple query
        query = "Raffie Jewelers in Kensington, MD address"
        logger.info(f"Performing web search with query: {query}")
        
        results = web_search(query=query, num_results=5)
        logger.info(f"Web search results received: {len(results)} characters")
        logger.info(f"Results: {results}")
        
        return True
    except Exception as e:
        logger.error(f"Error using web-search function: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Web search test completed successfully")
    else:
        logger.error("Web search test failed")
