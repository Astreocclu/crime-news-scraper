#!/usr/bin/env python3
"""
Manually test the web search address validation functionality using the Augment web-search tool.
"""

import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manual_web_search_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Manually test the web search address validation functionality."""
    logger.info("=== STARTING MANUAL WEB SEARCH TEST ===")
    
    # Test cases
    test_cases = [
        {
            "name": "Raffie Jewelers",
            "location": "Kensington, MD",
            "ground_truth": "3774 Howard Ave, Kensington, MD 20895"
        },
        {
            "name": "Kim Tin Jewelry",
            "location": "Sacramento, CA",
            "ground_truth": "6830 Stockton Blvd, Suite 190, Sacramento, CA 95823"
        },
        {
            "name": "Jewelry Kiosk at Eastridge Mall",
            "location": "Gastonia, NC",
            "ground_truth": "246 N New Hope Rd, Gastonia, NC 28054"
        },
        {
            "name": "Home Consignment Center",
            "location": "San Carlos, CA",
            "ground_truth": "1123 Industrial Road, San Carlos, CA 94070"
        },
        {
            "name": "South Hill Mall",
            "location": "Puyallup, WA",
            "ground_truth": "3500 S Meridian, Puyallup, WA 98373"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']} in {test_case['location']}")
        
        # Create search query
        search_query = f'"{test_case["name"]}" in "{test_case["location"]}" address'
        logger.info(f"Search query: {search_query}")
        
        # Perform web search
        try:
            from web_search import web_search
            search_results = web_search(query=search_query, num_results=5)
            logger.info(f"Search results: {search_results}")
            
            # Extract address from search results
            # This is a simplified version of the address extraction logic
            address = "Not found"
            if search_results:
                # Look for address patterns in the search results
                import re
                
                # Common address patterns
                address_patterns = [
                    r'(\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})',  # Full address with zip
                    r'(\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2})',  # Address without zip
                    r'(\d+\s+[A-Za-z\s]+(?:Ave|Avenue|St|Street|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Pl|Place|Ct|Court|Cir|Circle|Way|Hwy|Highway|Pkwy|Parkway)\.?(?:\s+[A-Za-z\s]+)?)'  # Street address
                ]
                
                for pattern in address_patterns:
                    matches = re.findall(pattern, search_results, re.IGNORECASE)
                    if matches:
                        address = matches[0]
                        break
            
            # Compare with ground truth
            ground_truth = test_case['ground_truth']
            is_match = address.lower() in ground_truth.lower() or ground_truth.lower() in address.lower()
            
            result = {
                "name": test_case['name'],
                "location": test_case['location'],
                "search_query": search_query,
                "extracted_address": address,
                "ground_truth": ground_truth,
                "is_match": is_match
            }
            
            results.append(result)
            
            logger.info(f"Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
    
    # Calculate metrics
    total = len(results)
    correct = sum(1 for r in results if r['is_match'])
    
    logger.info("\n=== TEST METRICS ===")
    logger.info(f"Total test cases: {total}")
    logger.info(f"Correct addresses: {correct} ({correct/total*100:.1f}%)")
    
    logger.info("=== MANUAL WEB SEARCH TEST COMPLETED ===")
    
    return results

if __name__ == "__main__":
    main()
