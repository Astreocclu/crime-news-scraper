"""
Utility functions for the NewsAPI scraper module.

This module provides specialized functions for processing news articles from NewsAPI:
- Location detection for targeted regional sales efforts
- Keyword extraction to identify theft-related incidents
- Business relevance filtering to focus on B2B sales opportunities
- Date standardization for consistent lead tracking and follow-up
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
from .config import LOCATION_VARIATIONS, THEFT_KEYWORDS, BUSINESS_KEYWORDS

logger = logging.getLogger(__name__)

def detect_location(content: str) -> Optional[str]:
    """
    Detect location from content using location variations to identify sales territories.
    
    Analyzes article text to identify which sales region the potential lead belongs to,
    enabling targeted outreach by the appropriate regional sales team.
    
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
    
    # First try to find state matches
    for location, variations in LOCATION_VARIATIONS.items():
        # Check state name and abbreviation first
        state_variations = [variations[0], variations[1]]  # State name and abbreviation
        if any(re.search(r'\b' + re.escape(v.lower()) + r'\b', content) for v in state_variations):
            return location
            
        # Then check cities
        city_variations = variations[2:]  # All other variations are cities
        if any(re.search(r'\b' + re.escape(v.lower()) + r'\b', content) for v in city_variations):
            return location
                
    return None

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
    Standardize dates from NewsAPI to consistent YYYY-MM-DD format.
    
    NewsAPI returns dates in ISO 8601 format, but this function handles other formats
    as well for consistency with other scrapers.
    
    Parameters:
    -----------
    date_str : str
        Date string to standardize
        
    Returns:
    --------
    str
        Standardized date string in YYYY-MM-DD format
    """
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
        
    try:
        # Handle ISO 8601 format (standard for NewsAPI)
        date_str = date_str.split('T')[0] if 'T' in date_str else date_str
        
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
            '%m/%d/%Y'
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