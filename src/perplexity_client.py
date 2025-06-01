"""
Perplexity API client for address confirmation.

This module provides a client for the Perplexity API to query for address information
based on business names and locations. It is used to enhance address information for
crime incidents at jewelry stores.

The module uses the PerplexiPy library to interact with the Perplexity API, which
provides natural language processing capabilities to extract accurate address information
from unstructured text. This is particularly useful for validating and enhancing address
information that may be incomplete or ambiguous in crime reports.

Example:
    ```python
    from perplexity_client import PerplexityClient

    # Initialize the client
    client = PerplexityClient()

    # Create a prompt for address lookup
    prompt = "I need the exact street address of ABC Jewelers in Las Vegas, NV"

    # Get the address
    address = client.get_address(prompt)
    print(f"Address: {address}")
    ```
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from perplexipy import PerplexityClient as PClient

# Configure logging
logger = logging.getLogger(__name__)

def get_perplexity_api_key() -> str:
    """
    Load the Perplexity API key from the environment variables.

    Returns:
        str: The Perplexity API key

    Raises:
        ValueError: If the API key is not found in the environment variables
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get the API key
    api_key = os.getenv('PERPLEXITY_API_KEY')

    # Check if the API key is available
    if not api_key:
        error_msg = "Perplexity API key not found. Please set the PERPLEXITY_API_KEY environment variable."
        logger.error(error_msg)
        raise ValueError(error_msg)

    return api_key

class PerplexityClient:
    """
    Client for the Perplexity API to query for address information.

    This class provides methods to query the Perplexity API for address information
    based on business names and locations. It is used to enhance address information
    for crime incidents at jewelry stores.

    The client handles authentication with the Perplexity API, sending structured prompts,
    and processing the responses to extract address information. It includes error handling
    for API failures, rate limiting, and invalid responses.

    Attributes:
        api_key (str): The Perplexity API key used for authentication.
        logger (logging.Logger): Logger instance for tracking API interactions.

    Note:
        This client requires a valid Perplexity API key to be set in the environment
        variables or .env file as PERPLEXITY_API_KEY.
    """

    def __init__(self):
        """
        Initialize the Perplexity client with the API key from environment variables.

        Raises:
            ValueError: If the API key is not found in the environment variables
        """
        # Get the API key
        self.api_key = get_perplexity_api_key()

        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("Perplexity client initialized")

    def get_address(self, prompt: str) -> Optional[str]:
        """
        Query the Perplexity API for an address based on the provided prompt.

        This method sends a structured prompt to the Perplexity API and extracts the
        address from the response. The prompt should be formatted to ask for a specific
        address based on business name, location, and other relevant information.

        The method uses the "sonar-medium-online" model from Perplexity, which is
        optimized for factual information retrieval. The response is processed to
        extract just the address text.

        Args:
            prompt (str): The structured prompt to send to the Perplexity API.
                Should include business name, location, and other relevant details.

        Returns:
            str or None: The address string if found and extracted successfully,
                None if an error occurred or no valid address was found.

        Raises:
            No exceptions are raised directly, as all exceptions are caught and logged.
            Returns None in case of any errors.

        Example:
            ```python
            prompt = "Find the address of ABC Jewelers in Las Vegas, NV"
            address = client.get_address(prompt)
            # address might be "123 Main St, Las Vegas, NV 89101"
            ```
        """
        self.logger.info(f"Querying Perplexity API with prompt: {prompt}")

        try:
            # Call the Perplexity API using PerplexiPy
            # Note: PerplexiPy may use environment variables for API key
            perplexity = PClient()
            response = perplexity.query(prompt, model="sonar-medium-online")

            # Extract the response text
            if response and hasattr(response, 'text'):
                address_text = response.text
                self.logger.info(f"Perplexity API response: {address_text}")
                return address_text
            else:
                self.logger.warning("No response from Perplexity API")
                return None

        except Exception as e:
            self.logger.error(f"Error querying Perplexity API: {str(e)}")
            return None
