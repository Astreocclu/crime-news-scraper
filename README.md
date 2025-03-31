# Crime News Scraper

A modular and extensible crime news scraper that collects articles from multiple sources and analyzes them using Claude AI.

GitHub Repository: [https://github.com/Astreocclu/crime-news-scraper](https://github.com/Astreocclu/crime-news-scraper)

## Features

- Modular architecture for easy addition of new news sources
- Unified data format across all sources
- AI-powered analysis of crime articles
- Configurable batch processing
- Detailed logging and error handling

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
   - Acts as the main orchestrator
   - Manages the execution of individual scraper modules
   - Handles data aggregation and storage

2. **Modular Scrapers**
   - Each scraper module (JSA, DFW, etc.) is self-contained
   - Inherits from the base scraper class
   - Implements specific scraping logic for its target source
   - Outputs standardized CSV files

3. **Analyzer**
   - Processes the generated CSV files
   - Uses Claude AI to:
     - Identify and validate locations
     - Assess article quality
     - Categorize incidents
     - Extract relevant keywords
     - Analyze crime severity and recency
     - Identify stores for security improvements (steel mesh recommendations)

## Workflow

1. The unified scraper is initiated
2. Based on configuration, it calls the appropriate modular scraper(s)
3. Each modular scraper:
   - Fetches data from its source
   - Processes and standardizes the data
   - Saves results to CSV in the output directory
4. The analyzer processes the new CSV files:
   - Uses Claude AI to validate and enrich the data
   - Identifies locations and incident types
   - Analyzes crime patterns and severity
   - Generates security recommendations
   - Creates analysis reports

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