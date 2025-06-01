"""
Tests for the AddressInferrer class.
"""
import unittest
from src.address_finder.address_inferrer import AddressInferrer

class TestAddressInferrer(unittest.TestCase):
    """Tests for the AddressInferrer class."""
    
    def setUp(self):
        """Set up the test case."""
        self.inferrer = AddressInferrer()
    
    def test_empty_clues(self):
        """Test that empty clues return empty results."""
        result = self.inferrer.infer_addresses({})
        self.assertEqual(result, [])
    
    def test_no_entities(self):
        """Test that clues with no entities return empty results."""
        clues = {
            "geographic_entities": [],
            "business_entities": [],
            "contextual_info": []
        }
        result = self.inferrer.infer_addresses(clues)
        self.assertEqual(result, [])
    
    def test_geographic_only(self):
        """Test inference with only geographic entities."""
        clues = {
            "geographic_entities": ["Frisco, TX"],
            "business_entities": [],
            "contextual_info": []
        }
        result = self.inferrer.infer_addresses(clues)
        
        # Check that we got at least one candidate
        self.assertGreater(len(result), 0)
        
        # Check that the candidate has the expected fields
        candidate = result[0]
        self.assertIn("query", candidate)
        self.assertIn("business_name", candidate)
        self.assertIn("location", candidate)
        self.assertIn("confidence", candidate)
        
        # Check that the location is correct
        self.assertEqual(candidate["location"], "Frisco, TX")
    
    def test_business_only(self):
        """Test inference with only business entities."""
        clues = {
            "geographic_entities": [],
            "business_entities": ["jewelry store"],
            "contextual_info": []
        }
        result = self.inferrer.infer_addresses(clues)
        
        # Check that we got at least one candidate
        self.assertGreater(len(result), 0)
        
        # Check that the candidate has the expected fields
        candidate = result[0]
        self.assertIn("query", candidate)
        self.assertIn("business_name", candidate)
        self.assertIn("location", candidate)
        self.assertIn("confidence", candidate)
        
        # Check that the business name is correct
        self.assertEqual(candidate["query"], "jewelry store")
    
    def test_combined_entities(self):
        """Test inference with both geographic and business entities."""
        clues = {
            "geographic_entities": ["Frisco, TX"],
            "business_entities": ["jewelry store"],
            "contextual_info": []
        }
        result = self.inferrer.infer_addresses(clues)
        
        # Check that we got at least one candidate
        self.assertGreater(len(result), 0)
        
        # Check that the candidate has the expected fields
        candidate = result[0]
        self.assertIn("query", candidate)
        self.assertIn("business_name", candidate)
        self.assertIn("location", candidate)
        self.assertIn("confidence", candidate)
        
        # Check that the query combines the business and location
        self.assertEqual(candidate["query"], "jewelry store in Frisco, TX")
        
        # Check that the business name and location are correct
        self.assertEqual(candidate["business_name"], "jewelry store")
        self.assertEqual(candidate["location"], "Frisco, TX")
    
    def test_with_contextual_info(self):
        """Test inference with contextual information."""
        clues = {
            "geographic_entities": ["Main Street", "Frisco, TX"],
            "business_entities": ["jewelry store"],
            "contextual_info": ["near", "corner of"]
        }
        result = self.inferrer.infer_addresses(clues)
        
        # Check that we got multiple candidates
        self.assertGreater(len(result), 1)
        
        # Check that at least one candidate includes contextual information
        has_contextual = False
        for candidate in result:
            if "near" in candidate["query"] or "corner of" in candidate["query"]:
                has_contextual = True
                break
        
        self.assertTrue(has_contextual)
    
    def test_confidence_scoring(self):
        """Test that confidence scoring works as expected."""
        clues = {
            "geographic_entities": ["Frisco, TX", "123 Main Street, Frisco, TX"],
            "business_entities": ["jewelry store", "Diamond Jewelers"],
            "contextual_info": []
        }
        result = self.inferrer.infer_addresses(clues)
        
        # Check that we got multiple candidates
        self.assertGreater(len(result), 1)
        
        # Check that the candidates are sorted by confidence
        for i in range(len(result) - 1):
            self.assertGreaterEqual(result[i]["confidence"], result[i+1]["confidence"])
        
        # Check that the most specific query has the highest confidence
        self.assertIn("123 Main Street", result[0]["query"])

if __name__ == "__main__":
    unittest.main()
