# Claude Instructions

This file contains instructions for Claude to help maintain and develop this project.

## Project Overview
This is a crime news scraper that collects jewelry theft articles from multiple sources and analyzes them using Claude AI to identify sales opportunities for security screen products.

## API Keys
- NewsAPI: 010ae97959454a2c930036138e2f42ee

## Commands to Run

### Testing
```bash
pytest tests/
```

### Linting
```bash
# Add linting commands here when available
```

### Running the Application
```bash
python3 src/main.py
```

## Development Workflow
1. Follow the testing workflow described in README.md
2. Use modular architecture when adding new scrapers
3. Maintain focus on generating quality sales leads for security screen products
4. Check for sensitive information before commits (never commit API keys)
5. Follow existing code patterns and styles

## Important Guidelines
1. NEVER create random test scripts. Follow the testing workflow in README.md that uses a specific approach with test copies
2. Use the designated test directory (tests/) for permanent test files
3. When testing new code, create test copies within the same directory as the original file
4. If dependencies are missing, notify the user rather than installing them automatically