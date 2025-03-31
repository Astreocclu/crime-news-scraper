"""Base scraper class that all scrapers will inherit from."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Article:
    """Data class to represent a scraped article"""
    title: str
    url: str
    date: str
    excerpt: str
    source: str
    city: str
    is_theft_related: bool
    is_business_related: bool
    keywords_found: List[str]

class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self._stop_requested = False
    
    @abstractmethod
    def scrape(self, deep_check: bool = True, max_deep_check: int = 20) -> Dict[str, List[Dict]]:
        """
        Scrape articles from the source
        
        Parameters:
        -----------
        deep_check : bool
            Whether to perform deep checking (fetching full articles)
        max_deep_check : int
            Maximum number of articles to deep check
            
        Returns:
        --------
        Dict[str, List[Dict]]
            Dictionary with locations as keys and lists of article dictionaries as values
        """
        pass
    
    def stop(self):
        """Request the scraper to stop gracefully"""
        self._stop_requested = True 