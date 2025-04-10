# Crime News Scraper

A modular and extensible crime news scraper that collects jewelry theft articles from multiple sources and analyzes them using Claude AI to identify sales opportunities for security screen products.

GitHub Repository: [https://github.com/Astreocclu/crime-news-scraper](https://github.com/Astreocclu/crime-news-scraper)

## Product Focus

This system is specifically designed to generate qualified sales leads for **American Security Screens** - high-quality stainless steel mesh security screens for windows and doors that prevent smash-and-grab and forced entry incidents at jewelry businesses. The scraper identifies businesses that have recently experienced theft, creating targeted sales opportunities with a 5% commission structure.

## Features

- **Sales Lead Generation**: Identify jewelry businesses that recently experienced theft incidents
- **Risk Assessment Scoring**: Evaluate security vulnerabilities and priority sales targets
- **Sales Intelligence**: Generate engaging headlines and security recommendations for security screen sales pitches
- **Business Impact Analysis**: Calculate potential impact scores to strengthen sales conversations
- **Modular Architecture**: Easily expand to new news sources for wider lead generation
- **AI-powered Analysis**: Extract actionable intelligence to drive security screen product sales
- **High-Value Target Expansion**: Discover nearby luxury goods, sports memorabilia, vape/smoke shops, and jewelry stores for additional sales opportunities

## Prerequisites

- Python 3.8+
- Chrome browser (for Selenium)
- Anthropic API key (for Claude AI)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Astreocclu/crime-news-scraper.git
cd crime-news-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

The project uses environment variables for sensitive configuration:

1. Create a `.env` file in the project root with the following variables:
```
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Database Configuration
DATABASE_PATH=crime_data.db  # Path to SQLite database file
```

2. The application will automatically load these environment variables when started.

> Note: A `.env.example` file is provided as a template. Copy it to `.env` and fill in your specific values.

### Analyzer Configuration
- `batch_size`: Number of articles to process in each batch (default: 10)
- `max_tokens`: Maximum tokens for Claude API calls (default: 4000)
- `temperature`: Temperature setting for Claude API (default: 0.7)
- `output_dir`: Directory for storing processed data (default: output)

### Sales Intelligence Features
The analyzer extracts key sales-focused data points specifically optimized for security screen product sales:

- `riskAssessment`: Priority classification (SEVERE, HIGH, MODERATE, BASIC) to identify highest-need targets
- `businessImpactScore`: 1-10 rating of impact severity for sales urgency
- `securityRecommendation`: Specific security screen recommendations based on crime type
- `businessName` and `exactAddress`: Automatically enriched target business information
- `salesPitchHeadline`: Attention-grabbing headlines for security screen sales outreach
- `comparableIncident`: Similar incidents to reference during sales conversations
- `interestingFactForSales`: Data points to strengthen security screen product conversations

## Usage

1. Run the scraper with default settings (CSV storage):
```bash
python src/main.py
```

2. Run with SQLite database storage:
```bash
python src/main.py --use-database
```

3. Additional options:
```bash
python src/main.py --no-scrape --use-database  # Use database, skip scraping
python src/main.py --batch-size 20             # Process 20 articles at once
python src/main.py --input-file path/to/file.csv  # Use specific input file
```

4. View the results in the `output` directory or query the SQLite database (`crime_data.db`)

## Project Structure

```
.
├── src/
│   ├── scrapers/           # Scraper modules
│   │   ├── base.py        # Base scraper class
│   │   ├── jsa/           # JSA scraper module
│   │   │   ├── config.py  # JSA-specific configuration
│   │   │   ├── scraper.py # JSA scraper implementation
│   │   │   └── utils.py   # JSA utility functions
│   │   └── dfw/           # DFW scraper module
│   ├── analyzer/          # Analysis module
│   │   ├── __init__.py
│   │   ├── analyzer.py    # Main analyzer implementation
│   │   └── claude_client.py # Claude API integration
│   ├── database.py        # Database operations and schema
│   └── nearby_finder/     # Nearby business finder module
│       ├── __init__.py
│       ├── finder.py      # Main nearby business finder implementation
│       ├── google_client.py # Google Maps API integration
│       └── config.py      # Finder configuration (radius, target types)
├── tests/                 # Test files
├── config/               # Global configuration
├── output/              # Generated output files
│   ├── scraped/         # Original scraped data
│   ├── analyzed/        # Analyzed business data
│   └── nearby/          # Nearby business data
├── test_data/           # Test data files
├── crime_data.db        # SQLite database for articles and analysis results
├── requirements.txt     # Project dependencies
└── .env                # Environment variables
```

## System Architecture

The system follows a modular design with five main components:

1. **Database Module**
   - Centralizes data storage and retrieval using SQLite
   - Maintains consistent schema for articles and analysis results
   - Provides efficient data querying and storage capabilities
   - Ensures data integrity through constraints like unique article URLs
   - Handles all database connections and operations

2. **Unified Scraper**
   - Acts as the main orchestrator for lead generation
   - Manages the execution of individual scraper modules
   - Stores articles in SQLite database or CSV files (backward compatibility)
   - Creates standardized lead source data

3. **Modular Scrapers**
   - Each scraper module (JSA, DFW, etc.) targets specific news sources
   - Inherits from the base scraper class
   - Implements specific scraping logic to extract potential sales leads
   - Outputs standardized data for storage in database or CSV files

4. **Sales Intelligence Analyzer**
   - Processes articles from database or CSV files to identify sales opportunities
   - Uses Claude AI to:
     - Identify and validate business locations
     - Enhance data with business names and addresses
     - Assess security risk levels and urgency
     - Calculate business impact scores
     - Generate tailored security product recommendations
     - Prioritize leads based on multiple factors
   - Stores analysis results in database for efficient querying

5. **Nearby Business Finder**
   - Uses Google Maps API to identify additional high-value targets near incident locations
   - Focuses on luxury goods stores, sports memorabilia shops, vape/smoke shops, and jewelry stores
   - Generates a dedicated spreadsheet with:
     - Business name, address, and store type
     - Distance from original incident location
     - Original incident details (date, crime type, value of stolen items)
   - Provides target locations for cross-referencing with existing lead lists for outreach campaigns

## Sales Lead Generation Workflow

1. **Source Monitoring**: The unified scraper continuously monitors news sources for jewelry crime incidents, focusing on the JSA (Jewelers Security Alliance) website initially
2. **Lead Collection**: Modular scrapers extract relevant business theft incidents, particularly those involving forced entry or smash-and-grab crimes
3. **Data Storage and Standardization**:
   - Fetches theft incident details from news sources
   - Processes and standardizes the data for analysis
   - Stores articles in SQLite database with unique constraints to prevent duplicates
   - Optionally saves data to CSV files for backward compatibility
4. **Lead Qualification**:
   - Uses Claude AI to validate leads and enrich business information
   - Pulls unanalyzed articles from database for processing
   - Identifies precise business locations and contact information for security screen sales visits
   - Analyzes crime patterns and severity to determine security screen sales urgency
   - Calculates business impact scores to prioritize security screen outreach
   - Generates specific security screen product recommendations
   - Stores analysis results in database for efficient querying and reporting
   - Creates prioritized lead reports for American Security Screens sales teams
5. **High-Value Target Expansion**:
   - Identifies nearby luxury goods stores, sports memorabilia shops, vape/smoke shops, and jewelry businesses within configurable radius of incident locations
   - Generates a dedicated spreadsheet of high-value targets for targeted security screen outreach
   - References original incident details with each nearby business to strengthen sales urgency
   - Creates an "early prevention" sales strategy for businesses that haven't yet experienced theft
   - Enables "neighborhood sweep" approach for efficient in-person sales visits focusing on all high-value merchandise locations
6. **Commission Structure**:
   - The system is optimized to generate qualified leads that convert to actual security screen sales
   - Each successful sale initiated through the system's leads generates a 5% commission

## Development

### Adding a New Scraper
1. Create a new module in `src/scrapers/`
2. Implement the base scraper interface
3. Add configuration in the module's directory
4. Update the unified scraper to include the new module

### Setting Up the Nearby Business Finder

To utilize the Google Maps API for finding nearby high-value targets:

1. **Get a Google Maps API Key**
   - Create a project in Google Cloud Platform
   - Enable the Places API and Maps JavaScript API
   - Generate an API key with appropriate restrictions
   - Add the key to your `.env` file

2. **Configure Target Types**
   - Edit `src/nearby_finder/config.py` to modify:
     - Search radius (default: 1 mile)
     - Target business types (luxury goods, sports memorabilia, vape/smoke shops, jewelry)
     - Maximum number of results per category

3. **Run the Nearby Finder**
   ```bash
   python src/nearby_finder/finder.py --input-file output/analyzed/analyzed_leads_YYYYMMDD_HHMMSS.csv
   ```

4. **Output Files**
   - Results are saved to `output/nearby/nearby_businesses_YYYYMMDD_HHMMSS.csv`
   - Each row contains both the original incident data and the nearby business information

## Development Philosophy

### Testing Workflow
The project follows a specific testing workflow to ensure reliability:

1. **Create Test Copy**
   - Copy the current working file to a test file (e.g., `analyzer.py` → `test_analyzer.py`)
   - This preserves the working version while testing changes

2. **Test Implementation**
   - Make changes and test the new functionality in the test file
   - Verify all features work as expected
   - Debug and fix any issues

3. **Merge Changes**
   - Once testing is complete and successful
   - The LLM (AI assistant) merges the test file back into the main implementation
   - Ensures a clean, working codebase
   - Avoids confusion about which files to run

This approach ensures:
- Safe testing without breaking working code
- Clear separation between testing and production code
- Clean final codebase without duplicate files
- No confusion about which files to run

### Example Workflow
```bash
# 1. Create test copy
cp src/analyzer/analyzer.py src/analyzer/test_analyzer.py

# 2. Make and test changes in test_analyzer.py
# ... make changes and test ...

# 3. Once verified, merge back to main file
# (This is done by the LLM to ensure clean integration)
```

### Comprehensive Testing System

The project also includes a formal testing framework in the `tests/` directory:

1. **Unit Tests**: Test individual components in isolation
   - Scraper modules
   - Utility functions
   - Parser functions

2. **Integration Tests**: Verify components work together
   - Scraper pipelines
   - Combined scrapers via the unified scraper
   - Data storage processes

3. **Mock Tests**: Test without making real web requests
   - Use fixture data
   - Mock API responses

To run the test suite:
```bash
pytest tests/
```

See `tests/README.md` for detailed information about the testing system and guidelines for adding new tests.

## Testing

- Test files are located in the `tests/`