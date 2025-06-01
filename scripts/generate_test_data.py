#!/usr/bin/env python3
"""
Script to generate test data for the nearby business finder.
"""
import os
import csv
import random
import datetime
from typing import List, Dict

# Define output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample data for generating test incidents
CITIES = [
    {"city": "Los Angeles", "state": "CA", "zip": "90001"},
    {"city": "San Francisco", "state": "CA", "zip": "94103"},
    {"city": "San Diego", "state": "CA", "zip": "92101"},
    {"city": "Sacramento", "state": "CA", "zip": "95814"},
    {"city": "Las Vegas", "state": "NV", "zip": "89101"},
    {"city": "Reno", "state": "NV", "zip": "89501"},
    {"city": "Phoenix", "state": "AZ", "zip": "85001"},
    {"city": "Tucson", "state": "AZ", "zip": "85701"},
    {"city": "Dallas", "state": "TX", "zip": "75201"},
    {"city": "Houston", "state": "TX", "zip": "77002"},
    {"city": "Austin", "state": "TX", "zip": "78701"},
    {"city": "Atlanta", "state": "GA", "zip": "30303"},
    {"city": "Savannah", "state": "GA", "zip": "31401"}
]

STREETS = [
    "Main St", "Broadway", "First Ave", "Second St", "Third Ave", 
    "Fourth St", "Fifth Ave", "Oak St", "Pine Ave", "Maple St",
    "Washington Blvd", "Lincoln Ave", "Jefferson St", "Roosevelt Blvd",
    "Highland Ave", "Sunset Blvd", "Wilshire Blvd", "Market St"
]

BUSINESS_NAMES = [
    "Diamond Exchange", "Gold & Silver Jewelers", "Luxury Watches",
    "Fine Jewelry Co.", "Precious Gems", "Royal Jewelers", "Crown Jewels",
    "Elite Timepieces", "Elegant Designs", "Sparkle & Shine",
    "Golden Touch", "Silver Lining", "Platinum Plus", "Ruby Red",
    "Sapphire Blue", "Emerald Green", "Pearl White", "Crystal Clear"
]

CRIME_TYPES = [
    "robbery", "burglary", "theft", "smash-and-grab"
]

METHODS = [
    "armed robbery", "overnight break-in", "smash-and-grab", "distraction theft",
    "forced entry", "lock picking", "window smash", "door forced"
]

def generate_address() -> str:
    """Generate a random address."""
    number = random.randint(100, 9999)
    street = random.choice(STREETS)
    city_data = random.choice(CITIES)
    return f"{number} {street}, {city_data['city']}, {city_data['state']} {city_data['zip']}"

def generate_test_incident() -> Dict:
    """Generate a test incident."""
    business_name = random.choice(BUSINESS_NAMES)
    address = generate_address()
    crime_type = random.choice(CRIME_TYPES)
    method = random.choice(METHODS)
    
    # Generate a random date within the last year
    days_ago = random.randint(1, 365)
    incident_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Generate a random value for the stolen items
    value = f"${random.randint(1, 100)},{random.randint(0, 999):03d}"
    
    return {
        "crimeType": crime_type,
        "method": method,
        "target": "jewelry store",
        "storeType": "retail jewelry store",
        "businessName": business_name,
        "detailedLocation": address,
        "estimatedValue": value,
        "numSuspects": str(random.randint(1, 5)),
        "characteristics": "suspects fled in a vehicle",
        "incidentDate": incident_date,
        "dateOfArticle": datetime.datetime.now().strftime("%Y-%m-%d"),
        "summary": f"A {crime_type} occurred at {business_name} located at {address}. The suspects used {method} to steal merchandise valued at {value}.",
        "valueScore": random.randint(1, 5),
        "recencyScore": random.randint(1, 5),
        "totalScore": random.randint(1, 10),
        "entryMethod": method,
        "exactAddress": address,
        "addressConfidence": "high",
        "addressSource": "police report",
        "salesPitchHeadline": "PROTECT YOUR INVESTMENT: Comprehensive Security for Jewelry Businesses",
        "comparableIncident": "Similar patterns emerging in retail jewelry crime statistics nationwide",
        "riskAssessment": "HIGH: Immediate security upgrades recommended",
        "businessImpactScore": random.randint(1, 10),
        "businessImpactAreas": "Inventory loss, property damage, business interruption",
        "securityRecommendation": "Comprehensive security assessment and tailored prevention strategies",
        "interestingFactForSales": "Jewelry crimes are among the most profitable and targeted retail crimes nationwide",
        "article_id": random.randint(1, 1000),
        "analyzed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "businessNameConfidence": "high",
        "businessInferenceReasoning": ""
    }

def generate_batch(batch_size: int, batch_number: int) -> str:
    """
    Generate a batch of test incidents and save to CSV.
    
    Args:
        batch_size: Number of incidents to generate
        batch_number: Batch number for filename
        
    Returns:
        str: Path to the generated CSV file
    """
    incidents = [generate_test_incident() for _ in range(batch_size)]
    
    # Generate a timestamp for the output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"test_batch_{batch_number}_{timestamp}.csv")
    
    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        if incidents:
            fieldnames = incidents[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(incidents)
    
    print(f"Generated {batch_size} test incidents in {output_file}")
    return output_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for the nearby business finder')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of incidents per batch')
    parser.add_argument('--num-batches', type=int, default=1, help='Number of batches to generate')
    
    args = parser.parse_args()
    
    for i in range(args.num_batches):
        generate_batch(args.batch_size, i+1)
