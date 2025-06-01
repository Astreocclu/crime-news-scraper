#!/usr/bin/env python3
"""
Performance test script for the crime-news-scraper workflow.

This script tests the system performance with larger datasets to identify
bottlenecks and validate scalability requirements.
"""

import os
import sys
import logging
import time
import psutil
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import main as run_main
from src.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_performance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor system performance during testing."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
        
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        self.start_cpu = psutil.cpu_percent()
        logger.info(f"Performance monitoring started - Memory: {self.start_memory:.1f}MB, CPU: {self.start_cpu:.1f}%")
        
    def get_current_stats(self):
        """Get current performance statistics."""
        current_time = time.time()
        current_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        current_cpu = psutil.cpu_percent()
        
        elapsed_time = current_time - self.start_time if self.start_time else 0
        memory_delta = current_memory - self.start_memory if self.start_memory else 0
        
        return {
            'elapsed_time': elapsed_time,
            'current_memory': current_memory,
            'memory_delta': memory_delta,
            'current_cpu': current_cpu
        }
        
    def log_stats(self, prefix=""):
        """Log current performance statistics."""
        stats = self.get_current_stats()
        logger.info(f"{prefix}Elapsed: {stats['elapsed_time']:.1f}s, "
                   f"Memory: {stats['current_memory']:.1f}MB (+{stats['memory_delta']:.1f}MB), "
                   f"CPU: {stats['current_cpu']:.1f}%")

def check_database_state():
    """Check the current state of the database."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return None
            
        cursor = conn.cursor()
        
        # Check articles count
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        # Check unanalyzed articles
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE id NOT IN (SELECT article_id FROM analysis_results)
        """)
        unanalyzed_count = cursor.fetchone()[0]
        
        # Check analysis results count
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        analysis_count = cursor.fetchone()[0]
        
        # Check nearby businesses count
        cursor.execute("SELECT COUNT(*) FROM nearby_businesses")
        nearby_count = cursor.fetchone()[0]
        
        state = {
            'articles': articles_count,
            'unanalyzed': unanalyzed_count,
            'analysis_results': analysis_count,
            'nearby_businesses': nearby_count
        }
        
        logger.info(f"Database state: {articles_count} articles ({unanalyzed_count} unanalyzed), "
                   f"{analysis_count} analysis results, {nearby_count} nearby businesses")
        
        conn.close()
        return state
        
    except Exception as e:
        logger.error(f"Error checking database state: {str(e)}")
        return None

def test_performance_batch(batch_size, max_runtime_minutes=15):
    """Test performance with a specific batch size."""
    logger.info(f"Starting performance test with batch size: {batch_size}")
    
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Check initial database state
    initial_state = check_database_state()
    if not initial_state:
        return False
    
    if initial_state['unanalyzed'] < batch_size:
        logger.warning(f"Only {initial_state['unanalyzed']} unanalyzed articles available, "
                      f"but requested batch size is {batch_size}")
        batch_size = initial_state['unanalyzed']
        if batch_size == 0:
            logger.info("No unanalyzed articles available for testing")
            return True
    
    # Test parameters
    test_args = [
        'src/main.py',
        '--use-database',
        '--max-runtime', str(max_runtime_minutes),
        'workflow',
        '--no-scrape',  # Skip scraping to use existing data
    ]
    
    # Override sys.argv for the test
    original_argv = sys.argv
    sys.argv = test_args
    
    try:
        logger.info(f"Starting workflow test with {batch_size} articles (max runtime: {max_runtime_minutes} min)")
        
        # Run the main workflow
        result = run_main()
        
        # Log final performance stats
        monitor.log_stats("Final stats - ")
        
        # Check final database state
        final_state = check_database_state()
        if not final_state:
            return False
        
        # Calculate processing metrics
        articles_processed = final_state['analysis_results'] - initial_state['analysis_results']
        businesses_found = final_state['nearby_businesses'] - initial_state['nearby_businesses']
        
        stats = monitor.get_current_stats()
        processing_time = stats['elapsed_time']
        
        # Log performance summary
        logger.info("=" * 60)
        logger.info("PERFORMANCE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Articles processed: {articles_processed}")
        logger.info(f"Nearby businesses found: {businesses_found}")
        logger.info(f"Total processing time: {processing_time:.1f} seconds")
        logger.info(f"Average time per article: {processing_time/max(articles_processed, 1):.1f} seconds")
        logger.info(f"Memory usage delta: {stats['memory_delta']:.1f} MB")
        logger.info(f"Peak CPU usage: {stats['current_cpu']:.1f}%")
        
        # Performance benchmarks
        if articles_processed > 0:
            time_per_article = processing_time / articles_processed
            if time_per_article < 20:  # Less than 20 seconds per article
                logger.info("✅ EXCELLENT performance - under 20s per article")
            elif time_per_article < 60:  # Less than 1 minute per article
                logger.info("✅ GOOD performance - under 1 minute per article")
            else:
                logger.warning("⚠️ SLOW performance - over 1 minute per article")
        
        if stats['memory_delta'] < 100:  # Less than 100MB increase
            logger.info("✅ EXCELLENT memory efficiency")
        elif stats['memory_delta'] < 500:  # Less than 500MB increase
            logger.info("✅ GOOD memory efficiency")
        else:
            logger.warning("⚠️ HIGH memory usage")
        
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error during performance test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

def main():
    """Main entry point for the performance test script."""
    logger.info("=" * 60)
    logger.info("CRIME NEWS SCRAPER - PERFORMANCE TEST")
    logger.info("=" * 60)
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    # Test different batch sizes
    test_scenarios = [
        {'batch_size': 20, 'max_runtime': 10},  # Medium test
        {'batch_size': 50, 'max_runtime': 20},  # Large test
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n{'='*20} TEST SCENARIO {i} {'='*20}")
        success = test_performance_batch(
            batch_size=scenario['batch_size'],
            max_runtime_minutes=scenario['max_runtime']
        )
        
        if success:
            logger.info(f"✅ Test scenario {i} PASSED")
        else:
            logger.error(f"❌ Test scenario {i} FAILED")
            all_passed = False
        
        # Wait between tests
        if i < len(test_scenarios):
            logger.info("Waiting 30 seconds before next test...")
            time.sleep(30)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✅ ALL PERFORMANCE TESTS PASSED")
        return 0
    else:
        logger.error("❌ SOME PERFORMANCE TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
