"""
Test configuration and fixtures for the Crime News Scraper project.

This file contains shared pytest fixtures and configuration for all tests.
"""

import os
import pytest
from datetime import datetime
import tempfile
import json

# Define fixture directories
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# Ensure fixture directories exist
os.makedirs(FIXTURE_DIR, exist_ok=True)
os.makedirs(os.path.join(FIXTURE_DIR, 'html'), exist_ok=True)
os.makedirs(os.path.join(FIXTURE_DIR, 'json'), exist_ok=True)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for test results."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_article():
    """Return a sample article dict for testing."""
    return {
        "title": "Jewelry Store Robbery in Test Location",
        "url": "https://example.com/test-article",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "excerpt": "Test excerpt about a jewelry store robbery for testing purposes.",
        "source": "Test Source",
        "keywords": ["jewelry", "robbery", "theft"],
        "is_theft_related": True,
        "is_business_related": True,
        "store_type": "Jewelry Store",
        "location": "Nevada"
    }

@pytest.fixture
def mock_response():
    """Return a mock response for API testing."""
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.text = json.dumps(json_data)
            
        def json(self):
            return self.json_data
            
    return MockResponse

@pytest.fixture
def newsapi_mock_data():
    """Return mock NewsAPI response data."""
    return {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "source": {"id": "test-source", "name": "Test News"},
                "author": "Test Author",
                "title": "Jewelry Store Robbery in Las Vegas",
                "description": "A jewelry store in Las Vegas was robbed yesterday.",
                "url": "https://example.com/vegas-robbery",
                "urlToImage": "https://example.com/image.jpg",
                "publishedAt": "2025-03-15T15:30:00Z",
                "content": "Full article content about the jewelry store robbery in Las Vegas."
            },
            {
                "source": {"id": "test-source2", "name": "Test News 2"},
                "author": "Another Author",
                "title": "Smash and Grab at Texas Luxury Store",
                "description": "Thieves targeted a luxury store in Dallas, Texas.",
                "url": "https://example.com/texas-theft",
                "urlToImage": "https://example.com/image2.jpg",
                "publishedAt": "2025-03-14T12:15:00Z",
                "content": "Full article content about the luxury store theft in Dallas, Texas."
            }
        ]
    }