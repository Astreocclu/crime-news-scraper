import os
import sqlite3
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define database file path from environment variable or use default
DATABASE_FILE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crime_data.db'))

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    
    Returns:
    --------
    sqlite3.Connection or None
        Database connection object or None if connection fails
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

def initialize_database():
    """Creates the necessary tables if they don't already exist."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection for initialization")
        return False
        
    try:
        # Create articles table
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
        
        # Create analysis_results table
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
        except sqlite3.Error as e:
            logger.error(f"Error creating analysis_results table: {str(e)}")
            raise
        
        # Create index for faster lookups
        try:
            conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_analysis_article_id ON analysis_results (article_id)
            ''')
        except sqlite3.Error as e:
            logger.error(f"Error creating index: {str(e)}")
            raise
        
        # Commit all changes
        try:
            conn.commit()
            logger.info("Database initialized successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error committing database changes: {str(e)}")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()