#!/usr/bin/env python3
"""
Test script to verify the focused search is working correctly.
This script tests that we only find jewelry stores, luxury goods stores, 
and sports memorabilia stores.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nearby_finder.finder import NearbyBusinessFinder
from src.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_focused_search():
    """Test that our search only returns target business types."""
    logger.info("Testing focused search for target business types only...")
    
    # Get the most recent analysis file
    output_dir = 'output'
    analysis_files = []
    
    for file in os.listdir(output_dir):
        if file.startswith('analyzed_leads_') and file.endswith('.csv'):
            analysis_files.append(file)
    
    if not analysis_files:
        logger.error("No analysis files found for testing")
        return False
    
    latest_analysis = max(analysis_files)
    analysis_path = os.path.join(output_dir, latest_analysis)
    
    logger.info(f"Using analysis file: {analysis_path}")
    
    # Initialize the finder
    finder = NearbyBusinessFinder()
    
    # Run the finder on a small subset
    logger.info("Running focused nearby business search...")
    success = finder.find_nearby_businesses(analysis_path)
    
    if not success:
        logger.error("Nearby business search failed")
        return False
    
    # Check the results in the database
    logger.info("Validating search results...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get business type breakdown
        cursor.execute("""
            SELECT businessType, COUNT(*) 
            FROM nearby_businesses 
            WHERE created_at >= datetime('now', '-1 hour')
            GROUP BY businessType 
            ORDER BY COUNT(*) DESC
        """)
        type_breakdown = cursor.fetchall()
        
        logger.info("Business types found in recent search:")
        target_types = ['jewelry', 'luxury_goods', 'sports_memorabilia']
        target_found = 0
        non_target_found = 0
        
        for business_type, count in type_breakdown:
            logger.info(f"  {business_type}: {count} businesses")
            
            if business_type in target_types:
                target_found += count
            elif business_type and business_type != '':
                non_target_found += count
                logger.warning(f"  ⚠️ NON-TARGET TYPE FOUND: {business_type}")
        
        # Summary
        total_found = target_found + non_target_found
        logger.info(f"\nSUMMARY:")
        logger.info(f"  Target businesses found: {target_found}")
        logger.info(f"  Non-target businesses found: {non_target_found}")
        logger.info(f"  Total businesses found: {total_found}")
        
        if non_target_found == 0:
            logger.info("✅ SUCCESS: Only target business types found!")
            success_rate = 100.0
        else:
            success_rate = (target_found / total_found * 100) if total_found > 0 else 0
            logger.warning(f"⚠️ PARTIAL SUCCESS: {success_rate:.1f}% target businesses")
        
        # Check lead scores
        cursor.execute("""
            SELECT lead_score, COUNT(*) 
            FROM nearby_businesses 
            WHERE created_at >= datetime('now', '-1 hour')
            GROUP BY lead_score 
            ORDER BY lead_score DESC
        """)
        score_breakdown = cursor.fetchall()
        
        logger.info(f"\nLead score distribution:")
        high_quality_leads = 0
        total_leads = 0
        
        for score, count in score_breakdown:
            logger.info(f"  Score {score}: {count} businesses")
            total_leads += count
            if score >= 5:
                high_quality_leads += count
        
        if total_leads > 0:
            quality_rate = (high_quality_leads / total_leads) * 100
            logger.info(f"  High-quality leads (score ≥5): {high_quality_leads}/{total_leads} ({quality_rate:.1f}%)")
        
        conn.close()
        
        # Return success if we only found target types
        return non_target_found == 0
        
    except Exception as e:
        logger.error(f"Error validating results: {str(e)}")
        return False

def main():
    """Main entry point for the focused search test."""
    logger.info("=" * 60)
    logger.info("FOCUSED SEARCH TEST - TARGET BUSINESS TYPES ONLY")
    logger.info("=" * 60)
    logger.info("Testing that we only find:")
    logger.info("1. Jewelry stores (primary target)")
    logger.info("2. Luxury goods stores (secondary target)")
    logger.info("3. Sports memorabilia stores (secondary target)")
    logger.info("=" * 60)
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    success = test_focused_search()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ FOCUSED SEARCH TEST PASSED")
        logger.info("Only target business types were found!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ FOCUSED SEARCH TEST FAILED")
        logger.error("Non-target business types were found!")
        logger.error("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
