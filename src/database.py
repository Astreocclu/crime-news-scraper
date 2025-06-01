"""
Crime News Scraper - Database Operations Module

This module provides database operations for the Crime News Scraper system,
including table creation, data storage, and retrieval operations.

The database schema supports:
- Article storage from multiple news sources
- AI-powered analysis results with comprehensive crime incident details
- Nearby business data with lead scoring for targeted business types
- Relationship tracking between articles, analysis, and nearby businesses

Database Tables:
    articles: Raw scraped news articles
    analysis_results: AI-analyzed crime incident data
    nearby_businesses: Target businesses near crime incidents

Target Business Types (Exclusive Focus):
    - Jewelry stores (primary target)
    - Sports memorabilia stores (secondary target)
    - Luxury goods stores (secondary target)

Author: Augment Agent
Version: 2.0.0
"""

"""
Standard library imports
"""
import os
import sqlite3
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple, Any

"""
Third-party imports
"""
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define database file path from environment variable or use default
DATABASE_FILE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crime_data.db'))

def get_db_connection() -> Optional[sqlite3.Connection]:
    """
    Establishes and returns a connection to the SQLite database.

    Returns:
        Optional[sqlite3.Connection]: Database connection object or None if connection fails
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error establishing database connection: {str(e)}")
        return None

def save_nearby_businesses(nearby_data_list: List[Dict[str, Union[str, int, float, bool]]]) -> bool:
    """
    Save nearby businesses to the database.

    This function stores nearby business data with lead scoring information,
    focusing exclusively on our three target business types:
    - Jewelry stores (primary target)
    - Sports memorabilia stores (secondary target)
    - Luxury goods stores (secondary target)

    Args:
        nearby_data_list: List of dictionaries containing nearby business data
                         Each dictionary should contain business information including
                         name, type, address, distance, and lead score

    Returns:
        bool: True if all businesses were saved successfully, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection for saving nearby businesses")
        return False

    try:
        cursor = conn.cursor()

        # Get the current timestamp
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Process each nearby business
        for nearby_data in nearby_data_list:
            # Extract the fields we want to save
            record_type = nearby_data.get('record_type', '')
            business_name = nearby_data.get('businessName', '')
            business_type = nearby_data.get('businessType', '')
            exact_address = nearby_data.get('exactAddress', '')
            distance = nearby_data.get('distance_from_incident', 0.0)
            lead_score = nearby_data.get('lead_score', 0)
            is_original = 1 if nearby_data.get('is_original_location', False) else 0

            # Get the analysis_id if available
            analysis_id = nearby_data.get('analysis_id', None)

            # Insert into the database
            cursor.execute('''
            INSERT INTO nearby_businesses
            (analysis_id, record_type, businessName, businessType, exactAddress,
             distance_from_incident, lead_score, is_original_location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (analysis_id, record_type, business_name, business_type, exact_address,
                  distance, lead_score, is_original, now))

        # Commit all insertions at once
        conn.commit()

        logger.info(f"Saved {len(nearby_data_list)} nearby businesses to database")
        return True

    except sqlite3.Error as e:
        logger.error(f"SQLite error saving nearby businesses: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving nearby businesses: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if conn:
            conn.close()

def initialize_database() -> bool:
    """
    Initialize the database by creating all necessary tables and indexes.

    Creates the complete database schema for the Crime News Scraper system:
    - articles: Raw scraped news articles from multiple sources
    - analysis_results: AI-analyzed crime incident data with comprehensive details
    - nearby_businesses: Target businesses near incidents with lead scoring

    The schema is optimized for our focused targeting approach, supporting
    efficient storage and retrieval of data for jewelry stores, sports
    memorabilia stores, and luxury goods stores.

    Returns:
        bool: True if database initialization was successful, False otherwise
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection for initialization")
        return False

    try:
        # Create all tables
        if not _create_articles_table(conn):
            return False
        if not _create_analysis_results_table(conn):
            return False
        if not _create_nearby_businesses_table(conn):
            return False

        # Commit all changes
        conn.commit()
        logger.info("Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()


def _create_articles_table(conn: sqlite3.Connection) -> bool:
    """Create the articles table."""
    try:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_name TEXT,
            location TEXT,
            title TEXT,
            article_date TEXT, -- Store as ISO format YYYY-MM-DD
            url TEXT UNIQUE NOT NULL, -- Ensure unique articles based on URL
            excerpt TEXT,
            source TEXT,
            keywords TEXT,
            is_theft_related INTEGER, -- Use 0 for False, 1 for True
            is_business_related INTEGER, -- Use 0 for False, 1 for True
            store_type TEXT,
            business_name TEXT,
            detailed_location TEXT,
            scraped_at TEXT NOT NULL -- Store as ISO format timestamp
        )
        ''')
        return True
    except sqlite3.Error as e:
        logger.error(f"Error creating articles table: {str(e)}")
        return False


def _create_analysis_results_table(conn: sqlite3.Connection) -> bool:
    """Create the analysis_results table and its indexes."""
    try:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL, -- Foreign key linking to articles table
            crimeType TEXT,
            method TEXT,
            target TEXT,
            storeType TEXT,
            businessName TEXT,
            detailedLocation TEXT,
            estimatedValue TEXT,
            numSuspects TEXT,
            characteristics TEXT,
            incidentDate TEXT, -- Store as ISO format YYYY-MM-DD
            dateOfArticle TEXT, -- Store as ISO format YYYY-MM-DD
            summary TEXT,
            valueScore INTEGER,
            recencyScore INTEGER,
            totalScore INTEGER,
            entryMethod TEXT,
            exactAddress TEXT,
            addressConfidence TEXT,
            businessNameConfidence TEXT,
            addressSource TEXT,
            businessInferenceReasoning TEXT,
            salesPitchHeadline TEXT,
            comparableIncident TEXT,
            riskAssessment TEXT,
            businessImpactScore INTEGER,
            businessImpactAreas TEXT,
            securityRecommendation TEXT,
            interestingFactForSales TEXT,
            analyzed_at TEXT NOT NULL, -- Store as ISO format timestamp
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
        ''')

        # Create index for faster lookups
        conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_analysis_article_id ON analysis_results (article_id)
        ''')

        return True
    except sqlite3.Error as e:
        logger.error(f"Error creating analysis_results table: {str(e)}")
        return False


def _create_nearby_businesses_table(conn: sqlite3.Connection) -> bool:
    """Create the nearby_businesses table and its indexes."""
    try:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS nearby_businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER, -- Foreign key linking to analysis_results table
            record_type TEXT, -- 'incident' or 'nearby'
            businessName TEXT,
            businessType TEXT,
            exactAddress TEXT,
            distance_from_incident REAL,
            lead_score INTEGER,
            is_original_location INTEGER, -- 0 for False, 1 for True
            latitude REAL,
            longitude REAL,
            created_at TEXT NOT NULL, -- Store as ISO format timestamp
            FOREIGN KEY (analysis_id) REFERENCES analysis_results (id)
        )
        ''')

        # Create index for faster lookups
        conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_nearby_analysis_id ON nearby_businesses (analysis_id)
        ''')

        return True
    except sqlite3.Error as e:
        logger.error(f"Error creating nearby_businesses table: {str(e)}")
        return False