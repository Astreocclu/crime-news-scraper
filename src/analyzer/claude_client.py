"""
Claude API client for article analysis.

This module provides a client for interacting with Anthropic's Claude API,
sending analysis prompts, and parsing the responses for crime article analysis.
"""

import os
import time
from typing import Dict, Optional, Any, List
import anthropic
from datetime import datetime
import json
from dotenv import load_dotenv

from src.utils.logger import get_logger, log_execution_time
from src.utils.exceptions import AnalyzerAPIError, AnalyzerParsingError

# Configure module logger
logger = get_logger(__name__)

def get_api_key() -> str:
    """Get the Anthropic API key from environment variables.
    
    Returns:
    --------
    str
        The Anthropic API key
        
    Raises:
    -------
    ValueError
        If the API key is not set
    """
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return api_key

class ClaudeClient:
    """Client for interacting with Claude AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude client with API key.
        
        Parameters:
        -----------
        api_key : Optional[str], optional
            The Anthropic API key. If not provided, it will be loaded from environment variables.
        """
        self.client = anthropic.Anthropic(api_key=api_key or get_api_key())
        
    @log_execution_time(logger, "Claude API: ")
    def analyze(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7, 
                max_retries: int = 3, retry_delay: float = 2.0) -> Dict:
        """
        Send prompt to Claude for analysis.
        
        Parameters:
        -----------
        prompt : str
            The analysis prompt
        max_tokens : int, optional
            Maximum number of tokens to generate
        temperature : float, optional
            Temperature for response generation (0.0 to 1.0)
        max_retries : int, optional
            Maximum number of retries on API failure
        retry_delay : float, optional
            Delay between retries in seconds (with exponential backoff)
            
        Returns:
        --------
        Dict
            Structured analysis results
            
        Raises:
        -------
        AnalyzerAPIError
            If API communication fails after all retries
        """
        # Truncate prompt in logs to avoid excessive verbosity
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        logger.info(f"Sending prompt to Claude (length: {len(prompt)}): {prompt_preview}")
        
        for attempt in range(max_retries):
            try:
                # Log attempt number if not first attempt
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt+1}/{max_retries}")
                
                # Get Claude's response
                start_time = time.time()
                response = self.client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                elapsed_time = time.time() - start_time
                
                # Log API response stats
                logger.info(f"Claude API response received in {elapsed_time:.2f}s")
                
                # Parse Claude's response
                content = response.content[0].text
                
                # Log a preview of the response
                response_preview = content[:100] + "..." if len(content) > 100 else content
                logger.info(f"Claude response: {response_preview}")
                
                # Parse and return the structured response
                return self._parse_response(content)
                
            except anthropic.APIError as e:
                # Handle API-specific errors
                logger.error(f"Claude API error: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Calculate backoff delay with exponential increase
                    current_delay = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {current_delay:.2f}s before retry")
                    time.sleep(current_delay)
                else:
                    # Raise custom exception on final retry
                    err_msg = f"Claude API error after {max_retries} retries: {str(e)}"
                    logger.critical(err_msg)
                    raise AnalyzerAPIError(err_msg)
                
            except Exception as e:
                # Handle other exceptions
                err_msg = f"Unexpected error during Claude analysis: {str(e)}"
                logger.error(err_msg)
                
                # Return fallback response for non-API errors
                return {
                    'severity': 0,
                    'crime_date': None,
                    'article_date': None,
                    'security_needed': False,
                    'error': str(e)
                }
            
    def _parse_response(self, content: str) -> Dict:
        """
        Parse Claude's response into structured data.
        
        Parameters:
        -----------
        content : str
            Claude's response text
            
        Returns:
        --------
        Dict
            Parsed analysis results
            
        Raises:
        -------
        AnalyzerParsingError
            If parsing fails in a critical way
        """
        # Default response structure
        result = {
            'severity': 0,
            'crime_date': None,
            'article_date': None,
            'security_needed': False,
            'explanation': '',
            'parse_method': 'line-by-line'  # Track how this was parsed
        }
        
        # First try to parse as JSON
        try:
            # Check for JSON formatted response (between triple backticks or alone)
            import re
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                parsed_json = json.loads(json_str)
                logger.info(f"Successfully parsed JSON response from Claude")
                result.update(parsed_json)
                result['parse_method'] = 'json'
                return result
                
            # Also try just parsing the whole thing as JSON
            try:
                parsed_json = json.loads(content)
                logger.info(f"Parsed entire response as JSON")
                result.update(parsed_json)
                result['parse_method'] = 'json'
                return result
            except json.JSONDecodeError:
                # Not JSON, continue with line parsing
                pass
                
        except Exception as json_err:
            logger.debug(f"JSON parsing failed, falling back to line parsing: {str(json_err)}")
        
        # Fallback: line-by-line parsing
        try:
            logger.debug("Performing line-by-line parsing")
            # Extract information from Claude's response
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip().lower()
                
                # Check for various field patterns
                try:
                    if 'severity' in line or 'priority' in line or 'risk' in line:
                        # Look for severity as a number (1-10 scale)
                        severity_match = re.search(r'(\d+)(?:\s*\/\s*10)?', line)
                        if severity_match:
                            result['severity'] = int(severity_match.group(1))
                            logger.debug(f"Parsed severity: {result['severity']}")
                    
                    # Date detection with multiple patterns
                    elif any(phrase in line for phrase in ['crime occurred', 'incident date', 'date of crime']):
                        date_part = line.split(':', 1)[-1].strip()
                        result['crime_date'] = date_part
                        logger.debug(f"Parsed crime date: {result['crime_date']}")
                        
                    elif any(phrase in line for phrase in ['article published', 'publication date', 'report date']):
                        date_part = line.split(':', 1)[-1].strip()
                        result['article_date'] = date_part
                        logger.debug(f"Parsed article date: {result['article_date']}")
                    
                    # Security recommendation detection
                    elif any(phrase in line for phrase in ['steel mesh', 'security screen', 'security recommendation']):
                        result['security_needed'] = any(word in line for word in ['yes', 'recommended', 'needed', 'require', 'benefit'])
                        logger.debug(f"Parsed security needed: {result['security_needed']}")
                    
                    # Explanation capture
                    elif any(phrase in line for phrase in ['explanation', 'rationale', 'reasoning', 'analysis']):
                        expl_parts = line.split(':', 1)
                        if len(expl_parts) > 1:
                            result['explanation'] = expl_parts[1].strip()
                            logger.debug(f"Parsed explanation: {result['explanation'][:50]}...")
                except Exception as line_err:
                    logger.warning(f"Error parsing specific line '{line[:30]}...': {str(line_err)}")
                    continue
            
            # Check if we got meaningful data
            if result['severity'] > 0 or result['crime_date'] or result['explanation']:
                logger.info(f"Successfully extracted data via line parsing")
                return result
            else:
                logger.warning(f"Line parsing yielded minimal results")
                # We'll still return what we have
                
            return result
            
        except Exception as e:
            err_msg = f"Error parsing Claude response: {str(e)}"
            logger.error(err_msg)
            
            # Include the error in the result
            result['error'] = str(e)
            result['parse_method'] = 'failed'
            
            # Still return a valid but empty result structure
            return result