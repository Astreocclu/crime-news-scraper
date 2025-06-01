"""Configuration for the NewsAPI scraper."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
NEWSAPI_CONFIG = {
    "name": "NewsAPI",
    "base_url": "https://newsapi.org/v2/",
    "api_key": os.getenv("NEWSAPI_KEY", "010ae97959454a2c930036138e2f42ee"),
    "default_params": {
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100
    },
    "search_terms": [
        # Location-specific searches
        "Nevada jewelry store theft",
        "California jewelry store theft",
        "Arizona jewelry store theft",
        "Texas jewelry store theft",
        "Las Vegas jewelry store robbery",
        "Los Angeles jewelry store robbery",
        "San Francisco jewelry store robbery",
        "Phoenix jewelry store robbery",
        "Dallas jewelry store robbery",
        "Houston jewelry store robbery",

        # Store type variations
        "luxury store smash and grab",
        "sports memorabilia theft",
        "high-end watch store robbery",
        "jeweler burglary",
        "luxury retail heist"
    ]
}

# Shared location configuration
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