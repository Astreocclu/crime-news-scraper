"""Test analyzer module for processing a single batch of crime articles."""

import logging
import os
import pandas as pd
from datetime import datetime
import anthropic
from anthropic import Anthropic  # Explicit import of the Anthropic class
import json
import re
import sys
import requests
from urllib.parse import quote_plus
from ..database import get_db_connection
from ..utils.address_extractor import extract_address_from_article, normalize_address
from ..perplexity_client import PerplexityClient

def web_search(query, num_results=5):
    """Use the web-search tool provided by the environment."""
    try:
        # Try to import from web_search module
        try:
            from web_search import web_search as augment_web_search
            logger.info(f"Using web-search from web_search module")
            return augment_web_search(query=query, num_results=num_results)
        except ImportError:
            pass

        # Try to import from the current environment
        try:
            import web_search as ws_module
            logger.info(f"Using web-search from web_search module")
            return ws_module.web_search(query=query, num_results=num_results)
        except ImportError:
            pass

        # Check if web_search is available in the global namespace (but not this function)
        import inspect
        frame = inspect.currentframe()
        try:
            # Get the caller's globals to avoid self-reference
            caller_globals = frame.f_back.f_globals if frame.f_back else globals()
            if 'web_search' in caller_globals and caller_globals['web_search'] is not web_search:
                logger.info(f"Using web-search from caller's global scope")
                return caller_globals['web_search'](query=query, num_results=num_results)
        finally:
            del frame

        # If no web search is available, log and return empty results
        logger.warning(f"Web search not available in environment, returning empty results")
        return "No web search results available - web search tool not found in environment"

    except Exception as e:
        logger.error(f"Error using web-search tool: {str(e)}")
        return f"Web search error: {str(e)}"

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

class SingleBatchAnalyzer:
    """Test analyzer module for processing a single batch of crime articles."""

    def __init__(self):
        """Initialize the analyzer with API key and parameters."""
        # Import the get_api_key function from claude_client
        from .claude_client import get_api_key

        self.api_key = get_api_key()  # This will load from .env and validate
        self.batch_size = 10
        self.max_tokens = 4000
        self.temperature = 0.7
        self.output_dir = 'output'
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Initialize the Perplexity client for address confirmation
        self.perplexity_client = PerplexityClient()

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

    def _enhance_business_info(self, analysis, article=None):
        """
        Enhance business information by guessing business names and finding addresses.
        Uses web search and inference when direct information is not available.

        Parameters:
        -----------
        analysis : dict
            The analysis dictionary from Claude
        article : dict, optional
            The original article data, used for address extraction

        Returns:
        --------
        dict
            Updated analysis with enhanced business information
        """
        # First try to extract address directly from the article if available
        if article:
            analysis = self._extract_address_from_article(article, analysis)

        # Skip if business name is already specified and not generic
        if (analysis.get('businessName') and
            analysis['businessName'] not in ['Not specified', 'Not mentioned', 'not specified in the excerpt']):
            analysis = self._find_business_address(analysis)
            # If we still have low confidence or unknown address, try web search
            if self._should_perform_web_search(analysis):
                analysis = self._enhance_with_web_search(analysis, article)
            return analysis

        # Extract location info for search
        location = analysis.get('detailedLocation', '')
        store_type = analysis.get('storeType', '')

        # Skip if we don't have enough information
        if not location or not store_type or store_type in ['Not specified', 'Not mentioned']:
            return analysis

        # Construct search query
        query = f"{store_type} in {location}"
        logger.info(f"Searching for business information with query: {query}")

        try:
            # Use Claude to infer the likely business name and address
            prompt = f"""
            Based on the following information about a jewelry crime incident, please infer the most likely jewelry business that was targeted.
            Then find its full address. Provide your best inference, but clearly indicate when you are making an educated guess.

            Crime location: {location}
            Store type: {store_type}
            Crime type: {analysis.get('crimeType', '')}
            Date of incident: {analysis.get('incidentDate', '')}
            Other relevant details: {analysis.get('summary', '')}

            Format your response as a JSON object with these fields:
            {{
                "inferredBusinessName": "the most likely business name",
                "confidence": "high|medium|low",
                "inferredAddress": "full address with street, city, state, zip",
                "addressConfidence": "high|medium|low",
                "reasoning": "brief explanation of your reasoning"
            }}
            """

            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                temperature=0.2,  # Use low temperature for more factual responses
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )

            # Parse the response
            result_text = response.content[0].text
            # Extract JSON from the response
            json_match = re.search(r'```json\s*({.*?})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                json_match = re.search(r'{.*}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)

            try:
                business_info = json.loads(result_text)

                # Update the analysis with the enhanced information
                if business_info.get('inferredBusinessName'):
                    analysis['businessName'] = business_info['inferredBusinessName']
                    analysis['businessNameConfidence'] = business_info.get('confidence', 'low')

                if business_info.get('inferredAddress'):
                    # Normalize address format
                    raw_address = business_info['inferredAddress']
                    normalized_address = self._normalize_address(raw_address)
                    analysis['exactAddress'] = normalized_address
                    analysis['addressConfidence'] = business_info.get('addressConfidence', 'low')
                    analysis['addressSource'] = 'inferred_from_analysis'

                analysis['businessInferenceReasoning'] = business_info.get('reasoning', '')

                logger.info(f"Enhanced business info: {business_info}")

            except json.JSONDecodeError:
                logger.warning(f"Could not parse business info response: {result_text}")

        except Exception as e:
            logger.error(f"Error enhancing business information: {str(e)}")

        # If we still have low confidence or unknown address, try web search
        if self._should_perform_web_search(analysis):
            analysis = self._enhance_with_web_search(analysis, article)

        return analysis

    def _normalize_location(self, location):
        """
        Normalize location string for better search results.

        Parameters:
        -----------
        location : str
            The location string to normalize

        Returns:
        --------
        str
            The normalized location string
        """
        if not location or location.lower() in ['unknown', 'not specified', 'not mentioned', 'not available', 'other']:
            return location

        # Convert to lowercase
        normalized = location.lower()

        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Standardize state abbreviations
        state_patterns = [
            (r'\balabama\b', 'AL'),
            (r'\balaska\b', 'AK'),
            (r'\barizona\b', 'AZ'),
            (r'\barkansas\b', 'AR'),
            (r'\bcalifornia\b', 'CA'),
            (r'\bcolorado\b', 'CO'),
            (r'\bconnecticut\b', 'CT'),
            (r'\bdelaware\b', 'DE'),
            (r'\bflorida\b', 'FL'),
            (r'\bgeorgia\b', 'GA'),
            (r'\bhawaii\b', 'HI'),
            (r'\bidaho\b', 'ID'),
            (r'\billinois\b', 'IL'),
            (r'\bindiana\b', 'IN'),
            (r'\biowa\b', 'IA'),
            (r'\bkansas\b', 'KS'),
            (r'\bkentucky\b', 'KY'),
            (r'\blouisiana\b', 'LA'),
            (r'\bmaine\b', 'ME'),
            (r'\bmaryland\b', 'MD'),
            (r'\bmassachusetts\b', 'MA'),
            (r'\bmichigan\b', 'MI'),
            (r'\bminnesota\b', 'MN'),
            (r'\bmississippi\b', 'MS'),
            (r'\bmissouri\b', 'MO'),
            (r'\bmontana\b', 'MT'),
            (r'\bnebraska\b', 'NE'),
            (r'\bnevada\b', 'NV'),
            (r'\bnew hampshire\b', 'NH'),
            (r'\bnew jersey\b', 'NJ'),
            (r'\bnew mexico\b', 'NM'),
            (r'\bnew york\b', 'NY'),
            (r'\bnorth carolina\b', 'NC'),
            (r'\bnorth dakota\b', 'ND'),
            (r'\bohio\b', 'OH'),
            (r'\boklahoma\b', 'OK'),
            (r'\boregon\b', 'OR'),
            (r'\bpennsylvania\b', 'PA'),
            (r'\brhode island\b', 'RI'),
            (r'\bsouth carolina\b', 'SC'),
            (r'\bsouth dakota\b', 'SD'),
            (r'\btennessee\b', 'TN'),
            (r'\btexas\b', 'TX'),
            (r'\butah\b', 'UT'),
            (r'\bvermont\b', 'VT'),
            (r'\bvirginia\b', 'VA'),
            (r'\bwashington\b', 'WA'),
            (r'\bwest virginia\b', 'WV'),
            (r'\bwisconsin\b', 'WI'),
            (r'\bwyoming\b', 'WY'),
            (r'\bdistrict of columbia\b', 'DC')
        ]

        for pattern, abbrev in state_patterns:
            normalized = re.sub(pattern, abbrev, normalized)

        return normalized

    def _extract_city_state(self, location):
        """
        Extract city and state from location string.

        Parameters:
        -----------
        location : str
            The location string to extract from

        Returns:
        --------
        tuple
            (city, state) tuple, or (None, None) if extraction fails
        """
        if not location or location.lower() in ['unknown', 'not specified', 'not mentioned', 'not available', 'other']:
            return None, None

        # Try to match city, state pattern
        match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})', location)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            return city, state

        # Try to match city and state without comma
        match = re.search(r'([A-Za-z\s]+)\s+([A-Z]{2})\b', location)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            return city, state

        return None, None

    def _should_perform_web_search(self, analysis):
        """
        Determine if web search should be performed based on trigger conditions.

        Web search is triggered when the address is unknown, missing, or has low confidence.
        This helps improve the quality of address information for crime incidents at jewelry stores.

        Parameters:
        -----------
        analysis : dict
            The analysis dictionary containing address information

        Returns:
        --------
        bool
            True if web search should be performed, False otherwise
        """
        # Check if address is missing or unknown
        address = analysis.get('exactAddress', '')
        if not address or address.lower() in ['unknown', 'unable to determine', 'not specified', 'not available']:
            logger.info("Triggering web search due to missing or unknown address")
            return True

        # Check if address confidence is low
        confidence = analysis.get('addressConfidence', 'low')
        if confidence == 'low':
            logger.info("Triggering web search due to low address confidence")
            return True

        return False

    def _parse_and_validate_address_from_search(self, web_search_results, analysis):
        """
        Parse and validate addresses from web search results.

        Parameters:
        -----------
        web_search_results : str
            The web search results in markdown format
        analysis : dict
            The analysis dictionary for context

        Returns:
        --------
        dict or None
            The best validated address with metadata, or None if no valid address found
        """
        if not web_search_results:
            logger.warning("No web search results to parse")
            return None

        # Extract potential addresses from search results
        logger.info("Extracting addresses from web search results")
        addresses = self._extract_addresses_from_search_results(web_search_results, analysis)

        if not addresses:
            logger.warning("No addresses found in web search results")
            return None

        logger.info(f"Found {len(addresses)} potential addresses in web search results")
        for i, addr in enumerate(addresses):
            logger.info(f"Address candidate {i+1}: {addr['address']} (Source: {addr['source']}, Relevant: {addr['is_relevant']}, Quality: {addr['source_quality']})")

        # Validate and select the best address
        logger.info("Validating addresses and selecting the best match")
        best_address = self._validate_addresses(addresses, analysis)

        if not best_address:
            logger.warning("No valid addresses found in web search results")
            return None

        logger.info(f"Found validated address: {best_address['address']} with confidence {best_address['confidence']}")
        logger.info(f"Validation reasoning: {best_address['reasoning']}")
        return best_address

    def _enhance_with_web_search(self, analysis, article=None):
        """
        Enhance address information using Perplexity API.

        This method queries the Perplexity API to find more accurate address information
        for crime incidents at jewelry stores. It extracts relevant information from
        the analysis data to create a structured prompt, sends it to the Perplexity API via
        the PerplexityClient, and then processes the response to extract, validate, and
        normalize the address.

        The process involves:
        1. Extracting information for the prompt (business name, location, crime type, etc.)
        2. Normalizing location information for better search results
        3. Creating a structured prompt for the Perplexity API
        4. Sending the prompt to the Perplexity API via the PerplexityClient
        5. Processing the response to extract and normalize the address
        6. Validating the address format and assigning a confidence score
        7. Updating the analysis with the enhanced address information

        The method includes special handling for cases where location information is missing
        or ambiguous, attempting to extract location details from the article summary or title.
        It also performs basic validation on the returned address to ensure it contains both
        numeric and alphabetic characters, which is typical for valid addresses.

        Parameters:
        -----------
        analysis : dict
            The analysis dictionary containing crime incident information, including:
            - businessName: Name of the business involved in the incident
            - detailedLocation: Location information (city, state)
            - crimeType: Type of crime (robbery, burglary, etc.)
            - incidentDate: Date of the incident
            - storeType: Type of store (jewelry store, pawn shop, etc.)
            - summary: Brief summary of the incident
        article : dict, optional
            The original article data for additional context, which may include:
            - title: Article title
            - excerpt: Article excerpt or content
            - source: Source of the article
            - date: Publication date

        Returns:
        --------
        dict
            Updated analysis with enhanced address information, including:
            - exactAddress: The normalized address string
            - addressConfidence: Confidence level (high, medium, low)
            - addressSource: Source of the address (perplexity_api)
            - webSearchReasoning: Explanation of the address validation process
        """
        # Ensure we have enough information to construct a prompt
        business_name = analysis.get('businessName', '')
        location = analysis.get('detailedLocation', '')
        crime_type = analysis.get('crimeType', '')
        incident_date = analysis.get('incidentDate', '')
        store_type = analysis.get('storeType', '')
        summary = analysis.get('summary', '')

        # Skip if we don't have enough information
        if not location and not business_name:
            logger.warning("Not enough information for Perplexity API query")
            return analysis

        # Extract location from summary if available
        extracted_location = None
        if summary:
            # Look for city and state pattern in the summary
            location_patterns = [
                r'([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})\s*-',  # City, State -
                r'([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})\s*\u2013',  # City, State – (with em dash)
                r'([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})\s*\.',  # City, State.
                r'([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})\s',  # City, State
                r'in\s+([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})',  # in City, State
                r'at\s+([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})'   # at City, State
            ]

            for pattern in location_patterns:
                matches = re.findall(pattern, summary)
                if matches:
                    city, state = matches[0]
                    extracted_location = f"{city.strip()}, {state.strip()}"
                    logger.info(f"Extracted location from summary: {extracted_location}")
                    break

        # Use the extracted location if available, otherwise use the provided location
        if extracted_location and (not location or location.lower() in ['unknown', 'not specified', 'not mentioned', 'not available']):
            location = extracted_location
            logger.info(f"Using extracted location for search: {location}")

        # Normalize location for better search results
        normalized_location = self._normalize_location(location)

        # Extract city and state from location if possible
        city, state = self._extract_city_state(normalized_location)

        # If we have city and state, use them for a more specific search
        if city and state:
            location = f"{city}, {state}"
            logger.info(f"Using normalized location for search: {location}")

        # Generate prompt for Perplexity API
        prompt = f"""I need the exact street address of a jewelry store that was involved in a crime incident.
        Please provide ONLY the full address with no additional commentary.

        Business name: {business_name if business_name and business_name.lower() not in ['unknown', 'not specified', 'not mentioned', 'not available'] else 'Not specified'}
        Store type: {store_type if store_type and store_type.lower() not in ['unknown', 'not specified', 'not mentioned'] else 'jewelry store'}
        Location: {location if location and location.lower() not in ['unknown', 'not specified', 'not mentioned', 'not available'] else 'Not specified'}
        Crime type: {crime_type if crime_type else 'Not specified'}
        Incident date: {incident_date if incident_date else 'Not specified'}

        Return ONLY the full street address with city, state, and zip code. If you cannot find the exact address, respond with 'Address not found'.
        """

        logger.info(f"Perplexity API prompt: {prompt}")

        try:
            # Query the Perplexity API
            logger.info("Querying Perplexity API for address information")
            address_response = self.perplexity_client.get_address(prompt)

            if not address_response:
                logger.warning("No response from Perplexity API")
                return analysis

            # Log the raw response
            logger.info(f"Perplexity API response: {address_response}")

            # Check if the response indicates no address was found
            if 'not found' in address_response.lower() or 'unable to' in address_response.lower():
                logger.warning("Perplexity API could not find an address")
                return analysis

            # Normalize the address
            normalized_address = self._normalize_address(address_response)
            logger.info(f"Normalized address: {normalized_address}")

            # Perform basic validation (contains numbers and text)
            if re.search(r'\d', normalized_address) and re.search(r'[A-Za-z]', normalized_address):
                # Update the analysis with the address from Perplexity
                analysis['exactAddress'] = normalized_address
                analysis['addressConfidence'] = 'medium'  # Default to medium confidence
                analysis['addressSource'] = 'perplexity_api'
                analysis['webSearchReasoning'] = "Address obtained via Perplexity API."

                # If the address contains the location, increase confidence
                if location and location.lower() not in ['unknown', 'not specified', 'not mentioned', 'not available']:
                    if location.lower() in normalized_address.lower():
                        analysis['addressConfidence'] = 'high'
                        analysis['webSearchReasoning'] = "Address obtained via Perplexity API and verified to contain the expected location."

                logger.info(f"Enhanced address from Perplexity API: {normalized_address}")
            else:
                logger.warning(f"Invalid address format from Perplexity API: {normalized_address}")

        except Exception as e:
            logger.error(f"Error enhancing with Perplexity API: {str(e)}")

        return analysis

    def _extract_addresses_from_search_results(self, search_results, analysis):
        """
        Extract potential addresses from web search results.

        Parameters:
        -----------
        search_results : str
            The web search results in markdown format
        analysis : dict
            The analysis dictionary for context

        Returns:
        --------
        list
            List of potential addresses with metadata
        """
        if not search_results or search_results.startswith("No web search results available"):
            logger.warning("No valid web search results to extract addresses from")
            return []

        addresses = []

        try:
            # Enhanced address patterns to match various formats
            address_patterns = [
                # Standard US address format: number street, city, state zip
                r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct|Place|Pl)\s*,?\s*[A-Za-z\s]+,?\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?\b',
                # Address with just street and city/state
                r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct|Place|Pl)\s*,?\s*[A-Za-z\s]+,?\s*[A-Z]{2}\b',
                # Address without number but with street name
                r'\b[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct|Place|Pl)\s*,?\s*[A-Za-z\s]+,?\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?\b',
                # Simple format: street, city state
                r'\b[A-Za-z0-9\s]+,\s*[A-Za-z\s]+,?\s*[A-Z]{2}\b'
            ]

            # Get location context from analysis
            location_context = analysis.get('detailedLocation', '').lower()
            business_name = analysis.get('businessName', '').lower()

            # Split search results into lines for processing
            lines = search_results.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Try each address pattern
                for pattern in address_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    for match in matches:
                        address = match.strip()

                        # Basic validation - skip if too short or generic
                        if len(address) < 10 or address.lower() in ['not available', 'unknown', 'not specified']:
                            continue

                        # Check relevance to the incident location
                        is_relevant = self._is_address_relevant(address, location_context, business_name)

                        # Assess source quality based on the line content
                        source_quality = self._assess_line_quality(line)

                        addresses.append({
                            'address': address,
                            'source': line,
                            'is_relevant': is_relevant,
                            'source_quality': source_quality
                        })

            # Remove duplicates while preserving order
            seen_addresses = set()
            unique_addresses = []
            for addr in addresses:
                addr_key = addr['address'].lower().strip()
                if addr_key not in seen_addresses:
                    seen_addresses.add(addr_key)
                    unique_addresses.append(addr)

            logger.info(f"Extracted {len(unique_addresses)} unique addresses from search results")
            return unique_addresses

        except Exception as e:
            logger.error(f"Error extracting addresses from search results: {str(e)}")
            return []

    # This method has been replaced by the Perplexity API integration
    # def _extract_business_name(self, title, snippet):
    #     """
    #     Extract business name from search result title and snippet.
    #
    #     DEPRECATED: This method has been replaced by the Perplexity API integration,
    #     which provides more accurate and reliable business name extraction directly.
    #     See the _enhance_with_web_search method for the new implementation.
    #     """
    #     return None

    # This method has been replaced by the Perplexity API integration
    # def _assess_source_quality(self, url):
    #     """
    #     Assess the quality of the source URL.
    #
    #     DEPRECATED: This method has been replaced by the Perplexity API integration,
    #     which provides more reliable information without needing to assess source quality.
    #     See the _enhance_with_web_search method for the new implementation.
    #     """
    #     return 'low'

    def _is_address_relevant(self, address, location_context, business_name):
        """
        Check if an address is relevant to the incident location.

        Parameters:
        -----------
        address : str
            The address to check
        location_context : str
            The location context from the analysis
        business_name : str
            The business name from the analysis

        Returns:
        --------
        bool
            True if the address appears relevant
        """
        address_lower = address.lower()

        # Check if location context appears in the address
        if location_context and any(word in address_lower for word in location_context.split() if len(word) > 3):
            return True

        # Check if business name appears in the address context
        if business_name and any(word in address_lower for word in business_name.split() if len(word) > 3):
            return True

        return False

    def _assess_line_quality(self, line):
        """
        Assess the quality of a search result line.

        Parameters:
        -----------
        line : str
            The line to assess

        Returns:
        --------
        str
            Quality assessment: 'high', 'medium', or 'low'
        """
        line_lower = line.lower()

        # High quality indicators
        if any(indicator in line_lower for indicator in ['address:', 'located at', 'store address', 'business address']):
            return 'high'

        # Medium quality indicators
        if any(indicator in line_lower for indicator in ['street', 'avenue', 'road', 'boulevard']):
            return 'medium'

        return 'low'

    def _validate_addresses(self, addresses, analysis):
        """
        Validate and select the best address from the list of potential addresses.

        Parameters:
        -----------
        addresses : list
            List of potential addresses with metadata
        analysis : dict
            The analysis dictionary for context

        Returns:
        --------
        dict or None
            The best validated address with metadata, or None if no valid address found
        """
        if not addresses:
            return None

        # Score each address
        scored_addresses = []
        for addr in addresses:
            score = 0

            # Relevance score
            if addr['is_relevant']:
                score += 3

            # Source quality score
            if addr['source_quality'] == 'high':
                score += 3
            elif addr['source_quality'] == 'medium':
                score += 2
            else:
                score += 1

            # Length and completeness score
            if len(addr['address']) > 20:
                score += 1
            if ',' in addr['address']:  # Has city/state separation
                score += 1
            if re.search(r'\d{5}', addr['address']):  # Has zip code
                score += 1

            scored_addresses.append({
                'address': addr['address'],
                'score': score,
                'confidence': min(score / 10.0, 1.0),  # Normalize to 0-1
                'reasoning': f"Score: {score}/10 based on relevance, source quality, and completeness"
            })

        # Sort by score and return the best
        scored_addresses.sort(key=lambda x: x['score'], reverse=True)

        if scored_addresses:
            best = scored_addresses[0]
            logger.info(f"Selected best address: {best['address']} with score {best['score']}")
            return best

        return None

    def _add_fun_analysis_elements(self, analysis):
        """Add engaging sales-oriented elements to the analysis for business development"""
        crime_type = str(analysis.get('crimeType', '')).lower()
        method = str(analysis.get('method', '')).lower()
        entry_method = str(analysis.get('entryMethod', '')).lower()
        value = str(analysis.get('estimatedValue', ''))
        num_suspects = str(analysis.get('numSuspects', ''))

        # Add attention-grabbing headline for sales pitches
        if 'smash' in method or 'smash' in entry_method:
            analysis['salesPitchHeadline'] = "PREVENT THE NEXT HEIST: Smash & Grab Protection That Works"
        elif 'armed' in method or 'armed' in crime_type:
            analysis['salesPitchHeadline'] = "STAFF SAFETY FIRST: Modern Solutions for Armed Robbery Prevention"
        elif 'distraction' in method:
            analysis['salesPitchHeadline'] = "DON'T GET FOOLED AGAIN: Counter-Distraction Training & Technology"
        elif 'grab and run' in method:
            analysis['salesPitchHeadline'] = "SECURE YOUR MERCHANDISE: Stop Grab & Run Losses Immediately"
        elif 'burglary' in crime_type:
            analysis['salesPitchHeadline'] = "AFTER-HOURS PROTECTION: Next-Gen Security Solutions for Jewelry Retailers"
        else:
            analysis['salesPitchHeadline'] = "PROTECT YOUR INVESTMENT: Comprehensive Security for Jewelry Businesses"

        # Add comparable incident for storytelling
        if 'smash' in method or 'smash' in entry_method:
            analysis['comparableIncident'] = "Ocean's Eleven-style coordinated attack - increasingly common in upscale retail"
        elif 'kidnapping' in crime_type or 'violent' in crime_type:
            analysis['comparableIncident'] = "High-intensity criminal operation similar to recent high-profile cases in Beverly Hills"
        elif 'distraction' in method:
            analysis['comparableIncident'] = "Classic distraction technique seen in multiple recent incidents across luxury retailers"
        elif 'armed' in method or 'armed' in crime_type:
            analysis['comparableIncident'] = "Professional armed robbery similar to incidents targeting high-end boutiques"
        elif 'burglary' in crime_type:
            analysis['comparableIncident'] = "Sophisticated overnight operation - a growing trend in jewelry retail crime"
        elif 'grab and run' in method:
            analysis['comparableIncident'] = "Quick opportunistic theft - the most common and preventable retail crime pattern"
        else:
            analysis['comparableIncident'] = "Similar patterns emerging in retail jewelry crime statistics nationwide"

        # Add risk assessment for sales conversations
        if 'armed' in method or 'violent' in crime_type or 'kidnapping' in crime_type:
            analysis['riskAssessment'] = "SEVERE: High-risk operation involving weapons and coordinated criminals"
        elif 'smash' in method:
            analysis['riskAssessment'] = "HIGH: Organized crime with significant planning and resources"
        elif 'distraction' in method:
            analysis['riskAssessment'] = "MODERATE: Requires social engineering and timing - but preventable with training"
        elif 'grab and run' in method:
            analysis['riskAssessment'] = "BASIC: Opportunistic crime that proper protocols can prevent"
        else:
            analysis['riskAssessment'] = "UNDETERMINED: Custom risk assessment recommended"

        # Calculate potential business impact
        impact_level = 1
        impact_description = []

        # Base impact on crime characteristics
        if 'armed' in method or 'armed' in crime_type:
            impact_level += 4
            impact_description.append("Staff trauma and potential injury")
        if 'smash' in method or 'smash' in entry_method:
            impact_level += 3
            impact_description.append("Significant property damage")
        if 'kidnapping' in crime_type:
            impact_level += 5
            impact_description.append("Severe personnel safety risks")

        # Add value-based impact
        try:
            if '$' in value:
                value_str = value.replace('$', '').replace(',', '')
                if 'million' in value_str.lower():
                    multiplier = float(value_str.split()[0])
                    value_num = multiplier * 1000000
                else:
                    value_num = float(value_str)

                if value_num > 1000000:
                    impact_level += 5
                    impact_description.append("Catastrophic inventory loss")
                elif value_num > 100000:
                    impact_level += 3
                    impact_description.append("Major inventory loss")
                elif value_num > 50000:
                    impact_level += 2
                    impact_description.append("Significant inventory loss")
                elif value_num > 10000:
                    impact_level += 1
                    impact_description.append("Notable inventory loss")
        except:
            pass

        # Format impact level as 1-10
        impact_level = min(10, impact_level)
        impact_level = max(1, impact_level)

        # Create business impact assessment
        analysis['businessImpactScore'] = impact_level
        analysis['businessImpactAreas'] = ", ".join(impact_description) if impact_description else "Undetermined"

        # Add practical security recommendations for sales conversations
        if 'smash' in method or 'smash' in entry_method:
            analysis['securityRecommendation'] = "Impact-resistant showcases, smash-sensor alarms, and rapid-response protocols"
        elif 'armed' in method or 'armed' in crime_type:
            analysis['securityRecommendation'] = "Staff safety training, panic buttons, and enhanced surveillance with remote monitoring"
        elif 'distraction' in method:
            analysis['securityRecommendation'] = "Anti-distraction protocols, staff training, and improved visibility of all showcases"
        elif 'grab and run' in method:
            analysis['securityRecommendation'] = "Tethered displays, showcase locks, and strategic merchandise placement"
        elif 'burglary' in crime_type:
            analysis['securityRecommendation'] = "Enhanced after-hours security, motion detection, and vault upgrades"
        else:
            analysis['securityRecommendation'] = "Comprehensive security assessment and tailored prevention strategies"

        # Add interesting fact for engagement
        if 'smash' in method or 'smash' in entry_method:
            analysis['interestingFactForSales'] = "Smash and grab crimes typically last less than 60 seconds, but can cost millions"
        elif 'armed' in method or 'armed' in crime_type:
            analysis['interestingFactForSales'] = "Over 60% of jewelry businesses will face an armed robbery attempt during their lifetime"
        elif 'distraction' in method:
            analysis['interestingFactForSales'] = "Distraction thefts increase 300% during holiday shopping seasons"
        elif 'grab and run' in method:
            analysis['interestingFactForSales'] = "The average grab and run takes just 8 seconds but costs retailers $10,000+"
        elif 'burglary' in crime_type:
            analysis['interestingFactForSales'] = "Most jewelry burglaries occur within 2 hours of closing or opening time"
        else:
            analysis['interestingFactForSales'] = "Jewelry crimes are among the most profitable and targeted retail crimes nationwide"

        return analysis



    def _extract_address_from_article(self, article, analysis):
        """
        Extract a potential street address from an article and add it to the analysis.

        Parameters:
        -----------
        article : dict
            The article data
        analysis : dict
            The analysis data to update

        Returns:
        --------
        dict
            The updated analysis data
        """
        # Skip if we already have an exact address
        if analysis.get('exactAddress'):
            return analysis

        # Try to extract address from article
        extracted_address = extract_address_from_article(article)
        if extracted_address:
            # Normalize the address
            normalized_address = normalize_address(extracted_address)
            analysis['exactAddress'] = normalized_address
            analysis['addressSource'] = 'extracted_from_article'
            analysis['extracted_incident_address'] = normalized_address
            analysis['addressConfidence'] = 'medium'
            logger.info(f"Extracted address from article: {normalized_address}")

        return analysis

    def _normalize_address(self, address):
        """
        Normalize address format for geocoding readiness.
        Uses the imported normalize_address function from address_extractor.

        Parameters:
        -----------
        address : str
            Raw address string to normalize

        Returns:
        --------
        str
            Normalized address string
        """
        return normalize_address(address)

    def _normalize_location(self, location):
        """
        Normalize location string for better matching.

        Parameters:
        -----------
        location : str
            Raw location string to normalize

        Returns:
        --------
        str
            Normalized location string
        """
        if not location:
            return ''

        # Convert to lowercase
        location = location.lower()

        # Handle common abbreviations
        location = location.replace('n.', 'north')
        location = location.replace('s.', 'south')
        location = location.replace('e.', 'east')
        location = location.replace('w.', 'west')

        # Handle state abbreviations
        state_map = {
            'al': 'alabama', 'ak': 'alaska', 'az': 'arizona', 'ar': 'arkansas',
            'ca': 'california', 'co': 'colorado', 'ct': 'connecticut', 'de': 'delaware',
            'fl': 'florida', 'ga': 'georgia', 'hi': 'hawaii', 'id': 'idaho',
            'il': 'illinois', 'in': 'indiana', 'ia': 'iowa', 'ks': 'kansas',
            'ky': 'kentucky', 'la': 'louisiana', 'me': 'maine', 'md': 'maryland',
            'ma': 'massachusetts', 'mi': 'michigan', 'mn': 'minnesota', 'ms': 'mississippi',
            'mo': 'missouri', 'mt': 'montana', 'ne': 'nebraska', 'nv': 'nevada',
            'nh': 'new hampshire', 'nj': 'new jersey', 'nm': 'new mexico', 'ny': 'new york',
            'nc': 'north carolina', 'nd': 'north dakota', 'oh': 'ohio', 'ok': 'oklahoma',
            'or': 'oregon', 'pa': 'pennsylvania', 'ri': 'rhode island', 'sc': 'south carolina',
            'sd': 'south dakota', 'tn': 'tennessee', 'tx': 'texas', 'ut': 'utah',
            'vt': 'vermont', 'va': 'virginia', 'wa': 'washington', 'wv': 'west virginia',
            'wi': 'wisconsin', 'wy': 'wyoming', 'dc': 'district of columbia'
        }

        # Check if location ends with a state abbreviation
        for abbr, full in state_map.items():
            if location.endswith(f', {abbr}'):
                location = location[:-len(abbr)-2] + f', {full}'
                break

        # Normalize whitespace
        location = re.sub(r'\s+', ' ', location).strip()

        return location

    def _extract_city_state(self, location):
        """
        Extract city and state from a location string.

        Parameters:
        -----------
        location : str
            Location string to parse

        Returns:
        --------
        tuple
            (city, state) tuple, empty strings if not found
        """
        if not location:
            return '', ''

        # Try to match city, state pattern
        match = re.search(r'([^,]+),\s*([^,]+)$', location)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            return city, state

        # If no comma, assume the whole string is a city or state
        return location, ''

    def _find_business_address(self, analysis):
        """Find the exact address for a known business name"""
        # Only skip if we don't have a business name AND don't have location info
        if (not analysis.get('businessName') or analysis['businessName'] in ['Not specified', 'Not mentioned']) and not analysis.get('detailedLocation'):
            return analysis

        business_name = analysis.get('businessName', '')
        location = analysis.get('detailedLocation', '')
        store_type = analysis.get('storeType', '')

        # Clean up inferred confidence notation if present
        if business_name and '(inferred:' in business_name:
            business_name = business_name.split('(inferred:')[0].strip()

        # Construct an appropriate query based on available information
        if business_name and business_name not in ['Not specified', 'Not mentioned']:
            query = f"{business_name} jewelry {location} address"
        elif location and store_type and store_type not in ['Not specified', 'Not mentioned']:
            query = f"{store_type} in {location} address"
        elif location:
            query = f"jewelry store in {location} address"
        else:
            return analysis  # Not enough info to search

        logger.info(f"Searching for address with query: {query}")

        try:
            # Use Claude to find the address
            prompt = f"""
            Please find the full address of this jewelry business:

            Business name: {business_name}
            Location area: {location}

            Format your response as a JSON object with these fields:
            {{
                "businessName": "verified business name",
                "address": "full address with street, city, state, zip",
                "confidence": "high|medium|low",
                "source": "where you found this information"
            }}
            """

            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )

            # Parse the response
            result_text = response.content[0].text
            # Extract JSON from the response
            json_match = re.search(r'```json\s*({.*?})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                json_match = re.search(r'{.*}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)

            try:
                address_info = json.loads(result_text)

                # Update the analysis with the address information
                if address_info.get('address'):
                    # Normalize address format
                    raw_address = address_info['address']
                    normalized_address = self._normalize_address(raw_address)
                    analysis['exactAddress'] = normalized_address
                    analysis['addressConfidence'] = address_info.get('confidence', 'low')

                if address_info.get('businessName') and address_info.get('businessName') != business_name:
                    analysis['businessName'] = address_info['businessName']
                    analysis['businessNameConfidence'] = 'high'  # Verified business name gets high confidence

                analysis['addressSource'] = address_info.get('source', '')

                logger.info(f"Found address info: {address_info}")

            except json.JSONDecodeError:
                logger.warning(f"Could not parse address info response: {result_text}")

        except Exception as e:
            logger.error(f"Error finding business address: {str(e)}")

        return analysis

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
Business Name Confidence: {analysis.get('businessNameConfidence', 'Not available')}
Exact Address: {analysis.get('exactAddress', 'Not available')}
Address Confidence: {analysis.get('addressConfidence', 'Not available')}
Store Type: {analysis.get('storeType', 'Not specified')}
Date of Article: {article_date if article_date else 'Not specified'}
Scraping Date: {scraping_date if scraping_date else 'Not available'}
Incident Date: {incident_date if incident_date else 'Not specified'}
Crime Type: {analysis.get('crimeType', 'Unknown')}
Method: {analysis.get('method', 'Unknown')}
Entry Method: {analysis.get('entryMethod', 'Not specified')}
Target: {analysis.get('target', 'Unknown')}
Estimated Value: {analysis.get('estimatedValue', 'Not specified')}
Number of Suspects: {analysis.get('numSuspects', 'Not specified')}
Key Details: {analysis.get('characteristics', 'No additional details available')}
Summary: {analysis.get('summary', 'No summary available')}
Lead Quality Score: {analysis.get('totalScore', 'Not scored')} (Value: {analysis.get('valueScore', 'N/A')}, Recency: {analysis.get('recencyScore', 'N/A')})
URL: {article.get('url', '')}
Address Source: {analysis.get('addressSource', 'Not available')}
Inference Reasoning: {analysis.get('businessInferenceReasoning', '')}

-- SALES ENGAGEMENT INFO --
Sales Pitch Headline: {analysis.get('salesPitchHeadline', 'Not available')}
Comparable Incident: {analysis.get('comparableIncident', 'Not analyzed')}
Risk Assessment: {analysis.get('riskAssessment', 'Not assessed')}
Business Impact Score: {analysis.get('businessImpactScore', 'Not calculated')} / 10
Impact Areas: {analysis.get('businessImpactAreas', 'Not determined')}
Security Recommendation: {analysis.get('securityRecommendation', 'Not available')}
Interesting Fact: {analysis.get('interestingFactForSales', 'Not available')}
"""
        return summary

    def _generate_summary(self, results):
        """Generate a summary of the analysis results."""
        # Create a list of dictionaries by parsing the article summaries
        parsed_results = []
        for result in results:
            # Extract info from each summary string
            lines = result.strip().split('\n')
            article_data = {}

            for line in lines:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    article_data[key] = value

            parsed_results.append(article_data)

        # Create DataFrame from parsed results
        df = pd.DataFrame(parsed_results)

        # Check if the DataFrame is valid
        if df.empty:
            logger.warning("No valid results to summarize")
            return "No valid results to summarize"

        # Count crime types
        crime_types = df['Crime Type'].value_counts() if 'Crime Type' in df.columns else pd.Series()

        # Count methods
        methods = df['Method'].value_counts() if 'Method' in df.columns else pd.Series()

        # Count targets
        targets = df['Target'].value_counts() if 'Target' in df.columns else pd.Series()

        # Calculate total estimated value (converting string values to numbers where possible)
        def extract_value(value):
            if pd.isna(value) or value == '' or value == 'Not specified' or value == 'Not mentioned':
                return 0
            try:
                # Convert to string first to handle both string and numeric inputs
                value_str = str(value).lower().strip()
                if 'million' in value_str:
                    # Handle "$1.5 million" format
                    amount = re.search(r'(\d+\.?\d*)\s*million', value_str)
                    if amount:
                        return float(amount.group(1)) * 1000000
                    return 0
                elif 'k' in value_str:
                    # Handle "100k" format
                    amount = re.search(r'(\d+\.?\d*)\s*k', value_str)
                    if amount:
                        return float(amount.group(1)) * 1000
                    return 0
                elif '$' in value_str:
                    # Remove $ and commas, then convert to float
                    # Handle "$100,000 in jewelry" format
                    amount = re.search(r'\$\s*(\d+[,\d]*\.?\d*)', value_str)
                    if amount:
                        return float(amount.group(1).replace(',', ''))
                    return 0
                elif isinstance(value, (int, float)):
                    return float(value)
                return 0
            except Exception as e:
                logger.warning(f"Could not parse value '{value}': {str(e)}")
                return 0

        total_value = sum(df['Estimated Value'].apply(extract_value)) if 'Estimated Value' in df.columns else 0

        # Count locations
        locations = df['Location'].value_counts() if 'Location' in df.columns else pd.Series()

        # Count risk assessments for sales information
        risk_assessments = df['Risk Assessment'].value_counts() if 'Risk Assessment' in df.columns else pd.Series()

        # Count comparable incidents
        comparable_incidents = df['Comparable Incident'].value_counts() if 'Comparable Incident' in df.columns else pd.Series()

        # Calculate average business impact
        try:
            if 'Business Impact Score' in df.columns:
                # Clean the data - remove any non-numeric parts like "/ 10"
                impact_scores = df['Business Impact Score'].astype(str).str.replace(r'\s*/\s*\d+', '', regex=True).astype(float)
                avg_impact = impact_scores.mean()
            else:
                avg_impact = 0
        except Exception as e:
            logger.warning(f"Could not calculate average impact score: {str(e)}")
            avg_impact = 0

        # Parse and sort by incident date
        if 'Incident Date' in df.columns:
            df['parsed_incident_date'] = df['Incident Date'].apply(self._parse_date)
            df = df.sort_values('parsed_incident_date', ascending=False)

        summary = f"""
Analysis Summary:
---------------
Total Incidents: {len(df)}
Total Estimated Value: ${total_value:,.2f}
Average Business Impact Score: {avg_impact:.1f} / 10

Crime Types:
{crime_types.to_string() if not crime_types.empty else 'None found'}

Methods Used:
{methods.to_string() if not methods.empty else 'None found'}

Targets:
{targets.to_string() if not targets.empty else 'None found'}

Locations:
{locations.to_string() if not locations.empty else 'None found'}

Risk Assessment Distribution:
{risk_assessments.to_string() if not risk_assessments.empty else 'None available'}

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

        # Add sales information patterns
        summary += "\n\nSales Engagement Information:"
        if not risk_assessments.empty:
            summary += f"\n- Most common risk level: {risk_assessments.index[0]} ({risk_assessments.iloc[0]} incidents)"
        if not comparable_incidents.empty:
            summary += f"\n- Most common comparable scenario: {comparable_incidents.index[0].split(' - ')[0]} ({comparable_incidents.iloc[0]} incidents)"

        # Extract common security recommendations
        if 'Security Recommendation' in df.columns:
            # Get all unique recommendations
            all_recommendations = []
            for rec in df['Security Recommendation']:
                if rec and rec != 'Not available':
                    parts = rec.split(', ')
                    all_recommendations.extend(parts)

            # Count occurrences
            from collections import Counter
            rec_counter = Counter(all_recommendations)
            top_recs = rec_counter.most_common(3)

            if top_recs:
                summary += "\n\nTop Security Recommendations:"
                for rec, count in top_recs:
                    summary += f"\n- {rec}"

        summary += "\n\nIndividual Article Summaries (Sorted by Incident Date):\n--------------------------------------------------\n"

        # Add individual article summaries directly
        for result in results:
            summary += result + "\n"

        return summary

    def process_single_batch(self, input_file: Optional[str] = None, batch_size: int = 10) -> bool:
        """
        Process a single batch of articles.

        Args:
            input_file: Path to input CSV file. If not provided, articles are fetched from the database.
            batch_size: Number of articles to process in one batch. Defaults to 10.

        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            # Set batch size
            self.batch_size = batch_size

            # Process articles - either from CSV or database
            if input_file:
                # Legacy CSV mode - read from CSV file
                df = pd.read_csv(input_file)
                logger.info(f"Found {len(df)} articles in {input_file}")
                articles_to_process = df.to_dict('records')
            else:
                # New mode - read from database using analyzer module
                try:
                    # Import locally to avoid circular imports
                    from .analyzer import get_unanalyzed_articles

                    with get_db_connection() as conn:
                        articles_to_process = get_unanalyzed_articles(conn, limit=self.batch_size)

                        if not articles_to_process:
                            logger.info("No unanalyzed articles found in the database")
                            return True
                except Exception as db_err:
                    logger.error(f"Database error: {db_err}")
                    return False

            # Process articles in the batch
            batch_results = []
            article_analyses = []  # Store full analysis results for database insertion

            logger.info(f"\nProcessing batch of {len(articles_to_process)} articles")

            for idx, article in enumerate(articles_to_process):
                try:
                    logger.info(f"\nAnalyzing article {idx + 1}: {article['title']}")
                    logger.info(f"Location: {article['location']}")
                    logger.info(f"URL: {article['url']}")

                    # Create the analysis prompt
                    prompt = self._create_analysis_prompt(article)

                    # Get analysis from Claude with timeout
                    try:
                        response = self.client.messages.create(
                            model="claude-3-7-sonnet-20250219",
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
                        # Enhance business information
                        logger.info(f"Enhancing business information for article {idx + 1}")
                        enhanced_analysis = self._enhance_business_info(analysis, article)

                        # Check if we should perform web search for address verification
                        should_search = self._should_perform_web_search(enhanced_analysis)
                        can_search = True  # Flag to track if web search is available

                        # Generate web search query if needed
                        web_search_query = None
                        if should_search:
                            try:
                                # Generate search query based on available information
                                business_name = enhanced_analysis.get('businessName', '')
                                location = enhanced_analysis.get('detailedLocation', '')
                                crime_type = enhanced_analysis.get('crimeType', '')
                                incident_date = enhanced_analysis.get('incidentDate', '')
                                store_type = enhanced_analysis.get('storeType', '')

                                # Skip if we don't have enough information
                                if not location and not business_name:
                                    logger.warning("Not enough information for web search")
                                else:
                                    # Generate search query based on available information
                                    query_parts = []

                                    # Add business name if available and not generic
                                    if business_name and business_name.lower() not in ['unknown', 'not specified', 'not mentioned', 'not available']:
                                        query_parts.append(f'"{business_name}"')
                                    elif store_type and store_type.lower() not in ['unknown', 'not specified', 'not mentioned']:
                                        query_parts.append(f'"{store_type}"')
                                    else:
                                        query_parts.append('"jewelry store"')

                                    # Add crime type if available
                                    if crime_type and crime_type.lower() not in ['unknown', 'not specified', 'not mentioned']:
                                        query_parts.append(f'"{crime_type}"')

                                    # Add location
                                    if location:
                                        query_parts.append(f'in "{location}"')

                                    # Add date if available and not generic
                                    if incident_date and incident_date.lower() not in ['not available', 'unknown', 'not specified']:
                                        query_parts.append(f'on "{incident_date}"')

                                    # Add 'address' keyword
                                    query_parts.append('address')

                                    # Construct the final query
                                    web_search_query = ' '.join(query_parts)
                                    logger.info(f"Generated web search query: {web_search_query}")
                            except Exception as e:
                                logger.error(f"Error generating web search query: {str(e)}")
                                web_search_query = None

                        # Perform web search if query was generated
                        web_search_results = None
                        if web_search_query:
                            try:
                                # Call the web_search function
                                logger.info(f"Performing web search with query: {web_search_query}")
                                web_search_results = web_search(query=web_search_query, num_results=5)
                                logger.info("Web search completed successfully")
                            except Exception as e:
                                logger.error(f"Error performing web search: {str(e)}")
                                can_search = False

                        # Parse and validate addresses from search results
                        validated_address = None
                        if should_search and can_search and web_search_results:
                            try:
                                # Parse and validate addresses
                                validated_address = self._parse_and_validate_address_from_search(web_search_results, enhanced_analysis)
                            except Exception as e:
                                logger.error(f"Error parsing/validating addresses: {str(e)}")

                        # Update analysis with validated address
                        if validated_address:
                            # Update the analysis with the validated address
                            enhanced_analysis['exactAddress'] = validated_address['address']
                            enhanced_analysis['addressConfidence'] = validated_address['confidence']
                            enhanced_analysis['addressSource'] = 'web_search_verification'
                            enhanced_analysis['webSearchReasoning'] = validated_address['reasoning']

                            # If business name was also found, update it
                            if validated_address.get('business_name') and validated_address['business_name'] != enhanced_analysis.get('businessName', ''):
                                enhanced_analysis['businessName'] = validated_address['business_name']
                                enhanced_analysis['businessNameConfidence'] = 'high'  # Web search verification gives high confidence

                            logger.info(f"Updated analysis with validated address: {validated_address['address']}")

                        # Add fun analysis elements
                        self._add_fun_analysis_elements(enhanced_analysis)

                        # Add article ID and timestamp for database storage
                        enhanced_analysis['article_id'] = article.get('id')
                        enhanced_analysis['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Create article summary
                        summary = self._create_article_summary(article, enhanced_analysis)
                        batch_results.append(summary)
                        article_analyses.append(enhanced_analysis)  # Store for database

                        logger.info(f"Analysis completed successfully")
                        logger.info(f"Analysis results: {json.dumps(enhanced_analysis, indent=2)}")
                    else:
                        logger.warning(f"Failed to extract analysis for article {idx + 1}")

                except Exception as e:
                    logger.error(f"Error processing article {idx + 1}: {str(e)}")
                    continue

            logger.info(f"\nCompleted batch processing")

            # Save results to database
            self._save_results_to_database(article_analyses)

            # Also save to CSV for backward compatibility
            if batch_results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                os.makedirs(self.output_dir, exist_ok=True)

                # Save summaries
                summary_file = os.path.join(self.output_dir, f'analysis_summary_{timestamp}.txt')
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(batch_results))
                logger.info(f"\nAnalysis summaries saved to {summary_file}")

                # Save raw analysis data
                json_file = os.path.join(self.output_dir, f'analyzed_leads_single_batch_{timestamp}.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(article_analyses, f, indent=2)
                logger.info(f"Raw analysis data saved to {json_file}")

                # Save CSV version
                csv_file = os.path.join(self.output_dir, f'analyzed_leads_single_batch_{timestamp}.csv')
                pd.DataFrame(article_analyses).to_csv(csv_file, index=False)
                logger.info(f"Analysis data saved to CSV: {csv_file}")

                # Generate final summary
                summary = self._generate_summary(batch_results)
                logger.info("\nAnalysis Summary:")
                logger.info(summary)

                # Save the summary to a file
                summary_output_file = os.path.join(self.output_dir, f'analysis_summary_{timestamp}.txt')
                with open(summary_output_file, 'w', encoding='utf-8') as f:
                    f.write(summary)
                logger.info(f"Analysis summary saved to {summary_output_file}")

            return True

        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            return False

    def _save_results_to_database(self, analyses):
        """Save analysis results to the SQLite database."""
        if not analyses:
            logger.info("No analysis results to save to database")
            return

        try:
            # Import locally to avoid circular imports
            from .analyzer import save_analysis_results

            with get_db_connection() as conn:
                # Use the refactored function to save results
                success = save_analysis_results(conn, analyses)

                if not success:
                    logger.error("Failed to save analysis results to database")

        except Exception as e:
            logger.error(f"Error saving analysis results to database: {e}")
            # Log full traceback for debugging
            import traceback
            logger.error(traceback.format_exc())

def main():
    """Main entry point for the analyzer."""
    # Get the input file path from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python -m src.analyzer.analyzer_manual_test <input_csv_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Initialize and run the analyzer
    analyzer = SingleBatchAnalyzer()
    analyzer.process_single_batch(input_file)

if __name__ == "__main__":
    main()