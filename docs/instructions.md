How to Run the Crime News Scraper
This file provides instructions for running the crime news scraper project.

Prerequisites
Python: Ensure you have Python 3.8 or later installed.
Clone Repository: If you haven't already, clone the project repository:
```bash
git clone https://github.com/Astreocclu/crime-news-scraper.git
cd crime-news-scraper
```
Install Dependencies: Install the required Python packages:
```bash
pip install -r requirements.txt
```
Environment Variables: Create a file named .env in the project's root directory (crime-news-scraper/). Copy the contents of .env.example (if it exists) or add the following lines, replacing the placeholder values with your actual keys:
```
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
Maps_API_KEY=your_Maps_api_key_here

# Database Configuration (Optional, defaults to crime_data.db)
# DATABASE_PATH=crime_data.db
```

Running the Workflow
There are several ways to run the scraper:

1. Full Workflow (Recommended)
This script handles scraping, analysis, and finding nearby businesses automatically.

```bash
python scripts/workflow.py
```

- Logs are saved to logs/workflow.log.
- You can skip steps using flags like --no-scrape, --no-analyze, --no-nearby.

2. Scrape and Analyze (Main Script)
Run the main scraper and analyzer. By default, it uses CSV files for storage.

```bash
python src/main.py
```

To use the SQLite database instead of CSV files:
```bash
python src/main.py --use-database
```
- Output files are saved in the output/ directory with subdirectories for different types of data.
- Logs are saved to application.log.

3. Run Only Nearby Business Finder
If you have already run the analysis and have an analyzed leads file (e.g., output/analyzed/analyzed_leads_*.csv), you can run the nearby finder separately:

```bash
python src/nearby_finder/finder.py --input-file path/to/your/analyzed_leads.csv
```

- Output is saved to output/nearby_businesses/nearby_businesses_*.csv.

Configuration Options
- Batch Size: Control how many articles are analyzed at once using --batch-size with src/main.py (e.g., python src/main.py --batch-size 20).
- Input File: Analyze a specific CSV file instead of scraping using --input-file with src/main.py (e.g., python src/main.py --no-scrape --input-file path/to/data.csv).

Refer to the README.md for more detailed information on configuration, architecture, and development.
