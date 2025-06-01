#!/usr/bin/env python3
"""
Test the improved address validation workflow using the Augment web-search tool.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the analyzer
from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation/improved_validation_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_improved_validation():
    """Test the improved address validation workflow."""
    logger.info("=== TESTING IMPROVED ADDRESS VALIDATION WORKFLOW ===")

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

    # Initialize the analyzer
    analyzer = SingleBatchAnalyzer()

    # Process each test case
    results = []
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']} in {test_case['location']}")

        # Create initial analysis
        initial_analysis = {
            'businessName': test_case['name'],
            'detailedLocation': test_case['location'],
            'storeType': 'jewelry store',
            'exactAddress': 'unknown',
            'addressConfidence': 'low'
        }

        # Create article dictionary
        article = {
            'url': f"https://example.com/{test_case['name'].replace(' ', '-').lower()}",
            'title': f"Robbery at {test_case['name']} in {test_case['location']}",
            'date': datetime.now().strftime('%Y-%m-%d'),
            'excerpt': f"A robbery occurred at {test_case['name']} located in {test_case['location']}.",
            'source': 'Test Source',
            'location': test_case['location'],
            'store_type': 'jewelry store',
            'business_name': test_case['name'],
            'detailed_location': test_case['location']
        }

        # Check if web search should be performed
        should_search = analyzer._should_perform_web_search(initial_analysis)
        logger.info(f"Web search trigger decision: {should_search}")

        # Perform web search if needed
        enhanced_analysis = None
        if should_search:
            logger.info("Performing web search enhancement...")

            # Use the web-search tool from the Augment environment
            try:
                # Create the search query
                business_name = initial_analysis.get('businessName', '')
                location = initial_analysis.get('detailedLocation', '')
                search_query = f'"{business_name}" in "{location}" address'
                logger.info(f"Web search query: {search_query}")

                # Import the web-search function from this environment
                from web_search import web_search

                # Perform the web search
                web_search_results = web_search(query=search_query, num_results=5)
                logger.info(f"Web search results received: {len(web_search_results)} characters")
                logger.info(f"First 200 characters of results: {web_search_results[:200]}...")

                # Monkey patch the web_search function in the analyzer
                def mock_web_search(query, num_results=5):
                    return web_search_results

                # Save the original function
                original_web_search = analyzer.web_search

                # Replace with our mock function
                analyzer.web_search = mock_web_search

                # Enhance the analysis with the web search results
                enhanced_analysis = analyzer._enhance_with_web_search(initial_analysis, article)

                # Restore the original function
                analyzer.web_search = original_web_search

                # Log the enhanced analysis
                logger.info("Enhanced analysis:")
                logger.info(json.dumps(enhanced_analysis, indent=2))
            except Exception as e:
                logger.error(f"Error using web-search tool: {str(e)}")
                enhanced_analysis = initial_analysis
        else:
            enhanced_analysis = initial_analysis
            logger.info("Web search was not triggered")

        # Compare with ground truth
        ground_truth = test_case['ground_truth']
        enhanced_address = enhanced_analysis.get('exactAddress', '').lower()

        # Normalize addresses for comparison
        import re
        enhanced_address_norm = re.sub(r'[,\s]+', '', enhanced_address)
        ground_truth_norm = re.sub(r'[,\s]+', '', ground_truth.lower())

        # Check for match
        is_match = False
        match_reason = "No match"

        # Check for exact match
        if enhanced_address_norm == ground_truth_norm:
            is_match = True
            match_reason = "Exact match"
        # Check for partial match (address contains street number and name)
        elif re.search(r'\d+\s+[a-z]+', enhanced_address) and re.search(r'\d+\s+[a-z]+', ground_truth):
            # Extract street number and name from both addresses
            enhanced_street = re.search(r'(\d+\s+[a-z]+)', enhanced_address)
            ground_truth_street = re.search(r'(\d+\s+[a-z]+)', ground_truth)

            if enhanced_street and ground_truth_street and enhanced_street.group(1) == ground_truth_street.group(1):
                is_match = True
                match_reason = "Partial match (street number and name)"

        # Record result
        result = {
            "name": test_case['name'],
            "location": test_case['location'],
            "ground_truth": ground_truth,
            "initial_address": initial_analysis.get('exactAddress', ''),
            "initial_confidence": initial_analysis.get('addressConfidence', ''),
            "web_search_triggered": should_search,
            "enhanced_address": enhanced_analysis.get('exactAddress', ''),
            "enhanced_confidence": enhanced_analysis.get('addressConfidence', ''),
            "address_source": enhanced_analysis.get('addressSource', ''),
            "is_match": is_match,
            "match_reason": match_reason,
            "web_search_reasoning": enhanced_analysis.get('webSearchReasoning', '')
        }

        results.append(result)

        logger.info(f"Result: {json.dumps(result, indent=2)}")

    # Calculate metrics
    total = len(results)
    triggered = sum(1 for r in results if r['web_search_triggered'])
    correct = sum(1 for r in results if r['is_match'])

    logger.info("\n=== TEST METRICS ===")
    logger.info(f"Total test cases: {total}")
    logger.info(f"Web search triggered: {triggered} ({triggered/total*100:.1f}%)")
    logger.info(f"Correct addresses: {correct} ({correct/total*100:.1f}%)")

    # Create comparison table
    table_rows = []
    table_rows.append("| Business | Location | Ground Truth | Enhanced Address | Confidence | Match? |")
    table_rows.append("|----------|----------|--------------|------------------|------------|--------|")

    for result in results:
        business = result['name']
        location = result['location']
        ground_truth = result['ground_truth']
        enhanced_address = result['enhanced_address'] if result['enhanced_address'] else "N/A"
        confidence = result['enhanced_confidence'] if result['enhanced_confidence'] else "N/A"
        match = "✅" if result['is_match'] else "❌"

        row = f"| {business} | {location} | {ground_truth} | {enhanced_address} | {confidence} | {match} |"
        table_rows.append(row)

    table_content = "\n".join(table_rows)

    # Save the table to a file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    table_file = f'evaluation/results/improved_validation_results_{timestamp}.md'

    os.makedirs('evaluation/results', exist_ok=True)

    with open(table_file, 'w') as f:
        f.write("# Improved Address Validation Results\n\n")
        f.write(table_content)

    logger.info(f"Results saved to {table_file}")
    logger.info("=== TESTING COMPLETED ===")

    return results

if __name__ == "__main__":
    test_improved_validation()
