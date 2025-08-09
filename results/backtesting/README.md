# Comprehensive Backtesting System

## Overview

This backtesting system analyzes historical trading performance using all available data sources in your trading platform. It combines multiple analysis approaches to provide comprehensive insights into strategy effectiveness.

## Features

### 📊 Data Sources Analyzed

1. **Yahoo Finance Historical Prices**
   - Real-time price data and charts
   - Technical indicators (RSI, MACD, Moving Averages)
   - Volume and volatility analysis

2. **News Sentiment Analysis** 
   - Sentiment scores from news articles
   - Confidence levels and news volume impact
   - Economic context integration

3. **Social Media Sentiment** (when available)
   - Social media sentiment tracking
   - Momentum and trend analysis

4. **Technical Analysis Metrics**
   - RSI, MACD, Bollinger Bands
   - Moving average crossovers
   - Support/resistance levels

5. **Machine Learning Predictions**
   - Multi-timeframe predictions (1h, 4h, 1d)
   - Ensemble model confidence scores
   - Direction and magnitude forecasts

6. **Combined Strategy Signals**
   - Weighted combination of all signals
   - Smoothed composite indicators
   - Risk-adjusted recommendations

## How to Use

### Quick Start (Recommended)

```bash
python -m app.main simple-backtest
```

This runs the lightweight backtesting system that:
- ✅ Works without external dependencies
- ✅ Generates HTML, CSV, and text reports
- ✅ Analyzes all available data in your databases
- ✅ Creates visual signal charts

### Advanced Usage

```bash
python -m app.main backtest              # Full backtesting with charts
python -m app.main backtest-dashboard    # Interactive dashboard
```

## Generated Reports

### 1. HTML Visualization (`backtesting_chart.html`)
Interactive charts showing:
- Signal strength over time
- Strategy comparison
- Individual symbol performance
- Confidence levels with color coding

### 2. CSV Data Export (`backtesting_signals.csv`)
Raw data including:
- Timestamps and symbols
- Signal types (BUY/SELL/HOLD)
- Confidence scores
- Strategy classifications

### 3. Summary Report (`backtesting_summary.txt`)
Statistical analysis covering:
- Overall performance metrics
- Strategy-specific breakdown
- Signal distribution analysis
- Symbol-by-symbol performance

## Results Interpretation

### Signal Types
- **BUY**: Bullish recommendation
- **SELL**: Bearish recommendation  
- **HOLD**: Neutral/wait recommendation

### Confidence Scores
- **0.7+**: High confidence signal
- **0.5-0.7**: Moderate confidence
- **0.3-0.5**: Low confidence
- **Below 0.3**: Very low confidence

### Strategy Types
- **Traditional**: Technical analysis + sentiment
- **ML**: Machine learning predictions
- **Evening_ML**: Enhanced ML with full feature set

## Performance Metrics

### Recent Results Summary
```
Total Signals Analyzed: 511
Unique Symbols: 7 (All major banks)
Strategies Analyzed: 3
Date Range: Jul 27 - Aug 8, 2025

Signal Distribution:
- HOLD: 88.6% (452 signals) 
- BUY: 7.3% (37 signals)
- SELL: 4.1% (22 signals)

Strategy Performance:
- Traditional: 0.511 avg confidence, 175 signals
- ML: 0.500 avg confidence, 168 signals
- Evening_ML: 0.600 avg confidence, 168 signals

Individual Symbol Performance (3-month):
- CBA.AX: +6.71% return, 17.54% volatility
- WBC.AX: +10.36% return, 17.94% volatility  
- ANZ.AX: +8.11% return, 17.15% volatility
- NAB.AX: +8.35% return, 16.78% volatility
- MQG.AX: +11.40% return, 23.86% volatility
- SUN.AX: -0.44% return, 16.63% volatility
- QBE.AX: -2.02% return, 24.60% volatility
```

## Key Insights

1. **Conservative Approach**: System tends toward HOLD signals (88.6%), indicating cautious strategy
2. **Balanced Coverage**: All 7 bank symbols receive equal analysis (73 signals each on average)
3. **Strategy Performance**: Evening ML shows higher confidence (0.600) compared to Traditional (0.511) and Standard ML (0.500)
4. **Risk Management**: Low percentage of SELL signals suggests focus on capital preservation
5. **Market Performance**: Most banks showed positive 3-month returns, with MQG leading at +11.40%
6. **Volatility Range**: Bank volatilities cluster around 16-18%, except MQG and QBE with higher volatility (23-24%)
7. **Mixed Results**: While most banks performed well, SUN.AX and QBE.AX showed negative returns

## Customization Options

### Symbol Selection
The system analyzes these ASX bank stocks by default:
- CBA.AX (Commonwealth Bank)
- WBC.AX (Westpac)
- ANZ.AX (ANZ Banking)
- NAB.AX (National Australia Bank)
- MQG.AX (Macquarie Group)
- SUN.AX (Suncorp Group)
- QBE.AX (QBE Insurance)

### Time Periods
- Default: 3 months historical analysis
- Configurable: 1 month to 1 year
- Real-time: Latest signals prioritized

## Technical Implementation

### Database Sources
- `trading_unified.db`: Consolidated trading data
- `trading_data.db`: Enhanced analysis results
- `ml_models/enhanced_training_data.db`: ML training data

### Signal Processing
1. Data extraction from SQLite databases
2. JSON parsing of complex signal structures
3. Confidence score normalization
4. Strategy classification and comparison

### Visualization Engine
- Pure HTML/CSS for compatibility
- Color-coded signal strength
- Responsive design for mobile/desktop
- No external dependencies required

## Troubleshooting

### Common Issues

**No data available**: 
- Ensure databases exist in `data/` directory
- Run morning/evening analysis first to populate data

**Low signal count**:
- Check database schema matches expected format
- Verify JSON parsing in signal extraction

**Missing visualizations**:
- HTML file generated in `results/backtesting/`
- Open directly in web browser
- Check file permissions

### Support

For technical issues:
1. Check the generated log files
2. Verify database connectivity
3. Ensure proper Python environment setup
4. Review signal extraction logic for schema changes

## Future Enhancements

### Planned Features
- [ ] Real-time signal streaming
- [ ] Portfolio optimization integration
- [ ] Risk metric calculations
- [ ] Benchmark comparison (S&P 500, ASX 200)
- [ ] Advanced statistical analysis
- [ ] Machine learning model performance tracking

### Integration Opportunities
- Alpaca trading execution
- Real-time data feeds
- Advanced charting libraries
- Mobile app integration
- API endpoints for external tools

---

**Generated**: August 8, 2025  
**Version**: 1.0.0  
**Compatibility**: Python 3.7+, SQLite 3.0+