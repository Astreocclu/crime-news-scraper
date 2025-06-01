"""
Client for interacting with Google Maps API to find nearby businesses.

This module provides functionality to geocode addresses and find nearby
TARGETED businesses using the Google Maps API. EXCLUSIVELY focuses on:
1. Jewelry stores (primary target)
2. Sports memorabilia stores (secondary target)
3. Luxury goods stores (secondary target)

All other business types are filtered out to ensure high-quality, targeted leads.
"""
import time
from typing import Dict, List, Optional
import googlemaps

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.nearby_finder.config import (
    GOOGLE_MAPS_API_KEY,
    TARGET_BUSINESS_TYPES,
    DEFAULT_SEARCH_RADIUS,
    MAX_RESULTS_PER_CATEGORY,
    LUXURY_KEYWORDS,
    SPORTS_MEMORABILIA_KEYWORDS,
    VAPE_SMOKE_KEYWORDS
)
from src.utils.logger import get_logger, log_execution_time
from src.utils.exceptions import NearbyFinderAPIError

# Get a configured logger for this module
logger = get_logger(__name__)

class GoogleMapsClient:
    """Client for Google Maps API interactions."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Google Maps client."""
        self.api_key = api_key or GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise ValueError("Google Maps API key is required. Set GOOGLE_MAPS_API_KEY in .env file.")

        # Initialize the Google Maps client
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.client = self.gmaps  # Keep backward compatibility

    def geocode_address(self, address: str) -> Dict:
        """Convert an address to geographic coordinates."""
        try:
            geocode_result = self.client.geocode(address)

            if not geocode_result:
                logger.error(f"Geocoding failed for address {address}: No results")
                return {}

            location = geocode_result[0]['geometry']['location']
            return location
        except Exception as e:
            logger.error(f"Geocoding error for address {address}: {str(e)}")
            return {}

    def find_nearby_businesses(self,
                              latitude: float,
                              longitude: float,
                              radius: int = DEFAULT_SEARCH_RADIUS) -> List[Dict]:
        """Find nearby businesses based on location and target types."""
        nearby_places = []

        # Search for each of our three target business types ONLY
        for business_type in TARGET_BUSINESS_TYPES:
            if business_type == "jewelry_store":
                # Search for jewelry stores
                places = self._search_places_by_type(latitude, longitude, business_type, radius)
                for place in places:
                    place["category"] = "jewelry"
                nearby_places.extend(places)

            elif business_type == "luxury_goods_store":
                # Search for luxury goods using targeted keywords
                luxury_places = self._search_luxury_goods(latitude, longitude, radius)
                nearby_places.extend(luxury_places)

            elif business_type == "sports_memorabilia_store":
                # Search for sports memorabilia using targeted keywords
                sports_places = self._search_sports_memorabilia(latitude, longitude, radius)
                nearby_places.extend(sports_places)

            # Respect API rate limits
            rate_limit_delay = float(os.getenv("GOOGLE_MAPS_RATE_LIMIT_DELAY", "0.2"))
            time.sleep(rate_limit_delay)

        return nearby_places

    def _search_places_by_type(self,
                              latitude: float,
                              longitude: float,
                              business_type: str,
                              radius: int) -> List[Dict]:
        """Search for places by type using the Places API."""
        try:
            places_result = self.client.places_nearby(
                location=(latitude, longitude),
                radius=radius,
                type=business_type
            )

            if 'results' not in places_result:
                logger.warning(f"No results found for type {business_type}")
                return []

            # Limit results per category
            return places_result['results'][:MAX_RESULTS_PER_CATEGORY]

        except Exception as e:
            logger.error(f"Places search error for type {business_type}: {str(e)}")
            return []

    def _search_luxury_goods(self, latitude: float, longitude: float, radius: int) -> List[Dict]:
        """Search specifically for luxury goods stores using targeted keywords."""
        luxury_places = []

        # Search using luxury-specific terms
        luxury_search_terms = [
            "luxury store", "designer boutique", "high-end store", "luxury goods",
            "Rolex", "Cartier", "Tiffany", "Gucci", "Louis Vuitton", "Prada",
            "luxury watches", "designer handbags", "fine jewelry", "luxury accessories"
        ]

        for search_term in luxury_search_terms[:5]:  # Limit to avoid too many API calls
            try:
                places = self.gmaps.places_nearby(
                    location=(latitude, longitude),
                    radius=radius,
                    keyword=search_term,
                    type="store"
                )

                if places.get("results"):
                    for place in places["results"]:
                        place["category"] = "luxury_goods"
                    luxury_places.extend(places["results"])

                # Rate limiting
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error searching for luxury goods with term '{search_term}': {str(e)}")
                continue

        return luxury_places

    def _search_sports_memorabilia(self, latitude: float, longitude: float, radius: int) -> List[Dict]:
        """Search specifically for sports memorabilia stores using targeted keywords."""
        sports_places = []

        # Search using sports memorabilia-specific terms
        sports_search_terms = [
            "sports memorabilia", "sports cards", "trading cards", "collectibles store",
            "baseball cards", "football cards", "basketball cards", "autographs",
            "sports collectibles", "card shop", "memorabilia store"
        ]

        for search_term in sports_search_terms[:5]:  # Limit to avoid too many API calls
            try:
                places = self.gmaps.places_nearby(
                    location=(latitude, longitude),
                    radius=radius,
                    keyword=search_term,
                    type="store"
                )

                if places.get("results"):
                    for place in places["results"]:
                        place["category"] = "sports_memorabilia"
                    sports_places.extend(places["results"])

                # Rate limiting
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error searching for sports memorabilia with term '{search_term}': {str(e)}")
                continue

        return sports_places

    def _add_store_category(self, stores: List[Dict], category: str) -> List[Dict]:
        """Add category classification to store results."""
        for store in stores:
            store["category"] = category
        return stores

    def get_place_details(self, place_id: str) -> Dict:
        """Get detailed information about a place."""
        try:
            place_details = self.client.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'geometry', 'formatted_phone_number', 'website']
            )

            if 'result' not in place_details:
                logger.warning(f"No details found for place_id {place_id}")
                return {}

            return place_details['result']

        except Exception as e:
            logger.error(f"Place details error for place_id {place_id}: {str(e)}")
            return {}