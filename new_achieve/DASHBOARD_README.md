# ASX Banks Trading Sentiment Dashboard

A simplified single-page dashboard for real-time trading sentiment analysis of Australian bank stocks.

## Overview

This dashboard provides a comprehensive view of machine learning predictions, sentiment analysis, and technical indicators for ASX bank stocks in a single, clean interface.

### Tracked Banks
- **CBA.AX** - Commonwealth Bank of Australia
- **ANZ.AX** - Australia and New Zealand Banking Group
- **WBC.AX** - Westpac Banking Corporation
- **NAB.AX** - National Australia Bank
- **MQG.AX** - Macquarie Group
- **SUN.AX** - Suncorp Group
- **QBE.AX** - QBE Insurance Group

## Features

### 🤖 Machine Learning Performance
- Real-time ML model accuracy and success rates
- Prediction volume and confidence metrics
- Trading performance analytics
- Signal distribution (BUY/SELL/HOLD)

### 📊 Current Sentiment Scores
- Latest sentiment analysis for all banks
- Confidence levels and signal strength
- News count and social media sentiment
- Clear visual indicators for trading signals

### 📈 Technical Analysis
- Technical indicators and event scores
- Reddit sentiment analysis
- Combined indicator strength visualization
- Historical pattern analysis

### 🔍 ML Feature Transparency
- Dynamic display of model inputs
- Feature usage statistics
- Confidence calculation explanations
- Real-time feature importance

## Technical Specifications

### Requirements
- **Python 3.12+** (Currently supports 3.13.5)
- **Virtual Environment** (automatically created)
- **Direct SQL Database Access**
- **Real-time Data Processing**

### Dependencies
- `streamlit` - Web UI framework
- `pandas` - Data manipulation
- `plotly` - Interactive visualizations
- `sqlite3` - Database connectivity (built-in)

### Data Source
- **Primary Database**: `data/ml_models/training_data.db`
- **Tables**: `sentiment_features`, `trading_outcomes`, `model_performance`
- **Data Flow**: Live SQL queries (no JSON dependencies)

## Installation & Usage

### Quick Start
```bash
# Clone the repository and navigate to it
cd /path/to/trading_feature

# Run the automated startup script
./start_dashboard.sh
```

The startup script will:
1. Create a Python virtual environment if needed
2. Install required dependencies
3. Test all dashboard components
4. Start the Streamlit dashboard

### Manual Setup
```bash
# Create virtual environment
python3 -m venv dashboard_env
source dashboard_env/bin/activate

# Install dependencies
pip install streamlit pandas plotly

# Test components
python test_dashboard_components.py

# Start dashboard
streamlit run dashboard.py
```

### Accessing the Dashboard
Once started, the dashboard will be available at:
- **Local Access**: http://localhost:8501
- **Network Access**: http://[your-ip]:8501

## Component Testing

Each dashboard section can be tested independently:

```bash
# Test all components
python test_dashboard_components.py

# Individual component verification
# - Database connectivity
# - ML performance metrics
# - Sentiment analysis
# - Feature analysis
# - Technical indicators
```

## Dashboard Sections

### 1. ML Performance Metrics
- **Predictions (7d)**: Total predictions in the last 7 days
- **Average Confidence**: Mean confidence across all predictions
- **Success Rate**: Percentage of profitable trades
- **Signal Distribution**: BUY/SELL/HOLD breakdown

### 2. Current Sentiment Scores
- **Real-time Sentiment**: Latest scores for all banks
- **Trading Signals**: Clear BUY/SELL/HOLD indicators
- **Confidence Levels**: Model confidence for each prediction
- **Data Freshness**: Timestamp of last update

### 3. Technical Analysis
- **Indicator Heatmap**: Visual representation of technical scores
- **Combined Strength**: Aggregated indicator power
- **Multi-source Analysis**: News, Reddit, events, technical data

### 4. ML Feature Analysis
- **Feature Usage Rates**: How often each feature is used
- **Feature Strength**: Average impact of each feature type
- **Dynamic Transparency**: Real-time feature importance
- **Model Explainability**: What drives predictions

### 5. Prediction Timeline
- **Performance Over Time**: ML accuracy trends
- **Volume Analysis**: Prediction frequency patterns
- **Recent Activity**: Latest predictions with details

## Error Handling

The dashboard implements robust error handling:

- **Database Errors**: Clear error messages for connectivity issues
- **Data Errors**: Informative warnings for missing data
- **Component Failures**: Independent component testing
- **Exception Raising**: No silent failures

## Configuration

### Database Path
Default: `data/ml_models/training_data.db`

To change the database location, modify the `DATABASE_PATH` variable in `dashboard.py`:

```python
DATABASE_PATH = "your/custom/path/to/training_data.db"
```

### Bank List
To modify tracked banks, update the `ASX_BANKS` list in `dashboard.py`:

```python
ASX_BANKS = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]
```

## Production Deployment

### Performance Optimization
- Enable Streamlit caching for database queries
- Use connection pooling for high-volume deployments
- Consider Redis for session state management

### Security Considerations
- Restrict database access permissions
- Use HTTPS for production deployments
- Implement authentication if needed

### Monitoring
- Database query performance
- Dashboard response times
- Error rates and exceptions

## Troubleshooting

### Common Issues

**Dashboard won't start:**
```bash
# Check Python version
python3 --version

# Verify virtual environment
source dashboard_env/bin/activate
which python

# Test components individually
python test_dashboard_components.py
```

**Database connection errors:**
```bash
# Verify database exists
ls -la data/ml_models/training_data.db

# Check database permissions
sqlite3 data/ml_models/training_data.db ".tables"
```

**Missing data:**
```bash
# Check recent data
sqlite3 data/ml_models/training_data.db \
"SELECT COUNT(*) FROM sentiment_features WHERE timestamp >= date('now', '-1 day')"
```

### Performance Issues
- Refresh the browser page to reload data
- Restart the dashboard if memory usage is high
- Check database size and optimize if needed

## Development

### Architecture
- **Modular Design**: Each section is independently testable
- **SQL-First**: Direct database queries, no JSON dependencies
- **Error Transparency**: All exceptions are surfaced clearly
- **Production Ready**: Proper logging and error handling

### Adding New Features
1. Create function for data fetching
2. Add corresponding UI rendering function
3. Update component tests
4. Integrate into main dashboard

### Testing
Run the comprehensive test suite:
```bash
python test_dashboard_components.py
```

All components must pass individual tests before the dashboard will start.

## License

This dashboard is part of the trading sentiment analysis system. See LICENSE file for details.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run component tests to isolate problems
3. Check database connectivity and data freshness
4. Review error messages in the dashboard UI
