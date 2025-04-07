"""
Configuration settings for the nearby business finder module.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Search configuration
DEFAULT_SEARCH_RADIUS = 1609  # 1 mile in meters
MAX_RESULTS_PER_CATEGORY = 5

# Target business types to look for
TARGET_BUSINESS_TYPES = [
    # Jewelry stores
    "jewelry_store",
    
    # Luxury goods
    "clothing_store",
    "shopping_mall",
    "store",  # Used for both luxury goods and sports memorabilia
]

# Keywords for narrowing down general store results
LUXURY_KEYWORDS = [
    "luxury",
    "high-end",
    "designer",
    "boutique",
    "premium"
]

SPORTS_MEMORABILIA_KEYWORDS = [
    "sports",
    "memorabilia",
    "collectibles",
    "cards",
    "autograph",
    "team"
]

# Remove vape/smoke shops from search
VAPE_SMOKE_KEYWORDS = []

# Output configuration
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output", "nearby")