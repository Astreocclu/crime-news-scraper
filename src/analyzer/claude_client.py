"""Claude API client for article analysis."""

import logging
from typing import Dict, Optional
import anthropic
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ClaudeClient:
    """Client for interacting with Claude AI API."""
    
    def __init__(self, api_key: str):
        """Initialize the Claude client with API key."""
        self.client = anthropic.Client(api_key=api_key)
        
    def analyze(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> Dict:
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
            
        Returns:
        --------
        Dict
            Structured analysis results
        """
        try:
            # Get Claude's response
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse Claude's response
            content = response.content[0].text
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"Error getting Claude analysis: {e}")
            return {
                'severity': 0,
                'crime_date': None,
                'article_date': None,
                'security_needed': False
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
        """
        try:
            # Extract information from Claude's response
            lines = content.strip().split('\n')
            result = {
                'severity': 0,
                'crime_date': None,
                'article_date': None,
                'security_needed': False,
                'explanation': ''
            }
            
            for line in lines:
                line = line.strip().lower()
                if 'severity' in line:
                    try:
                        result['severity'] = int(line.split(':')[-1].strip())
                    except:
                        pass
                elif 'crime occurred' in line:
                    result['crime_date'] = line.split(':')[-1].strip()
                elif 'article published' in line:
                    result['article_date'] = line.split(':')[-1].strip()
                elif 'steel mesh' in line:
                    result['security_needed'] = 'yes' in line
                elif 'explanation' in line:
                    result['explanation'] = line.split(':')[-1].strip()
                    
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Claude response: {e}")
            return {
                'severity': 0,
                'crime_date': None,
                'article_date': None,
                'security_needed': False
            } 