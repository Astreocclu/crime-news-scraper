"""Test analyzer module for processing a single batch of crime articles."""

import logging
import os
import pandas as pd
from datetime import datetime
import anthropic
import json
import re
import sys

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyzer.log'),
        logging.StreamHandler(sys.stdout)  # This ensures output goes to console
    ]
)
logger = logging.getLogger(__name__)

class TestAnalyzerSingleBatch:
    """Test analyzer module for processing a single batch of crime articles."""

    def __init__(self):
        """Initialize the analyzer with API key and parameters."""
        # Direct API key for testing
        self.api_key = "your_anthropic_api_key_here"  # Replace with your API key for testing
        self.batch_size = 10
        self.max_tokens = 4000
        self.temperature = 0.7
        self.output_dir = 'output'
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _format_timestamp(self, timestamp_str):
        """Convert timestamp string to human-readable format."""
        if not timestamp_str:
            return None
        try:
            # Parse YYYYMMDD_HHMMSS format
            dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp_str

    def _parse_date(self, date_str):
        """Parse and standardize date strings."""
        # Handle None, NaN, and empty values
        if pd.isna(date_str) or date_str == '':
            return None
            
        # Convert to string if it's a number
        if isinstance(date_str, (int, float)):
            try:
                # Try to parse as timestamp
                return datetime.fromtimestamp(float(date_str)).strftime('%Y-%m-%d')
            except:
                return None
            
        # Convert to string and check for special values
        date_str = str(date_str).strip()
        if date_str.lower() in ['not specified', 'unknown', '', 'none']:
            return None

        # Common date patterns with named capture groups
        patterns = [
            r'(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
            r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})',         # YYYY-MM-DD
            r'(?P<month>\d{1,2})[-/](?P<day>\d{1,2})[-/](?P<year>\d{2,4})',  # Various separators
            r'(?P<day>\d{1,2})\s+(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?P<year>\d{2,4})',  # Month names
            r'(?P<day>\d{1,2})\s+(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+(?P<year>\d{2,4})',  # Full month names
            r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})',  # ISO format with time
            r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}).\d{3}Z',  # ISO format with milliseconds
        ]

        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
            'january': '01', 'february': '02', 'march': '03', 'april': '04', 'june': '06',
            'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }

        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    d = match.groupdict()
                    
                    # Convert month names to numbers
                    if 'month' in d and d['month'].lower() in month_map:
                        d['month'] = month_map[d['month'].lower()]
                    
                    # Handle 2-digit years
                    if 'year' in d and len(d['year']) == 2:
                        year = int(d['year'])
                        if year < 50:  # Assuming years 00-49 are 2000-2049
                            year += 2000
                        else:  # Years 50-99 are 1950-1999
                            year += 1900
                        d['year'] = str(year)
                    
                    # Create ISO format date
                    date_str = f"{d['year']}-{int(d['month']):02d}-{int(d['day']):02d}"
                    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                except:
                    continue

        # Handle relative dates
        today = datetime.now()
        relative_dates = {
            'today': 0,
            'yesterday': 1,
            'last week': 7,
            'a week ago': 7,
            'last month': 30,
            'a month ago': 30,
            'last year': 365,
            'a year ago': 365
        }

        text_lower = date_str.lower()
        for rel_date, days in relative_dates.items():
            if rel_date in text_lower:
                return (today - pd.Timedelta(days=days)).strftime('%Y-%m-%d')

        return None

    def _infer_incident_date(self, article_date, article_text):
        """Infer incident date from article text and publication date."""
        if not article_text:
            return None
            
        article_text = str(article_text).lower()
        
        # First try to find explicit date mentions
        date_patterns = [
            r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
            r'occurred\s+(?:on|during|at)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
            r'occurred\s+(?:on|during|at)\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            r'occurred\s+(?:on|during|at)\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
            r'(?:in|during)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'(?:in|during)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
        ]

        # Try each pattern
        for pattern in date_patterns:
            match = re.search(pattern, article_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date

        # If no explicit date found, try to infer from relative time indicators
        relative_indicators = {
            'yesterday': 1,
            'last week': 7,
            'a week ago': 7,
            'last month': 30,
            'a month ago': 30,
            'last year': 365,
            'a year ago': 365,
            'earlier this week': 3,
            'earlier this month': 15,
            'earlier this year': 180,
            'this morning': 0,
            'this afternoon': 0,
            'this evening': 0,
            'last night': 1
        }

        if article_date:
            try:
                article_dt = datetime.strptime(article_date, '%Y-%m-%d')
                
                # Check for relative time indicators
                for indicator, days in relative_indicators.items():
                    if indicator in article_text:
                        return (article_dt - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
                        
                # If the article mentions specific days of the week
                days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                for i, day in enumerate(days_of_week):
                    if day in article_text:
                        article_dow = article_dt.weekday()
                        mentioned_dow = i
                        days_diff = (article_dow - mentioned_dow) % 7
                        if days_diff == 0:
                            days_diff = 7  # Assume it was last week if same day
                        return (article_dt - pd.Timedelta(days=days_diff)).strftime('%Y-%m-%d')

            except Exception as e:
                logger.warning(f"Error inferring date from relative indicators: {str(e)}")

        return None

    def _create_analysis_prompt(self, article):
        """Create a prompt for analyzing a single article."""
        # Handle keywords as a comma-separated string
        keywords = article.get('keywords', '')
        keywords_str = keywords if keywords else 'None'

        # Get scraping timestamp from filename
        scraping_timestamp = None
        if hasattr(article, 'scraping_timestamp'):
            scraping_timestamp = article.scraping_timestamp

        # Extract date from excerpt if available
        excerpt = article.get('excerpt', '')
        date_from_excerpt = None
        if excerpt:
            # Look for dates in common formats
            date_patterns = [
                r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
                r'(?:on|during|at)\s+(?:the\s+)?(?:night|morning|afternoon|evening|weekend)\s+of\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                r'occurred\s+(?:on|during|at)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                r'occurred\s+(?:on|during|at)\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
                r'occurred\s+(?:on|during|at)\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                r'(?:in|during)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
                r'(?:in|during)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
                r'(?:published|posted|written)\s+(?:on|at)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                r'(?:published|posted|written)\s+(?:on|at)\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
                r'(?:published|posted|written)\s+(?:on|at)\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})',
                r'(\d{1,2}/\d{1,2}/\d{2,4})',  # Fallback for any date in MM/DD/YYYY format
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',  # Fallback for any date with month name
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, excerpt, re.IGNORECASE)
                if match:
                    date_from_excerpt = match.group(1)
                    break

        prompt = f"""
        Please analyze this crime article and extract key information:

        Title: {article.get('title', '')}
        Location: {article.get('location', '')}
        Date from excerpt: {date_from_excerpt if date_from_excerpt else 'Not found'}
        Scraping Date: {scraping_timestamp if scraping_timestamp else 'Not available'}
        Keywords: {keywords_str}
        Excerpt: {excerpt}
        Source: {article.get('source', '')}
        Is Theft Related: {article.get('is_theft_related', '')}
        Is Business Related: {article.get('is_business_related', '')}

        Please provide:
        1. Type of crime (e.g., robbery, burglary, theft)
        2. Method used (e.g., smash and grab, armed robbery)
        3. Target (e.g., jewelry store, individual)
        4. Store type (e.g., retail jewelry store, pawn shop, luxury boutique)
        5. Business name of the victimized store
        6. Detailed location information (address, city, state, landmarks)
        7. Estimated value of items (if mentioned)
        8. Number of suspects involved
        9. Any unique characteristics or patterns
        10. Date of the incident (if mentioned in the article or can be inferred)
        11. Date of article (when the article was published)
        12. A brief summary of the incident
        13. Lead quality score (1-10) based on:
            - Value score (1-5): Higher for more valuable items
            - Recency score (1-5): Higher for more recent incidents
        14. Method of entry used by criminals

        For dates:
        - For the article date (dateOfArticle):
          - Look for explicit publication dates in the article text
          - Look for phrases like "published on", "posted on", "written on"
          - Look for dates in the article URL or metadata
          - If no publication date is found, use the scraping date
          - Format dates as YYYY-MM-DD when possible
          - If no date can be determined with confidence, use "Not available"

        - For the incident date (incidentDate):
          - Look for explicit dates mentioned in relation to the crime
          - Look for phrases indicating when the crime occurred
          - If relative dates are mentioned (e.g., "yesterday", "last week"), calculate based on the article date
          - Format dates as YYYY-MM-DD when possible
          - If only a partial date is known (e.g., only month and year), include that
          - If no date can be determined, use "Not available"

        Format the response as a JSON object with these fields:
        {{
            "crimeType": "type of crime",
            "method": "method used",
            "target": "target of the crime",
            "storeType": "type of store",
            "businessName": "name of the business",
            "detailedLocation": "detailed location information",
            "estimatedValue": "estimated value",
            "numSuspects": "number of suspects",
            "characteristics": "unique characteristics",
            "incidentDate": "date of the incident",
            "dateOfArticle": "when the article was published",
            "summary": "brief summary of the incident",
            "valueScore": "score from 1-5 based on value",
            "recencyScore": "score from 1-5 based on recency",
            "totalScore": "total score from 1-10",
            "entryMethod": "method used to enter premises"
        }}
        """
        return prompt

    def _extract_analysis(self, response_content):
        """Extract the JSON analysis from the Claude response."""
        try:
            # Extract the text content from TextBlock
            text_content = response_content[0].text if isinstance(response_content, list) else response_content
            logger.info(f"Response text: {text_content}")
            
            # Find the JSON object in the text using a more robust method
            json_matches = re.findall(r'\{[^{}]*\}', text_content)
            if json_matches:
                # Try each match until we find a valid JSON
                for json_str in json_matches:
                    try:
                        result = json.loads(json_str)
                        logger.info(f"Successfully parsed JSON: {json_str}")
                        return result
                    except json.JSONDecodeError:
                        continue
                        
            logger.error(f"No valid JSON object found in response: {text_content}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            logger.error(f"Response content: {response_content}")
        return None

    def _create_article_summary(self, article, analysis):
        """Create a brief summary for a single article."""
        # Parse and standardize dates
        incident_date = self._parse_date(analysis.get('incidentDate', ''))
        article_date = self._parse_date(article.get('date', ''))
        scraping_date = self._format_timestamp(article.get('scraping_timestamp', ''))
        
        # Build the summary with all available information
        summary = f"""
Article: {article.get('title', '')}
Location: {article.get('location', '')}
Detailed Location: {analysis.get('detailedLocation', 'Not specified')}
Business Name: {analysis.get('businessName', 'Not specified')}
Store Type: {analysis.get('storeType', 'Not specified')}
Date of Article: {article_date if article_date else 'Not specified'}
Scraping Date: {scraping_date if scraping_date else 'Not available'}
Incident Date: {incident_date if incident_date else 'Not specified'}
Crime Type: {analysis.get('crime_type', 'Unknown')}
Method: {analysis.get('method', 'Unknown')}
Entry Method: {analysis.get('entryMethod', 'Not specified')}
Target: {analysis.get('target', 'Unknown')}
Estimated Value: {analysis.get('estimated_value', 'Not specified')}
Number of Suspects: {analysis.get('num_suspects', 'Not specified')}
Key Details: {analysis.get('characteristics', 'No additional details available')}
Summary: {analysis.get('summary', 'No summary available')}
Lead Quality Score: {analysis.get('totalScore', 'Not scored')} (Value: {analysis.get('valueScore', 'N/A')}, Recency: {analysis.get('recencyScore', 'N/A')})
URL: {article.get('url', '')}
"""
        return summary

    def _generate_summary(self, results):
        """Generate a summary of the analysis results."""
        df = pd.DataFrame(results)
        
        # Count crime types
        crime_types = df['crime_type'].value_counts()
        
        # Count methods
        methods = df['method'].value_counts()
        
        # Count targets
        targets = df['target'].value_counts()
        
        # Calculate total estimated value (converting string values to numbers where possible)
        def extract_value(value):
            if pd.isna(value) or value == '':
                return 0
            try:
                # Convert to string first to handle both string and numeric inputs
                value_str = str(value).lower().strip()
                if 'million' in value_str:
                    return float(value_str.split()[0]) * 1000000
                elif 'k' in value_str:
                    return float(value_str.split()[0]) * 1000
                elif '$' in value_str:
                    # Remove $ and commas, then convert to float
                    return float(value_str.replace('$', '').replace(',', ''))
                elif isinstance(value, (int, float)):
                    return float(value)
                return 0
            except Exception as e:
                logger.warning(f"Could not parse value '{value}': {str(e)}")
                return 0
        
        total_value = sum(df['estimated_value'].apply(extract_value))
        
        # Count locations
        locations = df['location'].value_counts()
        
        # Parse and sort by incident date
        df['parsed_incident_date'] = df['incident_date'].apply(self._parse_date)
        df = df.sort_values('parsed_incident_date', ascending=False)
        
        summary = f"""
Analysis Summary:
---------------
Total Incidents: {len(df)}
Total Estimated Value: ${total_value:,.2f}

Crime Types:
{crime_types.to_string() if not crime_types.empty else 'None found'}

Methods Used:
{methods.to_string() if not methods.empty else 'None found'}

Targets:
{targets.to_string() if not targets.empty else 'None found'}

Locations:
{locations.to_string() if not locations.empty else 'None found'}

Key Patterns:"""

        # Only add pattern information if we have data
        if not crime_types.empty:
            summary += f"\n- Most common crime type: {crime_types.index[0]} ({crime_types.iloc[0]} incidents)"
        if not methods.empty:
            summary += f"\n- Most common method: {methods.index[0]} ({methods.iloc[0]} incidents)"
        if not targets.empty:
            summary += f"\n- Most common target: {targets.index[0]} ({targets.iloc[0]} incidents)"
        if not locations.empty:
            summary += f"\n- Most affected location: {locations.index[0]} ({locations.iloc[0]} incidents)"

        summary += "\n\nIndividual Article Summaries (Sorted by Incident Date):\n--------------------------------------------------\n"
        
        # Add individual article summaries
        for idx, row in df.iterrows():
            summary += self._create_article_summary(row, row.to_dict())
            summary += "\n"

        return summary

    def process_single_batch(self, input_file):
        """Process a single batch of articles."""
        try:
            # Read the input CSV file
            df = pd.read_csv(input_file)
            logger.info(f"Found {len(df)} articles in {input_file}")

            # Process articles in smaller batches
            batch_results = []
            num_batches = 2  # Process 2 batches
            self.batch_size = 5  # Reduce batch size to 5 articles
            
            for batch_num in range(num_batches):
                start_idx = batch_num * self.batch_size
                end_idx = start_idx + self.batch_size
                batch_df = df.iloc[start_idx:end_idx].copy()
                
                if batch_df.empty:
                    logger.info(f"No more articles to process in batch {batch_num + 1}")
                    break
                
                logger.info(f"\nProcessing batch {batch_num + 1} ({len(batch_df)} articles)")
                
                for idx, article in batch_df.iterrows():
                    try:
                        logger.info(f"\nAnalyzing article {idx + 1}: {article['title']}")
                        logger.info(f"Location: {article['location']}")
                        logger.info(f"URL: {article['url']}")
                        
                        # Create the analysis prompt
                        prompt = self._create_analysis_prompt(article)
                        
                        # Get analysis from Claude with timeout
                        try:
                            response = self.client.messages.create(
                                model="claude-3-sonnet-20240229",
                                max_tokens=self.max_tokens,
                                temperature=self.temperature,
                                messages=[{"role": "user", "content": prompt}],
                                timeout=30  # 30 second timeout
                            )
                        except Exception as e:
                            logger.error(f"API call failed for article {idx + 1}: {str(e)}")
                            continue
                        
                        # Extract and process the analysis
                        analysis = self._extract_analysis(response.content[0].text)
                        if analysis:
                            # Create article summary
                            summary = self._create_article_summary(article, analysis)
                            batch_results.append(summary)
                            logger.info(f"Analysis completed successfully")
                            logger.info(f"Analysis results: {json.dumps(analysis, indent=2)}")
                        else:
                            logger.warning(f"Failed to extract analysis for article {idx + 1}")
                            
                    except Exception as e:
                        logger.error(f"Error processing article {idx + 1}: {str(e)}")
                        continue
                
                logger.info(f"\nCompleted batch {batch_num + 1}")
                
                # Save intermediate results after each batch
                if batch_results:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_file = os.path.join(self.output_dir, f'analysis_results_{timestamp}.csv')
                    results_df = pd.DataFrame(batch_results)
                    results_df.to_csv(output_file, index=False)
                    logger.info(f"\nIntermediate results saved to {output_file}")
            
            if batch_results:
                # Generate final summary
                summary = self._generate_summary(batch_results)
                logger.info("\nAnalysis Summary:")
                logger.info(json.dumps(summary, indent=2))
                
            return True
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            return False

def main():
    """Main entry point for the analyzer."""
    # Get the input file path from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python -m src.analyzer.test_analyzer_single_batch <input_csv_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Initialize and run the analyzer
    analyzer = TestAnalyzerSingleBatch()
    analyzer.process_single_batch(input_file)

if __name__ == "__main__":
    main() 