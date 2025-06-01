"""
Configuration for the Enhanced Address Finder module.
"""
import os
from typing import List, Dict

# Google Places API configuration
# Use the existing API key from the nearby_finder module
from src.nearby_finder.config import GOOGLE_MAPS_API_KEY

# NLP configuration
# List of common city names to help with recognition
COMMON_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "El Paso", "Nashville",
    "Detroit", "Oklahoma City", "Portland", "Las Vegas", "Memphis", "Louisville",
    "Baltimore", "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento",
    "Kansas City", "Long Beach", "Mesa", "Atlanta", "Colorado Springs", "Raleigh",
    "Omaha", "Miami", "Oakland", "Minneapolis", "Tulsa", "Cleveland", "Wichita",
    "Arlington", "New Orleans", "Bakersfield", "Tampa", "Honolulu", "Aurora",
    "Anaheim", "Santa Ana", "St. Louis", "Riverside", "Corpus Christi", "Pittsburgh",
    "Lexington", "Anchorage", "Stockton", "Cincinnati", "St. Paul", "Toledo",
    "Newark", "Greensboro", "Plano", "Henderson", "Lincoln", "Buffalo", "Fort Wayne",
    "Jersey City", "Chula Vista", "Orlando", "St. Petersburg", "Norfolk", "Chandler",
    "Laredo", "Madison", "Durham", "Lubbock", "Winston-Salem", "Garland", "Glendale",
    "Hialeah", "Reno", "Baton Rouge", "Irvine", "Chesapeake", "Irving", "Scottsdale",
    "North Las Vegas", "Fremont", "Gilbert", "San Bernardino", "Boise", "Birmingham",
    "Frisco", "McKinney", "Plano", "Allen", "Richardson", "Garland", "Irving",
    "Carrollton", "Lewisville", "Denton", "Arlington", "Grand Prairie", "Mesquite"
]

# List of US state names and abbreviations
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}

# Common business types
BUSINESS_TYPES = [
    "jewelry store", "jewelry", "jeweler", "jewelers", "jewelry shop",
    "pawn shop", "pawnshop", "pawn broker", "pawnbroker",
    "gun store", "gun shop", "firearms dealer", "firearm dealer",
    "electronics store", "electronics shop", "electronics dealer",
    "convenience store", "convenience shop", "convenience mart",
    "gas station", "service station", "filling station",
    "liquor store", "liquor shop", "wine shop", "wine store",
    "smoke shop", "vape shop", "tobacco shop", "cigar shop",
    "bank", "credit union", "financial institution",
    "atm", "automated teller machine", "cash machine",
    "pharmacy", "drug store", "chemist",
    "dispensary", "cannabis dispensary", "marijuana dispensary",
    "check cashing", "payday loan", "cash advance",
    "luxury goods", "high-end", "designer", "boutique",
    "sports memorabilia", "collectibles", "memorabilia shop",
    "antique", "antiques", "antique shop", "antique store",
    "art gallery", "art dealer", "art store",
    "coin shop", "coin dealer", "numismatic",
    "stamp shop", "stamp dealer", "philatelic"
]

# Contextual phrases that might indicate location relationships
CONTEXTUAL_PHRASES = [
    "near", "next to", "adjacent to", "across from", "opposite", "opposite of",
    "in front of", "behind", "beside", "close to", "in the vicinity of",
    "in the area of", "around", "on the corner of", "at the intersection of",
    "between", "located at", "located in", "located on", "located near",
    "situated at", "situated in", "situated on", "situated near",
    "in the shopping center", "in the mall", "in the plaza", "in the strip mall",
    "in the shopping plaza", "in the shopping district", "in downtown",
    "in uptown", "in midtown", "in the north side", "in the south side",
    "in the east side", "in the west side", "in north", "in south", "in east", "in west",
    "on the north side", "on the south side", "on the east side", "on the west side"
]

# Google Places API configuration
PLACES_API_TEXT_SEARCH_ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_API_FIND_PLACE_ENDPOINT = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
PLACES_API_DETAILS_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json"

# Maximum number of API calls to make per address inference
MAX_API_CALLS_PER_INFERENCE = 3

# Confidence threshold for address confirmation (0.0 to 1.0)
CONFIDENCE_THRESHOLD = 0.7

# Common address patterns for extraction
ADDRESS_PATTERNS = [
    # Street number + street name + city/state
    r'(\d+\s+[A-Za-z0-9\s\.]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl)\.?(?:\s+[A-Za-z]+)?(?:\s*,\s*[A-Za-z\s]+,\s*[A-Z]{2}))',

    # Address mentioned after "located at" or similar phrases
    r'located\s+at\s+([^,\.;]+(?:,\s*[^,\.;]+){1,3})',
    r'address\s+(?:of|at|is|was)\s+([^,\.;]+(?:,\s*[^,\.;]+){1,3})',

    # Business name + at + address
    r'([A-Za-z0-9\s&\'-]+)\s+at\s+(\d+\s+[A-Za-z0-9\s\.]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl))',

    # Address in parentheses
    r'\(([^()]*\d+[^()]*(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Parkway|Pkwy|Terrace|Ter|Place|Pl)[^()]*)\)',
]
