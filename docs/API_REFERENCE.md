# Crime News Scraper - API Reference

This document provides comprehensive API documentation for the Crime News Scraper system.

## Table of Contents

1. [Database Operations](#database-operations)
2. [Scraper Modules](#scraper-modules)
3. [Analyzer Module](#analyzer-module)
4. [Nearby Finder Module](#nearby-finder-module)
5. [Utility Functions](#utility-functions)

## Database Operations

### `src.database`

Core database operations for the Crime News Scraper system.

#### Functions

##### `get_db_connection() -> Optional[sqlite3.Connection]`

Establishes and returns a connection to the SQLite database.

**Returns:**
- `Optional[sqlite3.Connection]`: Database connection object or None if connection fails

**Example:**
```python
from src.database import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    # Perform database operations
    conn.close()
```

##### `initialize_database() -> bool`

Initialize the database by creating all necessary tables and indexes.

**Returns:**
- `bool`: True if database initialization was successful, False otherwise

**Tables Created:**
- `articles`: Raw scraped news articles
- `analysis_results`: AI-analyzed crime incident data
- `nearby_businesses`: Target businesses near incidents with lead scoring

**Example:**
```python
from src.database import initialize_database

success = initialize_database()
if success:
    print("Database initialized successfully")
```

##### `save_nearby_businesses(nearby_data_list: List[Dict[str, Union[str, int, float, bool]]]) -> bool`

Save nearby businesses to the database with lead scoring information.

**Parameters:**
- `nearby_data_list`: List of dictionaries containing nearby business data

**Returns:**
- `bool`: True if all businesses were saved successfully, False otherwise

**Example:**
```python
from src.database import save_nearby_businesses

business_data = [
    {
        'businessName': 'Premium Jewelry Store',
        'businessType': 'jewelry',
        'exactAddress': '123 Main St, City, State',
        'distance_from_incident': 0.5,
        'lead_score': 6,
        'is_original_location': False
    }
]

success = save_nearby_businesses(business_data)
```

## Scraper Modules

### `src.scrapers.unified.UnifiedScraper`

Main orchestrator for multi-source news scraping.

#### Methods

##### `scrape_all(deep_check: bool = False) -> Dict[str, Any]`

Execute scraping across all configured news sources.

**Parameters:**
- `deep_check`: Whether to perform deep validation of scraped content

**Returns:**
- `Dict[str, Any]`: Results summary with statistics and file paths

**Example:**
```python
from src.scrapers.unified import UnifiedScraper

scraper = UnifiedScraper()
results = scraper.scrape_all(deep_check=False)
print(f"Scraped {results['total_articles']} articles")
```

### Base Scraper Interface

All scraper modules inherit from the base scraper class and implement:

##### `scrape() -> List[Dict[str, Any]]`

Scrape articles from the specific news source.

**Returns:**
- `List[Dict[str, Any]]`: List of article dictionaries

## Analyzer Module

### `src.analyzer.analyzer_manual_test.SingleBatchAnalyzer`

AI-powered crime incident analysis using Claude AI.

#### Methods

##### `process_single_batch(input_file: Optional[str] = None, batch_size: int = 10) -> bool`

Process a batch of articles through AI analysis.

**Parameters:**
- `input_file`: Path to input CSV file (None to use database)
- `batch_size`: Number of articles to process in the batch

**Returns:**
- `bool`: True if analysis completed successfully

**Example:**
```python
from src.analyzer.analyzer_manual_test import SingleBatchAnalyzer

analyzer = SingleBatchAnalyzer()
success = analyzer.process_single_batch(
    input_file="output/scraped_data.csv",
    batch_size=20
)
```

## Nearby Finder Module

### `src.nearby_finder.finder.NearbyBusinessFinder`

Targeted business discovery with exclusive focus on three business types.

#### Target Business Types (Exclusive)
1. **Jewelry stores** (primary target)
2. **Sports memorabilia stores** (secondary target)
3. **Luxury goods stores** (secondary target)

#### Methods

##### `find_nearby_businesses(analysis_file: str) -> bool`

Find nearby target businesses for analyzed crime incidents.

**Parameters:**
- `analysis_file`: Path to CSV file containing analyzed incidents

**Returns:**
- `bool`: True if nearby business search completed successfully

**Example:**
```python
from src.nearby_finder.finder import NearbyBusinessFinder

finder = NearbyBusinessFinder()
success = finder.find_nearby_businesses("output/analyzed_leads.csv")
```

### `src.nearby_finder.google_client.GoogleMapsClient`

Google Maps API client for business discovery.

#### Methods

##### `find_nearby_places(latitude: float, longitude: float, radius: int = 1609) -> List[Dict]`

Find nearby businesses based on location and target types.

**Parameters:**
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate  
- `radius`: Search radius in meters (default: 1609 = 1 mile)

**Returns:**
- `List[Dict]`: List of nearby business dictionaries

##### `geocode_address(address: str) -> Dict`

Convert an address to geographic coordinates.

**Parameters:**
- `address`: Address string to geocode

**Returns:**
- `Dict`: Geocoding result with latitude/longitude

## Lead Scoring System

### Scoring Algorithm

The system uses an intelligent scoring algorithm for lead quality:

**Score Range:** 3-6 points
- **Distance-based scoring:**
  - Within 0.25 miles: +2 points
  - Within 1.0 mile: +1 point
  - Beyond 1 mile: 0 points (filtered out)

- **Business type scoring:**
  - Jewelry stores: +3 points (primary target)
  - Sports memorabilia stores: +3 points (secondary target)
  - Luxury goods stores: +3 points (secondary target)
  - All other business types: 0 points (filtered out)

**High-Quality Leads:** Score ≥5 (62.2% of all leads)

## Configuration

### Environment Variables

Key configuration options:

```bash
# API Keys
ANTHROPIC_API_KEY=your_claude_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
PERPLEXITY_API_KEY=your_perplexity_key

# Database
DATABASE_PATH=crime_data.db

# Processing
DEFAULT_BATCH_SIZE=10
DEFAULT_SEARCH_RADIUS=1609

# Performance
GOOGLE_MAPS_RATE_LIMIT_DELAY=0.2
MAX_RESULTS_PER_CATEGORY=5
```

## Error Handling

All modules implement comprehensive error handling:

- **Database errors**: SQLite connection and operation errors
- **API errors**: Rate limiting, authentication, and service errors
- **Network errors**: Connection timeouts and retries
- **Data validation errors**: Schema validation and data integrity

## Performance Optimization

- **Database indexing**: Optimized queries with proper indexes
- **API rate limiting**: Respects service limits with delays
- **Batch processing**: Efficient processing of large datasets
- **Memory management**: Streaming processing for large files

For detailed implementation examples, see the `examples/` directory.
