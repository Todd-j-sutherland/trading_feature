# Testing Framework

This folder contains the comprehensive testing framework for the enhanced ML system.

## Files

### `test_validation_framework.py`
- **Purpose**: Core testing framework with realistic mock data generation
- **Features**: 
  - MockNewsGenerator: Generates realistic fake news articles
  - MockYahooDataFetcher: Fetches real Yahoo Finance historical data
  - TestValidationFramework: Orchestrates complete test scenarios
  - Isolated test database to prevent production data corruption

### `enhanced_ml_test_integration.py`
- **Purpose**: Integration tests for the enhanced ML pipeline
- **Features**:
  - Tests 54+ feature extraction
  - Validates multi-output prediction structure
  - 100% success rate achieved
  - Comprehensive feature validation

## Usage

### Run Enhanced ML Pipeline Tests
```bash
cd enhanced_ml_system/testing
python enhanced_ml_test_integration.py
```

### Expected Results
- ✅ CBA.AX: 54+ features extracted
- ✅ WBC.AX: 54+ features extracted  
- ✅ All prediction structures validated
- ✅ 100% success rate

## Test Capabilities
- **Realistic Mock Data**: Generates fake news articles matching real scraping patterns
- **Historical Market Data**: Uses real Yahoo Finance data for testing
- **Isolated Testing**: Separate test database prevents production corruption
- **Comprehensive Validation**: Tests all feature categories and prediction structures
- **Performance Metrics**: Tracks success rates and validation completeness

## Mock Data Generation
- **News Articles**: Realistic headlines and content for ASX stocks
- **Market Data**: Real historical OHLCV data from Yahoo Finance
- **Sentiment Labels**: Positive/negative/neutral sentiment assignments
- **Volume**: Realistic trading volume patterns
- **Timeframes**: Multiple timeframe data for testing
