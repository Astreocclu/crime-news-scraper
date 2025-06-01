"""
Text analyzer for extracting location clues from text.

This module implements Task 1 of the Enhanced Address Finding system:
Analyze Input Text for Location Clues.
"""
import re
import json
from typing import Dict, List, Optional, Tuple, Set

from src.address_finder.config import (
    COMMON_CITIES,
    US_STATES,
    BUSINESS_TYPES,
    CONTEXTUAL_PHRASES,
    ADDRESS_PATTERNS
)
from src.utils.logger import get_logger

# Get a configured logger for this module
logger = get_logger(__name__)

class TextAnalyzer:
    """
    Analyzes text to extract location clues.

    This class implements Task 1 of the Enhanced Address Finding system:
    Analyze Input Text for Location Clues.
    """

    def __init__(self):
        """Initialize the text analyzer."""
        # Compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for text analysis."""
        # Pattern for zip codes
        self.zip_pattern = re.compile(r'\b\d{5}(?:-\d{4})?\b')

        # Pattern for street names
        street_types = r'(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl)'
        self.street_pattern = re.compile(r'\b\d+\s+[A-Za-z0-9\s\.]+' + street_types + r'\.?\b', re.IGNORECASE)

        # Pattern for business types
        business_types_pattern = '|'.join(re.escape(bt) for bt in BUSINESS_TYPES)
        self.business_type_pattern = re.compile(r'\b(' + business_types_pattern + r')\b', re.IGNORECASE)

        # Pattern for contextual phrases
        contextual_phrases_pattern = '|'.join(re.escape(cp) for cp in CONTEXTUAL_PHRASES)
        self.contextual_pattern = re.compile(r'\b(' + contextual_phrases_pattern + r')\b', re.IGNORECASE)

        # Pattern for cities
        cities_pattern = '|'.join(re.escape(city) for city in COMMON_CITIES)
        self.city_pattern = re.compile(r'\b(' + cities_pattern + r')\b', re.IGNORECASE)

        # Pattern for states
        states_pattern = '|'.join(re.escape(state) for state in list(US_STATES.keys()) + list(US_STATES.values()))
        self.state_pattern = re.compile(r'\b(' + states_pattern + r')\b', re.IGNORECASE)

    def analyze_text(self, text: str) -> Dict:
        """
        Extract all potential geographic and business-related information from the input text.

        Args:
            text: Raw text data (e.g., news article snippet, user query)

        Returns:
            Dict: Structured data containing potential location clues
        """
        if not text:
            logger.warning("Empty text provided for analysis")
            return self._create_empty_result()

        logger.info(f"Analyzing text: {text[:100]}...")

        # Extract entities
        geographic_entities = self._extract_geographic_entities(text)
        business_entities = self._extract_business_entities(text)
        contextual_info = self._extract_contextual_info(text)

        # Extract address directly
        address = self.extract_address_from_text(text)

        # Create structured result
        result = {
            "geographic_entities": list(geographic_entities),
            "business_entities": list(business_entities),
            "contextual_info": list(contextual_info),
            "extracted_address": address
        }

        logger.info(f"Analysis result: {json.dumps(result)}")
        return result

    def _create_empty_result(self) -> Dict:
        """Create an empty result structure."""
        return {
            "geographic_entities": [],
            "business_entities": [],
            "contextual_info": [],
            "extracted_address": None
        }

    def _extract_geographic_entities(self, text: str) -> Set[str]:
        """
        Extract geographic entities from text.

        Args:
            text: The text to analyze

        Returns:
            Set[str]: Set of geographic entities
        """
        entities = set()

        # Extract zip codes
        zip_codes = self.zip_pattern.findall(text)
        entities.update(zip_codes)

        # Extract street names
        streets = self.street_pattern.findall(text)
        entities.update(streets)

        # Extract full addresses using patterns
        address = self.extract_address_from_text(text)
        if address:
            entities.add(address)

        # Extract cities
        cities = self.city_pattern.findall(text)
        entities.update(cities)

        # Extract states
        states = self.state_pattern.findall(text)
        entities.update(states)

        # Look for neighborhood indicators (e.g., "South Frisco")
        for direction in ["North", "South", "East", "West", "Downtown", "Uptown", "Midtown"]:
            pattern = re.compile(r'\b' + direction + r'\s+([A-Z][a-z]+)\b')
            neighborhoods = pattern.findall(text)
            for neighborhood in neighborhoods:
                if neighborhood in COMMON_CITIES:
                    entities.add(f"{direction} {neighborhood}")

        return entities

    def _extract_business_entities(self, text: str) -> Set[str]:
        """
        Extract business entities from text.

        Args:
            text: The text to analyze

        Returns:
            Set[str]: Set of business entities
        """
        entities = set()

        # Extract business types
        business_types = self.business_type_pattern.findall(text)
        entities.update(business_types)

        # Extract potential business names (capitalized phrases)
        # This is a simple heuristic and might need refinement
        business_name_pattern = re.compile(r'([A-Z][A-Za-z0-9\'\-&\s]+(?:Inc|LLC|Ltd|Co|Corp|Corporation|Company)?)\s+(?:' + '|'.join(re.escape(bt) for bt in BUSINESS_TYPES) + r')', re.IGNORECASE)
        business_names = business_name_pattern.findall(text)
        entities.update(name.strip() for name in business_names if len(name.strip()) > 2)

        return entities

    def _extract_contextual_info(self, text: str) -> Set[str]:
        """
        Extract contextual information from text.

        Args:
            text: The text to analyze

        Returns:
            Set[str]: Set of contextual information
        """
        entities = set()

        # Extract contextual phrases
        contextual_phrases = self.contextual_pattern.findall(text)
        entities.update(contextual_phrases)

        # Extract phrases like "on the corner of X and Y"
        corner_pattern = re.compile(r'(?:on|at)\s+the\s+corner\s+of\s+([^,\.;]+)\s+and\s+([^,\.;]+)', re.IGNORECASE)
        corners = corner_pattern.findall(text)
        for corner in corners:
            entities.add(f"corner of {corner[0]} and {corner[1]}")

        # Extract phrases like "at the intersection of X and Y"
        intersection_pattern = re.compile(r'(?:at|near)\s+the\s+intersection\s+of\s+([^,\.;]+)\s+and\s+([^,\.;]+)', re.IGNORECASE)
        intersections = intersection_pattern.findall(text)
        for intersection in intersections:
            entities.add(f"intersection of {intersection[0]} and {intersection[1]}")

        return entities

    def extract_address_from_text(self, text: str) -> Optional[str]:
        """
        Extract a potential street address from text using regex patterns.

        Args:
            text: The text to extract an address from

        Returns:
            Optional[str]: The extracted address, or None if no address found
        """
        if not text:
            return None

        # Try each pattern
        for pattern in ADDRESS_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the first match
                if isinstance(matches[0], tuple):
                    # If the match is a tuple (multiple capture groups), join them
                    address = ' at '.join(part for part in matches[0] if part)
                else:
                    address = matches[0]

                # Clean up the address
                address = address.strip()
                address = re.sub(r'\s+', ' ', address)  # Normalize whitespace

                logger.debug(f"Extracted address: {address}")
                return address

        return None
