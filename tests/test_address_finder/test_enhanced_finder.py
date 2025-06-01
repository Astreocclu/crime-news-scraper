"""
Tests for the EnhancedAddressFinder class.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.address_finder.enhanced_finder import EnhancedAddressFinder

class TestEnhancedAddressFinder(unittest.TestCase):
    """Tests for the EnhancedAddressFinder class."""
    
    def setUp(self):
        """Set up the test case."""
        # Mock the components to avoid making actual API calls
        self.text_analyzer_patcher = patch('src.address_finder.enhanced_finder.TextAnalyzer')
        self.address_inferrer_patcher = patch('src.address_finder.enhanced_finder.AddressInferrer')
        self.address_confirmer_patcher = patch('src.address_finder.enhanced_finder.AddressConfirmer')
        
        self.mock_text_analyzer_class = self.text_analyzer_patcher.start()
        self.mock_address_inferrer_class = self.address_inferrer_patcher.start()
        self.mock_address_confirmer_class = self.address_confirmer_patcher.start()
        
        self.mock_text_analyzer = MagicMock()
        self.mock_address_inferrer = MagicMock()
        self.mock_address_confirmer = MagicMock()
        
        self.mock_text_analyzer_class.return_value = self.mock_text_analyzer
        self.mock_address_inferrer_class.return_value = self.mock_address_inferrer
        self.mock_address_confirmer_class.return_value = self.mock_address_confirmer
        
        # Create the finder with the mocked components
        self.finder = EnhancedAddressFinder(api_key="fake_api_key")
    
    def tearDown(self):
        """Clean up after the test case."""
        self.text_analyzer_patcher.stop()
        self.address_inferrer_patcher.stop()
        self.address_confirmer_patcher.stop()
    
    def test_empty_text(self):
        """Test that empty text returns a failure result."""
        result = self.finder.find_address("")
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "Empty text provided")
    
    def test_no_location_clues(self):
        """Test handling of no location clues."""
        # Set up the mock to return no clues
        self.mock_text_analyzer.analyze_text.return_value = {
            "geographic_entities": [],
            "business_entities": [],
            "contextual_info": []
        }
        
        # Find the address
        result = self.finder.find_address("Some text without location clues")
        
        # Check that the result is a failure
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "No location clues found in text")
    
    def test_no_candidate_addresses(self):
        """Test handling of no candidate addresses."""
        # Set up the mock to return clues
        self.mock_text_analyzer.analyze_text.return_value = {
            "geographic_entities": ["Frisco, TX"],
            "business_entities": ["jewelry store"],
            "contextual_info": []
        }
        
        # Set up the mock to return no candidates
        self.mock_address_inferrer.infer_addresses.return_value = []
        
        # Find the address
        result = self.finder.find_address("Jewelry store in Frisco, TX")
        
        # Check that the result is a failure
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "No candidate addresses inferred")
    
    def test_confirmation_failure(self):
        """Test handling of confirmation failure."""
        # Set up the mock to return clues
        self.mock_text_analyzer.analyze_text.return_value = {
            "geographic_entities": ["Frisco, TX"],
            "business_entities": ["jewelry store"],
            "contextual_info": []
        }
        
        # Set up the mock to return candidates
        self.mock_address_inferrer.infer_addresses.return_value = [{
            "query": "jewelry store in Frisco, TX",
            "business_name": "jewelry store",
            "location": "Frisco, TX",
            "confidence": 0.8
        }]
        
        # Set up the mock to return a failure
        self.mock_address_confirmer.confirm_addresses.return_value = {
            "success": False,
            "reason": "No addresses could be confirmed"
        }
        
        # Find the address
        result = self.finder.find_address("Jewelry store in Frisco, TX")
        
        # Check that the result is a failure
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "No addresses could be confirmed")
    
    def test_successful_address_finding(self):
        """Test successful address finding."""
        # Set up the mock to return clues
        self.mock_text_analyzer.analyze_text.return_value = {
            "geographic_entities": ["Frisco, TX"],
            "business_entities": ["jewelry store"],
            "contextual_info": []
        }
        
        # Set up the mock to return candidates
        self.mock_address_inferrer.infer_addresses.return_value = [{
            "query": "jewelry store in Frisco, TX",
            "business_name": "jewelry store",
            "location": "Frisco, TX",
            "confidence": 0.8
        }]
        
        # Set up the mock to return a confirmed address
        self.mock_address_confirmer.confirm_addresses.return_value = {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Diamond Jewelers",
            "formatted_address": "123 Main St, Frisco, TX 75034, USA",
            "lat": 33.1506744,
            "lng": -96.8236306,
            "confidence": 0.9,
            "original_query": "jewelry store in Frisco, TX",
            "phone_number": "(123) 456-7890",
            "website": "https://example.com"
        }
        
        # Find the address
        result = self.finder.find_address("Jewelry store in Frisco, TX")
        
        # Check that the result is successful
        self.assertTrue(result["success"])
        self.assertEqual(result["formatted_address"], "123 Main St, Frisco, TX 75034, USA")
        self.assertEqual(result["name"], "Diamond Jewelers")
        self.assertEqual(result["phone_number"], "(123) 456-7890")
        self.assertEqual(result["website"], "https://example.com")
        
        # Check that the original text and location clues are included
        self.assertEqual(result["original_text"], "Jewelry store in Frisco, TX")
        self.assertEqual(result["location_clues"], {
            "geographic_entities": ["Frisco, TX"],
            "business_entities": ["jewelry store"],
            "contextual_info": []
        })

if __name__ == "__main__":
    unittest.main()
