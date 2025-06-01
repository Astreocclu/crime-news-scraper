"""
Enhanced Address Finder for improving the accuracy of identifying business addresses.

This module provides the main class that orchestrates the three tasks of the
Enhanced Address Finding system:

1. Analyze Input Text for Location Clues (TextAnalyzer)
   - Extracts geographic entities (cities, states, street names, etc.)
   - Identifies business entities (store types, business names)
   - Recognizes contextual phrases ("located at", "on the corner of", etc.)
   - Extracts potential addresses using regex patterns

2. Infer Potential Addresses (AddressInferrer)
   - Combines extracted information to generate address candidates
   - Prioritizes candidates based on completeness and context
   - Formats address queries for geocoding

3. Confirm Address using Google API (AddressConfirmer)
   - Verifies address candidates using Google Places API
   - Geocodes addresses to get precise coordinates
   - Retrieves additional business information (name, phone, website)
   - Assigns confidence scores to results

The workflow is designed to progressively refine location information from
unstructured text into verified, geocoded addresses suitable for business targeting.
"""
from typing import Dict, Optional

from src.address_finder.text_analyzer import TextAnalyzer
from src.address_finder.address_inferrer import AddressInferrer
from src.address_finder.address_confirmer import AddressConfirmer
from src.utils.logger import get_logger, log_execution_time

# Get a configured logger for this module
logger = get_logger(__name__)

class EnhancedAddressFinder:
    """
    Enhanced Address Finder for improving the accuracy of identifying business addresses.

    This class orchestrates the three tasks of the Enhanced Address Finding system:
    1. Analyze Input Text for Location Clues
    2. Infer Potential Addresses
    3. Confirm Address using Google API
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the enhanced address finder.

        Args:
            api_key: Google Maps API key (optional, will use the one from config if not provided)
        """
        self.text_analyzer = TextAnalyzer()
        self.address_inferrer = AddressInferrer()
        self.address_confirmer = AddressConfirmer(api_key)

    @log_execution_time(logger, "EnhancedAddressFinder: ")
    def find_address(self, text: str) -> Dict:
        """
        Find a business address in the given text.

        This method orchestrates the three-step process of address finding:
        1. Text analysis to extract location clues
        2. Address inference to generate candidate addresses
        3. Address confirmation using Google API

        Args:
            text: The text to analyze (e.g., news article content)

        Returns:
            Dict: The confirmed address or failure information with the following structure:
                - success (bool): Whether an address was found
                - formatted_address (str): The standardized address
                - lat, lng (float): Coordinates
                - name (str): Business name if available
                - place_id (str): Google Maps place ID
                - confidence (float): Confidence score (0.0-1.0)
                - original_text (str): The input text
                - location_clues (Dict): Extracted location information
                - reason (str): Failure reason if success is False
        """
        # Validate input
        if not text:
            logger.warning("Empty text provided for address finding")
            return {"success": False, "reason": "Empty text provided"}

        logger.info(f"Finding address in text: {text[:100]}...")

        # STEP 1: Analyze Input Text for Location Clues
        # The TextAnalyzer extracts geographic entities, business entities,
        # contextual phrases, and potential addresses from the text
        location_clues = self.text_analyzer.analyze_text(text)

        # Check if we found any clues
        if not location_clues["geographic_entities"] and not location_clues["business_entities"]:
            logger.warning("No location clues found in text")
            return {"success": False, "reason": "No location clues found in text"}

        # STEP 2: Infer Potential Addresses
        # The AddressInferrer combines the extracted clues to generate
        # candidate addresses for geocoding
        candidate_addresses = self.address_inferrer.infer_addresses(location_clues)

        # Check if we inferred any addresses
        if not candidate_addresses:
            logger.warning("No candidate addresses inferred")
            return {"success": False, "reason": "No candidate addresses inferred"}

        # STEP 3: Confirm Address using Google API
        # The AddressConfirmer verifies the candidate addresses using
        # Google Places API and returns the best match
        confirmed_address = self.address_confirmer.confirm_addresses(candidate_addresses)

        # Check if we confirmed an address
        if confirmed_address.get("success") is False:
            logger.warning(f"Failed to confirm address: {confirmed_address.get('reason')}")
            return confirmed_address

        # Enrich the result with the original text and location clues
        confirmed_address["original_text"] = text
        confirmed_address["location_clues"] = location_clues
        confirmed_address["success"] = True

        logger.info(f"Successfully found address: {confirmed_address.get('formatted_address')}")
        return confirmed_address
