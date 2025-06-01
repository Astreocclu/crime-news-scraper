#!/usr/bin/env python3
"""
Production data validation script for the crime-news-scraper.

This script validates the quality and completeness of production data
to ensure it meets business requirements and data quality standards.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
import sqlite3

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Comprehensive data validation for production data."""
    
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
    def validate_database_integrity(self):
        """Validate database structure and data integrity."""
        logger.info("Validating database integrity...")
        
        try:
            conn = get_db_connection()
            if not conn:
                self.errors.append("Failed to connect to database")
                return False
                
            cursor = conn.cursor()
            
            # Check table existence
            tables = ['articles', 'analysis_results', 'nearby_businesses']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.validation_results[f'{table}_count'] = count
                logger.info(f"Table {table}: {count} records")
                
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE article_id NOT IN (SELECT id FROM articles)
            """)
            orphaned_analysis = cursor.fetchone()[0]
            if orphaned_analysis > 0:
                self.errors.append(f"Found {orphaned_analysis} orphaned analysis records")
            
            # Check for missing analysis
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE id NOT IN (SELECT article_id FROM analysis_results)
            """)
            missing_analysis = cursor.fetchone()[0]
            self.validation_results['unanalyzed_articles'] = missing_analysis
            logger.info(f"Unanalyzed articles: {missing_analysis}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.errors.append(f"Database validation error: {str(e)}")
            return False
    
    def validate_address_completeness(self):
        """Validate address completeness in analysis results."""
        logger.info("Validating address completeness...")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check for complete addresses
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE exactAddress IS NOT NULL 
                AND exactAddress != '' 
                AND exactAddress != 'Not available'
                AND exactAddress != 'insufficient information'
                AND exactAddress != 'Not applicable'
            """)
            complete_addresses = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            total_analysis = cursor.fetchone()[0]
            
            if total_analysis > 0:
                completeness_rate = (complete_addresses / total_analysis) * 100
                self.validation_results['address_completeness_rate'] = completeness_rate
                logger.info(f"Address completeness: {complete_addresses}/{total_analysis} ({completeness_rate:.1f}%)")
                
                if completeness_rate < 80:
                    self.warnings.append(f"Address completeness rate ({completeness_rate:.1f}%) below 80% target")
                elif completeness_rate >= 95:
                    logger.info("✅ EXCELLENT address completeness rate")
            
            # Check address confidence levels
            cursor.execute("""
                SELECT addressConfidence, COUNT(*) 
                FROM analysis_results 
                WHERE addressConfidence IS NOT NULL
                GROUP BY addressConfidence
            """)
            confidence_breakdown = cursor.fetchall()
            
            for confidence, count in confidence_breakdown:
                logger.info(f"Address confidence '{confidence}': {count} records")
                self.validation_results[f'address_confidence_{confidence}'] = count
            
            conn.close()
            return True
            
        except Exception as e:
            self.errors.append(f"Address validation error: {str(e)}")
            return False
    
    def validate_business_name_quality(self):
        """Validate business name inference quality."""
        logger.info("Validating business name quality...")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check for inferred business names
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE businessName IS NOT NULL 
                AND businessName != '' 
                AND businessName != 'Not specified'
                AND businessName != 'Not available'
            """)
            named_businesses = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            total_analysis = cursor.fetchone()[0]
            
            if total_analysis > 0:
                naming_rate = (named_businesses / total_analysis) * 100
                self.validation_results['business_naming_rate'] = naming_rate
                logger.info(f"Business naming: {named_businesses}/{total_analysis} ({naming_rate:.1f}%)")
            
            # Check business name confidence levels
            cursor.execute("""
                SELECT businessNameConfidence, COUNT(*) 
                FROM analysis_results 
                WHERE businessNameConfidence IS NOT NULL
                GROUP BY businessNameConfidence
            """)
            confidence_breakdown = cursor.fetchall()
            
            for confidence, count in confidence_breakdown:
                logger.info(f"Business name confidence '{confidence}': {count} records")
                self.validation_results[f'business_name_confidence_{confidence}'] = count
            
            conn.close()
            return True
            
        except Exception as e:
            self.errors.append(f"Business name validation error: {str(e)}")
            return False
    
    def validate_lead_quality(self):
        """Validate nearby business lead quality."""
        logger.info("Validating lead quality...")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check lead score distribution
            cursor.execute("""
                SELECT lead_score, COUNT(*)
                FROM nearby_businesses
                GROUP BY lead_score
                ORDER BY lead_score DESC
            """)
            score_breakdown = cursor.fetchall()
            
            total_leads = 0
            high_quality_leads = 0
            
            for score, count in score_breakdown:
                logger.info(f"Lead score {score}: {count} businesses")
                self.validation_results[f'lead_score_{score}'] = count
                total_leads += count
                if score >= 5:
                    high_quality_leads += count
            
            if total_leads > 0:
                quality_rate = (high_quality_leads / total_leads) * 100
                self.validation_results['high_quality_lead_rate'] = quality_rate
                logger.info(f"High-quality leads (score ≥5): {high_quality_leads}/{total_leads} ({quality_rate:.1f}%)")
            
            # Check business type distribution
            cursor.execute("""
                SELECT businessType, COUNT(*) 
                FROM nearby_businesses 
                GROUP BY businessType 
                ORDER BY COUNT(*) DESC
            """)
            type_breakdown = cursor.fetchall()
            
            for business_type, count in type_breakdown:
                logger.info(f"Business type '{business_type}': {count} businesses")
                self.validation_results[f'business_type_{business_type}'] = count

            # Validate that we only have our three target business types
            target_types = ['jewelry', 'luxury_goods', 'sports_memorabilia']
            non_target_types = [bt for bt, _ in type_breakdown if bt not in target_types and bt != '']

            if non_target_types:
                self.warnings.append(f"Found non-target business types: {non_target_types}")
            else:
                logger.info("✅ EXCELLENT - Only target business types found")
            
            conn.close()
            return True
            
        except Exception as e:
            self.errors.append(f"Lead quality validation error: {str(e)}")
            return False
    
    def validate_output_files(self):
        """Validate output file quality and format."""
        logger.info("Validating output files...")
        
        try:
            output_dir = 'output'
            if not os.path.exists(output_dir):
                self.errors.append("Output directory does not exist")
                return False
            
            # Check for recent analysis files
            analysis_files = []
            for file in os.listdir(output_dir):
                if file.startswith('analyzed_leads_') and file.endswith('.csv'):
                    analysis_files.append(file)
            
            if not analysis_files:
                self.warnings.append("No analysis output files found")
            else:
                latest_analysis = max(analysis_files)
                analysis_path = os.path.join(output_dir, latest_analysis)
                
                # Validate analysis file format
                df = pd.read_csv(analysis_path)
                required_columns = ['businessName', 'detailedLocation', 'exactAddress', 'addressConfidence']
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    self.errors.append(f"Missing columns in analysis file: {missing_columns}")
                else:
                    logger.info(f"✅ Analysis file format valid: {latest_analysis}")
                    self.validation_results['latest_analysis_file'] = latest_analysis
                    self.validation_results['analysis_records'] = len(df)
            
            # Check for nearby business files
            nearby_dir = os.path.join(output_dir, 'nearby')
            if os.path.exists(nearby_dir):
                nearby_files = [f for f in os.listdir(nearby_dir) if f.endswith('.csv')]
                if nearby_files:
                    latest_nearby = max(nearby_files)
                    nearby_path = os.path.join(nearby_dir, latest_nearby)
                    
                    df = pd.read_csv(nearby_path)
                    logger.info(f"✅ Nearby businesses file valid: {latest_nearby}")
                    self.validation_results['latest_nearby_file'] = latest_nearby
                    self.validation_results['nearby_records'] = len(df)
            
            return True
            
        except Exception as e:
            self.errors.append(f"Output file validation error: {str(e)}")
            return False
    
    def generate_validation_report(self):
        """Generate comprehensive validation report."""
        logger.info("Generating validation report...")
        
        report_lines = [
            "=" * 80,
            "PRODUCTION DATA VALIDATION REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "VALIDATION RESULTS:",
        ]
        
        for key, value in self.validation_results.items():
            report_lines.append(f"  {key}: {value}")
        
        if self.errors:
            report_lines.extend([
                "",
                "ERRORS FOUND:",
            ])
            for error in self.errors:
                report_lines.append(f"  ❌ {error}")
        
        if self.warnings:
            report_lines.extend([
                "",
                "WARNINGS:",
            ])
            for warning in self.warnings:
                report_lines.append(f"  ⚠️ {warning}")
        
        if not self.errors and not self.warnings:
            report_lines.extend([
                "",
                "✅ ALL VALIDATIONS PASSED - PRODUCTION READY",
            ])
        elif not self.errors:
            report_lines.extend([
                "",
                "✅ NO CRITICAL ERRORS - PRODUCTION READY WITH WARNINGS",
            ])
        else:
            report_lines.extend([
                "",
                "❌ CRITICAL ERRORS FOUND - REQUIRES ATTENTION",
            ])
        
        report_lines.append("=" * 80)
        
        # Save report to file
        os.makedirs('logs', exist_ok=True)
        report_path = f"logs/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        # Print report
        for line in report_lines:
            logger.info(line)
        
        logger.info(f"Validation report saved to: {report_path}")
        
        return len(self.errors) == 0

def main():
    """Main entry point for the data validation script."""
    logger.info("Starting production data validation...")
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    validator = DataValidator()
    
    # Run all validations
    validations = [
        validator.validate_database_integrity,
        validator.validate_address_completeness,
        validator.validate_business_name_quality,
        validator.validate_lead_quality,
        validator.validate_output_files,
    ]
    
    all_passed = True
    for validation in validations:
        try:
            if not validation():
                all_passed = False
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            validator.errors.append(f"Validation exception: {str(e)}")
            all_passed = False
    
    # Generate final report
    success = validator.generate_validation_report()
    
    if success:
        logger.info("✅ ALL VALIDATIONS PASSED")
        return 0
    else:
        logger.error("❌ VALIDATION FAILURES DETECTED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
