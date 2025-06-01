"""
Address extraction utility for crime news articles.

This module provides functions to extract and validate street addresses from text.
"""
import re
import logging
from typing import Optional, Dict, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Common address patterns
ADDRESS_PATTERNS = [
    # Street number + street name + city/state
    r'(\d+\s+[A-Za-z0-9\s\.]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl)\.?(?:\s+[A-Za-z]+)?(?:\s*,\s*[A-Za-z\s]+,\s*[A-Z]{2}))',
    
    # Address mentioned after "located at" or similar phrases
    r'located\s+at\s+([^,\.;]+(?:,\s*[^,\.;]+){1,3})',
    r'address\s+(?:of|at|is|was)\s+([^,\.;]+(?:,\s*[^,\.;]+){1,3})',
    
    # Business name + at + address
    r'([A-Za-z0-9\s&\'-]+)\s+at\s+(\d+\s+[A-Za-z0-9\s\.]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl))',
    
    # Address in parentheses
    r'\(([^()]*\d+[^()]*(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl)[^()]*)\)',
]

def extract_address_from_text(text: str) -> Optional[str]:
    """
    Extract a potential street address from text.
    
    Args:
        text: The text to extract an address from
        
    Returns:
        str or None: The extracted address, or None if no address found
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

def extract_address_from_article(article: Dict) -> Optional[str]:
    """
    Extract a potential street address from an article.
    
    Args:
        article: The article data
        
    Returns:
        str or None: The extracted address, or None if no address found
    """
    # Check if we already have an address
    if article.get('exactAddress') or article.get('detailed_location'):
        return article.get('exactAddress') or article.get('detailed_location')
        
    # Try to extract from various fields
    potential_text_fields = [
        'excerpt', 
        'title',
        'content',
        'description'
    ]
    
    for field in potential_text_fields:
        if field in article and article[field]:
            address = extract_address_from_text(article[field])
            if address:
                return address
                
    return None

def normalize_address(address: str) -> str:
    """
    Normalize address format for geocoding readiness.
    
    Args:
        address: Raw address string to normalize
        
    Returns:
        str: Normalized address string
    """
    if not address:
        return ""
        
    # Common abbreviation mapping
    abbr_map = {
        r'\bSt\b': 'Street',
        r'\bAve\b': 'Avenue',
        r'\bBlvd\b': 'Boulevard',
        r'\bRd\b': 'Road',
        r'\bDr\b': 'Drive',
        r'\bLn\b': 'Lane',
        r'\bCt\b': 'Court',
        r'\bPkwy\b': 'Parkway',
        r'\bHwy\b': 'Highway',
        r'\bSq\b': 'Square',
        r'\bPl\b': 'Place',
        r'\bTer\b': 'Terrace',
    }
    
    # Remove any confidence indicators or other parenthetical notes
    address = re.sub(r'\s*\([^)]*\)', '', address)
    
    # Apply abbreviation standardization
    normalized = address
    for abbr, full in abbr_map.items():
        normalized = re.sub(abbr, full, normalized)
    
    # Ensure consistent comma separation
    normalized = re.sub(r'\s*,\s*', ', ', normalized)
    
    # Ensure consistent spacing
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Clean up any trailing punctuation
    normalized = normalized.strip('.,; ')
    
    return normalized

def is_valid_address(address: str) -> bool:
    """
    Check if an address appears to be valid.
    
    Args:
        address: The address to check
        
    Returns:
        bool: True if the address appears valid, False otherwise
    """
    if not address:
        return False
        
    # Check if the address contains a number (most street addresses do)
    has_number = bool(re.search(r'\d', address))
    
    # Check if the address contains a street type
    street_types = ['street', 'st', 'avenue', 'ave', 'boulevard', 'blvd', 'road', 'rd', 
                   'drive', 'dr', 'lane', 'ln', 'way', 'court', 'ct', 'plaza', 'plz', 
                   'square', 'sq', 'highway', 'hwy', 'parkway', 'pkwy', 'terrace', 'ter', 'place', 'pl']
    has_street_type = any(re.search(r'\b' + st + r'\b', address, re.IGNORECASE) for st in street_types)
    
    # Check if the address is too short
    is_long_enough = len(address) > 10
    
    return has_number and has_street_type and is_long_enough
