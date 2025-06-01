"""
Tests for the TextAnalyzer class.
"""
import unittest
from src.address_finder.text_analyzer import TextAnalyzer

class TestTextAnalyzer(unittest.TestCase):
    """Tests for the TextAnalyzer class."""
    
    def setUp(self):
        """Set up the test case."""
        self.analyzer = TextAnalyzer()
    
    def test_empty_text(self):
        """Test that empty text returns empty results."""
        result = self.analyzer.analyze_text("")
        self.assertEqual(result["geographic_entities"], [])
        self.assertEqual(result["business_entities"], [])
        self.assertEqual(result["contextual_info"], [])
    
    def test_geographic_entities(self):
        """Test extraction of geographic entities."""
        text = "The incident occurred in South Frisco, TX near 123 Main Street."
        result = self.analyzer.analyze_text(text)
        
        # Check that we found the geographic entities
        self.assertIn("TX", result["geographic_entities"])
        self.assertIn("123 Main Street", result["geographic_entities"])
        self.assertIn("South Frisco", result["geographic_entities"])
    
    def test_business_entities(self):
        """Test extraction of business entities."""
        text = "The robbery took place at Diamond Jewelry Store on Main Street."
        result = self.analyzer.analyze_text(text)
        
        # Check that we found the business entities
        self.assertTrue(any("jewelry" in entity.lower() for entity in result["business_entities"]))
        self.assertTrue(any("store" in entity.lower() for entity in result["business_entities"]))
    
    def test_contextual_info(self):
        """Test extraction of contextual information."""
        text = "The store is located near the intersection of Main Street and Broadway."
        result = self.analyzer.analyze_text(text)
        
        # Check that we found the contextual information
        self.assertTrue(any("near" in info.lower() for info in result["contextual_info"]))
        self.assertTrue(any("intersection" in info.lower() for info in result["contextual_info"]))
    
    def test_complex_text(self):
        """Test extraction from a complex text."""
        text = """
        A jewelry store in South Frisco, TX was robbed yesterday. 
        The store, Diamond Jewelers, is located at the corner of Main Street and 5th Avenue.
        The suspects fled in a car heading towards Dallas.
        """
        result = self.analyzer.analyze_text(text)
        
        # Check geographic entities
        self.assertTrue(any("Frisco" in entity for entity in result["geographic_entities"]))
        self.assertTrue(any("TX" in entity for entity in result["geographic_entities"]))
        self.assertTrue(any("Dallas" in entity for entity in result["geographic_entities"]))
        
        # Check business entities
        self.assertTrue(any("jewelry" in entity.lower() for entity in result["business_entities"]))
        self.assertTrue(any("store" in entity.lower() for entity in result["business_entities"]))
        
        # Check contextual info
        self.assertTrue(any("corner" in info.lower() for info in result["contextual_info"]))

if __name__ == "__main__":
    unittest.main()
