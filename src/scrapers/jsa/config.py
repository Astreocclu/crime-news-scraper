"""Configuration for the JSA scraper."""

# Shared configuration
MONITORED_LOCATIONS = [
    "Nevada", "California", "Georgia", "Texas", "Arizona"
]

LOCATION_VARIATIONS = {
    "Nevada": ["Nevada", "NV", "Las Vegas", "Reno", "Henderson"],
    "California": ["California", "CA", "Los Angeles", "San Francisco", "San Diego", "Sacramento", "Monterey"],
    "Georgia": ["Georgia", "GA", "Atlanta", "Savannah", "Macon"],
    "Texas": ["Texas", "TX", "Dallas", "Houston", "Austin", "San Antonio"],
    "Arizona": ["Arizona", "AZ", "Phoenix", "Tucson", "Scottsdale", "Mesa"]
}

JSA_CONFIG = {
    "name": "Jewelers Security Alliance",
    "url": "https://jewelerssecurity.org/",
    "crimes_url": "https://jewelerssecurity.org/category/crime-news/crimes/",
    "selectors": {
        "posts": [
            "article",  # Most common container for blog posts
            ".post",    # Common WordPress post class
            ".entry",   # Another common post class
            ".blog-post" # Another variation
        ],
        "article": [
            ".post-content",
            ".entry-content",
            ".content"
        ],
        "title": ["h1", "h2", "h3", ".entry-title", ".post-title"],
        "date": ["time", ".date", ".post-date", ".entry-date"],
        "excerpt": ["p", ".excerpt", ".entry-summary", ".post-excerpt"],
        "pagination": {
            "next_page": ".next.page-numbers",
            "last_page": ".page-numbers:not(.next):not(.prev):not(.dots)"
        }
    }
}

# Keywords for classification
THEFT_KEYWORDS = [
    'theft', 'thefts', 'steal', 'stole', 'stolen', 
    'robbery', 'robber', 'robberies', 'rob', 'robbed',
    'burglary', 'burglar', 'burglaries',
    'smash-and-grab', 'smash and grab', 
    'jewelry', 'jeweler', 'jewelers', 'jewelery', 
    'necklace', 'bracelet', 'ring', 'watches', 'rolex',
    'diamond', 'gold', 'silver', 'precious'
]

BUSINESS_KEYWORDS = [
    'store', 'shop', 'business', 'retail', 'mall',
    'jeweler', 'jewelers', 'jewelry', 'jewelery'
] 