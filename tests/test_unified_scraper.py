"""
Tests for the unified scraper module.

These tests verify the functionality of the unified scraper, including:
- Initialization with multiple scraper instances
- Running multiple scrapers
- Aggregating results
- Saving combined results
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock, mock_open

from src.scrapers.unified import UnifiedScraper

class TestUnifiedScraper:
    """Test suite for the Unified Scraper."""
    
    def setup_method(self):
        """Setup unified scraper for testing."""
        # Create mock implementations
        self.mock_jsa = MagicMock()
        self.mock_newsapi = MagicMock()
        self.mock_reviewjournal = MagicMock()
        
        # Setup return values for mocks
        self.mock_jsa.scrape.return_value = {
            "Nevada": [
                {
                    "title": "JSA Test Article 1",
                    "url": "https://example.com/jsa1",
                    "date": "2025-03-15",
                    "excerpt": "Test excerpt 1",
                    "source": "JSA",
                    "keywords": ["jewelry", "theft"],
                    "is_theft_related": True,
                    "is_business_related": True
                }
            ]
        }
        
        self.mock_newsapi.scrape.return_value = {
            "Texas": [
                {
                    "title": "NewsAPI Test Article 1",
                    "url": "https://example.com/newsapi1",
                    "date": "2025-03-16",
                    "excerpt": "Test excerpt 2",
                    "source": "NewsAPI",
                    "keywords": ["jewelry", "robbery"],
                    "is_theft_related": True,
                    "is_business_related": True,
                    "store_type": "Jewelry Store"
                }
            ]
        }
        
        self.mock_reviewjournal.scrape.return_value = {
            "Nevada": [
                {
                    "title": "Review Journal Test Article 1",
                    "url": "https://example.com/rj1",
                    "date": "2025-03-17",
                    "excerpt": "Test excerpt 3",
                    "source": "Review Journal",
                    "keywords": ["jewelry", "burglary"],
                    "is_theft_related": True,
                    "is_business_related": True,
                    "detailed_location": "Las Vegas"
                }
            ]
        }
    
    @patch('src.scrapers.jsa.scraper.JSAScraper')
    @patch('src.scrapers.newsapi.scraper.NewsAPIScraper')
    @patch('src.scrapers.reviewjournal.scraper.ReviewJournalScraper')
    def test_initialization(self, mock_rj_class, mock_newsapi_class, mock_jsa_class):
        """Test that the unified scraper initializes all configured scrapers."""
        # Setup mocks
        mock_jsa_class.return_value = self.mock_jsa
        mock_newsapi_class.return_value = self.mock_newsapi
        mock_rj_class.return_value = self.mock_reviewjournal
        
        # Create unified scraper
        unified = UnifiedScraper()
        
        # Verify scrapers are initialized
        assert "jsa" in unified.scrapers
        assert "newsapi" in unified.scrapers
        assert "reviewjournal" in unified.scrapers
        
    @patch('src.scrapers.unified.UnifiedScraper._save_results')
    @patch('src.scrapers.jsa.scraper.JSAScraper')
    @patch('src.scrapers.newsapi.scraper.NewsAPIScraper')
    @patch('src.scrapers.reviewjournal.scraper.ReviewJournalScraper')
    def test_scrape_all(self, mock_rj_class, mock_newsapi_class, mock_jsa_class, mock_save):
        """Test running all scrapers and aggregating results."""
        # Setup mocks
        mock_jsa_class.return_value = self.mock_jsa
        mock_newsapi_class.return_value = self.mock_newsapi
        mock_rj_class.return_value = self.mock_reviewjournal
        
        # Create unified scraper
        unified = UnifiedScraper()
        
        # Run scrapers
        results = unified.scrape_all(deep_check=False)
        
        # Verify all scrapers were called
        self.mock_jsa.scrape.assert_called_once()
        self.mock_newsapi.scrape.assert_called_once()
        self.mock_reviewjournal.scrape.assert_called_once()
        
        # Verify results were aggregated
        assert "jsa" in results
        assert "newsapi" in results
        assert "reviewjournal" in results
        
        # Verify save was called
        mock_save.assert_called_once()
        
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('src.scrapers.jsa.scraper.JSAScraper')
    @patch('src.scrapers.newsapi.scraper.NewsAPIScraper')
    @patch('src.scrapers.reviewjournal.scraper.ReviewJournalScraper')
    def test_save_results(self, mock_rj_class, mock_newsapi_class, mock_jsa_class, mock_makedirs, mock_file):
        """Test saving aggregated results to CSV files."""
        # Setup mocks
        mock_jsa_class.return_value = self.mock_jsa
        mock_newsapi_class.return_value = self.mock_newsapi
        mock_rj_class.return_value = self.mock_reviewjournal
        
        # Create unified scraper with mocked components
        unified = UnifiedScraper()
        
        # Run scrapers
        results = unified.scrape_all(deep_check=False)
        
        # Verify directory creation
        mock_makedirs.assert_called_once()
        
        # Verify file was opened for each scraper
        assert mock_file.call_count >= 3