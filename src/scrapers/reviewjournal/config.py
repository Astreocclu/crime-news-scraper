"""Configuration for the Review Journal scraper."""

# Reuse monitored locations from JSA
from ..jsa.config import MONITORED_LOCATIONS, LOCATION_VARIATIONS

# Review Journal-specific configuration
REVIEWJOURNAL_CONFIG = {
    "name": "Las Vegas Review Journal",
    "url": "https://www.reviewjournal.com/crime/",
    "selectors": {
        "posts": [
            ".rj-story",
            "article"
        ],
        "title": [
            ".tease-head a", 
            ".tease-head",
            "h2 a",
            "h3 a", 
            "h2", 
            "h3"
        ],
        "date": [
            "time.entry-date", 
            ".posted-date", 
            ".date"
        ],
        "excerpt": [
            ".tease-excerpt",
            ".excerpt",
            ".f-desc",
            "p.excerpt"
        ],
        "link": [
            ".tease-head a",
            "h2 a",
            "h3 a",
            "a.rj-article-title"
        ],
        "image": [
            ".rj-img img",
            "img"
        ]
    }
}

# Keywords specific to crime reporting - expanded to include Las Vegas terms
THEFT_KEYWORDS = [
    # Original theft terms
    'theft', 'steal', 'stolen', 'robbery', 'burglary',
    'smash-and-grab', 'shoplifting', 'larceny', 'heist',
    'break-in', 'stolen property', 'retail theft',
    'armed robbery', 'robbed', 'burglarized',
    'jewelry', 'store theft', 'business theft',
    
    # Additional Las Vegas specific terms
    'casino theft', 'strip robbery', 'resort crime',
    'pawn shop', 'luxury theft', 'watches', 'casino',
    'crime', 'criminal', 'arrest', 'police', 'suspect',
    'security', 'investigation', 'property crime'
]

BUSINESS_KEYWORDS = [
    'store', 'shop', 'business', 'retail', 'mall', 'shopping center',
    'merchant', 'vendor', 'commercial', 'retailer', 'jewelry store',
    'pawn shop', 'boutique', 'outlet', 'dealership', 'shop owner',
    'casino', 'resort', 'hotel', 'restaurant', 'strip mall'
]