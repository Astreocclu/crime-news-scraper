"""Configuration for the Nevada Current scraper."""

# Reuse monitored locations from JSA
from ..jsa.config import MONITORED_LOCATIONS, LOCATION_VARIATIONS

# Nevada Current configuration
NEVADACURRENT_CONFIG = {
    "name": "Nevada Current",
    "url": "https://nevadacurrent.com/justice/",
    "search_url": "https://nevadacurrent.com/?s=crime",
    "selectors": {
        "posts": [
            "article.post",
            "article.type-post",
            ".post",
            ".article",
            ".entry"
        ],
        "title": [
            "h2.entry-title a",
            "h3.entry-title a",
            "h2.entry-title",
            ".entry-title",
            "h2 a",
            "h3 a"
        ],
        "date": [
            "time.entry-date",
            ".entry-date",
            "time",
            ".posted-on"
        ],
        "excerpt": [
            ".entry-summary",
            ".entry-content",
            "p"
        ],
        "link": [
            "h2.entry-title a",
            "h3.entry-title a",
            ".entry-title a",
            "h2 a",
            "h3 a"
        ],
        "image": [
            ".post-thumbnail img",
            "img",
            ".wp-post-image"
        ],
        "pagination": [
            ".nav-links a.next",
            "a.next.page-numbers",
            ".pagination a.next"
        ]
    }
}

# Keywords specific to crime reporting with Nevada focus
THEFT_KEYWORDS = [
    # Original theft terms
    'theft', 'steal', 'stolen', 'robbery', 'burglary',
    'smash-and-grab', 'shoplifting', 'larceny', 'heist',
    'break-in', 'stolen property', 'retail theft',
    'armed robbery', 'robbed', 'burglarized',
    'jewelry', 'store theft', 'business theft',

    # Additional Nevada specific terms
    'casino theft', 'strip robbery', 'resort crime',
    'pawn shop', 'luxury theft', 'watches', 'casino',
    'crime', 'criminal', 'arrest', 'police', 'suspect',
    'security', 'investigation', 'property crime',

    # Justice system terms
    'court', 'trial', 'sentenced', 'verdict', 'justice'
]

BUSINESS_KEYWORDS = [
    'store', 'shop', 'business', 'retail', 'mall', 'shopping center',
    'merchant', 'vendor', 'commercial', 'retailer', 'jewelry store',
    'pawn shop', 'boutique', 'outlet', 'dealership', 'shop owner',
    'casino', 'resort', 'hotel', 'restaurant', 'strip mall',
    'convention', 'trade show', 'corporate'
]