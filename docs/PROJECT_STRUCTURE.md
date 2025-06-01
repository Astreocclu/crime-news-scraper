# Crime News Scraper - Project Structure

This document provides a comprehensive overview of the project structure and organization.

## 📁 **Root Directory Structure**

```
crime-news-scraper/
├── 📁 src/                     # Main source code
├── 📁 docs/                    # Documentation
├── 📁 scripts/                 # Utility and test scripts
├── 📁 config/                  # Configuration files
├── 📁 output/                  # Generated output files
├── 📁 logs/                    # Application logs
├── 📄 README.md               # Main project documentation
├── 📄 requirements.txt        # Python dependencies
├── 📄 .env.example           # Environment variables template
└── 📄 crime_data.db          # SQLite database (generated)
```

## 🏗️ **Source Code Structure (`src/`)**

### **Main Modules**

```
src/
├── 📄 __init__.py             # Package initialization
├── 📄 main.py                 # Main application entry point
├── 📄 database.py             # Database operations
└── 📄 perplexity_client.py    # Perplexity API client
```

### **Analyzer Module (`src/analyzer/`)**

```
src/analyzer/
├── 📄 __init__.py             # Module initialization
├── 📄 analyzer.py             # Main analyzer orchestrator
├── 📄 analyzer_manual_test.py # Single batch analyzer for testing
└── 📄 claude_client.py        # Claude AI API client
```

**Key Features:**
- AI-powered crime incident analysis using Claude AI
- Address validation and enhancement using Perplexity API
- Business impact scoring and risk assessment
- Processing speed: ~10.4 seconds per article
- Address validation: 81.4% success rate

### **Nearby Finder Module (`src/nearby_finder/`)**

```
src/nearby_finder/
├── 📄 __init__.py             # Module initialization
├── 📄 finder.py               # Main business discovery orchestrator
├── 📄 google_client.py        # Google Maps API client
├── 📄 config.py               # Configuration settings
├── 📄 example.py              # Usage examples
└── 📄 mock_finder.py          # Mock implementation for testing
```

**EXCLUSIVE TARGET FOCUS:**
- 💎 **Jewelry stores** (primary target - highest priority)
- 🏆 **Sports memorabilia stores** (secondary target)
- 👑 **Luxury goods stores** (secondary target)
- **100% target filtering** - all other business types excluded

### **Scrapers Module (`src/scrapers/`)**

```
src/scrapers/
├── 📄 __init__.py             # Module initialization
├── 📄 unified.py              # Unified scraper orchestrator
├── 📄 base.py                 # Base scraper class
├── 📁 base/                   # Base scraper implementation
├── 📁 jsa/                    # Jewelers Security Alliance scraper
├── 📁 dfw/                    # DFW news scrapers
├── 📁 wfaa/                   # WFAA news scraper
├── 📁 eightnews/              # 8News scraper
├── 📁 reviewjournal/          # Las Vegas Review Journal scraper
├── 📁 nevadacurrent/          # Nevada Current scraper
└── 📁 newsapi/                # NewsAPI integration
```

**Source-Specific Scrapers:**
Each scraper module contains:
- `scraper.py` - Main scraping logic
- `utils.py` - Utility functions
- `__init__.py` - Module initialization

### **Address Finder Module (`src/address_finder/`)**

```
src/address_finder/
├── 📄 __init__.py             # Module initialization
├── 📄 address_extractor.py    # Address extraction logic
├── 📄 address_inferrer.py     # Address inference algorithms
├── 📄 address_confirmer.py    # Address validation and confirmation
├── 📄 enhanced_finder.py      # Enhanced address finding
├── 📄 text_analyzer.py        # Text analysis for addresses
└── 📄 example.py              # Usage examples
```

### **Utilities Module (`src/utils/`)**

```
src/utils/
├── 📄 __init__.py             # Module initialization
└── 📄 logger.py               # Logging utilities and decorators
```

## 📚 **Documentation Structure (`docs/`)**

```
docs/
├── 📄 API_REFERENCE.md        # Comprehensive API documentation
├── 📄 CONFIGURATION.md        # Configuration guide
├── 📄 PROJECT_STRUCTURE.md    # This file - project structure
├── 📄 deployment_guide.md     # Production deployment guide
└── 📄 project_completion_summary.md  # Project completion summary
```

## 🔧 **Scripts Directory (`scripts/`)**

### **Main Workflow Scripts**
- `run_workflow.py` - Complete workflow execution
- `workflow.py` - Alternative workflow runner

### **Component-Specific Scripts**
- `scrape.py` - Scraping operations
- `analyze.py` - Analysis operations
- `nearby.py` - Nearby business finding
- `run_analyzer.py` - Analyzer execution
- `run_analysis_db.py` - Database-based analysis

### **Testing Scripts**
- `test_workflow_limited.py` - Limited workflow testing
- `test_focused_search.py` - Focused search validation
- `test_performance.py` - Performance benchmarking
- `test_enhanced_analyzer.py` - Enhanced analyzer testing
- `test_newsapi.py` - NewsAPI testing
- `test_web_search.py` - Web search testing
- `test_claude.py` - Claude AI testing

### **Utility Scripts**
- `validate_production_data.py` - Production data validation
- `export_analysis_to_csv.py` - Analysis data export
- `create_complete_scrape.py` - Complete scrape file creation
- `rename_output_files.py` - Output file management
- `code_quality_check.py` - Code quality assessment

### **Example Scripts**
- `nearby_finder_example.py` - Nearby finder usage examples
- `address_finder_example.py` - Address finder usage examples

## ⚙️ **Configuration Structure (`config/`)**

```
config/
└── 📄 nearby_finder.yaml      # Nearby finder configuration
```

## 📊 **Output Structure (`output/`)**

```
output/
├── 📁 scraping/               # Scraped articles
├── 📁 analysis/               # Analysis results
└── 📁 nearby/                 # Nearby business data
```

**File Naming Convention:**
- `YYYYMMDD-[type]_[timestamp].csv`
- Example: `20250601-Analysis_143022.csv`

## 📝 **Log Structure (`logs/`)**

```
logs/
├── 📄 application.log         # Main application logs
├── 📄 scraper.log            # Scraper-specific logs
├── 📄 analyzer.log           # Analyzer-specific logs
└── 📄 nearby_finder.log      # Nearby finder logs
```

## 🗄️ **Database Schema**

### **Tables:**

1. **`articles`** - Raw scraped news articles
   - Primary key: `id`
   - Unique constraint: `url`
   - Indexes: `date_scraped`, `source`

2. **`analysis_results`** - AI-analyzed crime incident data
   - Primary key: `id`
   - Foreign key: `article_id` → `articles.id`
   - Indexes: `totalScore`, `businessType`

3. **`nearby_businesses`** - Target businesses near incidents
   - Primary key: `id`
   - Foreign key: `analysis_id` → `analysis_results.id`
   - Indexes: `lead_score`, `businessType`, `distance_from_incident`

## 🎯 **Key Design Principles**

### **1. Modular Architecture**
- Clear separation of concerns
- Reusable components
- Easy to test and maintain

### **2. Focused Targeting**
- Exclusive focus on three target business types
- 100% filtering of non-target businesses
- High-quality lead generation (62.2% score ≥5)

### **3. Performance Optimization**
- Efficient database operations with proper indexing
- API rate limiting and error handling
- Batch processing for large datasets

### **4. Data Quality**
- Multiple validation layers
- Comprehensive error handling
- Data integrity constraints

### **5. Scalability**
- Database-first approach
- Configurable batch sizes
- Modular scraper architecture

## 📈 **Performance Metrics**

- **Processing Speed**: ~10.4 seconds per article
- **Address Validation**: 81.4% success rate
- **Lead Quality**: 62.2% high-quality leads (score ≥5)
- **Target Business Focus**: 100% (jewelry, sports memorabilia, luxury goods only)
- **Data Quality**: 95.1% business naming success rate

## 🔄 **Data Flow**

```
News Sources → Scrapers → Database → Analyzer → Analysis Results
                                                       ↓
Complete Scrape ← Nearby Finder ← Target Businesses ←
```

## 🛠️ **Development Workflow**

1. **Code Development**: Implement features in `src/`
2. **Testing**: Use scripts in `scripts/` for testing
3. **Documentation**: Update docs in `docs/`
4. **Configuration**: Modify settings in `config/`
5. **Deployment**: Follow `docs/deployment_guide.md`

## 📋 **File Conventions**

### **Python Files**
- PEP 8 compliant code style
- Comprehensive docstrings
- Type hints for all functions
- Proper import organization

### **Documentation**
- Markdown format
- Clear section headers
- Code examples where applicable
- Performance metrics included

### **Configuration**
- YAML format for complex configurations
- Environment variables for sensitive data
- Clear documentation of all options

This structure ensures maintainability, scalability, and ease of development while maintaining focus on our three target business types for maximum lead quality.
