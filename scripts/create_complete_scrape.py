#!/usr/bin/env python3
"""
Create a comprehensive 'Complete Scrape' file that combines all locations found.
"""
import os
import pandas as pd
import glob
from datetime import datetime

def main():
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Output file path
    output_file = f"output/Complete_Scrape_{timestamp}.csv"

    print(f"Creating comprehensive 'Complete Scrape' file: {output_file}")

    # Find the most recent JSA articles file (main source of crime data)
    jsa_files = sorted(glob.glob("output/jsa_articles_*.csv"), key=os.path.getmtime, reverse=True)
    if not jsa_files:
        print("No JSA articles files found!")
        return

    jsa_file = jsa_files[0]
    print(f"Using JSA articles file: {jsa_file}")

    # Find the most recent nearby businesses file
    nearby_files = sorted(glob.glob("output/nearby/nearby_businesses_*.csv"), key=os.path.getmtime, reverse=True)
    if not nearby_files:
        print("No nearby businesses files found!")
        return

    nearby_file = nearby_files[0]
    print(f"Using nearby businesses file: {nearby_file}")

    # Read the JSA articles file
    try:
        jsa_df = pd.read_csv(jsa_file)
        print(f"Read {len(jsa_df)} rows from JSA articles file")
    except Exception as e:
        print(f"Error reading JSA file: {e}")
        jsa_df = pd.DataFrame()

    # Read the nearby businesses file
    try:
        nearby_df = pd.read_csv(nearby_file)
        print(f"Read {len(nearby_df)} rows from nearby businesses file")
    except Exception as e:
        print(f"Error reading nearby businesses file: {e}")
        nearby_df = pd.DataFrame()

    # Create a comprehensive DataFrame
    all_locations = []

    # Add locations from JSA articles
    if not jsa_df.empty:
        for _, row in jsa_df.iterrows():
            # Get the best available address for detailed_location
            detailed_location = ''

            # First try exactAddress if available (from analyzer)
            if 'exactAddress' in row and row.get('exactAddress'):
                detailed_location = row.get('exactAddress')
            # Then try detailed_location
            elif 'detailed_location' in row and row.get('detailed_location'):
                detailed_location = row.get('detailed_location')
            # Then try constructing from business_name and location
            elif 'business_name' in row and row.get('business_name') and 'location' in row and row.get('location'):
                detailed_location = f"{row.get('business_name')}, {row.get('location')}"

            location_data = {
                'source': 'JSA Article',
                'location': row.get('location', ''),
                'detailed_location': detailed_location,
                'business_name': row.get('business_name', ''),
                'store_type': row.get('store_type', ''),
                'is_theft_related': row.get('is_theft_related', False),
                'is_business_related': row.get('is_business_related', False),
                'title': row.get('title', ''),
                'date': row.get('date', ''),
                'url': row.get('url', ''),
                'excerpt': row.get('excerpt', '')
            }
            all_locations.append(location_data)

    # Add locations from nearby businesses
    if not nearby_df.empty:
        for _, row in nearby_df.iterrows():
            location_data = {
                'source': 'Nearby Business',
                'location': '',  # No general location in nearby businesses file
                'detailed_location': row.get('exactAddress', ''),
                'business_name': row.get('businessName', ''),
                'store_type': row.get('category', ''),
                'is_theft_related': row.get('record_type', '') == 'victim',
                'is_business_related': True,
                'title': '',
                'date': '',
                'url': '',
                'excerpt': f"Distance from incident: {row.get('distance_from_incident', '')} miles, Status: {row.get('business_status', '')}"
            }
            all_locations.append(location_data)

    # Create DataFrame from all locations
    complete_df = pd.DataFrame(all_locations)

    # Save to CSV
    complete_df.to_csv(output_file, index=False)
    print(f"Saved {len(complete_df)} locations to {output_file}")

if __name__ == "__main__":
    main()
