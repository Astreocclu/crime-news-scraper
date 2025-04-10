"""
Analyzer module for crime news articles with database operations.

This module encapsulates the database interaction logic for the analyzer component.
"""

import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..database import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)

def get_unanalyzed_articles(db_conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve articles from the database that have not been analyzed yet.

    Parameters:
    -----------
    db_conn : sqlite3.Connection
        Database connection object
    limit : int, optional
        Maximum number of articles to retrieve (default: 10)

    Returns:
    --------
    List[Dict[str, Any]]
        List of unanalyzed articles as dictionaries
    """
    try:
        cursor = db_conn.cursor()
        
        # Query to find unanalyzed articles
        sql = '''
        SELECT a.* FROM articles a
        LEFT JOIN analysis_results ar ON a.id = ar.article_id
        WHERE ar.id IS NULL
        LIMIT ?
        '''
        
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No unanalyzed articles found in the database")
            return []
            
        # Convert to list of dictionaries
        articles = []
        for row in rows:
            article = dict(row)  # sqlite3.Row objects support dict conversion
            
            # Convert integer flags back to boolean for processing
            article['is_theft_related'] = bool(article.get('is_theft_related', 0))
            article['is_business_related'] = bool(article.get('is_business_related', 0))
            
            # Map database column names to expected dictionary keys
            # Database has article_date, but code expects 'date'
            article['date'] = article.get('article_date')
            articles.append(article)
            
        logger.info(f"Found {len(articles)} unanalyzed articles in the database")
        return articles
        
    except sqlite3.Error as e:
        logger.error(f"Error getting unanalyzed articles: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving unanalyzed articles: {str(e)}")
        return []

def save_analysis_results(db_conn: sqlite3.Connection, results: List[Dict[str, Any]]) -> bool:
    """
    Save analysis results to the database.

    Parameters:
    -----------
    db_conn : sqlite3.Connection
        Database connection object
    results : List[Dict[str, Any]]
        List of analysis results to save

    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    if not results:
        logger.info("No analysis results to save to database")
        return True
        
    try:
        cursor = db_conn.cursor()
        
        for analysis in results:
            # Only process analyses that have an article_id
            if not analysis.get('article_id'):
                logger.warning(f"Skipping analysis with missing article_id: {analysis}")
                continue
                
            # Ensure the analyzed_at timestamp is set
            if 'analyzed_at' not in analysis or not analysis['analyzed_at']:
                analysis['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            # Generate the list of field names dynamically from the schema
            cursor.execute("PRAGMA table_info(analysis_results)")
            columns = [row[1] for row in cursor.fetchall()]
            columns = [col for col in columns if col != 'id']  # Remove the ID column since it's auto-generated
            
            # Extract values from analysis dictionary, using None for missing fields
            values = []
            for col in columns:
                # Convert empty strings to None for the database
                val = analysis.get(col, None)
                if val == '':
                    val = None
                values.append(val)
            
            # Construct placeholders for SQL query
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)
            
            # SQL statement
            sql = f'''
            INSERT INTO analysis_results 
            ({columns_str})
            VALUES ({placeholders})
            '''
            
            # Execute the insert
            cursor.execute(sql, values)
        
        # Commit all insertions at once
        db_conn.commit()
        
        logger.info(f"Saved {len(results)} analysis results to database")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error saving analysis results: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving analysis results: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False