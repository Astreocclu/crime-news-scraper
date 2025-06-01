# Crime News Scraper - Quick Start Guide

This guide will help you get started with the Crime News Scraper quickly.

## Prerequisites

- Python 3.8+
- Chrome browser (for Selenium)
- Anthropic API key (for Claude AI)
- Google Maps API key (for nearby business finder)

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

3. Set up configuration:
```bash
cp .env.example .env
```

4. Edit the `.env` file to set your API keys and other configuration values:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
```

## Basic Usage

### Running the Complete Workflow

To run the complete workflow (scrape, analyze, nearby, complete):

```bash
python scripts/workflow.py
```

This will:
1. Scrape crime news articles from configured sources
2. Analyze the articles to identify victim businesses
3. Find nearby businesses in target industries
4. Generate a CSV with qualified leads

### Running Individual Components

#### Scraper

To run only the scraper:

```bash
python scripts/scrape.py
```

Options:
- `--sources SRC1,SRC2`: Comma-separated list of sources to scrape (default: all)
- `--use-database`: Use database for storage instead of CSV files

#### Analyzer

To run only the analyzer:

```bash
python scripts/analyze.py
```

Options:
- `--input-file FILE`: Specify an input CSV file for analysis
- `--batch-size SIZE`: Number of articles to process in one batch (default: 10)
- `--no-scrape`: Skip the scraping step
- `--use-database`: Use database for storage instead of CSV files

#### Nearby Business Finder

To run only the nearby business finder:

```bash
python scripts/nearby.py --analysis-file FILE
```

Options:
- `--analysis-file FILE`: Analysis file containing incidents (required)
- `--radius METERS`: Search radius in meters (default: 1609)

## Advanced Options

### Database vs. CSV Storage

By default, the system uses CSV files for storage. To use the SQLite database instead:

```bash
python scripts/workflow.py --use-database
```

### Maximum Runtime

To limit the maximum runtime of the workflow:

```bash
python scripts/workflow.py --max-runtime 10  # 10 minutes
```

### Progress Indicators

To change the type of progress indicator:

```bash
python scripts/workflow.py --progress-type spinner  # Options: spinner, dots, bar
```

### Skipping Steps

To skip specific steps in the workflow:

```bash
python scripts/workflow.py --no-scrape --no-nearby
```

## Output Files

The system generates output files in the following directories:

- `output/scraped_data/`: Original scraped data (files named like `YYYYMMDD-SourceArticles.csv`)
- `output/analysis_results/`: Analyzed business data (files named like `YYYYMMDD-AnalyzedLeads.csv`)
- `output/nearby_businesses/`: Nearby business data (files named like `YYYYMMDD-NearbyBusinesses.csv`)
- `output/reports/`: Generated reports and summaries (files named like `YYYYMMDD-ReportType.ext`)

## Database

The system uses a SQLite database (`crime_data.db`) to store articles and analysis results. You can query this database directly using SQL.

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your API keys are correctly set in the `.env` file.
2. **No Articles Found**: Check the scraper configuration and ensure the sources are available.
3. **Analysis Fails**: Verify that the Claude API key is valid and has sufficient quota.
4. **Nearby Finder Fails**: Ensure the Google Maps API key is valid and has the Places API enabled.

### Logs

Check the log files in the `logs/` directory for detailed error messages:

- `logs/application.log`: Main application log
- `logs/analyzer.log`: Analyzer log
- `logs/web_search.log`: Web search log

## Next Steps

- Explore the [README.md](../README.md) for more detailed information
- Check the [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Review the [System Architecture](../README.md#system-architecture) to understand the components
