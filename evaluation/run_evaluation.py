#!/usr/bin/env python3
"""
Run evaluation of the web search address validation functionality.
"""

import os
import sys
import json
import pandas as pd
import logging
import re
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the analyzer
from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation/evaluation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import the web-search function from test_web_search.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from test_web_search import web_search

def load_ground_truth():
    """Load the ground truth data."""
    with open('evaluation/ground_truth.json', 'r') as f:
        return json.load(f)

def load_sample_articles():
    """Load the sample articles."""
    return pd.read_csv('evaluation/sample_articles.csv')

def run_evaluation():
    """Run the evaluation of web search address validation."""
    logger.info("=== STARTING WEB SEARCH ADDRESS VALIDATION EVALUATION ===")

    # Load ground truth and sample articles
    ground_truth = load_ground_truth()
    sample_articles = load_sample_articles()

    logger.info(f"Loaded {len(sample_articles)} sample articles and {len(ground_truth)} ground truth entries")

    # Initialize the analyzer
    analyzer = SingleBatchAnalyzer()

    # Monkey patch the web_search function
    import src.analyzer.analyzer_manual_test
    src.analyzer.analyzer_manual_test.web_search = web_search

    # Create results directory
    results_dir = Path('evaluation/results')
    results_dir.mkdir(exist_ok=True)

    # Create timestamp for output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Initialize results
    results = []

    # Process each article
    for idx, article in sample_articles.iterrows():
        article_url = article.get('url', '')
        if not article_url or article_url not in ground_truth:
            logger.warning(f"Article {idx} has no URL or no ground truth entry, skipping")
            continue

        logger.info(f"\n=== Processing article {idx+1}/{len(sample_articles)}: {article['title']} ===")

        # Extract location from title or excerpt if available
        location = 'Unknown'
        title = str(article.get('title', '')) if not pd.isna(article.get('title')) else ''
        excerpt = str(article.get('excerpt', '')) if not pd.isna(article.get('excerpt')) else ''

        # Look for location in title first
        location_patterns = [
            r'([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})',  # City, State
            r'in\s+([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})',  # in City, State
            r'at\s+([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})'   # at City, State
        ]

        for text in [title, excerpt]:
            if location != 'Unknown':
                break

            for pattern in location_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    city, state = matches[0]
                    location = f"{city.strip()}, {state.strip()}"
                    logger.info(f"Extracted location from text: {location}")
                    break

        # If no location found, use the article location if available
        if location == 'Unknown':
            if not pd.isna(article.get('detailed_location')):
                location = str(article.get('detailed_location'))
            elif not pd.isna(article.get('location')):
                location = str(article.get('location'))

        # Create initial analysis from article
        initial_analysis = {
            'crimeType': article.get('keywords', '').split(',')[0] if article.get('keywords') else 'unknown',
            'method': 'unknown',
            'target': 'jewelry store',
            'storeType': 'retail jewelry store',
            'businessName': str(article.get('business_name', 'Unknown')) if not pd.isna(article.get('business_name')) else 'Unknown',
            'detailedLocation': location,
            'estimatedValue': 'Not specified',
            'numSuspects': 'Not specified',
            'characteristics': 'Not specified',
            'incidentDate': str(article.get('date', 'Not available')) if not pd.isna(article.get('date')) else 'Not available',
            'dateOfArticle': str(article.get('date', 'Not available')) if not pd.isna(article.get('date')) else 'Not available',
            'summary': excerpt,
            'exactAddress': 'unknown',
            'addressConfidence': 'low'
        }

        # Log the initial analysis
        logger.info("Initial analysis:")
        logger.info(json.dumps(initial_analysis, indent=2))

        # Check if web search should be performed
        should_search = analyzer._should_perform_web_search(initial_analysis)
        logger.info(f"Web search trigger decision: {should_search}")

        # Get ground truth data
        truth = ground_truth[article_url]
        logger.info(f"Ground truth: {json.dumps(truth, indent=2)}")

        # Perform web search if needed
        enhanced_analysis = None
        if should_search:
            logger.info("Performing web search enhancement...")
            enhanced_analysis = analyzer._enhance_with_web_search(initial_analysis)

            # Log the enhanced analysis
            logger.info("Enhanced analysis:")
            logger.info(json.dumps(enhanced_analysis, indent=2))
        else:
            enhanced_analysis = initial_analysis
            logger.info("Web search was not triggered")

        # Compare with ground truth
        is_correct = False
        match_reason = ""
        if truth.get('full_address'):
            # Check if the enhanced address matches the ground truth
            enhanced_address = enhanced_analysis.get('exactAddress', '').lower()
            truth_address = truth.get('full_address', '').lower()

            # Skip comparison if enhanced address is still unknown
            if enhanced_address == 'unknown':
                is_correct = False
                match_reason = "Enhanced address is still unknown"
            else:
                # Check for exact match
                if enhanced_address == truth_address:
                    is_correct = True
                    match_reason = "Exact match"
                # Check if all parts of the truth address are in the enhanced address
                elif all(part.strip() in enhanced_address for part in truth_address.split(',')):
                    is_correct = True
                    match_reason = "All parts of truth address found in enhanced address"
                # Check if street number and name match
                elif re.search(r'\d+\s+[A-Za-z]+', truth_address) and re.search(r'\d+\s+[A-Za-z]+', enhanced_address):
                    truth_street = re.search(r'(\d+\s+[A-Za-z]+)', truth_address).group(1)
                    if truth_street.lower() in enhanced_address:
                        is_correct = True
                        match_reason = f"Street match: {truth_street}"
                # Check if at least the street number matches
                elif re.search(r'\d+', truth_address) and re.search(r'\d+', enhanced_address):
                    truth_number = re.search(r'(\d+)', truth_address).group(1)
                    enhanced_number = re.search(r'(\d+)', enhanced_address).group(1)
                    if truth_number == enhanced_number:
                        is_correct = True
                        match_reason = f"Street number match: {truth_number}"

            logger.info(f"Address comparison - Enhanced: '{enhanced_address}', Truth: '{truth_address}'")
            logger.info(f"Match result: {'✅ Correct' if is_correct else '❌ Incorrect'} - {match_reason}")

        # Record result
        result = {
            'article_id': idx,
            'article_url': article_url,
            'article_title': article.get('title', ''),
            'ground_truth_business': truth.get('business_name', ''),
            'ground_truth_address': truth.get('full_address', ''),
            'initial_business': initial_analysis.get('businessName', ''),
            'initial_address': initial_analysis.get('exactAddress', ''),
            'initial_confidence': initial_analysis.get('addressConfidence', ''),
            'initial_location': initial_analysis.get('detailedLocation', ''),
            'web_search_triggered': should_search,
            'final_business': enhanced_analysis.get('businessName', ''),
            'final_address': enhanced_analysis.get('exactAddress', ''),
            'final_confidence': enhanced_analysis.get('addressConfidence', ''),
            'address_source': enhanced_analysis.get('addressSource', ''),
            'is_correct': is_correct,
            'match_reason': match_reason,
            'web_search_reasoning': enhanced_analysis.get('webSearchReasoning', '')
        }

        results.append(result)

    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_file = f'evaluation/results/evaluation_results_{timestamp}.csv'
    results_df.to_csv(results_file, index=False)
    logger.info(f"Results saved to {results_file}")

    # Calculate metrics
    total = len(results)
    triggered = sum(1 for r in results if r['web_search_triggered'])
    correct = sum(1 for r in results if r['is_correct'])
    improved = sum(1 for r in results if r['web_search_triggered'] and r['is_correct'])

    logger.info("\n=== EVALUATION METRICS ===")
    logger.info(f"Total articles evaluated: {total}")
    logger.info(f"Web search triggered: {triggered} ({triggered/total*100:.1f}%)")
    logger.info(f"Correct addresses: {correct} ({correct/total*100:.1f}%)")
    logger.info(f"Addresses improved by web search: {improved} ({improved/triggered*100:.1f}% of triggered searches)")

    # Save metrics to JSON
    metrics = {
        'timestamp': timestamp,
        'total_articles': total,
        'web_search_triggered': triggered,
        'web_search_triggered_pct': triggered/total*100 if total > 0 else 0,
        'correct_addresses': correct,
        'correct_addresses_pct': correct/total*100 if total > 0 else 0,
        'addresses_improved': improved,
        'addresses_improved_pct': improved/triggered*100 if triggered > 0 else 0
    }

    metrics_file = f'evaluation/results/evaluation_metrics_{timestamp}.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_file}")

    logger.info("=== EVALUATION COMPLETED ===")

    return results_df, metrics

if __name__ == "__main__":
    run_evaluation()
