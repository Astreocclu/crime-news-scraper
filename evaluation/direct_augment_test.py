#!/usr/bin/env python3
"""
Test the improved address validation workflow using the Augment web-search tool directly.
"""

import json
import logging
import sys
import os
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_augment_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def extract_address(search_results, business_name, location):
    """Extract address from search results."""
    if not search_results or search_results == "No results found.":
        return None, "No results found"

    # Common address patterns
    address_patterns = [
        # Full address with zip
        r'(\d+\s+[A-Za-z\s\.]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)',
        # Address without zip
        r'(\d+\s+[A-Za-z\s\.]+,\s*[A-Za-z\s]+,\s*[A-Z]{2})',
        # Street address with city and state
        r'(\d+\s+[A-Za-z\s\.]+(?:Ave|Avenue|St|Street|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Pl|Place|Ct|Court|Cir|Circle|Way|Hwy|Highway|Pkwy|Parkway)\.?(?:\s+[A-Za-z\s]+)?,\s*[A-Za-z\s]+,\s*[A-Z]{2})',
        # Street address with suite/unit
        r'(\d+\s+[A-Za-z\s\.]+(?:Suite|Ste|Unit|#)\s*[A-Za-z0-9\-]+,\s*[A-Za-z\s]+,\s*[A-Z]{2})',
        # Simple street address
        r'(\d+\s+[A-Za-z\s\.]+)'
    ]

    # Extract city and state from location
    city = state = None
    location_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})', location)
    if location_match:
        city = location_match.group(1).strip().lower()
        state = location_match.group(2).strip().lower()

    # Look for addresses in search results
    for pattern in address_patterns:
        matches = re.findall(pattern, search_results)
        if matches:
            # Filter matches by relevance
            relevant_matches = []
            for match in matches:
                # Check if the address contains the city or state
                if city and city in match.lower():
                    relevant_matches.append((match, 2))  # Higher score for city match
                elif state and state in match.lower():
                    relevant_matches.append((match, 1))  # Lower score for state match
                else:
                    relevant_matches.append((match, 0))  # No location match

            # Sort by relevance score (highest first)
            relevant_matches.sort(key=lambda x: x[1], reverse=True)

            if relevant_matches:
                return relevant_matches[0][0], f"Found using pattern: {pattern}"

    return None, "No address patterns matched"

def main():
    """Test the improved address validation workflow using the Augment web-search tool directly."""
    logger.info("=== STARTING DIRECT AUGMENT TEST ===")

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
        search_query = f"\"{test_case['name']}\" in \"{test_case['location']}\" address"
        logger.info(f"Search query: {search_query}")

        # Perform web search using the Augment web-search tool
        try:
            # Import the web-search function from the Augment environment
            from web_search import web_search

            # Perform the web search
            search_results = web_search(query=search_query, num_results=5)
            logger.info(f"Web search results received: {len(search_results)} characters")
            logger.info(f"First 200 characters of results: {search_results[:200]}...")

            # Extract address from search results
            extracted_address, extraction_reason = extract_address(
                search_results,
                test_case['name'],
                test_case['location']
            )

            # Compare with ground truth
            ground_truth = test_case['ground_truth']
            is_match = False
            match_reason = "No match"

            if extracted_address:
                # Normalize addresses for comparison
                extracted_norm = re.sub(r'[,\s]+', '', extracted_address.lower())
                ground_truth_norm = re.sub(r'[,\s]+', '', ground_truth.lower())

                # Check for exact match
                if extracted_norm == ground_truth_norm:
                    is_match = True
                    match_reason = "Exact match"
                # Check for partial match (address contains street number and name)
                elif re.search(r'\d+\s+[a-z]+', extracted_address.lower()) and re.search(r'\d+\s+[a-z]+', ground_truth.lower()):
                    # Extract street number and name from both addresses
                    extracted_street = re.search(r'(\d+\s+[a-z]+)', extracted_address.lower())
                    ground_truth_street = re.search(r'(\d+\s+[a-z]+)', ground_truth.lower())

                    if extracted_street and ground_truth_street and extracted_street.group(1) == ground_truth_street.group(1):
                        is_match = True
                        match_reason = "Partial match (street number and name)"

            result = {
                "name": test_case['name'],
                "location": test_case['location'],
                "search_query": search_query,
                "ground_truth": ground_truth,
                "extracted_address": extracted_address if extracted_address else "Not found",
                "extraction_reason": extraction_reason,
                "is_match": is_match,
                "match_reason": match_reason
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

    # Create comparison table
    table_rows = []
    table_rows.append("| Business | Location | Ground Truth | Extracted Address | Match? |")
    table_rows.append("|----------|----------|--------------|-------------------|--------|")

    for result in results:
        business = result['name']
        location = result['location']
        ground_truth = result['ground_truth']
        extracted_address = result['extracted_address']
        match = "✅" if result['is_match'] else "❌"

        row = f"| {business} | {location} | {ground_truth} | {extracted_address} | {match} |"
        table_rows.append(row)

    table_content = "\n".join(table_rows)

    # Save the table to a file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('evaluation/results', exist_ok=True)
    table_file = f'evaluation/results/direct_augment_results_{timestamp}.md'

    with open(table_file, 'w') as f:
        f.write("# Direct Augment Test Results\n\n")
        f.write(table_content)

    logger.info(f"Results saved to {table_file}")
    logger.info("=== DIRECT AUGMENT TEST COMPLETED ===")

    return results

if __name__ == "__main__":
    main()
