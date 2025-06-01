#!/usr/bin/env python3
"""
Mock implementation of the nearby business finder for testing purposes.
"""
import os
import csv
import json
import datetime
from typing import Dict, List, Optional

# Create output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output", "nearby")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_nearby_businesses(address: str, business_name: str, radius: int = 1500) -> List[Dict]:
    """
    Mock implementation of finding nearby businesses.
    
    Args:
        address: The address to search around
        business_name: The name of the business
        radius: The search radius in meters
        
    Returns:
        List of nearby businesses
    """
    print(f"Finding nearby businesses for {business_name} at {address} within {radius} meters")
    
    # Create mock nearby businesses
    nearby_businesses = [
        {
            "name": "Luxury Jewelers",
            "vicinity": "4200 Atlantic Avenue, Long Beach, CA 90807",
            "category": "jewelry",
            "distance": 0.2,
            "business_status": "OPERATIONAL"
        },
        {
            "name": "Diamond Exchange",
            "vicinity": "4050 Atlantic Avenue, Long Beach, CA 90807",
            "category": "jewelry",
            "distance": 0.3,
            "business_status": "OPERATIONAL"
        },
        {
            "name": "Sports Collectibles",
            "vicinity": "4300 Atlantic Avenue, Long Beach, CA 90807",
            "category": "sports_memorabilia",
            "distance": 0.4,
            "business_status": "OPERATIONAL"
        },
        {
            "name": "Luxury Boutique",
            "vicinity": "4150 Atlantic Avenue, Long Beach, CA 90807",
            "category": "luxury_goods",
            "distance": 0.25,
            "business_status": "OPERATIONAL"
        },
        {
            "name": "Closed Jewelry",
            "vicinity": "4100 Atlantic Avenue, Long Beach, CA 90807",
            "category": "jewelry",
            "distance": 0.1,
            "business_status": "CLOSED_PERMANENTLY"
        }
    ]
    
    # Create a timestamp for the output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"nearby_businesses_{timestamp}.csv")
    
    # Create the output CSV
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['record_type', 'businessName', 'exactAddress', 'category', 'distance_from_incident', 'business_status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        # Write the victim business
        writer.writerow({
            'record_type': 'victim',
            'businessName': business_name,
            'exactAddress': address,
            'category': 'jewelry',
            'distance_from_incident': 0.0,
            'business_status': 'OPERATIONAL'
        })
        
        # Write the nearby businesses
        for business in nearby_businesses:
            if business['business_status'] == 'OPERATIONAL':
                writer.writerow({
                    'record_type': 'nearby',
                    'businessName': business['name'],
                    'exactAddress': business['vicinity'],
                    'category': business['category'],
                    'distance_from_incident': business['distance'],
                    'business_status': business['business_status']
                })
    
    print(f"Results saved to {output_file}")
    
    # Return the operational nearby businesses
    return [b for b in nearby_businesses if b['business_status'] == 'OPERATIONAL']

def main():
    """Main entry point for the mock nearby business finder."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mock implementation of finding nearby businesses')
    parser.add_argument('--address', required=True, help='Address to search around')
    parser.add_argument('--business-name', required=True, help='Name of the business')
    parser.add_argument('--radius', type=int, default=1500, help='Search radius in meters')
    
    args = parser.parse_args()
    
    nearby_businesses = find_nearby_businesses(args.address, args.business_name, args.radius)
    
    print(f"Found {len(nearby_businesses)} nearby businesses:")
    for business in nearby_businesses:
        print(f"- {business['name']} ({business['category']}) at {business['vicinity']}")

if __name__ == "__main__":
    main()
