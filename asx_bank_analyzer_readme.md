# ASX Bank News Trading Analyzer

A sophisticated Python-based system for analyzing Australian banking sector sentiment through multi-source news analysis, economic indicators, and technical analysis to generate actionable trading signals.

## 🎯 Overview

This system provides comprehensive sentiment analysis for Australian banks by combining:
- **Multi-source news analysis** (RSS feeds, web scraping, Reddit, official announcements)
- **Economic sentiment monitoring** (RBA decisions, economic indicators, regulatory changes)
- **Technical analysis integration** (momentum indicators, price trends)
- **Machine learning predictions** (trained on historical sentiment-price correlations)
- **Real-time dashboard visualization** (Streamlit-based interactive dashboards)

### Key Features

- 📰 **Real-time news aggregation** from 15+ Australian financial sources
- 🤖 **Advanced NLP sentiment analysis** using traditional methods + transformer models
- 📊 **Economic context integration** for sector-wide impact assessment
- 📈 **Technical momentum analysis** with multi-timeframe support
- 🧠 **ML-powered predictions** with continuous learning capabilities
- 🎯 **Divergence signal detection** for identifying outperformers/underperformers
- 📱 **Interactive dashboards** for monitoring and analysis
- ⚡ **Automated trading signals** with confidence scoring

## 🏗️ Architecture

```
ASX Bank News Trading Analyzer/
├── src/
│   ├── news_sentiment.py           # Core sentiment analysis engine
│   ├── economic_sentiment_analyzer.py # Market-wide economic analysis
│   ├── technical_analysis.py       # Technical indicators and momentum
│   ├── data_feed.py               # Market data fetching (yfinance)
│   ├── ml_training_pipeline.py    # ML model training and updates
│   ├── sentiment_history.py       # Historical data management
│   ├── news_impact_analyzer.py    # Correlation analysis
│   └── bank_keywords.py           # Enhanced keyword filtering
├── config/
│   └── settings.py                # System configuration
├── utils/
│   └── cache_manager.py           # Caching utilities
├── data/
│   ├── sentiment_history/         # Historical sentiment data
│   ├── ml_models/                 # Trained ML models
│   └── active_trades.json         # Trading signal tracking
├── scripts/
│   ├── news_trading_analyzer.py   # Main entry point
│   ├── enhanced_news_trading_system.py # Economic integration
│   ├── news_analysis_dashboard.py # Technical analysis dashboard
│   └── economic_sentiment_dashboard.py # Economic sentiment dashboard
└── reports/                       # Generated analysis reports
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (3.11 or 3.12 recommended for full transformer support)
- 8GB+ RAM recommended for transformer models
- Internet connection for real-time data feeds

### Installation

```bash
# Clone the repository
git clone https://github.com/yourrepo/asx-bank-analyzer.git
cd asx-bank-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Analyze single bank
python news_trading_analyzer.py -s CBA.AX

# Analyze all major banks
python news_trading_analyzer.py --all

# Enhanced analysis with economic context
python news_trading_analyzer.py -s CBA.AX --enhanced

# Export results
python news_trading_analyzer.py --all --export
```

### Running Dashboards

```bash
# Technical analysis dashboard
streamlit run news_analysis_dashboard.py

# Economic sentiment dashboard
streamlit run economic_sentiment_dashboard.py
```

## 📊 System Components

### 1. News Sentiment Analysis (`news_sentiment.py`)

**Purpose**: Aggregates and analyzes news from multiple sources

**Data Sources**:
- RSS Feeds: Reuters, Bloomberg, AFR
- Web Scraping: ABC News, News.com.au, The Market Online
- Yahoo Finance API
- Reddit (r/AusFinance, r/ASX_Bets)
- ASX Official Announcements

**Sentiment Methods**:
- TextBlob polarity analysis
- VADER sentiment scoring
- Transformer models (FinBERT, RoBERTa) if available
- Custom financial keyword weighting

**Output**:
```python
{
    'symbol': 'CBA.AX',
    'overall_sentiment': 0.234,  # -1 to 1 scale
    'confidence': 0.78,          # 0 to 1 scale
    'news_count': 15,
    'significant_events': {...},
    'recent_headlines': [...]
}
```

### 2. Economic Sentiment Analyzer (`economic_sentiment_analyzer.py`)

**Purpose**: Monitors broad economic factors affecting all banks

**Categories Tracked**:
- **RBA Policy** (90% correlation): Interest rate decisions, monetary policy
- **Economic Indicators** (70% correlation): GDP, inflation, employment
- **Banking Regulation** (85% correlation): APRA rules, compliance changes
- **Global Economy** (60% correlation): International markets, trade
- **Financial Stability** (95% correlation): Systemic risks, credit conditions

**Market Regime Detection**:
- Expansion: Positive growth, supportive conditions
- Contraction: Economic weakness, defensive positioning
- Tightening: Rising rates, margin pressure
- Easing: Rate cuts, growth concerns
- Neutral: Stable conditions

### 3. Technical Analysis (`technical_analysis.py`)

**Indicators Calculated**:
- **Momentum**: RSI, MACD, price rate of change
- **Trend**: Moving averages (20, 50, 200), trend strength
- **Volume**: Volume ratio, accumulation/distribution
- **Volatility**: ATR, Bollinger Bands

**Timeframes**:
- Short-term: 3 days (1-hour bars)
- Medium-term: 2 weeks (4-hour bars)
- Long-term: 3 months (daily bars)

### 4. Machine Learning Pipeline (`ml_training_pipeline.py`)

**Features Used**:
- Sentiment scores and confidence
- News volume and distribution
- Reddit sentiment metrics
- Event detection flags
- Time-based features
- Technical indicators

**Models**:
- Random Forest (primary)
- Gradient Boosting
- Neural Networks
- XGBoost (if available)

**Training Process**:
1. Collects sentiment data with `collect_training_data()`
2. Records actual price outcomes with `record_trading_outcome()`
3. Trains models when sufficient data available
4. Updates predictions in real-time

### 5. Enhanced Keyword System (`bank_keywords.py`)

**Filtering Categories**:
- Bank-specific keywords and variations
- Event type detection (dividends, earnings, scandals)
- Urgency indicators
- Sentiment modifiers
- Risk keywords

**Relevance Scoring**:
- Matches keywords across title and content
- Weights by category importance
- Considers urgency and time decay
- Outputs relevance score 0-1

## 📈 Trading Signal Generation

### Signal Flow

1. **Individual Bank Analysis**
   - Collect news from all sources
   - Calculate base sentiment score
   - Apply ML predictions if available
   - Generate initial signal

2. **Economic Adjustment**
   - Analyze market-wide economic sentiment
   - Determine market regime
   - Adjust bank sentiment ±20% based on economic context
   - Boost/reduce confidence based on data quality

3. **Divergence Detection**
   - Compare bank sentiment to sector average
   - Identify outperformers (positive divergence)
   - Flag underperformers (negative divergence)
   - Generate opportunity signals

4. **Final Signal Generation**
   ```
   STRONG_BUY:  Sentiment > 0.3, Confidence > 0.7, Positive momentum
   BUY:         Sentiment > 0.1, Confidence > 0.5
   HOLD:        -0.1 < Sentiment < 0.1 or Low confidence
   SELL:        Sentiment < -0.1, Confidence > 0.5
   STRONG_SELL: Sentiment < -0.3, Confidence > 0.7, Negative momentum
   ```

### Confidence Scoring

Confidence increases with:
- Multiple reliable news sources (up to 25%)
- Consistent sentiment across sources (up to 15%)
- Significant events detected (up to 5%)
- Successful transformer model analysis (up to 12%)
- Strong ML model predictions (up to 8%)

## 🎮 Dashboard Features

### News Analysis Dashboard (`news_analysis_dashboard.py`)

- **Market Overview**: Sentiment scores for all banks
- **Technical Analysis**: Momentum and trend indicators
- **Individual Bank Details**: Deep dive into each bank
- **ML Predictions**: Model confidence and signals
- **Combined Analysis**: News + Technical signals

### Economic Sentiment Dashboard (`economic_sentiment_dashboard.py`)

- **Economic Overview**: Market regime and risk levels
- **Category Breakdown**: Sentiment by economic factor
- **Risk Monitor**: Active risk factors and mitigation
- **Trading Signals**: Adjusted recommendations
- **Divergence Opportunities**: Outlier identification

## 🔧 Configuration

### Settings (`config/settings.py`)

```python
# Key configuration options
BANK_SYMBOLS = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
CACHE_EXPIRY_MINUTES = 30
ML_CONFIDENCE_THRESHOLD = 0.6
SENTIMENT_ADJUSTMENT_FACTOR = 0.2
```

### Environment Variables

```bash
# Optional - for enhanced features
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
SKIP_TRANSFORMERS=1  # Skip large model downloads
```

## 📊 Data Management

### Historical Data Storage

- **Sentiment History**: JSON files per symbol (30-day retention)
- **ML Training Data**: SQLite database with features and outcomes
- **Model Versions**: Timestamped model files with metadata
- **Cache**: In-memory with configurable expiry

### Data Quality

The system includes validation for:
- Missing data handling
- Outlier detection
- Timestamp consistency
- Duplicate removal
- Source reliability scoring

## 🚨 Risk Management

### Built-in Safeguards

1. **Confidence Thresholds**: Only trade on high-confidence signals
2. **Divergence Limits**: Flag unusual bank-specific movements
3. **Risk Monitoring**: Track sector-wide risk factors
4. **Position Sizing**: Recommendations based on market regime
5. **Time Decay**: Reduce weight of older news

### Risk Categories Monitored

- **Market Risk**: Volatility, correlation breakdown
- **Regulatory Risk**: Policy changes, compliance issues
- **Economic Risk**: Recession, credit cycle
- **Operational Risk**: Bank-specific issues
- **Systemic Risk**: Financial stability concerns

## 🔄 Continuous Improvement

### ML Model Updates

```bash
# Retrain models with latest data
python scripts/retrain_ml_models.py

# Backtest model performance
python scripts/ml_backtester.py --symbol CBA.AX --days 90
```

### Performance Monitoring

The system tracks:
- Prediction accuracy
- Signal profitability
- False positive/negative rates
- Feature importance evolution

## 🛠️ Advanced Usage

### Custom Analysis Pipeline

```python
from src.news_sentiment import NewsSentimentAnalyzer
from src.economic_sentiment_analyzer import EconomicSentimentAnalyzer

# Initialize analyzers
news_analyzer = NewsSentimentAnalyzer()
econ_analyzer = EconomicSentimentAnalyzer()

# Get individual bank sentiment
bank_sentiment = news_analyzer.analyze_bank_sentiment('CBA.AX')

# Get economic context
econ_sentiment = econ_analyzer.analyze_economic_sentiment()

# Combine for final signal
if econ_sentiment['market_regime']['regime'] == 'expansion':
    adjusted_signal = bank_sentiment['overall_sentiment'] * 1.2
else:
    adjusted_signal = bank_sentiment['overall_sentiment'] * 0.8
```

### Batch Processing

```python
# Analyze multiple banks with economic context
analyzer = EnhancedNewsTradingAnalyzer()
results = analyzer.analyze_with_economic_context()  # All banks

# Export for further analysis
analyzer.export_analysis(results, 'full_analysis.json')
```

## 📈 Performance Considerations

### System Requirements

- **Minimum**: 4GB RAM, Python 3.8+
- **Recommended**: 8GB RAM, Python 3.11+
- **Optimal**: 16GB RAM, GPU for transformers

### Optimization Tips

1. **Caching**: Adjust cache expiry based on trading frequency
2. **Transformer Models**: Use `SKIP_TRANSFORMERS=1` for faster analysis
3. **Parallel Processing**: Run multiple symbols concurrently
4. **Database Indexing**: Index sentiment history by symbol and timestamp

## 🐛 Troubleshooting

### Common Issues

1. **No transformer models loading**
   - Solution: Use Python 3.11 or 3.12, install PyTorch/TensorFlow

2. **Rate limiting on news sources**
   - Solution: Increase delays in scraping, use caching

3. **ML predictions unavailable**
   - Solution: Ensure sufficient training data (100+ samples)

4. **Dashboard not updating**
   - Solution: Clear cache with refresh button, check data feeds

## 📚 Dependencies

### Core Requirements
```
pandas>=1.3.0
numpy>=1.21.0
yfinance>=0.2.18
beautifulsoup4>=4.9.3
requests>=2.26.0
streamlit>=1.20.0
plotly>=5.0.0
scikit-learn>=1.0.0
textblob>=0.15.3
vaderSentiment>=3.3.2
feedparser>=6.0.0
praw>=7.0.0
```

### Optional (Enhanced Features)
```
transformers>=4.30.0
torch>=2.0.0  # or tensorflow>=2.13.0
xgboost>=1.7.0
optuna>=3.0.0
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This system is for educational and research purposes. Always perform your own due diligence before making trading decisions. Past performance does not guarantee future results.

## 🙏 Acknowledgments

- Australian financial news providers
- Open source sentiment analysis libraries
- ASX for market data access
- Reddit communities for social sentiment data