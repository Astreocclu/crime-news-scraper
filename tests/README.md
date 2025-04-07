# Comprehensive Testing System

This document outlines the comprehensive testing approach for the Crime News Scraper project.

## Testing Philosophy

The project follows a specific testing workflow designed to protect production code while still allowing thorough testing:

1. **Test Copy Approach**: When testing new functionality or changes, create a test copy of the file to be modified rather than modifying the original directly.
2. **Isolated Testing**: Test new features in isolation before integrating them into the main codebase.
3. **Standardized Test Directory**: All permanent test files should reside in the `tests/` directory.
4. **Integration Testing**: The `unified.py` scraper provides a framework for testing multiple scrapers together.

## Test Types

### 1. Unit Tests

Unit tests focus on testing individual components in isolation:

- **Scraper Module Tests**: Test each scraper module's basic functionality
- **Utility Function Tests**: Test helper functions like date parsing, location detection, etc.
- **Parser Tests**: Test HTML/response parsing functions

Unit tests should be placed in the `tests/` directory with a naming convention of `test_[module_name].py`.

### 2. Integration Tests

Integration tests verify that multiple components work together correctly:

- **Scraper Pipeline Tests**: Test the entire scraping, parsing, and data extraction pipeline
- **Combined Scraper Tests**: Test the unified scraper with multiple sources
- **Storage Tests**: Verify that scraped data is correctly saved to CSV/JSON

### 3. Mock Tests

Mock tests avoid making real web requests during testing:

- **Mock Response Tests**: Test scrapers with pre-recorded or simulated API/web responses
- **HTML Fixture Tests**: Use saved HTML fixtures to test parsing logic

### 4. Development Tests

For in-progress development, create temporary test copies:

- Create a copy of the file being modified (e.g., `analyzer.py` → `test_analyzer.py`)
- Implement and test changes in the test copy
- Once verified, merge changes back to the original file

## Test Data Management

- **Fixture Directory**: Store test fixtures in `tests/fixtures/`
- **Sample Responses**: Save sample HTML/API responses for mock testing
- **Expected Outputs**: Store expected output formats for validation

## Continuous Testing

For ongoing testing and continuous integration:

- Run `pytest tests/` to execute all defined test cases
- Always verify scrapers in isolation before updating the unified scraper
- Use the verbose flag for detailed output: `pytest -v tests/`

## Adding New Tests

When adding a new scraper module:

1. Create a corresponding test file in `tests/`
2. Define tests for:
   - Basic initialization and configuration loading
   - Response parsing and article extraction
   - Location detection and filtering
   - Keyword extraction and relevance checking

## Integration with Main Workflow

The testing system is integrated with the main development workflow:

1. Create test copy for new features
2. Implement and test in isolation
3. Add formal tests to the `tests/` directory
4. Merge changes to main implementation
5. Run full test suite to ensure compatibility