# Crime News Scraper

A modular and extensible crime news scraper that collects jewelry theft articles from multiple sources and analyzes them using Claude AI to identify security product sales opportunities.

GitHub Repository: [https://github.com/Astreocclu/crime-news-scraper](https://github.com/Astreocclu/crime-news-scraper)

## Features

- **Sales Lead Generation**: Identify jewelry businesses that recently experienced theft incidents
- **Risk Assessment Scoring**: Evaluate security vulnerabilities and priority sales targets
- **Sales Intelligence**: Generate engaging headlines and security recommendations for sales pitches
- **Business Impact Analysis**: Calculate potential impact scores to strengthen sales conversations
- **Modular Architecture**: Easily expand to new news sources for wider lead generation
- **AI-powered Analysis**: Extract actionable intelligence to drive security product sales

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

The project uses direct API keys in the test analyzer files for testing purposes. The main configuration parameters are:

### Analyzer Configuration
- `batch_size`: Number of articles to process in each batch (default: 10)
- `max_tokens`: Maximum tokens for Claude API calls (default: 4000)
- `temperature`: Temperature setting for Claude API (default: 0.7)
- `output_dir`: Directory for storing processed data (default: output)

### Sales Intelligence Features
The analyzer extracts key sales-focused data points:
- `riskAssessment`: Priority classification (SEVERE, HIGH, MODERATE, BASIC)
- `businessImpactScore`: 1-10 rating of impact severity for sales urgency
- `securityRecommendation`: Specific product recommendations based on crime type
- `businessName` and `exactAddress`: Automatically enriched target business information

## Usage

1. Run the scraper:
```bash
python src/main.py
```

2. View the results in the `output` directory

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
│   └── analyzer/          # Analysis module
│       ├── __init__.py
│       ├── analyzer.py    # Main analyzer implementation
│       └── claude_client.py # Claude API integration
├── tests/                 # Test files
├── config/               # Global configuration
├── output/              # Generated output files
├── test_data/           # Test data files
├── requirements.txt     # Project dependencies
└── .env                # Environment variables
```

## System Architecture

The system follows a modular design with three main components:

1. **Unified Scraper**
   - Acts as the main orchestrator for lead generation
   - Manages the execution of individual scraper modules
   - Handles data aggregation and storage
   - Creates standardized lead source data

2. **Modular Scrapers**
   - Each scraper module (JSA, DFW, etc.) targets specific news sources
   - Inherits from the base scraper class
   - Implements specific scraping logic to extract potential sales leads
   - Outputs standardized CSV files of potential target businesses

3. **Sales Intelligence Analyzer**
   - Processes the generated CSV files to identify sales opportunities
   - Uses Claude AI to:
     - Identify and validate business locations
     - Enhance data with business names and addresses
     - Assess security risk levels and urgency
     - Calculate business impact scores
     - Generate tailored security product recommendations
     - Prioritize leads based on multiple factors

## Sales Lead Generation Workflow

1. **Source Monitoring**: The unified scraper continuously monitors news sources for jewelry crime incidents
2. **Lead Collection**: Modular scrapers extract relevant business theft incidents
3. **Data Standardization**:
   - Fetches theft incident details from news sources
   - Processes and standardizes the data for analysis
   - Saves potential leads to CSV in the output directory
4. **Lead Qualification**:
   - Uses Claude AI to validate leads and enrich business information
   - Identifies precise business locations and contact information
   - Analyzes crime patterns and severity to determine urgency
   - Calculates business impact scores to prioritize outreach
   - Generates specific security product recommendations
   - Creates prioritized lead reports for sales teams

## Development

To add a new scraper:
1. Create a new module in `src/scrapers/`
2. Implement the base scraper interface
3. Add configuration in the module's directory
4. Update the unified scraper to include the new module

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

## Testing

- Test files are located in the `tests/`