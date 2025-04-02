"""
Main module for finding nearby businesses based on analyzed crime incidents.

This module processes analyzed crime incident CSV files, identifies nearby
high-value retail locations using Google Maps API, and produces a single
comprehensive CSV that includes both original incidents and nearby businesses
for efficient sales outreach.
"""
import argparse
import csv
import os
import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.nearby_finder.google_client import GoogleMapsClient
from src.nearby_finder.config import OUTPUT_DIR
from src.utils.logger import get_logger, log_execution_time
from src.utils.exceptions import NearbyFinderError, NearbyFinderAPIError

# Get a configured logger for this module
logger = get_logger(__name__)

class NearbyBusinessFinder:
    """Find nearby businesses around crime incident locations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the nearby business finder."""
        self.google_client = GoogleMapsClient(api_key)
        self.ensure_output_dir()
        
    def ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    @log_execution_time(logger, "NearbyBusinessFinder: ")
    def find_nearby_businesses(self, input_file: str):
        """
        Process analyzed crime incidents and find nearby businesses.
        
        Args:
            input_file: Path to the CSV file with analyzed crime incidents
            
        Returns:
            str: Path to the output CSV file with combined incident and nearby business data
            
        Raises:
            NearbyFinderError: If there's an error processing the input file
        """
        # Generate a timestamp for the output file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"nearby_businesses_{timestamp}.csv")
        
        logger.info(f"Processing analyzed file: {input_file}")
        logger.info(f"Output will be saved to: {output_file}")
        
        try:
            # Read the analyzed incidents CSV
            incidents_df = pd.read_csv(input_file)
            logger.info(f"Read {len(incidents_df)} incidents from input file")
            
            # Track statistics for logging
            stats = {
                'total_incidents': len(incidents_df),
                'incidents_with_address': 0,
                'successful_geocodes': 0,
                'total_nearby_businesses': 0,
                'locations_by_type': {}
            }
            
            # Create a new list for the combined results
            combined_results = []
            
            # Process each incident
            logger.info(f"Beginning to process {len(incidents_df)} incidents")
            for idx, incident in incidents_df.iterrows():
                # Log progress at intervals
                if idx > 0 and idx % 10 == 0:
                    logger.info(f"Processed {idx}/{len(incidents_df)} incidents")
                
                # First add the original incident to the results
                incident_data = incident.to_dict()
                incident_data['record_type'] = 'incident'
                incident_data['distance_from_incident'] = 0.0
                combined_results.append(incident_data)
                
                # Find nearby businesses for this incident
                address = self._get_best_address(incident)
                if not address:
                    logger.warning(f"No address found for incident #{idx+1}: {incident.get('title', 'Unnamed')}")
                    continue
                    
                stats['incidents_with_address'] += 1
                
                # Default missing fields - this helps handle different CSV formats
                for field in ['businessName', 'businessType', 'exactAddress']:
                    if field not in incident_data:
                        incident_data[field] = ''
                
                logger.info(f"Finding nearby businesses for: {address}")
                
                try:
                    # Get coordinates for the address
                    coordinates = self.google_client.geocode_address(address)
                    if not coordinates:
                        logger.warning(f"Could not geocode address: {address}")
                        continue
                        
                    stats['successful_geocodes'] += 1
                    logger.debug(f"Geocoded {address} to lat: {coordinates['lat']}, lng: {coordinates['lng']}")
                    
                    # Find nearby businesses
                    nearby_places = self.google_client.find_nearby_businesses(
                        coordinates['lat'],
                        coordinates['lng']
                    )
                    
                    logger.info(f"Found {len(nearby_places)} nearby businesses for {address}")
                    stats['total_nearby_businesses'] += len(nearby_places)
                    
                    # Process each nearby business
                    for place in nearby_places:
                        # Track business type statistics
                        place_category = place.get('category', 'unknown')
                        if place_category not in stats['locations_by_type']:
                            stats['locations_by_type'][place_category] = 0
                        stats['locations_by_type'][place_category] += 1
                        
                        # Get detailed information about the place
                        if place.get('place_id'):
                            details = self.google_client.get_place_details(place['place_id'])
                        else:
                            details = {}
                        
                        # Create a new row with both incident data and nearby business data
                        nearby_data = incident_data.copy()
                        
                        # Mark as a nearby business
                        nearby_data['record_type'] = 'nearby'
                        
                        # Calculate and add distance information
                        distance = self._calculate_distance(
                            coordinates['lat'], coordinates['lng'],
                            place
                        )
                        nearby_data['distance_from_incident'] = distance
                        
                        # Replace business info with nearby business info
                        nearby_data['businessName'] = place.get('name', '')
                        nearby_data['exactAddress'] = details.get('formatted_address', place.get('vicinity', ''))
                        nearby_data['businessType'] = place.get('category', '')
                        
                        # Add to combined results
                        combined_results.append(nearby_data)
                        
                except NearbyFinderAPIError as api_e:
                    logger.error(f"API error processing {address}: {str(api_e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing {address}: {str(e)}", exc_info=True)
                    continue
            
            # Log processing statistics
            logger.info(f"Processing statistics:")
            logger.info(f"- Total incidents: {stats['total_incidents']}")
            logger.info(f"- Incidents with valid addresses: {stats['incidents_with_address']}")
            logger.info(f"- Successful geocode operations: {stats['successful_geocodes']}")
            logger.info(f"- Total nearby businesses found: {stats['total_nearby_businesses']}")
            
            # Log business type breakdown
            if stats['locations_by_type']:
                logger.info("Business type breakdown:")
                for biz_type, count in stats['locations_by_type'].items():
                    logger.info(f"- {biz_type}: {count}")
            
            # Convert to DataFrame and save to CSV
            results_df = pd.DataFrame(combined_results)
            results_df.to_csv(output_file, index=False)
            
            logger.info(f"Found {len(results_df) - len(incidents_df)} nearby businesses")
            logger.info(f"Final results saved to {output_file}")
            
            return output_file
            
        except Exception as e:
            error_msg = f"Error processing input file {input_file}: {str(e)}"
            logger.exception(error_msg)
            raise NearbyFinderError(error_msg) from e
            
    def _get_best_address(self, incident) -> Optional[str]:
        """
        Extract the best available address from an incident.
        
        Args:
            incident: The incident data
            
        Returns:
            str or None: The best address found, or None if no address available
        """
        # Try different address fields in order of preference
        address_fields = ['exactAddress', 'businessAddress', 'address', 'location']
        
        for field in address_fields:
            if field in incident and incident[field]:
                addr = str(incident[field]).strip()
                if addr and addr.lower() not in ['unknown', 'none', 'na', 'n/a']:
                    return addr
                    
        # If we have a business name and a state/city, we might be able to construct a usable address
        if 'businessName' in incident and incident['businessName']:
            business = str(incident['businessName']).strip()
            
            # If we have a city/state, combine with business name
            for field in ['city', 'state', 'location']:
                if field in incident and incident[field]:
                    location = str(incident[field]).strip()
                    if location and location.lower() not in ['unknown', 'none', 'na', 'n/a']:
                        return f"{business}, {location}"
        
        return None
        
    def _calculate_distance(self, incident_lat: float, incident_lng: float, place: dict) -> Optional[float]:
        """
        Calculate the distance between incident location and a nearby business.
        
        Args:
            incident_lat: Latitude of the incident
            incident_lng: Longitude of the incident
            place: The place data from Google Maps API
            
        Returns:
            float or None: The distance in miles, or None if coordinates aren't available
        """
        if 'geometry' in place and 'location' in place['geometry']:
            business_lat = place['geometry']['location']['lat']
            business_lng = place['geometry']['location']['lng']
            
            # Calculate the great circle distance (Haversine formula)
            from math import radians, sin, cos, sqrt, atan2
            
            R = 3958.8  # Earth radius in miles
            
            lat1, lng1 = radians(incident_lat), radians(incident_lng)
            lat2, lng2 = radians(business_lat), radians(business_lng)
            
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance_miles = R * c
            
            return round(distance_miles, 2)
        else:
            logger.warning("Missing geometry in place data, cannot calculate distance")
            return None
        
def main():
    """Main entry point for the nearby business finder."""
    from src.utils.logger import get_logger, log_execution_time
    
    # Get a logger specifically for the main function
    main_logger = get_logger("nearby_finder_main")
    main_logger.info("Starting Nearby Business Finder")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Find nearby businesses from analyzed crime incidents')
    parser.add_argument('--input-file', '-i', required=True, help='Path to the analyzed CSV file')
    parser.add_argument('--radius', '-r', type=int, help='Search radius in meters (default: use config value)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        from src.utils.logger import logging
        get_logger(__name__, level=logging.DEBUG)
        main_logger.info("Verbose logging enabled")
    
    try:
        # Initialize the finder
        finder = NearbyBusinessFinder()
        
        # Run the finder
        output_file = finder.find_nearby_businesses(args.input_file)
        
        # Success message
        if output_file:
            print(f"\nSuccess! Results saved to: {output_file}")
            print(f"Check logs for details: logs/nearby_finder.log")
        else:
            print("\nError: No output file was generated")
            
    except Exception as e:
        main_logger.exception(f"Error in main: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Check logs for details: logs/nearby_finder.log")
        return 1
        
    return 0
    
if __name__ == "__main__":
    import sys
    sys.exit(main())