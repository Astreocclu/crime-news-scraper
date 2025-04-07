"""Configuration for the 8 News Now scraper."""

# Reuse monitored locations from JSA
from ..jsa.config import MONITORED_LOCATIONS, LOCATION_VARIATIONS

# 8 News Now configuration
EIGHTNEWS_CONFIG = {
    "name": "8 News Now Las Vegas",
    "url": "https://www.8newsnow.com/news/local-news/crime/",
    "selectors": {
        "posts": [
            "article",
            ".article-list__article",
            ".article"
        ],
        "title": [
            "h3.article-list__article-title", 
            ".article-list__article-title",
            "h2", 
            "h3"
        ],
        "date": [
            "time",
            ".article-date", 
            ".posted-date"
        ],
        "excerpt": [
            ".article-list__article-description",
            ".article-description",
            "p"
        ],
        "link": [
            ".article-list__article-headline a",
            "h3 a",
            "a.article-headline"
        ],
        "image": [
            "img",
            ".article-list__image"
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