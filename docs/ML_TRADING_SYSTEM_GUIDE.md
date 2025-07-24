# ML Trading System Implementation Guide

## Overview

This document explains the comprehensive ML trading system implementation that was added to the trading analysis platform. The system provides advanced sentiment analysis, ML-powered trading scores, pre-trade analysis, and Alpaca integration for automated trading.

## System Architecture

### Core Components

1. **ML Trading Manager** (`app/core/ml/trading_manager.py`)
   - Central orchestrator for all ML trading operations
   - Coordinates sentiment analysis, economic analysis, divergence detection, and ML scoring
   - Provides unified interface for pre-trade analysis

2. **ML Trading Scorer** (`app/core/ml/trading_scorer.py`)
   - Calculates comprehensive ML scores using 6 components:
     - Sentiment Strength (0-100)
     - Sentiment Confidence (0-100)
     - Economic Context (0-100)
     - Divergence Score (0-100)
     - Technical Momentum (0-100)
     - ML Prediction Confidence (0-100)

3. **Enhanced News Sentiment Analyzer** (`app/core/sentiment/news_analyzer.py`)
   - Multi-source news aggregation (RSS, Yahoo Finance, web scraping)
   - Advanced transformer-based sentiment analysis
   - ML trading features integration
   - Enhanced sentiment scoring with market context

4. **Economic Sentiment Analyzer** (`app/core/analysis/economic.py`)
   - Market regime detection (Bullish, Bearish, Neutral)
   - Economic sentiment scoring (-1 to +1)
   - Market context analysis

5. **Divergence Detector** (`app/core/analysis/divergence.py`)
   - Sector-wide sentiment divergence analysis
   - Identifies outlier banks with unusual sentiment patterns
   - Provides divergence scores and sector averages

6. **Alpaca Trading Integration** (`app/core/trading/alpaca_integration.py`)
   - Paper trading integration with Alpaca Markets
   - Automated order placement based on ML scores
   - Position management and risk controls

## Major Changes Made

### 1. Fixed Critical Error: 'NewsSentimentAnalyzer' object has no attribute 'get_all_news'

**Problem:** The system was crashing with a missing method error.

**Solution:** Added the `get_all_news()` method to aggregate news from multiple sources:

```python
def get_all_news(self, search_terms: list, symbol: str) -> List[Dict]:
    """
    Collect news from all available sources for the given symbol and search terms.
    """
    all_news = []
    
    # Fetch from RSS feeds
    rss_news = self._fetch_rss_news(symbol)
    all_news.extend(rss_news)
    
    # Fetch from Yahoo News
    yahoo_news = self._fetch_yahoo_news(symbol)
    all_news.extend(yahoo_news)
    
    # Scrape from news websites
    scraped_news = self._scrape_news_sites(symbol)
    all_news.extend(scraped_news)
    
    # Remove duplicates
    all_news = self._remove_duplicate_news(all_news)
    
    return all_news
```

### 2. Fixed Transformer Models Attribute Error

**Problem:** Code was trying to access `transformer_models` but the attribute was named `transformer_pipelines`.

**Solution:** Updated the sentiment analysis method to use the correct attribute:

```python
# Fixed line 1724 in news_analyzer.py
if self.transformer_pipelines.get('general'):
    transformer_result = self.transformer_pipelines['general'](text)
```

### 3. Added Missing ML Trading Component Initialization

**Problem:** Missing `feature_engineer`, `reddit`, and other ML-related attributes causing AttributeError.

**Solution:** Added proper initialization in the `NewsSentimentAnalyzer.__init__()` method:

```python
# Initialize ML trading components
self.feature_engineer = None
self.reddit = None
self.ml_model = None
self.enhanced_integration = None

# Try to initialize ML trading components
if ML_TRADING_AVAILABLE:
    try:
        self.feature_engineer = FeatureEngineer()
        logger.info("FeatureEngineer initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize FeatureEngineer: {e}")
        self.feature_engineer = None

# Try to initialize enhanced sentiment integration
if ENHANCED_SENTIMENT_AVAILABLE:
    try:
        self.enhanced_integration = SentimentIntegrationManager()
        logger.info("Enhanced sentiment integration initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize enhanced sentiment integration: {e}")
        self.enhanced_integration = None

# Load ML model if available
self.ml_model = self._load_ml_model()
```

### 4. Added Reddit Sentiment Analysis

**Problem:** `reddit_sentiment` variable was undefined in the sentiment calculation.

**Solution:** Added call to `_get_reddit_sentiment()` method:

```python
# Get Reddit sentiment
reddit_sentiment = self._get_reddit_sentiment(symbol)
```

### 5. Enhanced CLI Commands

Added new CLI commands for ML trading functionality:

- `ml-scores` - Display ML scores for all banks
- `pre-trade --symbol SYMBOL` - Run pre-trade analysis for specific symbol
- `dashboard --enhanced` - Launch enhanced dashboard with ML features

## How to Run the System

### Prerequisites

1. **Python Environment**: Python 3.11 or 3.12 (recommended for full transformer support)
2. **Virtual Environment**: Activate the project's virtual environment
3. **Dependencies**: All required packages should be installed via `requirements.txt`

### Basic Commands

1. **Activate Environment**:
   ```bash
   source .venv312/bin/activate
   cd /Users/toddsutherland/Repos/trading_analysis
   ```

2. **Run ML Scores Analysis**:
   ```bash
   python app/main.py ml-scores
   ```
   This displays ML trading scores for all configured bank stocks.

3. **Run Pre-Trade Analysis**:
   ```bash
   python app/main.py pre-trade --symbol QBE.AX
   ```
   Replace `QBE.AX` with any supported bank symbol (CBA.AX, WBC.AX, ANZ.AX, NAB.AX, etc.)

4. **Launch Enhanced Dashboard**:
   ```bash
   python app/main.py enhanced-dashboard
   ```

5. **Run Complete Analysis**:
   ```bash
   python app/main.py analyze
   ```

### Supported Bank Symbols

- `CBA.AX` - Commonwealth Bank
- `WBC.AX` - Westpac Banking Corporation
- `ANZ.AX` - ANZ Bank
- `NAB.AX` - National Australia Bank
- `MQG.AX` - Macquarie Group
- `SUN.AX` - Suncorp Group
- `QBE.AX` - QBE Insurance Group

### Example Output

When running `python app/main.py pre-trade --symbol QBE.AX`, you'll see:

```
🔍 Pre-Trade ML Analysis for QBE.AX
========================================

🌍 Analyzing economic context...
   Market Regime: Neutral

🏦 Analyzing sentiment for 1 banks...
   QBE.AX: Sentiment +0.007 (Confidence: 0.59)

🎯 Analyzing sector divergence...
   Sector Average: +0.000
   Divergent Banks: 0

🧠 Calculating ML trading scores...
   QBE.AX: ML Score 42.9/100 | HOLD | Risk: MEDIUM

📈 Generating trading recommendations...

✅ Complete ML analysis finished
ML Score: 42.9/100
Recommendation: HOLD
Risk Level: MEDIUM
Position Size: 4.5%
Economic Regime: Neutral

✅ Confidence Factors:
   • Strong economic context alignment

⚠️ Risk Factors:
   • Low ML model confidence

📊 Component Scores:
   Sentiment Strength: 0.7
   Sentiment Confidence: 59.0
   Economic Context: 81.3
   Divergence Score: 50.0
   Technical Momentum: 50.0
   Ml Prediction Confidence: 25.0
```

## Configuration Options

### Environment Variables

- `SKIP_TRANSFORMERS=1` - Skip downloading transformer models (reduces memory usage)
- `ALPACA_API_KEY` - Your Alpaca API key for paper trading
- `ALPACA_SECRET_KEY` - Your Alpaca secret key
- `ALPACA_BASE_URL` - Alpaca API base URL (paper trading: https://paper-api.alpaca.markets)

### News Sources

The system aggregates news from multiple sources:
- RSS feeds (ABC News, AFR, etc.)
- Yahoo Finance
- Google News
- Australian financial websites
- ASX announcements

## ML Features

### Sentiment Analysis Components

1. **Traditional Methods**:
   - VADER sentiment analysis
   - TextBlob sentiment analysis
   - Custom financial keyword analysis

2. **Advanced Transformer Models**:
   - FinBERT for financial sentiment
   - RoBERTa for general sentiment
   - Emotion detection models
   - News classification models

3. **ML Trading Features**:
   - Feature engineering for trading signals
   - ML model integration for predictions
   - Enhanced sentiment scoring
   - Market context analysis

### ML Score Calculation

The ML score (0-100) is calculated using weighted components:

```python
ml_score = (
    sentiment_strength * 0.25 +
    sentiment_confidence * 0.20 +
    economic_context * 0.20 +
    divergence_score * 0.15 +
    technical_momentum * 0.10 +
    ml_prediction_confidence * 0.10
)
```

## Troubleshooting

### Common Issues

1. **Transformer Loading Errors**:
   - Set `SKIP_TRANSFORMERS=1` to disable transformer models
   - Use Python 3.11 or 3.12 instead of 3.13

2. **Memory Issues**:
   - Transformer models require significant memory (~268MB download)
   - Consider running on a machine with at least 8GB RAM

3. **Network Issues**:
   - News scraping may fail due to rate limiting
   - Some websites may block automated requests

4. **Missing Dependencies**:
   - Ensure all packages in `requirements.txt` are installed
   - Check that scikit-learn, transformers, and torch are properly installed

### Performance Optimization

- The system caches sentiment analysis results for 30 minutes
- News articles are limited to the last 7 days for relevance
- Transformer models are loaded once and reused

## Future Enhancements

1. **Real Trading Integration**: Extend beyond paper trading to live markets
2. **Additional Data Sources**: Integrate more financial data providers
3. **Advanced ML Models**: Implement more sophisticated prediction models
4. **Risk Management**: Enhanced position sizing and risk controls
5. **Backtesting**: Historical performance analysis capabilities

## Support

For issues or questions:
1. Check the logs in the `logs/` directory
2. Review error messages in the terminal output
3. Ensure all dependencies are correctly installed
4. Verify your Python environment is properly activated

The system is designed to be robust and continue operating even if some components fail, providing graceful degradation of functionality.
