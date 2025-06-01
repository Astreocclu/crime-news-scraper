"""
Unit tests for the Perplexity API client.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.perplexity_client import PerplexityClient, get_perplexity_api_key
from perplexipy import PerplexityClient as PClient


class TestPerplexityClient(unittest.TestCase):
    """Test cases for the PerplexityClient class."""

    @patch('src.perplexity_client.get_perplexity_api_key')
    def setUp(self, mock_get_api_key):
        """Set up the test case with mocked dependencies."""
        mock_get_api_key.return_value = 'test_api_key'
        self.client = PerplexityClient()

    @patch('src.perplexity_client.load_dotenv')
    @patch('src.perplexity_client.os.getenv')
    def test_get_perplexity_api_key_success(self, mock_getenv, mock_load_dotenv):
        """Test successful API key retrieval."""
        mock_getenv.return_value = 'test_api_key'
        api_key = get_perplexity_api_key()
        self.assertEqual(api_key, 'test_api_key')
        mock_load_dotenv.assert_called_once()
        mock_getenv.assert_called_once_with('PERPLEXITY_API_KEY')

    @patch('src.perplexity_client.load_dotenv')
    @patch('src.perplexity_client.os.getenv')
    def test_get_perplexity_api_key_failure(self, mock_getenv, mock_load_dotenv):
        """Test API key retrieval failure."""
        mock_getenv.return_value = None
        with self.assertRaises(ValueError):
            get_perplexity_api_key()
        mock_load_dotenv.assert_called_once()
        mock_getenv.assert_called_once_with('PERPLEXITY_API_KEY')

    @patch('perplexipy.PerplexityClient')
    def test_get_address_success(self, mock_perplexity_class):
        """Test successful address retrieval."""
        # Mock the Perplexity API response
        mock_perplexity_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "123 Main St, Anytown, CA 12345"

        mock_perplexity_instance.query.return_value = mock_response
        mock_perplexity_class.return_value = mock_perplexity_instance

        prompt = "Find the address of a jewelry store in Anytown, CA"
        result = self.client.get_address(prompt)

        self.assertEqual(result, "123 Main St, Anytown, CA 12345")
        mock_perplexity_instance.query.assert_called_once()

        # Verify the correct parameters were passed
        mock_perplexity_class.assert_called_once_with(api_key='test_api_key')
        call_args = mock_perplexity_instance.query.call_args
        self.assertEqual(call_args[0][0], prompt)
        self.assertEqual(call_args[1]['model'], "sonar-medium-online")

    @patch('perplexipy.PerplexityClient')
    def test_get_address_empty_response(self, mock_perplexity_class):
        """Test handling of empty response from Perplexity API."""
        # Mock an empty response
        mock_perplexity_instance = MagicMock()
        mock_response = MagicMock()
        # Remove the text attribute to simulate an empty response
        delattr(mock_response, 'text') if hasattr(mock_response, 'text') else None

        mock_perplexity_instance.query.return_value = mock_response
        mock_perplexity_class.return_value = mock_perplexity_instance

        prompt = "Find the address of a jewelry store in Anytown, CA"
        result = self.client.get_address(prompt)

        self.assertIsNone(result)
        mock_perplexity_instance.query.assert_called_once()

    @patch('perplexipy.PerplexityClient')
    def test_get_address_api_error(self, mock_perplexity_class):
        """Test handling of API error."""
        # Mock an API error
        mock_perplexity_instance = MagicMock()
        mock_perplexity_instance.query.side_effect = Exception("API Error")
        mock_perplexity_class.return_value = mock_perplexity_instance

        prompt = "Find the address of a jewelry store in Anytown, CA"
        result = self.client.get_address(prompt)

        self.assertIsNone(result)
        mock_perplexity_instance.query.assert_called_once()


if __name__ == '__main__':
    unittest.main()
