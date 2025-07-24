# 📚 Documentation Index

Welcome to the Trading Analysis System documentation! This directory contains comprehensive guides, references, and development documentation.

## 🚀 Getting Started

Start here if you're new to the system:

- **[Quick Start Guide](QUICK_START.md)** - 5-minute setup and basic usage
- **[Features Overview](FEATURES.md)** - Complete feature breakdown and capabilities
- **[Architecture Overview](ARCHITECTURE.md)** - Technical architecture and design patterns

## 📖 User Guides

### Daily Usage
- **Morning Routine** - See [Quick Start](QUICK_START.md#morning-analysis)
- **Evening Summary** - See [Quick Start](QUICK_START.md#evening-summary)
- **Dashboard Usage** - See [Features](FEATURES.md#-professional-dashboard)

### Advanced Features
- **Sentiment Analysis** - See [Features](FEATURES.md#-enhanced-sentiment-analysis)
- **Technical Analysis** - See [Features](FEATURES.md#-technical-analysis-integration)
- **Automated Operations** - See [Features](FEATURES.md#-automated-operations)

## 🔧 Development Documentation

### Project Evolution
- **[Project Restructuring](RESTRUCTURE_COMPLETE.md)** - Complete architectural migration
- **[File Organization](ORGANIZATION_COMPLETE.md)** - Structure evolution and cleanup
- **[Legacy Cleanup](CLEANUP_COMPLETE.md)** - Migration from old structure

### Technical Implementation
- **[Testing Framework](TESTING_COMPLETE_SUMMARY.md)** - Comprehensive testing suite
- **[Architecture Details](ARCHITECTURE.md)** - Deep technical overview
- **Code Organization** - See [File Organization](FILE_ORGANIZATION.md)

## 🎯 Quick References

### Command Reference
```bash
# System commands
python -m app.main status      # Health check
python -m app.main morning     # Morning analysis
python -m app.main evening     # Evening summary
python -m app.main dashboard   # Web interface
streamlit run app/dashboard/main.py

# Testing commands
python -m pytest tests/ -v                # All tests
python -m pytest tests/unit/ -v           # Unit tests
python -m pytest tests/integration/ -v    # Integration tests
```

### Key File Locations
```
app/
├── main.py                    # CLI entry point
├── config/settings.py         # Configuration
├── core/sentiment/           # Sentiment analysis
├── dashboard/main.py         # Web interface
└── services/daily_manager.py # Daily operations

docs/                         # This documentation
tests/                        # Test suite
data/                         # Data storage
logs/                         # Application logs
```

### Configuration Files
- **`app/config/settings.py`** - Main system configuration
- **`app/config/ml_config.yaml`** - ML model settings
- **`.env`** - Environment variables (create from `.env.example`)
- **`requirements.txt`** - Python dependencies

## 🆘 Troubleshooting

### Common Issues
1. **Import Errors** - Ensure virtual environment is activated
2. **Dashboard Not Loading** - Check port 8501 availability
3. **Test Failures** - Run `python -m app.main status` first
4. **Data Issues** - Check `data/` directory permissions

### Getting Help
1. **Check System Status** - `python -m app.main status`
2. **Review Logs** - Check `logs/` directory
3. **Run Tests** - `python -m pytest tests/ -v`
4. **Consult Documentation** - Review relevant guide above

## 📊 Project Metrics

### Current Status
- **✅ 63+ Tests** - Comprehensive test coverage
- **✅ Professional Architecture** - Industry-standard Python package
- **✅ Full Documentation** - Complete user and developer guides
- **✅ Legacy Cleanup** - 100+ legacy files properly archived

### Test Coverage
- **Unit Tests**: 19 tests covering core functionality
- **Integration Tests**: 44 tests validating system integration
- **Success Rate**: 100% passing tests
- **Performance**: Sub-second test execution

### Architecture Quality
- **Modular Design** - Clean separation of concerns
- **Type Safety** - Full type annotation coverage
- **Error Handling** - Comprehensive error recovery
- **Logging** - Structured logging with rotation

## 🔗 External Resources

### Dependencies
- **[Streamlit](https://streamlit.io/)** - Dashboard framework
- **[Plotly](https://plotly.com/python/)** - Interactive charts
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation
- **[Pytest](https://pytest.org/)** - Testing framework

### Related Tools
- **Financial Data APIs** - Yahoo Finance, Alpha Vantage
- **News Sources** - RSS feeds, financial news APIs
- **Deployment Options** - Docker, cloud platforms

## 📝 Contributing to Documentation

### Writing Guidelines
1. **Clear Structure** - Use consistent heading hierarchy
2. **Code Examples** - Include practical examples
3. **Screenshots** - Visual guides where helpful
4. **Links** - Cross-reference related documentation

### File Organization
- **User Guides** - Focus on practical usage
- **Technical Docs** - Architecture and implementation details
- **Reference** - Quick lookup information
- **Historical** - Project evolution and decisions

### Updating Documentation
1. Keep documentation current with code changes
2. Test all code examples before publishing
3. Use consistent markdown formatting
4. Include version information for significant changes

---

**📖 Start with the [Quick Start Guide](QUICK_START.md) to begin using the system!**
