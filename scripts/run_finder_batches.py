#!/usr/bin/env python3
"""
Script to run the nearby business finder in batches.
"""
import os
import subprocess
import time
import pandas as pd
from typing import List, Dict

# Import the test data generator
from generate_test_data import generate_batch

def run_finder(input_file: str, verbose: bool = True) -> str:
    """
    Run the nearby business finder on the input file.
    
    Args:
        input_file: Path to the input CSV file
        verbose: Whether to enable verbose logging
        
    Returns:
        str: Path to the output CSV file, or empty string if failed
    """
    cmd = ["python3", "-m", "src.nearby_finder.finder", "--input-file", input_file]
    if verbose:
        cmd.append("--verbose")
    
    print(f"Running finder on {input_file}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running finder: {result.stderr}")
        return ""
    
    # Extract the output file path from the output
    for line in result.stdout.split("\n"):
        if line.startswith("Success! Results saved to:"):
            output_file = line.split(":", 1)[1].strip()
            print(f"Finder completed successfully. Output saved to {output_file}")
            return output_file
    
    print("Could not find output file path in finder output")
    return ""

def count_original_locations(output_files: List[str]) -> int:
    """
    Count the number of original locations in the output files.
    
    Args:
        output_files: List of output CSV files
        
    Returns:
        int: Number of original locations
    """
    count = 0
    for file in output_files:
        try:
            df = pd.read_csv(file)
            count += len(df[df['is_original_location'] == True])
        except Exception as e:
            print(f"Error reading {file}: {str(e)}")
    
    return count

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the nearby business finder in batches')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of incidents per batch')
    parser.add_argument('--target-count', type=int, default=20, help='Target number of original locations')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    output_files = []
    batch_number = 1
    
    while count_original_locations(output_files) < args.target_count:
        print(f"\nBatch {batch_number}: Generating test data...")
        input_file = generate_batch(args.batch_size, batch_number)
        
        print(f"Batch {batch_number}: Running finder...")
        output_file = run_finder(input_file, args.verbose)
        
        if output_file:
            output_files.append(output_file)
            
        current_count = count_original_locations(output_files)
        print(f"Batch {batch_number} completed. Current count: {current_count}/{args.target_count} original locations")
        
        batch_number += 1
        
        # Sleep briefly to avoid overwhelming the system
        time.sleep(1)
    
    # Print summary
    total_original = count_original_locations(output_files)
    
    # Count nearby locations
    total_nearby = 0
    for file in output_files:
        try:
            df = pd.read_csv(file)
            total_nearby += len(df[df['is_original_location'] == False])
        except Exception as e:
            print(f"Error reading {file}: {str(e)}")
    
    print("\nSummary:")
    print(f"Total batches processed: {batch_number - 1}")
    print(f"Total original locations: {total_original}")
    print(f"Total nearby locations: {total_nearby}")
    print(f"Output files:")
    for file in output_files:
        print(f"  - {file}")

if __name__ == "__main__":
    main()
