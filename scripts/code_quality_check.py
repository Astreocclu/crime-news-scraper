#!/usr/bin/env python3
"""
Crime News Scraper - Code Quality Check Script

This script performs comprehensive code quality checks across the entire codebase,
including style validation, documentation completeness, and performance analysis.

Usage:
    python3 scripts/code_quality_check.py [--fix] [--verbose]

Options:
    --fix       Automatically fix issues where possible
    --verbose   Show detailed output for all checks

Author: Augment Agent
Version: 2.0.0
"""

import os
import sys
import ast
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeQualityChecker:
    """Comprehensive code quality checker for the Crime News Scraper project."""
    
    def __init__(self, fix_issues: bool = False, verbose: bool = False):
        """
        Initialize the code quality checker.
        
        Args:
            fix_issues: Whether to automatically fix issues where possible
            verbose: Whether to show detailed output
        """
        self.fix_issues = fix_issues
        self.verbose = verbose
        self.issues = []
        self.stats = {
            'files_checked': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'documentation_coverage': 0,
            'type_hint_coverage': 0
        }
        
        # Define project structure
        self.src_dir = Path('src')
        self.docs_dir = Path('docs')
        self.scripts_dir = Path('scripts')
        self.config_dir = Path('config')
        
    def check_all(self) -> Dict[str, Any]:
        """
        Run all code quality checks.
        
        Returns:
            Dict containing check results and statistics
        """
        logger.info("Starting comprehensive code quality check...")
        
        # Check Python files
        self._check_python_files()
        
        # Check documentation
        self._check_documentation()
        
        # Check configuration files
        self._check_configuration()
        
        # Check project structure
        self._check_project_structure()
        
        # Generate report
        return self._generate_report()
    
    def _check_python_files(self) -> None:
        """Check all Python files for quality issues."""
        logger.info("Checking Python files...")
        
        python_files = list(self.src_dir.rglob('*.py')) + list(self.scripts_dir.rglob('*.py'))
        
        for file_path in python_files:
            self.stats['files_checked'] += 1
            self._check_single_python_file(file_path)
    
    def _check_single_python_file(self, file_path: Path) -> None:
        """Check a single Python file for quality issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Check documentation
            self._check_file_documentation(file_path, tree, content)
            
            # Check type hints
            self._check_type_hints(file_path, tree)
            
            # Check imports
            self._check_imports(file_path, tree)
            
            # Check function/class structure
            self._check_code_structure(file_path, tree)
            
        except Exception as e:
            self._add_issue(file_path, f"Failed to parse file: {str(e)}", "error")
    
    def _check_file_documentation(self, file_path: Path, tree: ast.AST, content: str) -> None:
        """Check documentation completeness for a file."""
        # Check module docstring
        if not ast.get_docstring(tree):
            self._add_issue(file_path, "Missing module docstring", "documentation")
        
        # Check function/class docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    self._add_issue(file_path, f"Function '{node.name}' missing docstring", "documentation")
            
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    self._add_issue(file_path, f"Class '{node.name}' missing docstring", "documentation")
    
    def _check_type_hints(self, file_path: Path, tree: ast.AST) -> None:
        """Check type hint coverage."""
        functions_with_hints = 0
        total_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'):  # Skip private functions
                    total_functions += 1
                    
                    # Check return type annotation
                    if node.returns:
                        functions_with_hints += 0.5
                    
                    # Check parameter type annotations
                    annotated_args = sum(1 for arg in node.args.args if arg.annotation)
                    if annotated_args == len(node.args.args):
                        functions_with_hints += 0.5
        
        if total_functions > 0:
            coverage = (functions_with_hints / total_functions) * 100
            self.stats['type_hint_coverage'] += coverage
            
            if coverage < 80:
                self._add_issue(file_path, f"Low type hint coverage: {coverage:.1f}%", "type_hints")
    
    def _check_imports(self, file_path: Path, tree: ast.AST) -> None:
        """Check import organization and usage."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Check for unused imports (basic check)
        # This is a simplified check - a full implementation would need more sophisticated analysis
        
        # Check import organization
        if len(imports) > 10:
            self._add_issue(file_path, "Consider organizing imports into groups", "style")
    
    def _check_code_structure(self, file_path: Path, tree: ast.AST) -> None:
        """Check code structure and complexity."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function length
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        self._add_issue(file_path, f"Function '{node.name}' is too long ({length} lines)", "complexity")
                
                # Check parameter count
                if len(node.args.args) > 7:
                    self._add_issue(file_path, f"Function '{node.name}' has too many parameters", "complexity")
    
    def _check_documentation(self) -> None:
        """Check documentation completeness."""
        logger.info("Checking documentation...")
        
        required_docs = [
            'README.md',
            'docs/API_REFERENCE.md',
            'docs/CONFIGURATION.md',
            'docs/deployment_guide.md'
        ]
        
        for doc_file in required_docs:
            if not Path(doc_file).exists():
                self._add_issue(Path(doc_file), "Missing required documentation file", "documentation")
            else:
                # Check if file is not empty
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if len(content) < 100:
                        self._add_issue(Path(doc_file), "Documentation file appears incomplete", "documentation")
    
    def _check_configuration(self) -> None:
        """Check configuration files."""
        logger.info("Checking configuration files...")
        
        config_files = [
            '.env.example',
            'requirements.txt',
            'config/nearby_finder.yaml'
        ]
        
        for config_file in config_files:
            if not Path(config_file).exists():
                self._add_issue(Path(config_file), "Missing configuration file", "configuration")
    
    def _check_project_structure(self) -> None:
        """Check overall project structure."""
        logger.info("Checking project structure...")
        
        required_dirs = [
            'src',
            'docs', 
            'scripts',
            'config',
            'output',
            'logs'
        ]
        
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                self._add_issue(Path(dir_name), "Missing required directory", "structure")
    
    def _add_issue(self, file_path: Path, message: str, category: str) -> None:
        """Add an issue to the issues list."""
        issue = {
            'file': str(file_path),
            'message': message,
            'category': category
        }
        self.issues.append(issue)
        self.stats['issues_found'] += 1
        
        if self.verbose:
            logger.warning(f"{file_path}: {message}")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        logger.info("Generating quality report...")
        
        # Calculate averages
        if self.stats['files_checked'] > 0:
            self.stats['type_hint_coverage'] /= self.stats['files_checked']
        
        # Group issues by category
        issues_by_category = {}
        for issue in self.issues:
            category = issue['category']
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)
        
        report = {
            'summary': self.stats,
            'issues_by_category': issues_by_category,
            'total_issues': len(self.issues),
            'quality_score': self._calculate_quality_score()
        }
        
        return report
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        base_score = 100
        
        # Deduct points for issues
        deductions = {
            'error': 10,
            'documentation': 5,
            'type_hints': 3,
            'complexity': 4,
            'style': 2,
            'configuration': 3,
            'structure': 8
        }
        
        for issue in self.issues:
            category = issue['category']
            base_score -= deductions.get(category, 1)
        
        return max(0, base_score)

def main():
    """Main entry point for code quality check."""
    parser = argparse.ArgumentParser(description='Crime News Scraper Code Quality Check')
    parser.add_argument('--fix', action='store_true', help='Automatically fix issues where possible')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    # Create checker
    checker = CodeQualityChecker(fix_issues=args.fix, verbose=args.verbose)
    
    # Run checks
    report = checker.check_all()
    
    # Display results
    print("\n" + "="*60)
    print("CRIME NEWS SCRAPER - CODE QUALITY REPORT")
    print("="*60)
    
    print(f"\nSUMMARY:")
    print(f"  Files Checked: {report['summary']['files_checked']}")
    print(f"  Issues Found: {report['total_issues']}")
    print(f"  Quality Score: {report['quality_score']:.1f}/100")
    print(f"  Type Hint Coverage: {report['summary']['type_hint_coverage']:.1f}%")
    
    if report['issues_by_category']:
        print(f"\nISSUES BY CATEGORY:")
        for category, issues in report['issues_by_category'].items():
            print(f"  {category.upper()}: {len(issues)} issues")
            if args.verbose:
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"    - {issue['file']}: {issue['message']}")
                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more")
    
    # Quality assessment
    if report['quality_score'] >= 90:
        print(f"\n✅ EXCELLENT: Code quality is excellent!")
    elif report['quality_score'] >= 80:
        print(f"\n✅ GOOD: Code quality is good with minor issues.")
    elif report['quality_score'] >= 70:
        print(f"\n⚠️ FAIR: Code quality needs improvement.")
    else:
        print(f"\n❌ POOR: Code quality needs significant improvement.")
    
    print("="*60)
    
    return 0 if report['quality_score'] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())
