Simplified Coding Guidelines for Cursor AI
Project Structure
Copybreak-in-marketing/
├── config/                   # Configuration files
├── src/                      # Source code
│   ├── scrapers/             # Web scraping modules
│   ├── analysis/             # Claude integration
│   ├── sheets/               # Google Sheets integration
│   ├── geo/                  # Geocoding and mapping
│   └── email/                # Email campaign integration
├── scripts/                  # Standalone scripts
└── requirements.txt          # Dependencies
General Coding Rules

Keep it simple - Prioritize working code over perfect architecture
Use Python 3.9+ with standard PEP 8 formatting
Add comments for complex logic and function docstrings
Handle errors with specific try/except blocks
Log important events (errors, key operations)

Naming Conventions

Files: lowercase with underscores (web_scraper.py)
Classes: CamelCase (NewsArticleScraper)
Functions: lowercase with underscores (get_nearby_businesses)
Variables: lowercase with underscores (business_list)

Component-Specific Guidelines
Web Scraper

Add delays between requests (1-3 seconds)
Use a proper user agent string
Implement retry logic for failed requests
Extract only the data we need (titles, content, dates)

Claude Integration

Use Anthropic's Python SDK
Set temperature to 0.0 for consistent results
Keep prompts clear and specific
Handle API errors with proper retries

Google Sheets

Use the gspread library
Create clear, structured sheet layouts
Batch updates where possible
Cache data when appropriate

Geocoding

Use Google Maps API for geocoding
Implement caching to reduce API costs
Handle invalid addresses gracefully
Calculate distances accurately

Email Integration

Follow Email Chaser's recommendations
Keep email templates short (<100 words)
Use custom variables for personalization
Start with small batches (5-10 emails/day)

Error Handling

Log all errors with appropriate context
Implement retries for network operations
Fail gracefully when services are unavailable
Preserve data when operations fail midway

Testing Approach

Test each component individually before integration
Create small test cases with known inputs/outputs
Manually verify results before scaling up
Check edge cases (empty data, rate limits, etc.)

Development Workflow

Start with manual processes to validate concepts
Implement minimal versions first, then enhance
Test with real data frequently
Scale gradually once core functions work

Security Basics

Never commit API keys to source control
Use environment variables for secrets
Validate all external inputs
Follow rate limits for external APIs