"""
Custom exception classes for the crime-news-scraper application.

This module defines application-specific exceptions to provide better error
handling and reporting throughout the codebase.
"""

class CrimeNewsScraperError(Exception):
    """Base exception class for all application-specific errors."""
    pass


class ScraperError(CrimeNewsScraperError):
    """Base exception for scraper-related errors."""
    pass


class ScraperInitializationError(ScraperError):
    """Exception raised when a scraper fails to initialize properly."""
    pass


class ScraperNetworkError(ScraperError):
    """Exception raised when a scraper encounters network-related issues."""
    pass


class ScraperParsingError(ScraperError):
    """Exception raised when a scraper fails to parse content."""
    pass


class AnalyzerError(CrimeNewsScraperError):
    """Base exception for analyzer-related errors."""
    pass


class AnalyzerAPIError(AnalyzerError):
    """Exception raised when there's an error communicating with the Claude API."""
    pass


class AnalyzerParsingError(AnalyzerError):
    """Exception raised when the analyzer fails to parse API responses."""
    pass


class NearbyFinderError(CrimeNewsScraperError):
    """Base exception for nearby finder related errors."""
    pass


class NearbyFinderAPIError(NearbyFinderError):
    """Exception raised when there's an error with the Google Maps API."""
    pass


class ConfigurationError(CrimeNewsScraperError):
    """Exception raised when there's an error in the configuration."""
    pass


class ValidationError(CrimeNewsScraperError):
    """Exception raised when data validation fails."""
    pass