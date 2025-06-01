#!/usr/bin/env python
"""
Example script to demonstrate the Enhanced Address Finder.

This script shows how to use the Enhanced Address Finder to extract and
confirm addresses from text.

Usage:
    python -m src.address_finder.example [--text TEXT]
"""
import argparse
import json
import os
import sys
from typing import Dict

from src.address_finder import EnhancedAddressFinder
from src.utils.logger import get_logger

# Get a configured logger for this module
logger = get_logger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Enhanced Address Finder Example")
    parser.add_argument(
        "--text",
        type=str,
        help="Text to analyze for addresses"
    )
    return parser.parse_args()

def main():
    """Main entry point for the example script."""
    args = parse_arguments()
    
    # Initialize the enhanced address finder
    finder = EnhancedAddressFinder()
    
    # Get the text to analyze
    if args.text:
        text = args.text
    else:
        # Use a default example if no text is provided
        text = """
        A jewelry store in South Frisco, TX was robbed yesterday. 
        The store, Diamond Jewelers, is located at the corner of Main Street and 5th Avenue.
        The suspects fled in a car heading towards Dallas.
        """
        print(f"Using default example text:\n{text}\n")
    
    # Find the address
    print("Finding address...")
    result = finder.find_address(text)
    
    # Print the result
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    if result.get("success", False):
        print("\nSuccess! Found address:")
        print(f"Name: {result.get('name', 'N/A')}")
        print(f"Address: {result.get('formatted_address', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0)}")
        if result.get("phone_number"):
            print(f"Phone: {result['phone_number']}")
        if result.get("website"):
            print(f"Website: {result['website']}")
    else:
        print(f"\nFailed to find address: {result.get('reason', 'Unknown reason')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
