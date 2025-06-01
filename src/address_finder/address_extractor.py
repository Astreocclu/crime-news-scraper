#!/usr/bin/env python
"""
Command-Line LLM: Crime Article Address Extraction & Geocoding

This script implements the tasks outlined in tasks.md:
1. Input Acquisition & Preprocessing
2. Address Inference using LLM
3. Address Verification & Geocoding via Google API
4. Output Results

Usage:
    python -m src.address_finder.address_extractor --text "Article text..."
    python -m src.address_finder.address_extractor --file /path/to/article.txt
    python -m src.address_finder.address_extractor --url http://example.com/article
    
    Additional context can be provided:
    python -m src.address_finder.address_extractor --text "..." --city "Dallas" --state "TX"
"""
import argparse
import json
import os
import sys
import requests
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.address_finder import EnhancedAddressFinder
from src.utils.logger import get_logger

# Get a configured logger for this module
logger = get_logger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract and geocode addresses from crime news articles"
    )
    
    # Input methods (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text",
        type=str,
        help="Direct text input containing the article content"
    )
    input_group.add_argument(
        "--file",
        type=str,
        help="Path to a file containing the article content"
    )
    input_group.add_argument(
        "--url",
        type=str,
        help="URL to scrape for article content"
    )
    
    # Additional context
    parser.add_argument(
        "--city",
        type=str,
        help="City context to improve geocoding accuracy"
    )
    parser.add_argument(
        "--state",
        type=str,
        help="State context to improve geocoding accuracy"
    )
    
    # Output format
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)"
    )
    
    return parser.parse_args()

def load_content_from_file(file_path: str) -> str:
    """
    Load content from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Content of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully loaded content from file: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {str(e)}")
        print(f"Error: Could not load file {file_path}: {str(e)}")
        sys.exit(1)

def fetch_content_from_url(url: str) -> str:
    """
    Fetch content from a URL.
    
    Args:
        url: URL to fetch
        
    Returns:
        str: Content of the URL
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
            
        # Fetch content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple HTML cleaning (extract text from HTML)
        # This is a very basic approach - a real implementation would use a proper HTML parser
        content = response.text
        
        logger.info(f"Successfully fetched content from URL: {url}")
        return content
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        print(f"Error: Could not fetch URL {url}: {str(e)}")
        sys.exit(1)

def basic_cleaning(text: str) -> str:
    """
    Perform basic cleaning on the text.
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove excessive whitespace
    cleaned_text = ' '.join(text.split())
    
    # Remove common HTML tags if present
    # This is a very basic approach - a real implementation would use a proper HTML parser
    html_tags = ['<p>', '</p>', '<div>', '</div>', '<span>', '</span>', '<br>', '<br/>', '<hr>', '<hr/>']
    for tag in html_tags:
        cleaned_text = cleaned_text.replace(tag, ' ')
    
    return cleaned_text

def format_output(result: Dict, output_format: str) -> str:
    """
    Format the result according to the specified output format.
    
    Args:
        result: The result to format
        output_format: The output format (text, json, csv)
        
    Returns:
        str: Formatted output
    """
    if output_format == "json":
        return json.dumps(result, indent=2)
    
    elif output_format == "csv":
        if result.get("success", False):
            # Create CSV header and row
            header = "inferred_query,formatted_address,lat,lng,confidence,place_id,name,phone_number,website"
            row = f"{result.get('original_query', '')},{result.get('formatted_address', '')},{result.get('lat', '')},{result.get('lng', '')},{result.get('confidence', '')},{result.get('place_id', '')},{result.get('name', '')},{result.get('phone_number', '')},{result.get('website', '')}"
            return f"{header}\n{row}"
        else:
            return f"success,reason\nFalse,{result.get('reason', 'Unknown reason')}"
    
    else:  # text format
        if result.get("success", False):
            output = "\nAddress Extraction Results:\n"
            output += f"Inferred: \"{result.get('original_query', '')}\" -> "
            output += f"Verified: \"{result.get('formatted_address', '')}\" "
            output += f"(Lat: {result.get('lat', '')}, Lng: {result.get('lng', '')})\n"
            
            if result.get("name"):
                output += f"Business Name: {result['name']}\n"
            if result.get("phone_number"):
                output += f"Phone: {result['phone_number']}\n"
            if result.get("website"):
                output += f"Website: {result['website']}\n"
                
            output += f"Confidence: {result.get('confidence', 0)}\n"
            return output
        else:
            return f"\nAddress Extraction Failed: {result.get('reason', 'Unknown reason')}\n"

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Initialize the enhanced address finder
    finder = EnhancedAddressFinder()
    
    # Task 1: Input Acquisition & Preprocessing
    if args.text:
        # Direct text input
        text = args.text
        logger.info("Using direct text input")
    elif args.file:
        # File input
        text = load_content_from_file(args.file)
        logger.info(f"Loaded content from file: {args.file}")
    elif args.url:
        # URL input
        text = fetch_content_from_url(args.url)
        logger.info(f"Fetched content from URL: {args.url}")
    else:
        # This should never happen due to the mutually exclusive group being required
        logger.error("No input method specified")
        print("Error: Please specify an input method (--text, --file, or --url)")
        sys.exit(1)
    
    # Basic cleaning
    text = basic_cleaning(text)
    
    # Add city/state context if provided
    context = ""
    if args.city:
        context += f" in {args.city}"
    if args.state:
        context += f", {args.state}"
    
    if context:
        text += f" The incident occurred{context}."
        logger.info(f"Added context: {context}")
    
    # Task 2 & 3: Address Inference and Verification
    print("Extracting and verifying addresses...")
    result = finder.find_address(text)
    
    # Task 4: Output Results
    formatted_output = format_output(result, args.output_format)
    print(formatted_output)
    
    return 0 if result.get("success", False) else 1

if __name__ == "__main__":
    sys.exit(main())
