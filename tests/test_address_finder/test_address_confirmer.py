"""
Tests for the AddressConfirmer class.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.address_finder.address_confirmer import AddressConfirmer

class TestAddressConfirmer(unittest.TestCase):
    """Tests for the AddressConfirmer class."""
    
    def setUp(self):
        """Set up the test case."""
        # Mock the GoogleMapsClient to avoid making actual API calls
        self.patcher = patch('src.address_finder.address_confirmer.GoogleMapsClient')
        self.mock_client_class = self.patcher.start()
        self.mock_client = MagicMock()
        self.mock_client_class.return_value = self.mock_client
        
        # Create the confirmer with the mocked client
        self.confirmer = AddressConfirmer(api_key="fake_api_key")
    
    def tearDown(self):
        """Clean up after the test case."""
        self.patcher.stop()
    
    def test_empty_candidates(self):
        """Test that empty candidates return a failure result."""
        result = self.confirmer.confirm_addresses([])
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "No candidate addresses provided")
    
    def test_search_places_error(self):
        """Test handling of errors in search_places."""
        # Set up the mock to raise an exception
        self.mock_client.client.places.side_effect = Exception("API error")
        
        # Create a candidate address
        candidate = {
            "query": "jewelry store in Frisco, TX",
            "business_name": "jewelry store",
            "location": "Frisco, TX",
            "confidence": 0.8
        }
        
        # Confirm the address
        result = self.confirmer.confirm_addresses([candidate])
        
        # Check that the result is a failure
        self.assertFalse(result["success"])
    
    def test_no_places_found(self):
        """Test handling of no places found."""
        # Set up the mock to return no results
        self.mock_client.client.places.return_value = {"results": []}
        
        # Create a candidate address
        candidate = {
            "query": "jewelry store in Frisco, TX",
            "business_name": "jewelry store",
            "location": "Frisco, TX",
            "confidence": 0.8
        }
        
        # Confirm the address
        result = self.confirmer.confirm_addresses([candidate])
        
        # Check that the result is a failure
        self.assertFalse(result["success"])
    
    def test_successful_confirmation(self):
        """Test successful address confirmation."""
        # Set up the mock to return a place
        place = {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Diamond Jewelers",
            "formatted_address": "123 Main St, Frisco, TX 75034, USA",
            "geometry": {
                "location": {
                    "lat": 33.1506744,
                    "lng": -96.8236306
                }
            },
            "rating": 4.5
        }
        self.mock_client.client.places.return_value = {"results": [place]}
        
        # Set up the mock to return place details
        place_details = {
            "formatted_phone_number": "(123) 456-7890",
            "website": "https://example.com"
        }
        self.mock_client.get_place_details.return_value = place_details
        
        # Create a candidate address
        candidate = {
            "query": "jewelry store in Frisco, TX",
            "business_name": "jewelry store",
            "location": "Frisco, TX",
            "confidence": 0.8
        }
        
        # Confirm the address
        result = self.confirmer.confirm_addresses([candidate])
        
        # Check that the result is successful
        self.assertTrue(result["success"])
        self.assertEqual(result["formatted_address"], "123 Main St, Frisco, TX 75034, USA")
        self.assertEqual(result["name"], "Diamond Jewelers")
        self.assertEqual(result["phone_number"], "(123) 456-7890")
        self.assertEqual(result["website"], "https://example.com")
    
    def test_multiple_candidates(self):
        """Test confirmation with multiple candidates."""
        # Set up the mock to return different places for different queries
        def mock_places(query, **kwargs):
            if "jewelry store in Frisco" in query:
                return {"results": [{
                    "place_id": "place1",
                    "name": "Diamond Jewelers",
                    "formatted_address": "123 Main St, Frisco, TX 75034, USA",
                    "geometry": {"location": {"lat": 33.15, "lng": -96.82}},
                    "rating": 4.5
                }]}
            elif "pawn shop in Frisco" in query:
                return {"results": [{
                    "place_id": "place2",
                    "name": "Frisco Pawn",
                    "formatted_address": "456 Oak St, Frisco, TX 75034, USA",
                    "geometry": {"location": {"lat": 33.16, "lng": -96.83}},
                    "rating": 4.0
                }]}
            else:
                return {"results": []}
        
        self.mock_client.client.places.side_effect = mock_places
        
        # Set up the mock to return place details
        self.mock_client.get_place_details.return_value = {
            "formatted_phone_number": "(123) 456-7890",
            "website": "https://example.com"
        }
        
        # Create candidate addresses
        candidates = [
            {
                "query": "jewelry store in Frisco, TX",
                "business_name": "jewelry store",
                "location": "Frisco, TX",
                "confidence": 0.8
            },
            {
                "query": "pawn shop in Frisco, TX",
                "business_name": "pawn shop",
                "location": "Frisco, TX",
                "confidence": 0.7
            }
        ]
        
        # Confirm the addresses
        result = self.confirmer.confirm_addresses(candidates)
        
        # Check that the result is successful and the highest confidence match is returned
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "Diamond Jewelers")

if __name__ == "__main__":
    unittest.main()
