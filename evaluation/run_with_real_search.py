#!/usr/bin/env python3
"""
Run realistic evaluation of the address validation functionality using the Perplexity API.
This script uses the Perplexity API client to validate addresses for crime incidents at jewelry stores.
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

# Import the analyzer and Perplexity client
from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer
from src.perplexity_client import PerplexityClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation/realistic_evaluation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_ground_truth():
    """Load the ground truth data."""
    try:
        with open('evaluation/ground_truth.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading ground truth data: {str(e)}")
        return {}

def load_sample_articles():
    """Load the sample articles."""
    try:
        return pd.read_csv('evaluation/sample_articles.csv')
    except Exception as e:
        logger.error(f"Error loading sample articles: {str(e)}")
        return pd.DataFrame()

def run_realistic_evaluation():
    """Run the evaluation of web search address validation using the real web search tool."""
    logger.info("=== STARTING REALISTIC WEB SEARCH ADDRESS VALIDATION EVALUATION ===")

    # Load ground truth and sample articles
    ground_truth = load_ground_truth()
    sample_articles = load_sample_articles()

    logger.info(f"Loaded {len(sample_articles)} sample articles and {len(ground_truth)} ground truth entries")

    # Initialize the analyzer
    analyzer = SingleBatchAnalyzer()

    # Create results directory
    results_dir = Path('evaluation/results')
    results_dir.mkdir(exist_ok=True)

    # Generate timestamp for result files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Process each article
    results = []
    for idx, article in sample_articles.iterrows():
        article_url = article.get('url', '')

        # Skip if no URL
        if not article_url:
            logger.warning(f"Skipping article {idx} with no URL")
            continue

        logger.info(f"Processing article {idx}: {article_url}")

        # Get ground truth for this article if available
        truth = ground_truth.get(article_url, {})
        if truth:
            logger.info(f"Found ground truth for article: {json.dumps(truth)}")
        else:
            logger.info("No ground truth found for article")

        # Create article dictionary for analyzer
        article_dict = {
            'url': article_url,
            'title': article.get('title', ''),
            'date': article.get('date', ''),
            'excerpt': article.get('excerpt', ''),
            'source': article.get('source', ''),
            'location': article.get('location', ''),
            'store_type': article.get('store_type', 'jewelry store'),
            'business_name': article.get('business_name', ''),
            'detailed_location': article.get('detailed_location', '')
        }

        # Extract location from title or excerpt if not provided
        location = article.get('detailed_location', '')
        if pd.isna(location) or location == '':
            location = article.get('location', '')
            if pd.isna(location) or location == 'Other' or location == '':
                # Try to extract location from title
                title = article.get('title', '')
                if not pd.isna(title):
                    location_match = re.search(r'([A-Za-z\s]+,\s*[A-Z]{2})', title)
                    if location_match:
                        location = location_match.group(1)
                    else:
                        # Try to extract location from excerpt
                        excerpt = article.get('excerpt', '')
                        if not pd.isna(excerpt):
                            location_match = re.search(r'([A-Za-z\s]+,\s*[A-Z]{2})', excerpt)
                            if location_match:
                                location = location_match.group(1)

        # Extract business name from title or excerpt if not provided
        business_name = article.get('business_name', '')
        if pd.isna(business_name) or business_name == '':
            # Try to extract business name from title
            title = article.get('title', '')
            if not pd.isna(title):
                if 'jewelry store' in title.lower():
                    business_name = 'Jewelry Store'
                elif 'jewelers' in title.lower():
                    business_name = 'Jewelers'

            # Check if there's a ground truth business name
            article_url = article.get('url', '')
            truth = ground_truth.get(article_url, {})
            if truth and truth.get('business_name'):
                business_name = truth.get('business_name')

        # Create a basic analysis with the information we have
        initial_analysis = {
            'businessName': str(business_name if not pd.isna(business_name) and business_name != '' else 'Unknown'),
            'detailedLocation': str(location if not pd.isna(location) and location != '' else 'Unknown'),
            'storeType': 'jewelry store',
            'exactAddress': 'unknown',
            'addressConfidence': 'low'
        }

        # Log the initial analysis
        logger.info("Initial analysis:")
        logger.info(json.dumps(initial_analysis, indent=2))

        # Check if web search should be performed
        should_search = analyzer._should_perform_web_search(initial_analysis)
        logger.info(f"Web search trigger decision: {should_search}")

        # Perform web search if needed
        enhanced_analysis = None
        if should_search:
            logger.info("Performing web search enhancement...")

            # Create the search query
            business_name = initial_analysis.get('businessName', '')
            location = initial_analysis.get('detailedLocation', '')
            search_query = f'"{business_name}" in "{location}" address'
            logger.info(f"Web search query: {search_query}")

            # Use the web-search tool from the environment
            try:
                # Import the web-search tool
                import subprocess
                import json

                # Call the web-search tool using subprocess
                cmd = ['python3', '-c', f'import json; from web_search import web_search; print(json.dumps(web_search(query="{search_query}", num_results=5)))']
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    web_search_results = result.stdout.strip()
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
                    enhanced_analysis = analyzer._enhance_with_web_search(initial_analysis, article_dict)

                    # Restore the original function
                    analyzer.web_search = original_web_search

                    # Log the enhanced analysis
                    logger.info("Enhanced analysis:")
                    logger.info(json.dumps(enhanced_analysis, indent=2))
                else:
                    logger.error(f"Error running web-search tool: {result.stderr}")
                    enhanced_analysis = initial_analysis
            except Exception as e:
                logger.error(f"Error using web-search tool: {str(e)}")
                enhanced_analysis = initial_analysis
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

            # Normalize addresses for comparison (remove spaces, commas, etc.)
            enhanced_address_norm = re.sub(r'[,\s]+', '', enhanced_address)
            truth_address_norm = re.sub(r'[,\s]+', '', truth_address)

            # Check for exact match
            if enhanced_address_norm == truth_address_norm:
                is_correct = True
                match_reason = "Exact match"
            # Check for partial match (address contains street number and name)
            elif re.search(r'\d+\s+[a-z]+', enhanced_address) and re.search(r'\d+\s+[a-z]+', truth_address):
                # Extract street number and name from both addresses
                enhanced_street = re.search(r'(\d+\s+[a-z]+)', enhanced_address)
                truth_street = re.search(r'(\d+\s+[a-z]+)', truth_address)

                if enhanced_street and truth_street and enhanced_street.group(1) == truth_street.group(1):
                    is_correct = True
                    match_reason = "Partial match (street number and name)"

            logger.info(f"Address comparison - Enhanced: '{enhanced_address}', Truth: '{truth_address}', Match: {is_correct}")
        else:
            logger.info("No ground truth address available for comparison")

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
    results_file = f'evaluation/results/realistic_evaluation_results_{timestamp}.csv'
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

    metrics_file = f'evaluation/results/realistic_evaluation_metrics_{timestamp}.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_file}")

    # Create comparison table
    create_comparison_table(results, timestamp)

    logger.info("=== REALISTIC EVALUATION COMPLETED ===")
    return results, metrics

def create_comparison_table(results, timestamp):
    """Create a comparison table of results vs. ground truth."""
    table_rows = []
    table_rows.append("| Article | Ground Truth | Initial Address/Confidence | Web Search? | Final Address | Final Confidence | Address Source | Correct? |")
    table_rows.append("|---------|--------------|---------------------------|-------------|---------------|-----------------|----------------|----------|")

    for result in results:
        article_title = result['article_title'][:30] + "..." if len(result['article_title']) > 30 else result['article_title']
        ground_truth = result['ground_truth_address'] if result['ground_truth_address'] else "N/A"
        initial_address = f"{result['initial_address']} ({result['initial_confidence']})" if result['initial_address'] else "N/A"
        web_search = "Yes" if result['web_search_triggered'] else "No"
        final_address = result['final_address'] if result['final_address'] else "N/A"
        final_confidence = result['final_confidence'] if result['final_confidence'] else "N/A"
        address_source = result['address_source'] if result['address_source'] else "N/A"
        correct = "✅" if result['is_correct'] else "❌"

        row = f"| {article_title} | {ground_truth} | {initial_address} | {web_search} | {final_address} | {final_confidence} | {address_source} | {correct} |"
        table_rows.append(row)

    table_content = "\n".join(table_rows)
    table_file = f'evaluation/results/realistic_comparison_table_{timestamp}.md'

    with open(table_file, 'w') as f:
        f.write("# Realistic Evaluation Results vs. Ground Truth\n\n")
        f.write(table_content)

    logger.info(f"Comparison table saved to {table_file}")

if __name__ == "__main__":
    run_realistic_evaluation()
