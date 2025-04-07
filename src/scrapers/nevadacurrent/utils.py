"""
Utility functions for the Nevada Current scraper module.

This module provides specialized functions for processing Nevada Current justice news:
- Location detection focusing on Nevada regions
- Keyword extraction to identify theft-related incidents
- Business relevance filtering to focus on B2B sales opportunities
- Date standardization for consistent lead tracking and follow-up
"""

import re
import logging
from typing import List, Optional
from datetime import datetime
from .config import LOCATION_VARIATIONS, THEFT_KEYWORDS, BUSINESS_KEYWORDS

logger = logging.getLogger(__name__)

def detect_location(content: str) -> Optional[str]:
    """
    Detect location from content, with enhanced focus on Nevada cities.
    
    Since Nevada Current is a Nevada news source, this function defaults to Nevada
    but checks for mentions of specific cities and regions for more precise targeting.
    
    Parameters:
    -----------
    content : str
        Content to analyze for location mentions
        
    Returns:
    --------
    Optional[str]
        Detected location or None if no location found
    """
    content = content.lower()
    
    # First try to find Nevada-specific matches
    nevada_variations = LOCATION_VARIATIONS.get("Nevada", [])
    # Since it's Nevada Current, default to Nevada if no other location is found
    location_found = "Nevada"
    
    # Check if Nevada is explicitly mentioned
    if any(re.search(r'\b' + re.escape(v.lower()) + r'\b', content) for v in nevada_variations):
        return "Nevada"
    
    # Then check other locations
    for location, variations in LOCATION_VARIATIONS.items():
        if location == "Nevada":  # Already checked
            continue
            
        # Check state name and abbreviation first
        state_variations = [variations[0], variations[1]]  # State name and abbreviation
        if any(re.search(r'\b' + re.escape(v.lower()) + r'\b', content) for v in state_variations):
            return location
            
        # Then check cities
        city_variations = variations[2:]  # All other variations are cities
        if any(re.search(r'\b' + re.escape(v.lower()) + r'\b', content) for v in city_variations):
            return location
                
    # If no specific location is found, default to Nevada for Nevada Current
    return location_found

def extract_keywords(content: str) -> List[str]:
    """
    Extract theft-related keywords to qualify leads and determine product needs.
    
    Identifies specific crime patterns to match appropriate security solutions.
    
    Parameters:
    -----------
    content : str
        Content to analyze for keywords
        
    Returns:
    --------
    List[str]
        List of found keywords indicating specific security needs
    """
    content = content.lower()
    keywords = []
    
    # Check theft keywords
    for keyword in THEFT_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', content):
            keywords.append(keyword)
            
    return keywords

def is_business_related(content: str) -> bool:
    """
    Filter for B2B sales opportunities by identifying business-related incidents.
    
    Focuses sales efforts on businesses rather than individual theft incidents.
    
    Parameters:
    -----------
    content : str
        Content to analyze for business relevance
        
    Returns:
    --------
    bool
        True if content contains business keywords indicating sales opportunity
    """
    content = content.lower()
    return any(re.search(r'\b' + re.escape(keyword) + r'\b', content) for keyword in BUSINESS_KEYWORDS)

def standardize_date(date_str: str) -> str:
    """
    Standardize incident dates for lead prioritization and follow-up timing.
    
    Handles Nevada Current specific date formats and converts to YYYY-MM-DD.
    
    Parameters:
    -----------
    date_str : str
        Date string to standardize for sales tracking
        
    Returns:
    --------
    str
        Standardized date string in YYYY-MM-DD format
    """
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
        
    try:
        # Remove timezone information if present
        date_str = re.sub(r'\s*[A-Z]{3,4}$', '', date_str)
        
        # Remove common prefixes in dates
        date_str = re.sub(r'^(Published|Updated|Posted)\s*:?\s*', '', date_str, flags=re.IGNORECASE)
        
        # Handle formatted dates like "April 2, 2025"
        date_str = re.sub(r'\s+at\s+\d+:\d+\s*(?:am|pm).*$', '', date_str, flags=re.IGNORECASE)
        
        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%B %d, %Y',
            '%B %d %Y',
            '%b %d, %Y',
            '%b %d %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%m/%d/%y'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        # If no format matches, use current date
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.now().strftime('%Y-%m-%d')
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        return datetime.now().strftime('%Y-%m-%d')

def extract_location_details(content: str) -> str:
    """
    Extract more detailed location information from content.
    
    Attempts to identify specific streets, neighborhoods, or areas within a city
    for more precise lead targeting.
    
    Parameters:
    -----------
    content : str
        Content to analyze for location details
        
    Returns:
    --------
    str
        Detailed location information or empty string if none found
    """
    # Common Nevada location patterns
    patterns = [
        r'in\s+([\w\s-]+)\s+Las\s+Vegas',
        r'in\s+([\w\s-]+)\s+Henderson',
        r'in\s+([\w\s-]+)\s+Reno',
        r'in\s+([\w\s-]+)\s+North\s+Las\s+Vegas',
        r'on\s+([\w\s-]+)\s+Boulevard',
        r'on\s+([\w\s-]+)\s+Blvd',
        r'on\s+([\w\s-]+)\s+Ave',
        r'on\s+([\w\s-]+)\s+Avenue',
        r'at\s+([\w\s-]+)\s+Casino',
        r'at\s+([\w\s-]+)\s+Resort',
        r'at\s+([\w\s-]+)\s+Hotel',
        r'at\s+the\s+([\w\s-]+)'
    ]
    
    content = content.lower()
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
    return ""