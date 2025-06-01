"""
Address confirmer for verifying inferred addresses using Google Places API.

This module implements Task 3 of the Enhanced Address Finding system:
Confirm Address using Google API.
"""
import time
from typing import Dict, List, Optional, Tuple

from src.address_finder.config import (
    GOOGLE_MAPS_API_KEY,
    MAX_API_CALLS_PER_INFERENCE,
    CONFIDENCE_THRESHOLD
)
from src.nearby_finder.google_client import GoogleMapsClient
from src.utils.logger import get_logger

# Get a configured logger for this module
logger = get_logger(__name__)

class AddressConfirmer:
    """
    Confirms inferred addresses using Google Places API.

    This class implements Task 3 of the Enhanced Address Finding system:
    Confirm Address using Google API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the address confirmer.

        Args:
            api_key: Google Maps API key (optional, will use the one from config if not provided)
        """
        self.api_key = api_key or GOOGLE_MAPS_API_KEY
        self.google_client = GoogleMapsClient(self.api_key)

    def confirm_addresses(self, candidate_addresses: List[Dict]) -> Dict:
        """
        Verify the inferred addresses using the Google Places API.

        Args:
            candidate_addresses: List of potential business names and addresses from Task 2

        Returns:
            Dict: Confirmed address with high confidence, or indication of failure
        """
        if not candidate_addresses:
            logger.warning("Empty candidate addresses provided for confirmation")
            return self._create_failure_result("No candidate addresses provided")

        logger.info(f"Confirming {len(candidate_addresses)} candidate addresses")

        # Limit the number of API calls to avoid excessive usage
        candidates_to_check = candidate_addresses[:MAX_API_CALLS_PER_INFERENCE]

        confirmed_addresses = []

        for candidate in candidates_to_check:
            query = candidate["query"]
            logger.info(f"Checking candidate: {query}")

            # Format and execute API request
            places = self._search_places(query)

            if places:
                # Process API response
                confirmed = self._process_places_response(places, candidate)
                if confirmed:
                    confirmed_addresses.append(confirmed)

            # Respect API rate limits
            time.sleep(0.2)

        # Select the best match
        best_match = self._select_best_match(confirmed_addresses)

        if best_match:
            logger.info(f"Found confirmed address: {best_match['formatted_address']}")
            # Add success flag to the result
            best_match["success"] = True
            return best_match
        else:
            logger.warning("Failed to confirm any address")
            return self._create_failure_result("No addresses could be confirmed")

    def _search_places(self, query: str) -> List[Dict]:
        """
        Search for places using the Google Places API.

        Args:
            query: The search query

        Returns:
            List[Dict]: List of places found
        """
        try:
            # Use the Text Search API
            places_result = self.google_client.client.places(
                query=query,
                type="establishment"
            )

            if 'results' not in places_result:
                logger.warning(f"No results found for query: {query}")
                return []

            return places_result['results']

        except Exception as e:
            logger.error(f"Places search error for query {query}: {str(e)}")
            return []

    def _process_places_response(self, places: List[Dict], candidate: Dict) -> Optional[Dict]:
        """
        Process the places API response.

        Args:
            places: List of places from the API
            candidate: The candidate address that was used for the query

        Returns:
            Dict or None: Processed place information if found, None otherwise
        """
        if not places:
            return None

        # Get the first (most relevant) result
        place = places[0]

        # Extract relevant information
        place_id = place.get('place_id')
        name = place.get('name', '')
        formatted_address = place.get('formatted_address', '')
        geometry = place.get('geometry', {})
        location = geometry.get('location', {})

        if not place_id or not formatted_address:
            logger.warning(f"Incomplete place information: {place}")
            return None

        # Get additional details
        details = self._get_place_details(place_id)

        # Calculate confidence score
        confidence = self._calculate_place_confidence(place, candidate)

        if confidence < CONFIDENCE_THRESHOLD:
            logger.info(f"Place confidence too low: {confidence} < {CONFIDENCE_THRESHOLD}")
            return None

        # Create result
        result = {
            "place_id": place_id,
            "name": name,
            "formatted_address": formatted_address,
            "lat": location.get('lat'),
            "lng": location.get('lng'),
            "confidence": confidence,
            "original_query": candidate["query"]
        }

        # Add additional details if available
        if details:
            result.update({
                "phone_number": details.get('formatted_phone_number', ''),
                "website": details.get('website', '')
            })

        return result

    def _get_place_details(self, place_id: str) -> Dict:
        """
        Get detailed information about a place.

        Args:
            place_id: The place ID

        Returns:
            Dict: Place details
        """
        try:
            place_details = self.google_client.get_place_details(place_id)
            return place_details

        except Exception as e:
            logger.error(f"Place details error for place_id {place_id}: {str(e)}")
            return {}

    def _calculate_place_confidence(self, place: Dict, candidate: Dict) -> float:
        """
        Calculate a confidence score for a place.

        Args:
            place: The place information from the API
            candidate: The candidate address that was used for the query

        Returns:
            float: Confidence score between 0 and 1
        """
        # Start with the candidate's confidence
        confidence = candidate.get("confidence", 0.5)

        # Adjust based on the place information

        # Check if the place has a name
        if place.get('name'):
            confidence += 0.1

            # Check if the name matches the business name in the candidate
            if candidate.get('business_name') and candidate['business_name'].lower() in place['name'].lower():
                confidence += 0.2

        # Check if the place has a formatted address
        if place.get('formatted_address'):
            confidence += 0.1

            # Check if the address contains the location in the candidate
            if candidate.get('location') and candidate['location'].lower() in place['formatted_address'].lower():
                confidence += 0.2

        # Check if the place has a high rating
        if place.get('rating', 0) > 4.0:
            confidence += 0.1

        # Cap at 1.0
        return min(confidence, 1.0)

    def _select_best_match(self, confirmed_addresses: List[Dict]) -> Optional[Dict]:
        """
        Select the best match from the confirmed addresses.

        Args:
            confirmed_addresses: List of confirmed addresses

        Returns:
            Dict or None: The best match, or None if no match found
        """
        if not confirmed_addresses:
            return None

        # Sort by confidence
        confirmed_addresses.sort(key=lambda x: x["confidence"], reverse=True)

        # Return the highest confidence match
        return confirmed_addresses[0]

    def _create_failure_result(self, reason: str) -> Dict:
        """
        Create a failure result.

        Args:
            reason: The reason for the failure

        Returns:
            Dict: Failure result
        """
        return {
            "success": False,
            "reason": reason
        }
