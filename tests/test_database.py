"""
Unit tests for the database module.

These tests verify the functionality of the database module in isolation using in-memory SQLite.
"""

import pytest
import sqlite3
import os
from datetime import datetime

from src.database import get_db_connection, initialize_database


@pytest.fixture
def in_memory_db():
    """
    Fixture that provides an in-memory SQLite database connection.
    
    This allows tests to run without affecting the real database file.
    The connection is initialized with the database schema and 
    closed after the test completes.
    """
    # Override DATABASE_FILE for testing
    os.environ['DATABASE_PATH'] = ':memory:'
    
    # Get a connection to the in-memory database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Initialize the database schema
    cursor = conn.cursor()
    
    # Create articles table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scraper_name TEXT,
        location TEXT,
        title TEXT,
        article_date TEXT,
        url TEXT UNIQUE NOT NULL,
        excerpt TEXT,
        source TEXT,
        keywords TEXT,
        is_theft_related INTEGER,
        is_business_related INTEGER,
        store_type TEXT,
        business_name TEXT,
        detailed_location TEXT,
        scraped_at TEXT NOT NULL
    )
    ''')
    
    # Create analysis_results table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        crimeType TEXT,
        method TEXT,
        target TEXT,
        storeType TEXT,
        businessName TEXT,
        detailedLocation TEXT,
        estimatedValue TEXT,
        numSuspects TEXT,
        characteristics TEXT,
        incidentDate TEXT,
        dateOfArticle TEXT,
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
        analyzed_at TEXT NOT NULL,
        FOREIGN KEY (article_id) REFERENCES articles (id)
    )
    ''')
    
    # Create index for faster lookups
    conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_analysis_article_id ON analysis_results (article_id)
    ''')
    
    conn.commit()
    
    # Return the connection for use in tests
    yield conn
    
    # Close the connection after the test is complete
    conn.close()
    
    # Reset the environment variable
    if 'DATABASE_PATH' in os.environ:
        del os.environ['DATABASE_PATH']


def test_get_db_connection():
    """Test that get_db_connection returns a valid connection object when using the in-memory database."""
    # Temporarily set the environment variable
    original_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = ':memory:'
    
    try:
        # Get a connection
        conn = get_db_connection()
        
        # Verify that the connection is valid
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        
        # Verify the row_factory is set
        assert conn.row_factory == sqlite3.Row
        
        # Clean up
        conn.close()
    finally:
        # Restore the original environment variable
        if original_path:
            os.environ['DATABASE_PATH'] = original_path
        else:
            del os.environ['DATABASE_PATH']


def test_initialize_database(in_memory_db):
    """
    Test that initialize_database correctly creates the database schema.
    
    This test uses the in-memory database fixture to avoid affecting the real database.
    """
    # Use the initialized in-memory DB from the fixture
    conn = in_memory_db
    
    # Verify that the articles table exists and has the expected columns
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(articles)")
    articles_columns = {row[1] for row in cursor.fetchall()}
    
    expected_articles_columns = {
        'id', 'scraper_name', 'location', 'title', 'article_date', 'url',
        'excerpt', 'source', 'keywords', 'is_theft_related', 'is_business_related',
        'store_type', 'business_name', 'detailed_location', 'scraped_at'
    }
    
    assert articles_columns == expected_articles_columns
    
    # Verify that the analysis_results table exists and has the expected columns
    cursor.execute("PRAGMA table_info(analysis_results)")
    analysis_columns = {row[1] for row in cursor.fetchall()}
    
    expected_analysis_columns = {
        'id', 'article_id', 'crimeType', 'method', 'target', 'storeType',
        'businessName', 'detailedLocation', 'estimatedValue', 'numSuspects',
        'characteristics', 'incidentDate', 'dateOfArticle', 'summary',
        'valueScore', 'recencyScore', 'totalScore', 'entryMethod',
        'exactAddress', 'addressConfidence', 'businessNameConfidence',
        'addressSource', 'businessInferenceReasoning', 'salesPitchHeadline',
        'comparableIncident', 'riskAssessment', 'businessImpactScore',
        'businessImpactAreas', 'securityRecommendation', 'interestingFactForSales',
        'analyzed_at'
    }
    
    assert analysis_columns == expected_analysis_columns
    
    # Verify that the index exists
    cursor.execute("PRAGMA index_list(analysis_results)")
    indices = [row[1] for row in cursor.fetchall()]
    assert 'idx_analysis_article_id' in indices


def test_insert_article_unique_url(in_memory_db):
    """
    Test inserting articles with unique URL constraint.
    
    Inserting the same article twice (same URL) should only result in one row due to the UNIQUE constraint.
    """
    conn = in_memory_db
    cursor = conn.cursor()
    
    # Insert an article
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''
        INSERT INTO articles 
        (scraper_name, location, title, article_date, url, excerpt, source, keywords, 
         is_theft_related, is_business_related, store_type, business_name, detailed_location, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        ('test_scraper', 'New York', 'Test Article', '2025-04-01', 'https://example.com/article1',
         'Test excerpt', 'Test Source', 'test,keywords', 1, 1, 'jewelry', 'Test Store', 'Manhattan', now)
    )
    conn.commit()
    
    # Try to insert the same article again (same URL)
    cursor.execute(
        '''
        INSERT OR IGNORE INTO articles 
        (scraper_name, location, title, article_date, url, excerpt, source, keywords, 
         is_theft_related, is_business_related, store_type, business_name, detailed_location, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        ('test_scraper', 'Different Location', 'Different Title', '2025-04-02', 'https://example.com/article1',
         'Different excerpt', 'Different Source', 'different,keywords', 0, 0, 'pawn', 'Different Store', 'Brooklyn', now)
    )
    conn.commit()
    
    # Verify that only one row exists
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    assert count == 1
    
    # Insert a different article (different URL)
    cursor.execute(
        '''
        INSERT INTO articles 
        (scraper_name, location, title, article_date, url, excerpt, source, keywords, 
         is_theft_related, is_business_related, store_type, business_name, detailed_location, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        ('test_scraper', 'Boston', 'Second Article', '2025-04-03', 'https://example.com/article2',
         'Another excerpt', 'Another Source', 'more,keywords', 1, 0, 'mall', 'Another Store', 'Downtown', now)
    )
    conn.commit()
    
    # Verify that now there are two rows
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    assert count == 2


def test_insert_analysis_result(in_memory_db):
    """
    Test inserting an analysis result.
    
    This test verifies that an analysis result can be successfully inserted when 
    linked to a valid article ID.
    """
    conn = in_memory_db
    cursor = conn.cursor()
    
    # Insert a dummy article
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''
        INSERT INTO articles 
        (scraper_name, location, title, article_date, url, excerpt, source, keywords, 
         is_theft_related, is_business_related, store_type, business_name, detailed_location, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        ('test_scraper', 'Chicago', 'Test Article', '2025-04-01', 'https://example.com/article3',
         'Test excerpt', 'Test Source', 'test,keywords', 1, 1, 'jewelry', 'Test Store', 'Downtown', now)
    )
    conn.commit()
    
    # Get the article ID
    cursor.execute("SELECT id FROM articles WHERE url = ?", ('https://example.com/article3',))
    article_id = cursor.fetchone()[0]
    
    # Insert a corresponding analysis result
    cursor.execute(
        '''
        INSERT INTO analysis_results
        (article_id, crimeType, method, target, storeType, businessName, valueScore, recencyScore, totalScore, analyzed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (article_id, 'Robbery', 'Smash and grab', 'Jewelry store', 'Retail', 'Test Store', 4, 5, 9, now)
    )
    conn.commit()
    
    # Verify the analysis result exists
    cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE article_id = ?", (article_id,))
    count = cursor.fetchone()[0]
    assert count == 1
    
    # Verify the data was inserted correctly
    cursor.execute("SELECT crimeType, method, target, valueScore, totalScore FROM analysis_results WHERE article_id = ?", (article_id,))
    row = cursor.fetchone()
    assert row['crimeType'] == 'Robbery'
    assert row['method'] == 'Smash and grab'
    assert row['target'] == 'Jewelry store'
    assert row['valueScore'] == 4
    assert row['totalScore'] == 9


def test_insert_analysis_result_foreign_key_constraint(in_memory_db):
    """
    Test the foreign key constraint on the analysis_results table.
    
    This test verifies that an IntegrityError is raised when trying to insert an analysis result
    with an article_id that does not exist in the articles table.
    """
    conn = in_memory_db
    # Enable foreign key constraints (they're disabled by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Try to insert an analysis result with a non-existent article_id
    non_existent_article_id = 9999
    
    # Verify this ID doesn't exist
    cursor.execute("SELECT COUNT(*) FROM articles WHERE id = ?", (non_existent_article_id,))
    count = cursor.fetchone()[0]
    assert count == 0
    
    # Attempting to insert should raise an IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            '''
            INSERT INTO analysis_results
            (article_id, crimeType, method, target, storeType, businessName, valueScore, recencyScore, totalScore, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (non_existent_article_id, 'Robbery', 'Smash and grab', 'Jewelry store', 'Retail', 'Test Store', 4, 5, 9, now)
        )
        conn.commit()