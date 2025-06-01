#!/usr/bin/env python3
"""
Test script for the enhanced analyzer with improved web search functionality.

This script tests the integration of the enhanced web search wrapper
with the analyzer module.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the analyzer
from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer

# Configure logging
logs_dir = 'logs'
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, f'enhanced_analyzer_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_web_search_integration():
    """Test the integration of the enhanced web search with the analyzer."""
    logger.info("Testing web search integration with analyzer")
    
    # Create a test analysis with low confidence address
    test_analysis = {
        "crimeType": "robbery",
        "method": "smash and grab",
        "target": "jewelry store",
        "storeType": "retail jewelry store",
        "businessName": "Raffie Jewelers",
        "detailedLocation": "Kensington, MD",
        "estimatedValue": "Not specified",
        "numSuspects": "2",
        "characteristics": "Two suspects broke into the jewelry store and stole merchandise",
        "incidentDate": "2023-11-10",
        "dateOfArticle": "2023-11-10",
        "summary": "Two suspects broke into Raffie Jewelers in Kensington, MD and stole merchandise.",
        "valueScore": 3,
        "recencyScore": 4,
        "totalScore": 7,
        "entryMethod": "Smash and grab",
        "exactAddress": "unknown",
        "addressConfidence": "low"
    }
    
    # Initialize the analyzer
    analyzer = SingleBatchAnalyzer()
    
    # Test the web search integration
    logger.info("=== STARTING WEB SEARCH INTEGRATION TEST ===")
    logger.info("Test analysis data:")
    logger.info(json.dumps(test_analysis, indent=2))
    
    # Check if web search should be performed
    logger.info("Checking if web search should be triggered...")
    should_search = analyzer._should_perform_web_search(test_analysis)
    logger.info(f"Web search trigger decision: {should_search}")
    
    # Log the trigger conditions
    address = test_analysis.get('exactAddress', '')
    confidence = test_analysis.get('addressConfidence', 'low')
    logger.info(f"Trigger conditions - Address: '{address}', Confidence: '{confidence}'")
    
    if should_search:
        # Enhance with web search
        logger.info("Performing web search enhancement...")
        enhanced_analysis = analyzer._enhance_with_web_search(test_analysis)
        
        # Print the results
        logger.info("=== WEB SEARCH ENHANCEMENT RESULTS ===")
        logger.info(json.dumps(enhanced_analysis, indent=2))
        
        # Check if the address was enhanced
        if enhanced_analysis.get('exactAddress') != 'unknown':
            logger.info("Web search enhancement successful!")
            logger.info(f"Enhanced address: {enhanced_analysis.get('exactAddress')}")
            logger.info(f"Address confidence: {enhanced_analysis.get('addressConfidence')}")
            logger.info(f"Address source: {enhanced_analysis.get('addressSource')}")
            if 'webSearchReasoning' in enhanced_analysis:
                logger.info(f"Web search reasoning: {enhanced_analysis.get('webSearchReasoning')}")
            return True
        else:
            logger.warning("Web search enhancement did not improve the address")
            return False
    else:
        logger.warning("Web search was not triggered")
        return False

def main():
    """Run the enhanced analyzer tests."""
    parser = argparse.ArgumentParser(description='Test enhanced analyzer with web search integration')
    args = parser.parse_args()
    
    logger.info("Starting enhanced analyzer tests")
    
    # Test web search integration
    success = test_web_search_integration()
    
    # Summarize results
    if success:
        logger.info("Enhanced analyzer tests completed successfully")
    else:
        logger.warning("Enhanced analyzer tests completed with issues")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
