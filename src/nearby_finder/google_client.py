"""
Client for interacting with Google Maps API to find nearby businesses.

This module provides functionality to geocode addresses and find nearby
luxury goods stores, sports memorabilia shops, jewelry stores and other
high-value retail targets using the Google Maps API.
"""
import time
from typing import Dict, List, Optional
import googlemaps

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
        
        self.client = googlemaps.Client(key=self.api_key)
        
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
        
        # Search for each business type
        for business_type in TARGET_BUSINESS_TYPES:
            places = self._search_places_by_type(latitude, longitude, business_type, radius)
            if places:
                # Filter general stores based on keywords if needed
                if business_type == "store":
                    # Filter for luxury stores
                    luxury_stores = [
                        place for place in places 
                        if any(keyword.lower() in place.get("name", "").lower() for keyword in LUXURY_KEYWORDS)
                    ]
                    nearby_places.extend(self._add_store_category(luxury_stores, "luxury_goods"))
                    
                    # Filter for sports memorabilia stores
                    sports_stores = [
                        place for place in places 
                        if any(keyword.lower() in place.get("name", "").lower() for keyword in SPORTS_MEMORABILIA_KEYWORDS)
                    ]
                    nearby_places.extend(self._add_store_category(sports_stores, "sports_memorabilia"))
                    
                    # Filter for vape/smoke shops
                    vape_stores = [
                        place for place in places 
                        if any(keyword.lower() in place.get("name", "").lower() for keyword in VAPE_SMOKE_KEYWORDS)
                    ]
                    nearby_places.extend(self._add_store_category(vape_stores, "vape_smoke_shop"))
                else:
                    # For specific types like jewelry_store
                    for place in places:
                        place["category"] = "jewelry" if business_type == "jewelry_store" else business_type
                    nearby_places.extend(places)
            
            # Respect API rate limits
            time.sleep(0.2)
            
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