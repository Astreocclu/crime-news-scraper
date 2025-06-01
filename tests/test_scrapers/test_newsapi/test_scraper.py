"""
Tests for the NewsAPI scraper module.

These tests verify the functionality of the NewsAPI scraper, including:
- API response handling
- Article filtering and processing
- Location detection
- Store type detection
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock

from src.scrapers.newsapi.scraper import NewsAPIScraper
from src.scrapers.newsapi.utils import detect_location, extract_keywords, is_business_related
from src.utils.exceptions import ScraperNetworkError

class TestNewsAPIScraper:
    """Test suite for the NewsAPI scraper."""
    
    def test_initialization(self):
        """Test that the scraper initializes correctly."""
        scraper = NewsAPIScraper()
        assert scraper.name == "NewsAPI"
        assert scraper.url == "https://newsapi.org/v2/"
        assert scraper.api_key == "010ae97959454a2c930036138e2f42ee"
        
    @patch('requests.Session.get')
    def test_search_articles_success(self, mock_get, mock_response, newsapi_mock_data):
        """Test article search with successful API response."""
        # Setup the mock
        mock_get.return_value = mock_response(newsapi_mock_data, 200)
        
        # Create scraper and search
        scraper = NewsAPIScraper()
        response = scraper.search_articles("test query")
        
        # Assertions
        assert response['status'] == 'ok'
        assert len(response['articles']) == 2
        assert response['articles'][0]['title'] == "Jewelry Store Robbery in Las Vegas"
        
    @patch('requests.Session.get')
    def test_search_articles_error(self, mock_get, mock_response):
        """Test handling of API error response."""
        # Setup the mock for error response
        error_response = {
            "status": "error",
            "code": "apiKeyInvalid",
            "message": "Your API key is invalid or incorrect."
        }
        mock_get.return_value = mock_response(error_response, 401)
        
        # Create scraper and test error handling
        scraper = NewsAPIScraper()
        with pytest.raises(ScraperNetworkError):
            scraper.search_articles("test query")
            
    def test_process_article(self):
        """Test article processing and filtering."""
        scraper = NewsAPIScraper()
        
        # Create a test article
        test_article = {
            "title": "Jewelry Store Robbery in Nevada",
            "description": "A jewelry store in Las Vegas was robbed yesterday.",
            "content": "Thieves stole watches and jewelry worth thousands of dollars.",
            "url": "https://example.com/robbery",
            "publishedAt": "2025-03-15T00:00:00Z",
            "source": {"name": "Test News"}
        }
        
        # Process the article
        processed = scraper.process_article(test_article)
        
        # Assertions
        assert processed is not None
        assert processed['title'] == "Jewelry Store Robbery in Nevada"
        assert processed['date'] == "2025-03-15"
        assert "robbery" in processed['keywords']
        assert processed['store_type'] == "Jewelry Store"
        
    def test_detect_store_type(self):
        """Test store type detection based on content."""
        scraper = NewsAPIScraper()
        
        # Test jewelry store detection
        jewelry_content = "The jewelry store was robbed overnight."
        assert scraper._detect_store_type(jewelry_content) == "Jewelry Store"
        
        # Test watch store detection
        watch_content = "The Rolex dealer reported a theft of luxury watches."
        assert scraper._detect_store_type(watch_content) == "Watch Store"
        
        # Test sports memorabilia
        sports_content = "The sports memorabilia shop had signed jerseys stolen."
        assert scraper._detect_store_type(sports_content) == "Sports Memorabilia"
        
        # Test luxury retail
        luxury_content = "The high-end retail store was targeted by thieves."
        assert scraper._detect_store_type(luxury_content) == "Luxury Retail"
        
class TestNewsAPIUtils:
    """Test suite for the NewsAPI utility functions."""
    
    def test_detect_location(self):
        """Test location detection in article content."""
        # Test Nevada detection
        nevada_text = "This incident occurred in Las Vegas, Nevada."
        assert detect_location(nevada_text) == "Nevada"
        
        # Test California detection
        california_text = "The store in Los Angeles, CA was broken into."
        assert detect_location(california_text) == "California"
        
        # Test non-matching location
        other_text = "This happened in New York City last night."
        assert detect_location(other_text) is None
        
    def test_extract_keywords(self):
        """Test keyword extraction from article content."""
        test_text = "The jewelry store experienced a smash and grab robbery."
        keywords = extract_keywords(test_text)
        
        assert "jewelry" in keywords
        assert "robbery" in keywords
        assert "smash and grab" in keywords
        
    def test_is_business_related(self):
        """Test business relevance detection."""
        # Test business related content
        business_text = "The jewelry store owner reported the theft to police."
        assert is_business_related(business_text) is True
        
        # Test non-business related content
        personal_text = "The woman had her purse stolen at the park."
        assert is_business_related(personal_text) is False