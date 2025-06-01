#!/usr/bin/env python3
"""
Script to rename output files to a more human-readable format.
Converts filenames from patterns like 'analyzed_leads_20250329_121339.csv'
to more readable formats like '20250329-AnalyzedLeads.csv'
"""

import os
import re
import glob
from pathlib import Path
from collections import defaultdict

# Define the output directory
OUTPUT_DIR = Path("/home/reid/projects/crime-news-scraper/output")

# Define patterns to match and their replacements
PATTERNS = [
    # Analysis results
    (r'analysis_results_(\d{8})_(\d{6})\.csv', r'\1-AnalysisResults.csv'),
    (r'analysis_summary_(\d{8})_(\d{6})\.txt', r'\1-AnalysisSummary.txt'),
    (r'analyzed_leads_(\d{8})_(\d{6})\.json', r'\1-AnalyzedLeads.json'),
    (r'analyzed_leads_(\d{8})_(\d{6})\.csv', r'\1-AnalyzedLeads.csv'),
    (r'analyzed_leads_single_batch_(\d{8})_(\d{6})\.json', r'\1-AnalyzedLeadsBatch.json'),
    (r'analyzed_leads_single_batch_(\d{8})_(\d{6})\.csv', r'\1-AnalyzedLeadsBatch.csv'),

    # Scraped data
    (r'Complete_Scrape_(\d{8})_(\d{6})\.csv', r'\1-CompleteScrape.csv'),
    (r'(\w+)_articles_(\d{8})_(\d{6})\.csv', r'\2-\1Articles.csv'),

    # Nearby businesses
    (r'nearby_businesses_(\d{8})_(\d{6})\.csv', r'\1-NearbyBusinesses.csv'),

    # Reports
    (r'enhanced_web_search_results_(\d{8})_(\d{6})\.json', r'\1-WebSearchResults.json'),
    (r'web_search_diagnostics_(\d{8})_(\d{6})\.json', r'\1-WebSearchDiagnostics.json'),

    # DFW theft news
    (r'dfw_theft_news_(\d{8})_(\d{6})\.csv', r'\1-DFWTheftNews.csv'),
]

# Additional patterns for files that might have been missed
ADDITIONAL_PATTERNS = [
    # Any remaining files with date patterns
    (r'.*_(\d{8})_(\d{6})\.(csv|json|txt)', r'\1-\3'),
]

def rename_files():
    """Rename files in the output directory to a more human-readable format."""
    # Count of renamed files
    renamed_count = 0
    skipped_count = 0

    # Keep track of file counts by base name to handle duplicates
    file_counts = defaultdict(int)

    # First pass: collect all files and their new names
    rename_map = {}

    # Walk through all subdirectories in the output directory
    for root, _, files in os.walk(OUTPUT_DIR):
        for filename in files:
            # Skip .gitkeep files
            if filename == '.gitkeep':
                continue

            # Get the full path to the file
            old_path = os.path.join(root, filename)

            # Try to match the filename against our patterns
            new_filename = filename
            matched = False

            # Try main patterns first
            for pattern, replacement in PATTERNS:
                if re.match(pattern, filename):
                    new_filename = re.sub(pattern, replacement, filename)
                    matched = True
                    break

            # If no match found, try additional patterns
            if not matched:
                for pattern, replacement in ADDITIONAL_PATTERNS:
                    match = re.match(pattern, filename)
                    if match:
                        # Extract the file type from the original name
                        file_type = filename.split('_')[0].capitalize()
                        if '_' in filename:
                            new_filename = f"{match.group(1)}-{file_type}.{match.group(3)}"
                        else:
                            new_filename = f"{match.group(1)}-File.{match.group(3)}"
                        matched = True
                        break

            # If the filename was changed, add it to our rename map
            if new_filename != filename:
                new_path = os.path.join(root, new_filename)

                # Check if the new filename already exists or is a duplicate
                base_name = os.path.splitext(new_filename)[0]
                if os.path.exists(new_path) or base_name in [os.path.splitext(n)[0] for n in rename_map.values()]:
                    # Add a sequence number to make it unique
                    file_counts[base_name] += 1
                    name, ext = os.path.splitext(new_filename)
                    new_filename = f"{name}-{file_counts[base_name]}{ext}"
                    new_path = os.path.join(root, new_filename)

                rename_map[old_path] = new_filename

    # Second pass: perform the actual renames
    for old_path, new_filename in rename_map.items():
        root = os.path.dirname(old_path)
        filename = os.path.basename(old_path)
        new_path = os.path.join(root, new_filename)

        print(f"Renaming: {filename} -> {new_filename}")

        try:
            os.rename(old_path, new_path)
            renamed_count += 1
        except Exception as e:
            print(f"  Error: {e}")
            skipped_count += 1

    print(f"\nRenamed {renamed_count} files, skipped {skipped_count} files")

def cleanup_remaining_files():
    """Find any files that still have the old naming pattern and rename them."""
    # Look for files with the pattern *_YYYYMMDD_HHMMSS.*
    pattern = re.compile(r'.*_(\d{8})_(\d{6})\.(csv|json|txt)')
    renamed_count = 0

    for root, _, files in os.walk(OUTPUT_DIR):
        for filename in files:
            if filename == '.gitkeep':
                continue

            match = pattern.match(filename)
            if match:
                old_path = os.path.join(root, filename)
                date = match.group(1)
                ext = match.group(3)

                # Extract a meaningful name from the filename
                name_part = filename.split('_')[0].capitalize()
                new_filename = f"{date}-{name_part}.{ext}"

                # Check if the new filename already exists
                new_path = os.path.join(root, new_filename)
                if os.path.exists(new_path):
                    # Add a sequence number
                    i = 1
                    while os.path.exists(os.path.join(root, f"{date}-{name_part}-{i}.{ext}")):
                        i += 1
                    new_filename = f"{date}-{name_part}-{i}.{ext}"
                    new_path = os.path.join(root, new_filename)

                print(f"Cleanup: {filename} -> {new_filename}")
                try:
                    os.rename(old_path, new_path)
                    renamed_count += 1
                except Exception as e:
                    print(f"  Error: {e}")

    if renamed_count > 0:
        print(f"\nCleaned up {renamed_count} additional files")

if __name__ == "__main__":
    rename_files()
    cleanup_remaining_files()
