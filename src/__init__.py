"""
Crime News Scraper - Main Package

A comprehensive system for scraping crime news articles, analyzing incidents,
and finding nearby businesses for security lead generation.

This package provides:
- News scraping from multiple sources
- AI-powered crime incident analysis
- Address validation and geocoding
- Nearby business discovery with lead scoring
- Focused targeting on jewelry stores, sports memorabilia, and luxury goods

Modules:
    analyzer: Crime incident analysis using Claude AI
    nearby_finder: Targeted business discovery and lead scoring
    scrapers: News source scraping modules
    address_finder: Address validation and geocoding
    utils: Shared utilities and helpers
    database: Database operations and schema management
    main: Command-line interface and workflow orchestration

Author: Augment Agent
Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__author__ = "Augment Agent"
__license__ = "MIT"

# Package metadata
__all__ = [
    "analyzer",
    "nearby_finder",
    "scrapers",
    "address_finder",
    "utils",
    "database",
    "main"
]
