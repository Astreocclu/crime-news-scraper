"""Configuration for the WFAA scraper."""

# Reuse monitored locations from JSA
from ..jsa.config import MONITORED_LOCATIONS, LOCATION_VARIATIONS

# WFAA-specific configuration
WFAA_CONFIG = {
    "name": "WFAA Crime News",
    "url": "https://www.wfaa.com/section/crime",
    "selectors": {
        "posts": [
            ".grid__module",
            "[data-module]",
            "article",
            ".story-card",
            ".article-card"
        ],
        "title": [
            ".grid__module-heading", 
            ".headline", 
            "h2", 
            "h3", 
            "h4"
        ],
        "date": [
            ".published-date", 
            "time", 
            ".date",
            ".timestamp"
        ],
        "excerpt": [
            ".description", 
            ".summary", 
            "p",
            ".grid__module-description"
        ],
        "link": [
            "a",
            ".story-link",
            ".grid__module-heading a"
        ],
        "image": [
            "img",
            ".story-image",
            ".lazy-image"
        ]
    }
}

# Keywords specific to Texas crime reporting - expanded to include more general crime terms
THEFT_KEYWORDS = [
    # Original theft terms
    'theft', 'steal', 'stolen', 'robbery', 'burglary',
    'smash-and-grab', 'shoplifting', 'larceny', 'heist',
    'break-in', 'stolen property', 'retail theft',
    'armed robbery', 'robbed', 'burglarized',
    'jewelry', 'store theft', 'business theft',
    
    # Additional general crime terms that might be relevant
    'crime', 'criminal', 'arrest', 'police', 'suspect',
    'security', 'investigation', 'property crime', 
    'shop owner', 'business owner', 'retail crime'
]

BUSINESS_KEYWORDS = [
    'store', 'shop', 'business', 'retail', 'mall', 'shopping center',
    'merchant', 'vendor', 'commercial', 'retailer', 'jewelry store',
    'pawn shop', 'boutique', 'outlet', 'dealership', 'shop owner'
]