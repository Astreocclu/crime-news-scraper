The AI will log any errors encountered during the process and mark tasks/sub-tasks as completed.
Restrictions:

The AI should avoid changing the core logic of the scrapers, analyzers, or finders unless specifically instructed (e.g., to adapt to new configuration methods). The focus is primarily on structure and organization.
The AI should back up critical files before making major changes, or the process should be done under version control (like Git).
Here are the instructions for the CLI Agentic AI, broken down into tasks and sub-tasks. Please ensure the agent marks each off as completed and logs any issues.

Phase 1: Preparation and Analysis

Task 1.1: Backup Project (Optional but Recommended)
Sub-task 1.1.1: Create a compressed archive (e.g., zip) of the entire crime-news-scraper directory as a backup before starting modifications. Name it descriptively, like crime-news-scraper-backup-YYYYMMDD.zip.
Task 1.2: Analyze Current Structure
Sub-task 1.2.1: List all files and directories in the root crime-news-scraper directory.
Sub-task 1.2.2: Identify files that appear to be scripts (e.g., run_*.py, export_*.py, generate_*.py, test_*.py).
Sub-task 1.2.3: Identify log files (e.g., *.log).
Sub-task 1.2.4: Identify potential data/output files (e.g., *.csv, *.json, *.txt, *.html - excluding documentation).
Sub-task 1.2.5: Identify configuration-related files (e.g., requirements*.txt, potentially config.py files throughout the project).
Sub-task 1.2.6: Identify documentation files (*.md).
Sub-task 1.2.7: List the contents of the src/, tests/, evaluation/, logs/, and output/ directories.
Phase 2: Directory Structure Reorganization

Task 2.1: Create Standard Directories
Sub-task 2.1.1: If it doesn't exist, create a scripts/ directory in the root.
Sub-task 2.1.2: If it doesn't exist, create a config/ directory in the root (we might consolidate config files here later).
Sub-task 2.1.3: If it doesn't exist, create a data/ directory in the root (for sample/test data).
Sub-task 2.1.4: Ensure the logs/ directory exists.
Sub-task 2.1.5: Ensure the output/ directory exists. Standardize its structure if needed (e.g., create output/scraping, output/analysis, output/nearby, output/evaluation).
Task 2.2: Move Root Files to Appropriate Directories
Sub-task 2.2.1: Move identified scripts (from Sub-task 1.2.2, excluding test_*.py files which might belong elsewhere or indicate tests run from the root) into the scripts/ directory. Initial candidates: run_analyzer.py, run_analysis_db.py, run_finder_batches.py, run_workflow.py, export_analysis_to_csv.py, generate_test_data.py, create_complete_scrape.py.
Sub-task 2.2.2: Move identified log files (from Sub-task 1.2.3) from the root into the logs/ directory. Initial candidates: web_search_test.log, analyzer_db.log, manual_web_search_test.log, application.log, web_search.log, direct_augment_test.log, export_analysis.log, analyzer.log.
Sub-task 2.2.3: Move identified sample/test data files (from Sub-task 1.2.4) into the data/ directory. Initial candidates: dfw_business_theft_test.csv, nevada_search.html, test_article.txt, temp_preprocessed.csv.
Sub-task 2.2.4: Move general documentation files (CONTRIBUTING.md, CLAUDE.md, instructions.md, tasks.md, cursor.rules.md) into a potential docs/ directory or decide if they should be merged into the main README.md. For now, create docs/ and move them there.
Sub-task 2.2.5: Examine test_*.py files in the root (test_reviewjournal.py, test_newsapi.py, test_claude.py, test_web_search.py). Determine if they are misplaced tests that should be in tests/ or utility scripts. If they are tests, move them to the appropriate location within tests/. If they are utility/testing scripts, move them to scripts/.
Task 2.3: Clean Up Output Directories
Sub-task 2.3.1: Examine the output - Copy/ directory. Determine if its contents are valuable backups or redundant. If redundant, delete the output - Copy/ directory. If valuable, consider archiving it or merging relevant files into the main output/ directory with clear naming. (Agent should ask for confirmation before deleting).
Sub-task 2.3.2: Move any remaining output files from the root (e.g., analysis_results_*.csv) into the appropriate subdirectory within output/ (e.g., output/analysis/).
Phase 3: Configuration Management

Task 3.1: Identify Configuration Points
Sub-task 3.1.1: Scan the codebase (especially src/ subdirectories and scripts/) for files named config.py. List them.
Sub-task 3.1.2: Scan the codebase for hardcoded configuration values (API keys, file paths, database URLs, specific parameters like batch sizes, model names). Pay attention to modules like claude_client.py, google_client.py, database.py, scraper modules, and run scripts.
Task 3.2: Centralize Configuration (Example using .env)
Sub-task 3.2.1: Create a .env.example file in the root directory. Add placeholder entries for all identified configuration parameters (API keys, DB credentials, paths, etc.).
Sub-task 3.2.2: Add python-dotenv to requirements.txt.
Sub-task 3.2.3: Modify the code (e.g., in src/main.py, relevant config files, or utility modules) to load configuration from environment variables (using dotenv.load_dotenv() and os.getenv()).
Sub-task 3.2.4: Replace hardcoded values and values read from multiple config.py files with values loaded from the environment.
Sub-task 3.2.5: Add .env (the actual file with secrets) to the .gitignore file if it exists, or create one if needed.
Sub-task 3.2.6: Update relevant documentation (e.g., README.md) to explain the new configuration process using a .env file based on .env.example.
Phase 4: Code Refactoring & Optimization

Task 4.1: Review and Refactor utils/
Sub-task 4.1.1: Analyze the purpose of src/utils/address_extractor.py. Compare it with the components in src/address_finder/. Determine if it's redundant or should be integrated into src/address_finder/. Refactor or remove as needed.
Sub-task 4.1.2: Examine other modules in src/utils/ (logger.py, exceptions.py). Ensure they contain general-purpose utilities.
Task 4.2: Consolidate Scraper Utilities (If Applicable)
Sub-task 4.2.1: Review the utils.py files within each scraper's directory (src/scrapers/*/utils.py). Identify common functions or patterns.
Sub-task 4.2.2: If significant common functionality exists, consider creating a shared src/scrapers/utils.py module and refactoring the specific scrapers to use it, reducing code duplication.
Task 4.3: Standardize Database Interaction
Sub-task 4.3.1: Ensure all database operations go through the src/database.py module. Refactor any direct DB interactions found elsewhere.
Task 4.4: Review address_finder Complexity
Sub-task 4.4.1: Analyze the interactions between address_extractor.py, address_inferrer.py, address_confirmer.py, text_analyzer.py, and enhanced_finder.py within src/address_finder/.
Sub-task 4.4.2: Add docstrings and comments to clarify the role of each component and the overall workflow if they are missing. (Further refactoring might be a separate, more involved task).
Phase 5: Testing Improvements

Task 5.1: Organize tests/ Directory
Sub-task 5.1.1: Ensure the structure within tests/ mirrors the structure of src/. For example, tests for src/analyzer/analyzer.py should be in tests/test_analyzer/test_analyzer.py.
Sub-task 5.1.2: Move any relevant test files identified in Sub-task 2.2.5 into the correct location within tests/.
Task 5.2: Verify Test Execution
Sub-task 5.2.1: Ensure tests can be discovered and run (e.g., using pytest) from the root directory after the reorganization. Fix any import errors resulting from moved files.
Phase 6: Workflow & Entry Point Refinement

Task 6.1: Define Main Entry Point(s)
Sub-task 6.1.1: Analyze src/main.py and the scripts moved to scripts/ (especially run_workflow.py). Determine the intended primary way(s) to run the application's different functionalities (e.g., scrape all, scrape specific source, analyze, find nearby, full workflow).
Sub-task 6.1.2: Refactor src/main.py or scripts/run_workflow.py to be the main entry point.
Sub-task 6.1.3: Implement command-line argument parsing (using argparse or click) in the main entry point to allow users to specify tasks (e.g., python src/main.py scrape --source newsapi, python src/main.py analyze, python src/main.py workflow).
Sub-task 6.1.4: Update other scripts in scripts/ to be callable from the main entry point or document their specific uses if they are standalone tools.
Phase 7: Logging & Output Cleanup

Task 7.1: Standardize Logging
Sub-task 7.1.1: Ensure all modules use the logger configured in src/utils/logger.py. Remove any other logging configurations.
Sub-task 7.1.2: Verify that logs are consistently written to the logs/ directory with appropriate naming.
Task 7.2: Standardize Output
Sub-task 7.2.1: Refactor code (in scrapers, analyzer, nearby_finder, scripts) to write output files to the designated subdirectories within output/ (e.g., output/scraping/, output/analysis/).
Sub-task 7.2.2: Ensure output filenames are consistent and informative (e.g., including date, source, or type of data).
Phase 8: Documentation Update

Task 8.1: Update README.md
Sub-task 8.1.1: Update the project structure description in README.md.
Sub-task 8.1.2: Update setup instructions (including Python version, dependencies, and the new .env configuration).
Sub-task 8.1.3: Update usage instructions, explaining how to run the main entry point with different command-line arguments (from Task 6.1).
Sub-task 8.1.4: Review the contents of the docs/ directory (from Sub-task 2.2.4) and merge essential information into README.md or keep docs/ for supplementary details, linking to it from the README.
Task 8.2: Review Code Documentation
Sub-task 8.2.1: Add or update docstrings for key modules, classes, and functions, especially those modified during refactoring.

