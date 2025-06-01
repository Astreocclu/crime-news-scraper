"""
Tests for the Review Journal scraper module.

These tests verify the functionality of the Review Journal scraper, including:
- HTML parsing and article extraction
- Filtering for theft and business-related content
- Location detection for Nevada-focused content
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from src.scrapers.reviewjournal.scraper import ReviewJournalScraper
from src.scrapers.reviewjournal.utils import extract_keywords, is_business_related, detect_location
from src.utils.exceptions import ScraperNetworkError

class TestReviewJournalScraper:
    """Test suite for the Review Journal scraper."""

    def test_initialization(self):
        """Test that the scraper initializes correctly."""
        scraper = ReviewJournalScraper()
        assert scraper.name == "Las Vegas Review Journal"
        assert scraper.url == "https://www.reviewjournal.com/crime/"
        assert "Nevada" in scraper.monitored_locations

    @patch.object(ReviewJournalScraper, 'fetch_page')
    @patch.object(ReviewJournalScraper, 'setup_driver')
    @patch.object(ReviewJournalScraper, 'scroll_to_load_more')
    def test_scrape_crime_news(self, mock_scroll, mock_setup, mock_fetch):
        """Test crime news scraping functionality."""
        # Setup mocks
        mock_setup.return_value = MagicMock()

        # Create a mock HTML response with sample articles
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'html')
        mock_html_path = os.path.join(fixtures_dir, 'reviewjournal_sample.html')

        # If fixture exists, use it, otherwise use a simple mock HTML
        if os.path.exists(mock_html_path):
            with open(mock_html_path, 'r', encoding='utf-8') as f:
                mock_html = f.read()
        else:
            mock_html = """
            <html>
            <body>
                <a href="/crime/test-article-1/" class="test-link">Jewelry Store Robbery in Las Vegas</a>
                <time>March 15, 2025</time>
                <p>A jewelry store was robbed in downtown Las Vegas yesterday.</p>

                <a href="/crime/test-article-2/" class="test-link">Non-theft related news</a>
                <time>March 16, 2025</time>
                <p>Some other news not related to theft.</p>
            </body>
            </html>
            """

            # Save the mock HTML for future use
            os.makedirs(fixtures_dir, exist_ok=True)
            with open(mock_html_path, 'w', encoding='utf-8') as f:
                f.write(mock_html)

        # Set up the mock to return our sample HTML
        mock_fetch.return_value = mock_html
        scraper = ReviewJournalScraper()
        scraper.driver = MagicMock()
        scraper.driver.page_source = mock_html

        # Run the scraper
        results = scraper.scrape_crime_news()

        # Verify results
        assert "Nevada" in results
        assert len(results["Nevada"]) > 0

    def test_utility_functions(self):
        """Test the utility functions used by the Review Journal scraper."""
        # Test keyword extraction
        test_text = "There was a jewelry store robbery in Las Vegas."
        keywords = extract_keywords(test_text)
        assert "jewelry" in keywords
        assert "robbery" in keywords
        # Las Vegas is detected by the location detection function, not keywords
        location = detect_location(test_text)
        assert location == "Nevada"

        # Test business relevance detection
        assert is_business_related(test_text) is True

        # Test location detection (should prioritize Nevada for Review Journal)
        assert detect_location(test_text) == "Nevada"