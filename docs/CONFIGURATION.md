# Crime News Scraper - Configuration Guide

This document provides comprehensive configuration instructions for the Crime News Scraper system.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [API Configuration](#api-configuration)
3. [Database Configuration](#database-configuration)
4. [Scraper Configuration](#scraper-configuration)
5. [Analyzer Configuration](#analyzer-configuration)
6. [Nearby Finder Configuration](#nearby-finder-configuration)
7. [Performance Tuning](#performance-tuning)

## Environment Variables

### Setting Up Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your specific configuration:
```bash
nano .env
```

### Required Environment Variables

```bash
# API Keys (Required)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Optional API Keys
NEWSAPI_KEY=your_newsapi_key_here
```

### Database Configuration

```bash
# Database Settings
DATABASE_PATH=crime_data.db
```

### Directory Configuration

```bash
# Output Directories
OUTPUT_DIR=output
LOGS_DIR=logs

# Subdirectories (automatically created)
SCRAPING_OUTPUT_DIR=output/scraping
ANALYSIS_OUTPUT_DIR=output/analysis
NEARBY_OUTPUT_DIR=output/nearby
```

### Processing Configuration

```bash
# Scraper Settings
SCRAPE_DEEP_CHECK=false
MAX_ARTICLES_PER_SOURCE=100

# Analyzer Settings
DEFAULT_BATCH_SIZE=10
CLAUDE_MODEL=claude-3-7-sonnet-20250219
MAX_TOKENS=4000
TEMPERATURE=0.7

# Nearby Finder Settings
DEFAULT_SEARCH_RADIUS=1609
MAX_RESULTS_PER_CATEGORY=5
GOOGLE_MAPS_RATE_LIMIT_DELAY=0.2
```

## API Configuration

### Anthropic Claude AI

1. **Get API Key:**
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create an account and generate an API key
   - Add to `.env` file: `ANTHROPIC_API_KEY=your_key_here`

2. **Model Configuration:**
```bash
CLAUDE_MODEL=claude-3-7-sonnet-20250219
MAX_TOKENS=4000
TEMPERATURE=0.7
```

3. **Usage Limits:**
   - Monitor usage in Anthropic Console
   - Set appropriate batch sizes to manage costs
   - Default batch size: 10 articles per request

### Google Maps API

1. **Setup Google Cloud Project:**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable the following APIs:
     - Places API
     - Geocoding API
     - Maps JavaScript API

2. **Generate API Key:**
   - Go to "Credentials" in Google Cloud Console
   - Create API Key
   - Restrict key to your specific APIs
   - Add to `.env` file: `GOOGLE_MAPS_API_KEY=your_key_here`

3. **API Restrictions (Recommended):**
   - Restrict by IP address for production
   - Restrict to specific APIs only
   - Set usage quotas to prevent overuse

### Perplexity API

1. **Get API Key:**
   - Visit [Perplexity AI](https://www.perplexity.ai/)
   - Create account and generate API key
   - Add to `.env` file: `PERPLEXITY_API_KEY=your_key_here`

2. **Usage Configuration:**
   - Used for address validation and enhancement
   - Fallback option for address resolution
   - Rate limits apply

## Database Configuration

### SQLite Database

```bash
# Database file location
DATABASE_PATH=crime_data.db
```

### Database Schema

The system automatically creates three main tables:

1. **articles**: Raw scraped news articles
2. **analysis_results**: AI-analyzed crime incident data
3. **nearby_businesses**: Target businesses with lead scoring

### Database Maintenance

```bash
# Initialize database
python -c "from src.database import initialize_database; initialize_database()"

# Check database size
ls -lh crime_data.db

# Backup database
cp crime_data.db backup_$(date +%Y%m%d).db
```

## Scraper Configuration

### General Scraper Settings

```bash
# Enable/disable deep content validation
SCRAPE_DEEP_CHECK=false

# Maximum articles per source per run
MAX_ARTICLES_PER_SOURCE=100

# Selenium WebDriver settings
WEBDRIVER_TIMEOUT=30
WEBDRIVER_IMPLICIT_WAIT=10
```

### Source-Specific Configuration

Edit `src/scrapers/[source]/config.py` for source-specific settings:

```python
# Example: JSA scraper configuration
BASE_URL = "https://www.jewelerssecurity.org"
MAX_PAGES = 5
ARTICLE_SELECTOR = ".article-item"
```

## Analyzer Configuration

### Claude AI Settings

```bash
# Model selection
CLAUDE_MODEL=claude-3-7-sonnet-20250219

# Token limits
MAX_TOKENS=4000

# Creativity setting (0.0-1.0)
TEMPERATURE=0.7

# Processing batch size
DEFAULT_BATCH_SIZE=10
```

### Analysis Output Format

The analyzer generates comprehensive incident reports with:
- Crime type and method analysis
- Business impact scoring (1-10)
- Address validation and confidence scores
- Security recommendations
- Lead prioritization data

## Nearby Finder Configuration

### Target Business Types (Exclusive Focus)

The system is configured to find ONLY these three business types:

```python
TARGET_BUSINESS_TYPES = [
    "jewelry_store",           # Primary target
    "luxury_goods_store",      # Secondary target  
    "sports_memorabilia_store" # Secondary target
]
```

### Search Parameters

```bash
# Search radius in meters (1609 = 1 mile)
DEFAULT_SEARCH_RADIUS=1609

# Maximum results per business category
MAX_RESULTS_PER_CATEGORY=5

# API rate limiting (seconds between calls)
GOOGLE_MAPS_RATE_LIMIT_DELAY=0.2
```

### Lead Scoring Configuration

The system uses intelligent lead scoring:

- **Distance-based scoring:**
  - Within 0.25 miles: +2 points
  - Within 1.0 mile: +1 point
  - Beyond 1 mile: Filtered out

- **Business type scoring:**
  - All target types: +3 points
  - Non-target types: Filtered out (score = 0)

**Result:** Score range 3-6, with 62.2% high-quality leads (score ≥5)

## Performance Tuning

### Processing Optimization

```bash
# Batch size optimization
DEFAULT_BATCH_SIZE=10          # Start with 10
# Increase to 20-50 for faster processing
# Decrease to 5 if hitting API limits

# Memory management
MAX_ARTICLES_PER_SOURCE=100    # Limit per source
```

### API Rate Limiting

```bash
# Google Maps API
GOOGLE_MAPS_RATE_LIMIT_DELAY=0.2  # 200ms between calls

# Claude AI - built-in rate limiting
# Perplexity API - built-in rate limiting
```

### Database Performance

```bash
# Enable WAL mode for better concurrency
# Automatically configured in database.py

# Regular maintenance
PRAGMA optimize;
VACUUM;
```

### Monitoring and Logging

```bash
# Log levels
LOG_LEVEL=INFO

# Log file rotation
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Performance monitoring
ENABLE_PERFORMANCE_LOGGING=true
```

## Security Configuration

### API Key Security

1. **Never commit `.env` file to version control**
2. **Use environment-specific keys**
3. **Rotate keys regularly**
4. **Monitor API usage for anomalies**

### Database Security

1. **Regular backups**
2. **File permissions (600)**
3. **Encryption at rest (if required)**

### Network Security

1. **Use HTTPS for all API calls**
2. **Implement proper error handling**
3. **Log security events**

## Troubleshooting

### Common Configuration Issues

1. **Missing API Keys:**
   - Check `.env` file exists and has correct keys
   - Verify API keys are valid and active

2. **Database Connection Errors:**
   - Check file permissions on database file
   - Ensure directory exists and is writable

3. **API Rate Limiting:**
   - Increase delay between API calls
   - Reduce batch sizes
   - Monitor API quotas

4. **Performance Issues:**
   - Optimize batch sizes
   - Check available memory
   - Monitor API response times

For additional support, see the troubleshooting section in the deployment guide.
