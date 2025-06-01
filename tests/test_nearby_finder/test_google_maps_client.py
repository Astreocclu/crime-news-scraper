"""
Unit tests for the Google Maps client.

These tests verify that the Google Maps client is initialized correctly
and that it can geocode addresses, find nearby businesses, and retrieve
place details.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.nearby_finder.google_client import GoogleMapsClient
from src.nearby_finder.config import GOOGLE_MAPS_API_KEY

class TestGoogleMapsClient(unittest.TestCase):
    """Test the Google Maps client."""

    def setUp(self):
        """Set up the test environment."""
        # Ensure the API key is available
        self.api_key = GOOGLE_MAPS_API_KEY
        self.assertIsNotNone(self.api_key, "Google Maps API key is not set in the environment")
        self.assertNotEqual(self.api_key, "", "Google Maps API key is empty")

        # Create a mock client
        self.mock_client = MagicMock()

        # Create a patcher for the googlemaps.Client
        self.client_patcher = patch('googlemaps.Client', return_value=self.mock_client)
        self.mock_client_class = self.client_patcher.start()

        # Create the Google Maps client
        self.google_client = GoogleMapsClient(self.api_key)

    def tearDown(self):
        """Clean up after the test."""
        self.client_patcher.stop()

    def test_init(self):
        """Test that the client is initialized correctly."""
        # Check that the API key is set
        self.assertEqual(self.google_client.api_key, self.api_key)

        # Check that the client is created with the API key
        self.mock_client_class.assert_called_once_with(key=self.api_key)

    def test_geocode_address(self):
        """Test that geocode_address works correctly."""
        # Set up the mock response
        mock_response = [
            {
                'geometry': {
                    'location': {
                        'lat': 37.7749,
                        'lng': -122.4194
                    }
                }
            }
        ]
        self.mock_client.geocode.return_value = mock_response

        # Call the method
        result = self.google_client.geocode_address("San Francisco, CA")

        # Check that the client method was called correctly
        self.mock_client.geocode.assert_called_once_with("San Francisco, CA")

        # Check that the result is correct
        self.assertEqual(result, {'lat': 37.7749, 'lng': -122.4194})

    def test_geocode_address_no_results(self):
        """Test that geocode_address handles no results correctly."""
        # Set up the mock response
        self.mock_client.geocode.return_value = []

        # Call the method
        result = self.google_client.geocode_address("Invalid Address")

        # Check that the client method was called correctly
        self.mock_client.geocode.assert_called_once_with("Invalid Address")

        # Check that the result is correct
        self.assertEqual(result, {})

    def test_geocode_address_exception(self):
        """Test that geocode_address handles exceptions correctly."""
        # Set up the mock response
        self.mock_client.geocode.side_effect = Exception("API Error")

        # Call the method
        result = self.google_client.geocode_address("San Francisco, CA")

        # Check that the client method was called correctly
        self.mock_client.geocode.assert_called_once_with("San Francisco, CA")

        # Check that the result is correct
        self.assertEqual(result, {})

    def test_find_nearby_businesses(self):
        """Test that find_nearby_businesses works correctly."""
        # Set up the mock response for jewelry_store type
        jewelry_store_response = {
            'results': [
                {
                    'name': 'Jewelry Store 1',
                    'place_id': 'place_id_1',
                    'geometry': {
                        'location': {
                            'lat': 37.7749,
                            'lng': -122.4194
                        }
                    }
                },
                {
                    'name': 'Jewelry Store 2',
                    'place_id': 'place_id_2',
                    'geometry': {
                        'location': {
                            'lat': 37.7749,
                            'lng': -122.4194
                        }
                    }
                }
            ]
        }

        # Set up mock responses for other types
        empty_response = {'results': []}

        # Configure the mock to return different responses for different calls
        self.mock_client.places_nearby.side_effect = [
            jewelry_store_response,  # For jewelry_store type
            empty_response,  # For clothing_store type
            empty_response,  # For shopping_mall type
            empty_response   # For store type
        ]

        # Call the method
        result = self.google_client.find_nearby_businesses(37.7749, -122.4194)

        # Check that the client method was called at least once
        self.mock_client.places_nearby.assert_called()

        # Check that the result contains the expected jewelry stores
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Jewelry Store 1')
        self.assertEqual(result[0]['category'], 'jewelry')
        self.assertEqual(result[1]['name'], 'Jewelry Store 2')
        self.assertEqual(result[1]['category'], 'jewelry')

    def test_get_place_details(self):
        """Test that get_place_details works correctly."""
        # Set up the mock response
        mock_response = {
            'result': {
                'name': 'Jewelry Store 1',
                'formatted_address': '123 Main St, San Francisco, CA 94105',
                'geometry': {
                    'location': {
                        'lat': 37.7749,
                        'lng': -122.4194
                    }
                },
                'formatted_phone_number': '(415) 555-1234',
                'website': 'https://example.com'
            }
        }
        self.mock_client.place.return_value = mock_response

        # Call the method
        result = self.google_client.get_place_details('place_id_1')

        # Check that the client method was called correctly
        self.mock_client.place.assert_called_once_with(
            place_id='place_id_1',
            fields=['name', 'formatted_address', 'geometry', 'formatted_phone_number', 'website']
        )

        # Check that the result is correct
        self.assertEqual(result['name'], 'Jewelry Store 1')
        self.assertEqual(result['formatted_address'], '123 Main St, San Francisco, CA 94105')
        self.assertEqual(result['formatted_phone_number'], '(415) 555-1234')
        self.assertEqual(result['website'], 'https://example.com')

    def test_get_place_details_no_results(self):
        """Test that get_place_details handles no results correctly."""
        # Set up the mock response
        self.mock_client.place.return_value = {}

        # Call the method
        result = self.google_client.get_place_details('invalid_place_id')

        # Check that the client method was called correctly
        self.mock_client.place.assert_called_once_with(
            place_id='invalid_place_id',
            fields=['name', 'formatted_address', 'geometry', 'formatted_phone_number', 'website']
        )

        # Check that the result is correct
        self.assertEqual(result, {})

    def test_get_place_details_exception(self):
        """Test that get_place_details handles exceptions correctly."""
        # Set up the mock response
        self.mock_client.place.side_effect = Exception("API Error")

        # Call the method
        result = self.google_client.get_place_details('place_id_1')

        # Check that the client method was called correctly
        self.mock_client.place.assert_called_once_with(
            place_id='place_id_1',
            fields=['name', 'formatted_address', 'geometry', 'formatted_phone_number', 'website']
        )

        # Check that the result is correct
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
