# Enhanced Address Finder

This module provides functionality to extract and geocode addresses from crime news articles using a combination of text analysis and the Google Geocoding API.

## Features

- Extract potential addresses from text using pattern matching and contextual clues
- Infer potential addresses based on business names and location information
- Verify and standardize addresses using the Google Geocoding API
- Command-line interface for easy integration into workflows

## Usage

### Command-Line Interface

The module provides a command-line interface for extracting addresses from text:

```bash
# Extract address from direct text input
python -m src.address_finder.address_extractor --text "A robbery occurred at the jewelry store located at 5500 Preston Road in Dallas, TX last night."

# Extract address from a file
python -m src.address_finder.address_extractor --file /path/to/article.txt

# Extract address from a URL (requires internet connection)
python -m src.address_finder.address_extractor --url http://example.com/article

# Add additional context to improve geocoding accuracy
python -m src.address_finder.address_extractor --text "..." --city "Dallas" --state "TX"

# Output in different formats
python -m src.address_finder.address_extractor --text "..." --output-format json
python -m src.address_finder.address_extractor --text "..." --output-format csv
```

### Programmatic Usage

You can also use the module programmatically in your Python code:

```python
from src.address_finder import EnhancedAddressFinder

# Initialize the finder
finder = EnhancedAddressFinder()

# Find address in text
text = "A jewelry store in North Dallas was robbed yesterday afternoon. The store, Diamond Treasures, is located at 5500 Preston Road."
result = finder.find_address(text)

# Check if an address was found
if result.get("success", False):
    print(f"Found address: {result['formatted_address']}")
    print(f"Business name: {result['name']}")
    print(f"Coordinates: {result['lat']}, {result['lng']}")
else:
    print(f"Failed to find address: {result.get('reason')}")
```

## Configuration

The module uses the following configuration:

- Google Maps API key: Set in the `.env` file or pass directly to the `EnhancedAddressFinder` constructor
- Confidence threshold: Minimum confidence score for address confirmation (default: 0.7)
- Maximum API calls: Maximum number of API calls per address inference (default: 3)

## Output Format

The module can output results in three formats:

### Text Format (default)

```
Address Extraction Results:
Inferred: "jewelry store in 5500 Preston Road" -> Verified: "6821 Preston Rd, Dallas, TX 75205, United States" (Lat: 32.8490103, Lng: -96.80454069999999)
Business Name: de Boulle Diamond & Jewelry - Patek Philippe Authorized Dealer
Phone: (214) 522-2400
Website: http://www.deboulle.com/
Confidence: 1.0
```

### JSON Format

```json
{
  "place_id": "ChIJvXRW3_eeToYRqFFapZN44AA",
  "name": "de Boulle Diamond & Jewelry - Patek Philippe Authorized Dealer",
  "formatted_address": "6821 Preston Rd, Dallas, TX 75205, United States",
  "lat": 32.8490103,
  "lng": -96.80454069999999,
  "confidence": 1.0,
  "original_query": "jewelry store in 5500 Preston Road",
  "phone_number": "(214) 522-2400",
  "website": "http://www.deboulle.com/",
  "original_text": "A robbery occurred at the jewelry store located at 5500 Preston Road in Dallas, TX last night.",
  "location_clues": {
    "geographic_entities": [
      "Dallas",
      "in",
      "TX",
      "5500 Preston Road"
    ],
    "business_entities": [
      "A robbery occurred at the",
      "jewelry store"
    ],
    "contextual_info": [
      "located at"
    ]
  },
  "success": true
}
```

### CSV Format

```
inferred_query,formatted_address,lat,lng,confidence,place_id,name,phone_number,website
jewelry store in 5500 Preston Road,6821 Preston Rd, Dallas, TX 75205, United States,32.8490103,-96.80454069999999,1.0,ChIJvXRW3_eeToYRqFFapZN44AA,de Boulle Diamond & Jewelry - Patek Philippe Authorized Dealer,(214) 522-2400,http://www.deboulle.com/
```
