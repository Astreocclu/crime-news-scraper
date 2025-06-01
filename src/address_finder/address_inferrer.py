"""
Address inferrer for generating potential addresses from location clues.

This module implements Task 2 of the Enhanced Address Finding system:
Infer Potential Addresses.
"""
import itertools
from typing import Dict, List, Optional, Tuple

from src.utils.logger import get_logger

# Get a configured logger for this module
logger = get_logger(__name__)

class AddressInferrer:
    """
    Infers potential addresses from location clues.
    
    This class implements Task 2 of the Enhanced Address Finding system:
    Infer Potential Addresses.
    """
    
    def __init__(self):
        """Initialize the address inferrer."""
        pass
    
    def infer_addresses(self, location_clues: Dict) -> List[Dict]:
        """
        Generate a list of candidate addresses based on the extracted clues.
        
        Args:
            location_clues: Structured data from Task 1 containing potential location clues
            
        Returns:
            List[Dict]: A list of potential business names and addresses
        """
        if not location_clues:
            logger.warning("Empty location clues provided for address inference")
            return []
            
        logger.info(f"Inferring addresses from location clues: {location_clues}")
        
        # Extract entities from the location clues
        geographic_entities = location_clues.get("geographic_entities", [])
        business_entities = location_clues.get("business_entities", [])
        contextual_info = location_clues.get("contextual_info", [])
        
        # If we don't have any geographic or business entities, we can't infer addresses
        if not geographic_entities and not business_entities:
            logger.warning("No geographic or business entities found in location clues")
            return []
        
        # Formulate search queries
        search_queries = self._formulate_search_queries(
            geographic_entities, business_entities, contextual_info
        )
        
        # Generate candidate addresses
        candidate_addresses = self._generate_candidate_addresses(search_queries)
        
        logger.info(f"Inferred {len(candidate_addresses)} candidate addresses")
        return candidate_addresses
    
    def _formulate_search_queries(
        self, 
        geographic_entities: List[str], 
        business_entities: List[str], 
        contextual_info: List[str]
    ) -> List[str]:
        """
        Formulate search queries from the extracted entities.
        
        Args:
            geographic_entities: List of geographic entities
            business_entities: List of business entities
            contextual_info: List of contextual information
            
        Returns:
            List[str]: List of search queries
        """
        queries = []
        
        # If we have both business and geographic entities, combine them
        if business_entities and geographic_entities:
            # Start with the most specific combinations
            for business in business_entities:
                for geo in geographic_entities:
                    # Basic combination
                    queries.append(f"{business} in {geo}")
                    
                    # Add contextual information if available
                    for context in contextual_info:
                        queries.append(f"{business} {context} {geo}")
        
        # If we only have geographic entities, use them as is
        elif geographic_entities:
            queries.extend(geographic_entities)
        
        # If we only have business entities, use them as is
        elif business_entities:
            queries.extend(business_entities)
        
        # Remove duplicates and sort by specificity (longer queries first)
        unique_queries = list(set(queries))
        unique_queries.sort(key=len, reverse=True)
        
        logger.debug(f"Formulated search queries: {unique_queries}")
        return unique_queries
    
    def _generate_candidate_addresses(self, search_queries: List[str]) -> List[Dict]:
        """
        Generate candidate addresses from search queries.
        
        Args:
            search_queries: List of search queries
            
        Returns:
            List[Dict]: List of candidate addresses
        """
        candidates = []
        
        # For each search query, create a candidate address
        for query in search_queries:
            # Extract business name and location from the query
            business_name, location = self._parse_query(query)
            
            candidate = {
                "query": query,
                "business_name": business_name,
                "location": location,
                "confidence": self._calculate_query_confidence(query)
            }
            
            candidates.append(candidate)
        
        # Sort candidates by confidence
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        
        return candidates
    
    def _parse_query(self, query: str) -> Tuple[str, str]:
        """
        Parse a search query to extract business name and location.
        
        Args:
            query: The search query
            
        Returns:
            Tuple[str, str]: Business name and location
        """
        # Check for "in" pattern
        if " in " in query:
            parts = query.split(" in ", 1)
            return parts[0].strip(), parts[1].strip()
        
        # Check for contextual patterns
        contextual_patterns = [" near ", " next to ", " across from ", " on the corner of "]
        for pattern in contextual_patterns:
            if pattern in query:
                parts = query.split(pattern, 1)
                return parts[0].strip(), parts[1].strip()
        
        # If no pattern is found, assume the whole query is a location
        return "", query
    
    def _calculate_query_confidence(self, query: str) -> float:
        """
        Calculate a confidence score for a search query.
        
        Args:
            query: The search query
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Simple heuristic: longer queries with more specific information get higher confidence
        # This is a placeholder and should be refined based on actual performance
        
        # Base confidence
        confidence = 0.5
        
        # Adjust based on query length
        if len(query) > 30:
            confidence += 0.2
        elif len(query) > 15:
            confidence += 0.1
        
        # Adjust based on presence of specific patterns
        if " in " in query:
            confidence += 0.1
        
        if any(pattern in query.lower() for pattern in ["street", "avenue", "boulevard", "road"]):
            confidence += 0.1
        
        if any(pattern in query.lower() for pattern in ["jewelry", "store", "shop"]):
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
