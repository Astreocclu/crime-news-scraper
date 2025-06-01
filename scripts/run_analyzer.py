#!/usr/bin/env python
"""
Run the analyzer on a limited number of articles.

This script is a simple wrapper around the SingleBatchAnalyzer class that allows
running the analyzer on a specific number of articles from a CSV file.

Usage:
    python run_analyzer.py --input-file FILE [--batch-size SIZE]

Options:
    --input-file    Specify an input CSV file for analysis
    --batch-size    Number of articles to process in one batch (default: 10)
"""

import argparse
import logging
import os
import sys
import json
import re
import shutil
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run analyzer on a limited number of articles')
    parser.add_argument('--input-file', type=str, required=True, help='Input CSV file for analysis')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of articles to process in one batch')
    return parser.parse_args()

def analyze_articles(input_file, batch_size=10):
    """Analyze articles from a CSV file."""
    try:
        # Load API key from environment variable
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            return False

        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)

        # Read the CSV file
        df = pd.read_csv(input_file)
        logger.info(f"Found {len(df)} articles in {input_file}")

        # Limit to batch_size
        if len(df) > batch_size:
            df = df.head(batch_size)
            logger.info(f"Limiting to {batch_size} articles")

        # Fill empty fields with default values
        df['excerpt'] = df['excerpt'].fillna('No excerpt available')
        df['date'] = df['date'].fillna('')
        df['keywords'] = df['keywords'].fillna('')

        # Process each article
        results = []
        for idx, article in df.iterrows():
            try:
                logger.info(f"\nAnalyzing article {idx + 1}: {article['title']}")
                logger.info(f"Location: {article['location']}")
                logger.info(f"URL: {article['url']}")

                # Create the analysis prompt
                prompt = create_analysis_prompt(article)

                # Get analysis from Claude
                try:
                    response = client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=4000,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=30  # 30 second timeout
                    )

                    # Extract the analysis
                    analysis_text = response.content[0].text
                    logger.info(f"Received response from Claude")

                    # Extract JSON from the response
                    json_match = None
                    for pattern in [r'```json\s*({.*?})\s*```', r'{.*}']:
                        import re
                        matches = re.findall(pattern, analysis_text, re.DOTALL)
                        if matches:
                            for match in matches:
                                try:
                                    json.loads(match)  # Test if it's valid JSON
                                    json_match = match
                                    break
                                except:
                                    continue
                        if json_match:
                            break

                    if json_match:
                        analysis = json.loads(json_match)

                        # Add article ID and timestamp
                        analysis['article_id'] = idx
                        analysis['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Add the article title and URL for reference
                        analysis['article_title'] = article['title']
                        analysis['article_url'] = article['url']

                        results.append(analysis)
                        logger.info(f"Successfully analyzed article {idx + 1}")
                    else:
                        logger.warning(f"Could not extract JSON from Claude response for article {idx + 1}")

                except Exception as e:
                    logger.error(f"Error calling Claude API for article {idx + 1}: {str(e)}")

            except Exception as e:
                logger.error(f"Error processing article {idx + 1}: {str(e)}")

        # Save results to CSV
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join('output', 'analysis')
            os.makedirs(output_dir, exist_ok=True)

            output_file = os.path.join(output_dir, f'analyzed_articles_{timestamp}.csv')
            pd.DataFrame(results).to_csv(output_file, index=False)
            logger.info(f"\nSaved {len(results)} analyzed articles to {output_file}")

            # Also save as JSON for easier inspection
            json_file = os.path.join(output_dir, f'analyzed_articles_{timestamp}.json')
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved analysis results as JSON to {json_file}")

            # Generate a summary file
            summary_file = os.path.join(output_dir, f'analysis_summary_{timestamp}.txt')
            with open(summary_file, 'w') as f:
                f.write(f"Analysis Summary\n")
                f.write(f"===============\n\n")
                f.write(f"Total articles analyzed: {len(results)}\n")
                f.write(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Write summary for each article
                for i, analysis in enumerate(results):
                    f.write(f"Article {i+1}: {analysis.get('article_title', 'No title')}\n")
                    f.write(f"URL: {analysis.get('article_url', 'No URL')}\n")
                    f.write(f"Crime Type: {analysis.get('crimeType', 'Unknown')}\n")
                    f.write(f"Method: {analysis.get('method', 'Unknown')}\n")
                    f.write(f"Target: {analysis.get('target', 'Unknown')}\n")
                    f.write(f"Business Name: {analysis.get('businessName', 'N/A')}\n")
                    f.write(f"Location: {analysis.get('detailedLocation', 'Unknown')}\n")
                    f.write(f"Summary: {analysis.get('summary', 'No summary available')}\n")
                    f.write(f"Lead Quality Score: {analysis.get('totalScore', 'Not scored')}\n\n")

            logger.info(f"Generated analysis summary: {summary_file}")

            return True
        else:
            logger.warning("No articles were successfully analyzed")
            return False

    except Exception as e:
        logger.error(f"Error analyzing articles: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_analysis_prompt(article):
    """Create a prompt for analyzing a single article."""
    # Handle keywords as a comma-separated string
    keywords = article.get('keywords', '')
    keywords_str = keywords if keywords else 'None'

    # Get excerpt
    excerpt = article.get('excerpt', 'No excerpt available')

    prompt = f"""
    Please analyze this crime article and extract key information:

    Title: {article.get('title', '')}
    Location: {article.get('location', '')}
    Date: {article.get('date', 'Not available')}
    Keywords: {keywords_str}
    Excerpt: {excerpt}
    Source: {article.get('source', '')}
    Is Theft Related: {article.get('is_theft_related', '')}
    Is Business Related: {article.get('is_business_related', '')}

    Please provide:
    1. Type of crime (e.g., robbery, burglary, theft)
    2. Method used (e.g., smash and grab, armed robbery)
    3. Target (e.g., jewelry store, individual)
    4. Store type (e.g., retail jewelry store, pawn shop, luxury boutique)
    5. Business name of the victimized store
    6. Detailed location information (address, city, state, landmarks)
    7. Estimated value of items (if mentioned)
    8. Number of suspects involved
    9. Any unique characteristics or patterns
    10. Date of the incident (if mentioned in the article or can be inferred)
    11. Date of article (when the article was published)
    12. A brief summary of the incident
    13. Lead quality score (1-10) based on:
        - Value score (1-5): Higher for more valuable items
        - Recency score (1-5): Higher for more recent incidents
    14. Method of entry used by criminals

    Format the response as a JSON object with these fields:
    {{
        "crimeType": "type of crime",
        "method": "method used",
        "target": "target of the crime",
        "storeType": "type of store",
        "businessName": "name of the business",
        "detailedLocation": "detailed location information",
        "estimatedValue": "estimated value",
        "numSuspects": "number of suspects",
        "characteristics": "unique characteristics",
        "incidentDate": "date of the incident",
        "dateOfArticle": "when the article was published",
        "summary": "brief summary of the incident",
        "valueScore": "score from 1-5 based on value",
        "recencyScore": "score from 1-5 based on recency",
        "totalScore": "total score from 1-10",
        "entryMethod": "method used to enter premises"
    }}
    """
    return prompt

def organize_output_folders():
    """Create and organize output folders for analysis and scraping."""
    # Create main output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Create subdirectories
    analysis_dir = os.path.join('output', 'analysis')
    scraping_dir = os.path.join('output', 'scraping')
    os.makedirs(analysis_dir, exist_ok=True)
    os.makedirs(scraping_dir, exist_ok=True)

    logger.info(f"Created output directories: {analysis_dir} and {scraping_dir}")

    # Move existing CSV files to appropriate folders
    for filename in os.listdir('output'):
        if not os.path.isfile(os.path.join('output', filename)):
            continue

        # Skip files in subdirectories
        if '/' in filename or '\\' in filename:
            continue

        file_path = os.path.join('output', filename)

        # Move analysis files
        if filename.startswith('analyzed_') or filename.startswith('analysis_'):
            # Skip if it's the file we just created
            if 'articles_' + datetime.now().strftime('%Y%m%d') in filename:
                shutil.copy2(file_path, os.path.join(analysis_dir, filename))
                os.remove(file_path)
                logger.info(f"Moved recent analysis file to analysis folder: {filename}")
            else:
                # Remove old analysis files
                os.remove(file_path)
                logger.info(f"Removed old analysis file: {filename}")

        # Move scraping files
        elif filename.endswith('.csv') and not filename.startswith('analyzed_'):
            shutil.copy2(file_path, os.path.join(scraping_dir, filename))
            logger.info(f"Moved scraping file to scraping folder: {filename}")

def clean_old_files():
    """Clean up old analysis files while preserving the most recent ones."""
    # Get today's date for comparison
    today = datetime.now().strftime('%Y%m%d')

    # Clean analysis directory
    analysis_dir = os.path.join('output', 'analysis')
    if os.path.exists(analysis_dir):
        # Group files by date in their filename
        files_by_date = {}
        for filename in os.listdir(analysis_dir):
            if not os.path.isfile(os.path.join(analysis_dir, filename)):
                continue

            # Extract date from filename (format: YYYYMMDD)
            date_match = re.search(r'\d{8}', filename)
            if date_match:
                file_date = date_match.group(0)
                if file_date not in files_by_date:
                    files_by_date[file_date] = []
                files_by_date[file_date].append(filename)

        # Keep only today's files and the most recent file from each previous date
        for file_date, filenames in files_by_date.items():
            if file_date == today:
                # Keep all of today's files
                continue

            # Sort files by timestamp (assuming format with timestamp after date)
            filenames.sort(reverse=True)

            # Keep only the most recent file from each date
            for filename in filenames[1:]:  # Skip the first (most recent) file
                file_path = os.path.join(analysis_dir, filename)
                os.remove(file_path)
                logger.info(f"Removed old analysis file: {filename}")

def main():
    """Main entry point for the script."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Organize output folders
        organize_output_folders()

        # Clean up old files
        clean_old_files()

        # Run the analyzer
        logger.info(f"Running analyzer on {args.input_file} with batch size {args.batch_size}")
        success = analyze_articles(args.input_file, args.batch_size)

        if success:
            logger.info("Analysis completed successfully")
        else:
            logger.error("Analysis failed")

    except Exception as e:
        logger.error(f"Error running analyzer: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
