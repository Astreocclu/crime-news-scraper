#!/usr/bin/env python3
"""
Test script for Perplexity API integration in the analyzer.
"""

import logging
import sys
import json
import re
from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer
from src.perplexity_client import PerplexityClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# This mock function has been replaced by the Perplexity API client

def test_web_search():
    """Test the Perplexity API integration for address enhancement."""
    # Create a test analysis with low confidence address
    test_analysis = {
        "crimeType": "robbery",
        "method": "smash and grab",
        "target": "jewelry store",
        "storeType": "retail jewelry store",
        "businessName": "El Paseo Jewelers",
        "detailedLocation": "Palm Desert, CA",
        "estimatedValue": "Not specified",
        "numSuspects": "6",
        "characteristics": "Multiple suspects arrested by Riverside County Sheriff's Department",
        "incidentDate": "2023-11-10",
        "dateOfArticle": "2023-11-10",
        "summary": "The Riverside County Sheriff's Department arrested six suspects following a smash and grab robbery in Palm Desert, California.",
        "valueScore": 3,
        "recencyScore": 4,
        "totalScore": 7,
        "entryMethod": "Smash and grab",
        "exactAddress": "unknown",
        "addressConfidence": "low"
    }

    # Initialize the analyzer
    analyzer = SingleBatchAnalyzer()

    # Test the Perplexity API integration
    logger.info("=== STARTING PERPLEXITY API INTEGRATION TEST ===")
    logger.info("Test analysis data:")
    logger.info(json.dumps(test_analysis, indent=2))

    # Check if address enhancement should be performed
    logger.info("Checking if address enhancement should be triggered...")
    should_enhance = analyzer._should_perform_web_search(test_analysis)
    logger.info(f"Address enhancement trigger decision: {should_enhance}")

    # Log the trigger conditions
    address = test_analysis.get('exactAddress', '')
    confidence = test_analysis.get('addressConfidence', 'low')
    logger.info(f"Trigger conditions - Address: '{address}', Confidence: '{confidence}'")

    if should_enhance:
        # Enhance with Perplexity API
        logger.info("Performing address enhancement with Perplexity API...")
        enhanced_analysis = analyzer._enhance_with_web_search(test_analysis)

        # Print the results
        logger.info("=== PERPLEXITY API ENHANCEMENT RESULTS ===")
        logger.info(json.dumps(enhanced_analysis, indent=2))

        # Check if the address was updated
        if enhanced_analysis.get('exactAddress') != "unknown":
            logger.info("✅ Address was updated successfully!")
            logger.info(f"Original address: {test_analysis.get('exactAddress')}")
            logger.info(f"New address: {enhanced_analysis.get('exactAddress')}")
            logger.info(f"Address confidence: {enhanced_analysis.get('addressConfidence')}")
            logger.info(f"Address source: {enhanced_analysis.get('addressSource')}")
            logger.info(f"Web search reasoning: {enhanced_analysis.get('webSearchReasoning')}")
        else:
            logger.info("❌ Address was not updated.")
            logger.info("Analyzing why the address was not updated...")
    else:
        logger.info("Address enhancement was not triggered based on the analysis data.")

    logger.info("=== PERPLEXITY API INTEGRATION TEST COMPLETED ===")

    return 0

if __name__ == "__main__":
    sys.exit(test_web_search())
