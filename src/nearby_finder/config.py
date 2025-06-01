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
DEFAULT_SEARCH_RADIUS = int(os.getenv("DEFAULT_SEARCH_RADIUS", "1609"))  # 1 mile in meters
MAX_RESULTS_PER_CATEGORY = int(os.getenv("MAX_RESULTS_PER_CATEGORY", "5"))

# Target business types to look for - ONLY OUR THREE TARGET TYPES
TARGET_BUSINESS_TYPES = [
    # Primary target - Jewelry stores (highest priority)
    "jewelry_store",

    # Secondary targets - Search specifically for these types
    "luxury_goods_store",
    "sports_memorabilia_store",
]

# Keywords for narrowing down general store results - ENHANCED FOR TARGET IDENTIFICATION
LUXURY_KEYWORDS = [
    # Core luxury terms
    "luxury", "high-end", "designer", "boutique", "premium", "exclusive", "upscale",
    "fine", "elite", "prestige", "couture", "bespoke", "artisan", "custom",

    # Luxury brands and categories
    "rolex", "cartier", "tiffany", "gucci", "louis vuitton", "prada", "chanel",
    "hermès", "versace", "armani", "dior", "burberry", "fendi", "bulgari",

    # Luxury product categories
    "watches", "handbags", "leather goods", "accessories", "timepieces",
    "fine jewelry", "diamonds", "pearls", "gold", "silver", "platinum"
]

SPORTS_MEMORABILIA_KEYWORDS = [
    # Core sports memorabilia terms
    "sports", "memorabilia", "collectibles", "cards", "autograph", "team",
    "trading cards", "baseball cards", "football cards", "basketball cards",

    # Sports categories
    "baseball", "football", "basketball", "hockey", "soccer", "golf", "tennis",
    "nfl", "nba", "mlb", "nhl", "mls", "ncaa", "olympics",

    # Collectible types
    "signed", "autographed", "vintage", "rookie card", "jersey", "helmet",
    "bat", "ball", "puck", "trophy", "championship", "hall of fame",

    # Collectible stores
    "card shop", "sports cards", "collectible shop", "memorabilia store"
]

# Remove vape/smoke shops from search
VAPE_SMOKE_KEYWORDS = []

# Output configuration
BASE_OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), BASE_OUTPUT_DIR, "nearby")