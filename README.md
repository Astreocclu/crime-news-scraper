# Crime News Scraper

A comprehensive system for scraping crime news articles, analyzing them for business-related incidents, and finding nearby businesses for **targeted security lead generation**.

GitHub Repository: [https://github.com/Astreocclu/crime-news-scraper](https://github.com/Astreocclu/crime-news-scraper)

## 🎯 **FOCUSED TARGETING APPROACH**

This system exclusively targets **three high-value business types** for maximum lead quality:

1. **💎 Jewelry Stores** (Primary Target - Highest Priority)
2. **🏆 Sports Memorabilia Stores** (Secondary Target)
3. **👑 Luxury Goods Stores** (Secondary Target)

**100% Target Focus**: The system filters out all other business types to ensure only high-quality, relevant leads.

## ✨ **Key Features**

- **🔍 Multi-Source News Scraping**: Automated collection from multiple news sources
- **🤖 AI-Powered Analysis**: Uses Claude AI to extract detailed crime incident information
- **📍 Address Validation**: 81.4% success rate with multiple validation sources
- **🎯 Targeted Business Discovery**: Exclusively finds our three target business types
- **📊 Intelligent Lead Scoring**: Advanced scoring system (62.2% high-quality leads)
- **💾 Database Storage**: SQLite database for persistent data management
- **📈 Performance Optimized**: ~10.4 seconds per article processing speed

## 📊 **Performance Benchmarks**

- **Processing Speed**: ~10.4 seconds per article (excellent)
- **Address Validation**: 81.4% success rate
- **Lead Quality**: 62.2% high-quality leads (score ≥5)
- **Target Business Focus**: 100% (jewelry, sports memorabilia, luxury goods only)
- **Data Quality**: 95.1% business naming success rate

## Prerequisites

- Python 3.8+
- Chrome browser (for Selenium)
- Anthropic API key (for Claude AI)
- Perplexity API key (for address validation)

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

The project uses environment variables for configuration:

1. Copy the `.env.example` file to create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit the `.env` file to set your configuration values:
```
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Database Configuration
DATABASE_PATH=crime_data.db

# Output Directories
OUTPUT_DIR=output
LOGS_DIR=logs

# Scraper Configuration
SCRAPE_DEEP_CHECK=false
MAX_ARTICLES_PER_SOURCE=100

# Analyzer Configuration
DEFAULT_BATCH_SIZE=10
CLAUDE_MODEL=claude-3-7-sonnet-20250219
MAX_TOKENS=4000
TEMPERATURE=0.7
```

2. The application will automatically load these environment variables when started.

> Note: A `.env.example` file is provided as a template. Copy it to `.env` and fill in your specific values.

### Analyzer Configuration
- `batch_size`: Number of articles to process in each batch (default: 10)
- `max_tokens`: Maximum tokens for Claude API calls (default: 4000)
- `temperature`: Temperature setting for Claude API (default: 0.7)
- `output_dir`: Directory for storing processed data (default: output)

### Address Validation with Perplexity API
The system uses the Perplexity API to validate and enhance address information for crime incidents:

- Automatically extracts business names and locations from crime reports
- Queries the Perplexity API with structured prompts to find exact addresses
- Normalizes and validates returned addresses for consistency
- Assigns confidence scores based on validation results
- Requires a valid Perplexity API key in the `.env` file

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

### Command-Line Interface

The application provides a unified command-line interface with multiple commands:

```bash
python -m src.main <command> [options]
```

Available commands:
- `scrape`: Run the scraper to collect articles from configured sources
- `analyze`: Process articles through the analyzer
- `nearby`: Find nearby businesses for analyzed incidents
- `workflow`: Run the complete workflow (scrape, analyze, nearby, complete)

### Convenience Scripts

For ease of use, wrapper scripts are provided in the `scripts/` directory:

```bash
# Run the scraper
python scripts/scrape.py [options]

# Run the analyzer
python scripts/analyze.py [options]

# Find nearby businesses
python scripts/nearby.py --analysis-file FILE [options]

# Run the complete workflow
python scripts/workflow.py [options]
```

### Examples

1. Run the complete workflow with default settings (CSV storage):
```bash
python scripts/workflow.py
```

2. Run with SQLite database storage:
```bash
python scripts/workflow.py --use-database
```

3. Run only the scraper with database storage:
```bash
python scripts/scrape.py --use-database
```

4. Run only the analyzer with a specific batch size:
```bash
python scripts/analyze.py --batch-size 20 --use-database
```

5. Find nearby businesses for a specific analysis file:
```bash
python scripts/nearby.py --analysis-file output/analysis/analyzed_leads_20250330_084420.csv
```

6. Run the workflow with a maximum runtime and progress indicator:
```bash
python scripts/workflow.py --max-runtime 10 --progress-type spinner
```

7. View the results in the `output` directory or query the SQLite database (`crime_data.db`)

## Project Structure

The project follows a standardized directory structure to improve clarity and maintainability:

```
crime-news-scraper/
├── config/             # Configuration files (settings, constants)
├── data/               # Input data and sample files
├── docs/               # Project documentation
├── evaluation/         # Evaluation scripts and data
├── logs/               # Runtime log files
├── output/             # Generated output files
│   ├── analysis_results/ # Structured analysis output
│   ├── nearby_businesses/ # Nearby business finder output
│   ├── reports/          # Generated reports and summaries
│   └── scraped_data/     # Raw scraped data
├── scripts/            # Utility and helper scripts
├── src/                # Main source code
│   ├── address_finder/ # Address finding and validation
│   ├── analyzer/       # Article analysis
│   ├── nearby_finder/  # Nearby business finder
│   ├── scrapers/       # News source scrapers
│   └── utils/          # Shared utilities
├── tests/              # Automated tests
├── .env                # Environment variables
├── requirements.txt    # Project dependencies
├── memories.md         # Agent operational memory - DO NOT MODIFY
└── tasks.md            # Agent task list - DO NOT MODIFY
```

**Important Note**: The `tasks.md` and `memories.md` files in the root directory contain critical operational information and should not be moved or modified.

For a more detailed explanation of the project structure, see [docs/STRUCTURE.md](docs/STRUCTURE.md).

## 🏗️ **System Architecture**

The system follows a modular design with five main components optimized for targeted lead generation:

### 1. **🗄️ Database Module**
   - Centralizes data storage using SQLite with optimized schema
   - Maintains relationships between articles, analysis, and nearby businesses
   - Ensures data integrity with unique constraints and foreign keys
   - Supports efficient querying for lead generation workflows
   - Handles all database connections and operations

### 2. **📰 Unified Scraper**
   - Orchestrates multi-source news collection
   - Manages individual scraper modules (JSA, DFW, etc.)
   - Stores articles in SQLite database with deduplication
   - Creates standardized data pipeline for analysis

### 3. **🔍 Modular Scrapers**
   - Source-specific scraping modules with inheritance from base class
   - Extracts crime incident data from various news sources
   - Implements intelligent parsing for different website structures
   - Outputs standardized data for downstream processing

### 4. **🧠 AI-Powered Analyzer**
   - Processes articles using Claude AI for incident analysis
   - Extracts detailed crime information with high accuracy
   - Validates and enhances address data using Perplexity API
   - Generates comprehensive incident reports with scoring
   - Stores analysis results for efficient lead generation

### 5. **🎯 Targeted Business Finder**
   - **EXCLUSIVE FOCUS**: Only searches for our three target business types
   - Uses Google Maps API with targeted keyword searches
   - Implements intelligent lead scoring (scores 3-6 based on proximity and type)
   - Generates high-quality lead lists with complete business information
   - **100% Target Filtering**: Eliminates all non-target business types

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
   - Edit your `.env` file to modify:
     - `DEFAULT_SEARCH_RADIUS`: Search radius in meters (default: 1609, which is 1 mile)
     - `MAX_RESULTS_PER_CATEGORY`: Maximum number of results per category (default: 5)
     - `GOOGLE_MAPS_RATE_LIMIT_DELAY`: Delay between API calls in seconds (default: 0.2)
   - Edit `src/nearby_finder/config.py` to modify:
     - Target business types (luxury goods, sports memorabilia, vape/smoke shops, jewelry)

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