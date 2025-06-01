#!/usr/bin/env python3
"""
Test script to verify that the Google Maps client works with the real API key.

This script tests the Google Maps client with the real API key to verify that
it can geocode addresses, find nearby businesses, and retrieve place details.

Note: This script makes actual API calls to the Google Maps API, so it should
be used sparingly to avoid exceeding API rate limits.
"""
import os
import sys
import json
import logging

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.nearby_finder.google_client import GoogleMapsClient
from src.nearby_finder.config import GOOGLE_MAPS_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('google_maps_client_test')

def test_geocode_address():
    """Test that geocode_address works correctly with the real API key."""
    logger.info("Testing geocode_address...")

    # Create the Google Maps client
    google_client = GoogleMapsClient(GOOGLE_MAPS_API_KEY)

    # Test geocoding a valid address
    address = "1600 Amphitheatre Parkway, Mountain View, CA"
    logger.info(f"Geocoding address: {address}")

    result = google_client.geocode_address(address)

    if result:
        logger.info(f"Successfully geocoded address: {address}")
        logger.info(f"Coordinates: {result}")
        return True
    else:
        logger.error(f"Failed to geocode address: {address}")
        return False

def test_find_nearby_businesses():
    """Test that find_nearby_businesses works correctly with the real API key."""
    logger.info("Testing find_nearby_businesses...")

    # Create the Google Maps client
    google_client = GoogleMapsClient(GOOGLE_MAPS_API_KEY)

    # Test finding nearby businesses
    latitude = 37.7749
    longitude = -122.4194
    logger.info(f"Finding nearby businesses at coordinates: ({latitude}, {longitude})")

    result = google_client.find_nearby_businesses(latitude, longitude)

    if result:
        logger.info(f"Successfully found {len(result)} nearby businesses")
        logger.info(f"First business: {result[0]['name']} ({result[0]['category']})")
        return True
    else:
        logger.error("Failed to find nearby businesses")
        return False

def test_get_place_details():
    """Test that get_place_details works correctly with the real API key."""
    logger.info("Testing get_place_details...")

    # Create the Google Maps client
    google_client = GoogleMapsClient(GOOGLE_MAPS_API_KEY)

    # First find a place to get its place_id
    latitude = 37.7749
    longitude = -122.4194
    logger.info(f"Finding a place at coordinates: ({latitude}, {longitude})")

    places = google_client.find_nearby_businesses(latitude, longitude)

    if not places:
        logger.error("Failed to find any places")
        return False

    place_id = places[0].get('place_id')

    if not place_id:
        logger.error("Failed to get place_id")
        return False

    logger.info(f"Getting details for place_id: {place_id}")

    result = google_client.get_place_details(place_id)

    if result:
        logger.info(f"Successfully got details for place: {result.get('name', 'Unknown')}")
        logger.info(f"Address: {result.get('formatted_address', 'Unknown')}")
        return True
    else:
        logger.error(f"Failed to get details for place_id: {place_id}")
        return False

def main():
    """Run the tests."""
    logger.info("Starting Google Maps client tests...")

    # Check that the API key is available
    if not GOOGLE_MAPS_API_KEY:
        logger.error("Google Maps API key is not set in the environment")
        return 1

    logger.info(f"Using Google Maps API key: {GOOGLE_MAPS_API_KEY[:5]}...{GOOGLE_MAPS_API_KEY[-5:]}")

    # Run the tests
    geocode_success = test_geocode_address()
    nearby_success = test_find_nearby_businesses()
    details_success = test_get_place_details()

    # Print the results
    logger.info("Test results:")
    logger.info(f"- Geocode address: {'Success' if geocode_success else 'Failure'}")
    logger.info(f"- Find nearby businesses: {'Success' if nearby_success else 'Failure'}")
    logger.info(f"- Get place details: {'Success' if details_success else 'Failure'}")

    # Return success if all tests passed
    if geocode_success and nearby_success and details_success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
