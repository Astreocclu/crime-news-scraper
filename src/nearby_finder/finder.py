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
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd

from src.nearby_finder.google_client import GoogleMapsClient
from src.nearby_finder.config import OUTPUT_DIR
from src.utils.logger import get_logger, log_execution_time
from src.utils.exceptions import NearbyFinderError, NearbyFinderAPIError
from src.database import save_nearby_businesses, initialize_database
from src.address_finder import EnhancedAddressFinder

# Get a configured logger for this module
logger = get_logger(__name__)

class NearbyBusinessFinder:
    """Find nearby businesses around crime incident locations."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the nearby business finder."""
        self.google_client = GoogleMapsClient(api_key)
        self.address_finder = EnhancedAddressFinder(api_key)
        self.ensure_output_dir()

    def ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    @log_execution_time(logger, "NearbyBusinessFinder: ")
    def find_nearby_businesses(self, input_file: str) -> bool:
        """
        Process analyzed crime incidents and find nearby businesses.

        Args:
            input_file: Path to the CSV file with analyzed crime incidents

        Returns:
            bool: True if processing completed successfully, False otherwise

        Raises:
            NearbyFinderError: If there's an error processing the input file
        """
        try:
            # Initialize processing
            output_file, incidents_df, stats = self._initialize_processing(input_file)

            # Process all incidents
            combined_results = self._process_all_incidents(incidents_df, stats)

            # Save results and log statistics
            success = self._save_results_and_log_stats(combined_results, output_file, stats, len(incidents_df))

            return success

        except Exception as e:
            error_msg = f"Error processing input file {input_file}: {str(e)}"
            logger.exception(error_msg)
            raise NearbyFinderError(error_msg) from e

    def _initialize_processing(self, input_file: str) -> Tuple[str, Any, Dict[str, Any]]:
        """Initialize processing by setting up output file and reading input data."""
        # Generate a timestamp for the output file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"nearby_businesses_{timestamp}.csv")

        logger.info(f"Processing analyzed file: {input_file}")
        logger.info(f"Output will be saved to: {output_file}")

        # Read the analyzed incidents CSV
        incidents_df = pd.read_csv(input_file)
        logger.info(f"Read {len(incidents_df)} incidents from input file")

        # Track statistics for logging
        stats = {
            'total_incidents': len(incidents_df),
            'incidents_with_address': 0,
            'successful_geocodes': 0,
            'total_nearby_businesses': 0,
            'locations_by_type': {},
            'lead_scores': {}
        }

        return output_file, incidents_df, stats

    def _process_all_incidents(self, incidents_df: Any, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process all incidents and find nearby businesses."""
        combined_results = []

        logger.info(f"Beginning to process {len(incidents_df)} incidents")
        for idx, incident in incidents_df.iterrows():
            # Log progress at intervals
            if idx > 0 and idx % 10 == 0:
                logger.info(f"Processed {idx}/{len(incidents_df)} incidents")

            # Process single incident
            incident_results = self._process_single_incident(incident, idx, stats)
            combined_results.extend(incident_results)

        return combined_results

    def _process_single_incident(self, incident: Any, idx: int, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single incident and find nearby businesses."""
        results = []

        # Find the best address for this incident
        address = self._get_best_address(incident)
        if not address:
            logger.warning(f"No address found for incident #{idx+1}: {incident.get('title', 'Unnamed')}")
            # Still add the incident to results even without an address
            incident_data = self._create_incident_data(incident, address)
            results.append(incident_data)
            return results

        # Add the original incident to results
        incident_data = self._create_incident_data(incident, address)
        results.append(incident_data)
        stats['incidents_with_address'] += 1

        # Find and process nearby businesses
        nearby_results = self._find_and_process_nearby_businesses(incident_data, address, stats)
        results.extend(nearby_results)

        return results

    def _create_incident_data(self, incident: Any, address: Optional[str]) -> Dict[str, Any]:
        """Create incident data dictionary."""
        incident_data = incident.to_dict()
        incident_data['record_type'] = 'incident'
        incident_data['distance_from_incident'] = 0.0
        incident_data['lead_score'] = 0  # Default lead score for incidents
        incident_data['is_original_location'] = True  # Mark as original location

        if address:
            incident_data['exactAddress'] = address

        # Default missing fields - this helps handle different CSV formats
        for field in ['businessName', 'businessType', 'exactAddress']:
            if field not in incident_data:
                incident_data[field] = ''

        return incident_data

    def _find_and_process_nearby_businesses(self, incident_data: Dict[str, Any], address: str, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find and process nearby businesses for a given address."""
        results = []

        logger.info(f"Finding nearby businesses for: {address}")

        try:
            # Get coordinates for the address
            coordinates = self.google_client.geocode_address(address)
            if not coordinates:
                logger.warning(f"Could not geocode address: {address}")
                return results

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
                nearby_business = self._process_nearby_business(incident_data, place, coordinates, stats)
                if nearby_business:
                    results.append(nearby_business)

        except NearbyFinderAPIError as api_e:
            logger.error(f"API error processing {address}: {str(api_e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing {address}: {str(e)}", exc_info=True)

        return results

    def _process_nearby_business(self, incident_data: Dict[str, Any], place: Dict[str, Any], coordinates: Dict[str, float], stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single nearby business."""
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
        nearby_data['is_original_location'] = False  # Mark as not original location

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

        # Calculate lead score
        lead_score = self._calculate_lead_score(distance, place_category)
        nearby_data['lead_score'] = lead_score

        # EXCLUSIVE FILTERING: Only include businesses with score > 0 (target types only)
        if lead_score > 0 and place_category in ['jewelry', 'luxury_goods', 'sports_memorabilia']:
            # Track lead score statistics
            if lead_score not in stats['lead_scores']:
                stats['lead_scores'][lead_score] = 0
            stats['lead_scores'][lead_score] += 1

            # Log the lead score calculation
            logger.debug(f"TARGET BUSINESS - Score {lead_score} for {nearby_data.get('businessName', 'Unknown Business')} (category: {place_category})")

            return nearby_data
        else:
            # Log filtered out businesses for debugging
            logger.debug(f"FILTERED OUT - Non-target business: {nearby_data.get('businessName', 'Unknown Business')} (category: {place_category}, score: {lead_score})")
            return None

    def _save_results_and_log_stats(self, combined_results: List[Dict[str, Any]], output_file: str, stats: Dict[str, Any], total_incidents: int) -> bool:
        """Save results to file and database, and log statistics."""
        # Log processing statistics
        self._log_processing_statistics(stats)

        # Convert to DataFrame and save to CSV
        results_df = pd.DataFrame(combined_results)
        results_df.to_csv(output_file, index=False)

        logger.info(f"Found {len(results_df) - total_incidents} nearby businesses")
        logger.info(f"Final results saved to {output_file}")

        # Save to database
        try:
            logger.info("Saving results to database...")
            save_result = save_nearby_businesses(combined_results)
            if save_result:
                logger.info("Successfully saved results to database")
                return True
            else:
                logger.warning("Failed to save results to database")
                return False
        except Exception as db_e:
            logger.error(f"Error saving to database: {str(db_e)}")
            return False

    def _log_processing_statistics(self, stats: Dict[str, Any]) -> None:
        """Log processing statistics."""
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

        # Log lead score breakdown
        if stats['lead_scores']:
            logger.info("Lead score breakdown:")
            for score, count in sorted(stats['lead_scores'].items()):
                logger.info(f"- Score {score}: {count} businesses")

    def _get_best_address(self, incident) -> Optional[str]:
        """
        Extract the best available address from an incident.

        Args:
            incident: The incident data

        Returns:
            str or None: The best address found, or None if no address available
        """
        # First check for extracted incident address from the analyzer
        if 'extracted_incident_address' in incident and incident['extracted_incident_address']:
            addr = str(incident['extracted_incident_address']).strip()
            if addr and addr.lower() not in ['unknown', 'none', 'na', 'n/a']:
                logger.info(f"Using extracted incident address: {addr}")
                return addr

        # Try different address fields in order of preference
        address_fields = ['exactAddress', 'businessAddress', 'address', 'location', 'detailed_location', 'detailedLocation']

        for field in address_fields:
            if field in incident and incident[field]:
                addr = str(incident[field]).strip()
                if addr and addr.lower() not in ['unknown', 'none', 'na', 'n/a']:
                    logger.info(f"Using address from {field}: {addr}")
                    return addr

        # If we have a business name and a state/city, we might be able to construct a usable address
        if 'businessName' in incident and incident['businessName']:
            business = str(incident['businessName']).strip()

            # If we have a city/state, combine with business name
            for field in ['city', 'state', 'location']:
                if field in incident and incident[field]:
                    location = str(incident[field]).strip()
                    if location and location.lower() not in ['unknown', 'none', 'na', 'n/a']:
                        constructed_addr = f"{business}, {location}"
                        logger.info(f"Constructed address from business name and location: {constructed_addr}")
                        return constructed_addr

        # Try to extract address from the incident description or content
        if 'description' in incident and incident['description']:
            logger.info("Trying to extract address from incident description using enhanced address finder")
            result = self.address_finder.find_address(incident['description'])
            if result.get('success', False):
                addr = result.get('formatted_address')
                logger.info(f"Enhanced address finder found: {addr}")
                return addr

        # Try to extract from content if available
        if 'content' in incident and incident['content']:
            logger.info("Trying to extract address from incident content using enhanced address finder")
            result = self.address_finder.find_address(incident['content'])
            if result.get('success', False):
                addr = result.get('formatted_address')
                logger.info(f"Enhanced address finder found: {addr}")
                return addr

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

    def _calculate_lead_score(self, distance_miles: Optional[float], business_category: str) -> int:
        """
        Calculate a lead score based on distance and business category.
        FOCUSED SCORING: Prioritizes jewelry stores, sports memorabilia, and luxury goods only.

        Args:
            distance_miles: Distance from incident in miles (can be None)
            business_category: Category of the business

        Returns:
            int: The calculated lead score (0-6, with 6 being highest priority)
        """
        score = 0

        # Enhanced proximity scoring logic - more granular for better targeting
        if distance_miles is not None:
            if distance_miles < 0.25:  # Very close (within 1/4 mile)
                score += 3
            elif distance_miles < 0.5:  # Close (within 1/2 mile)
                score += 2
            elif distance_miles < 1.0:  # Nearby (within 1 mile)
                score += 1
            # No points for businesses beyond 1 mile

        # EXCLUSIVE business type scoring - ONLY our three target types get points
        if business_category == 'jewelry':
            # PRIMARY TARGET: Jewelry stores get maximum business type points
            score += 3
        elif business_category == 'sports_memorabilia':
            # SECONDARY TARGET: Sports memorabilia stores get maximum points
            score += 3
        elif business_category == 'luxury_goods':
            # SECONDARY TARGET: Luxury goods stores get maximum points
            score += 3
        else:
            # ALL OTHER BUSINESSES: Return score of 0 to exclude them completely
            return 0

        return score

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
        # Initialize the database
        main_logger.info("Initializing database...")
        db_init_result = initialize_database()
        if db_init_result:
            main_logger.info("Database initialized successfully")
        else:
            main_logger.warning("Failed to initialize database")

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