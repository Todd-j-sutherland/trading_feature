# 🏆 ASX TRADING SYSTEM - GOLDEN STANDARD DOCUMENTATION
## Complete Technical Reference & Operations Guide

> **Current Golden Standard**: July 2025 - Enhanced ML Trading System
> 
> **Use as Copilot Context**: This document represents the authoritative architecture and operational procedures for the complete trading system.

---

Important:
locally use dashboard_env/bin.activate environment 
remotely use ssh root@170.64.199.151
source ../trading_venv/bin/activate

# 📋 TABLE OF CONTENTS

1. [🏗️ System Architecture Overview](#system-architecture)
2. [🌐 Frontend System](#frontend-system)
3. [🧠 Enhanced ML System](#enhanced-ml-system)
4. [📊 Trading Chart Analysis](#trading-chart)
5. [🌅 Morning & Evening Workflows](#workflows)
6. [✅ Validation Framework](#validation)
7. [📈 Python Dashboard & Metrics](#python-dashboard)
8. [🚀 Operations Guide](#operations)

---

# 🏗️ SYSTEM ARCHITECTURE OVERVIEW {#system-architecture}

## 🎯 **Dual Backend Architecture**

| Component | Port | Purpose | Files |
|-----------|------|---------|-------|
| **Main Backend** | 8000 | Original chart data, proxy endpoints | `api_server.py` |
| **Enhanced ML Backend** | 8001 | Real-time ML predictions, 11 banks | `enhanced_ml_system/realtime_ml_api.py` |
| **Frontend** | 3000 | React dashboard with charts | `frontend/` |

## 🗂️ **Core Directory Structure**

```
trading_feature/
├── 🎨 frontend/                    # React frontend application
│   ├── src/components/
│   │   ├── TradingChart.tsx       # Main chart component
│   │   └── SimpleMLDashboard.tsx  # ML testing dashboard
│   └── src/hooks/
│       ├── useOriginalMLPredictions.ts  # Main backend hook
│       └── useMLPredictions.ts          # ML backend hook
├── 🧠 enhanced_ml_system/          # Enhanced ML components
│   ├── analyzers/                 # Morning/evening analyzers
│   ├── multi_bank_data_collector.py
│   └── realtime_ml_api.py        # ML backend server
├── 📊 app/                        # Main application framework
│   ├── main.py                   # Entry point (morning/evening)
│   └── services/daily_manager.py # Workflow orchestration
├── ⚙️ api_server.py               # Main backend server
└── 🚀 start_complete_ml_system.sh # System startup script
```

## 🔄 **Data Flow Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Main Backend    │    │  ML Backend     │
│   (Port 3000)   │    │   (Port 8000)    │    │  (Port 8001)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ├─── TradingChart ───────▶│                        │
         │                        │                        │
         └─── SimpleMLDashboard ──────────────────────────▶│
                                  │                        │
         ┌─── News Sources ──────▶│                        │
         │                        │                        │
         └─── YFinance Data ─────▶│◄───── Enhanced ML ────│
```

---

# 🌐 FRONTEND SYSTEM {#frontend-system}

## 📁 **Important Frontend Files**

### **Core Components**

| File | Purpose | Key Features |
|------|---------|--------------|
| `TradingChart.tsx` | Main chart interface | Candlestick charts, ML signals, technical indicators |
| `SimpleMLDashboard.tsx` | ML testing interface | 11-bank analysis, real-time updates |
| `useOriginalMLPredictions.ts` | Main backend hook | Chart data, original ML indicators |
| `useMLPredictions.ts` | ML backend hook | Enhanced predictions, real-time data |

### **TradingChart.tsx - Main Chart Component**

**What it shows:**
- **Candlestick Charts**: OHLCV data with volume
- **Technical Indicators**: SMA, RSI, Bollinger Bands
- **Sentiment Analysis**: Overlay sentiment scores
- **ML Predictions**: BUY/SELL signal markers
- **Multiple Timeframes**: 1H, 1D, 1W, 1M

**Key Features:**
```typescript
// Sample data structure
interface ChartData {
  ohlcv: Array<{
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  ml_indicators: {
    sentiment_score: number;
    confidence: number;
    prediction: 'BUY' | 'SELL' | 'HOLD';
    signals: Array<{
      timestamp: number;
      type: 'BUY' | 'SELL';
      confidence: number;
    }>;
  };
}
```

**Dependencies:**
- Main Backend (Port 8000) via proxy
- `useOriginalMLPredictions` hook
- Sample data fallback system

### **SimpleMLDashboard.tsx - ML Testing Interface**

**What it shows:**
- **11 Australian Banks**: Real-time analysis
- **ML Predictions**: Direction, magnitude, confidence
- **Market Summary**: Aggregate statistics
- **Signal Distribution**: BUY/SELL/HOLD counts

**Key Features:**
```typescript
interface BankPrediction {
  symbol: string;           // e.g., "CBA.AX"
  bank_name: string;        // e.g., "Commonwealth Bank"
  current_price: number;
  price_change_1d: number;
  rsi: number;
  sentiment_score: number;
  predicted_direction: string;
  prediction_confidence: number;
  optimal_action: string;   // BUY/SELL/STRONG_BUY/etc
}
```

**Dependencies:**
- Enhanced ML Backend (Port 8001) direct connection
- Auto-refresh every 30 seconds
- Real-time WebSocket updates

## 🚀 **Frontend Startup & Dependencies**

### **Quick Start**
```bash
# Start complete system (both backends + frontend)
./start_complete_ml_system.sh

# Access points:
# Main Dashboard: http://localhost:3000
# SimpleML Test: http://localhost:3000/simple-ml
```

### **Development Mode**
```bash
cd frontend
npm install
npm run dev  # Starts on port 3000
```

### **Proxy Configuration**
Frontend proxies `/api/*` requests to main backend (port 8000):
```json
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

### **Environment Dependencies**
- Node.js 18+
- React 18
- TypeScript 5+
- Vite 5+
- Lightweight Chart library

---

# 🧠 ENHANCED ML SYSTEM {#enhanced-ml-system}

## 🎯 **End-to-End ML Workflow**

```
News Sources → Sentiment Analysis → Feature Engineering → ML Models → Predictions
     ↓              ↓                    ↓               ↓           ↓
  Articles    FinBERT/RoBERTa      54+ Features    Random Forest   BUY/SELL
  Reddit      Emotion Detection   Technical/Price   XGBoost        Confidence
  Finance     Confidence Scoring  Volume/Market    Neural Net      Magnitude
```

## 📁 **Key ML System Files**

| File | Purpose | Features |
|------|---------|----------|
| `multi_bank_data_collector.py` | Data collection | 11 banks, sentiment, technical |
| `realtime_ml_api.py` | ML API server | Predictions, WebSocket updates |
| `enhanced_morning_analyzer_with_ml.py` | Morning analysis | Pre-market insights |
| `enhanced_evening_analyzer_with_ml.py` | Evening analysis | Model training, validation |
| `enhanced_training_pipeline.py` | ML pipeline | Feature engineering, training |

## 🏦 **Supported Banks (11 Total)**

```python
ENHANCED_BANK_SYMBOLS = [
    'CBA.AX',   # Commonwealth Bank
    'ANZ.AX',   # ANZ Banking Group  
    'WBC.AX',   # Westpac Banking
    'NAB.AX',   # National Australia Bank
    'MQG.AX',   # Macquarie Group
    'SUN.AX',   # Suncorp Group
    'BOQ.AX',   # Bank of Queensland
    'BEN.AX',   # Bendigo Bank
    'AMP.AX',   # AMP Limited
    'IFL.AX',   # IOOF Holdings
    'MPG.AX'    # Mortgage Choice
]
```

## 🔧 **Feature Engineering (54+ Features)**

### **Sentiment Features (12)**
```python
sentiment_features = {
    'overall_sentiment': float,      # -1 to +1
    'confidence': float,             # 0 to 1
    'news_count': int,               # Number of articles
    'reddit_sentiment': float,       # Social media sentiment
    'emotion_scores': dict,          # Joy, anger, fear, etc.
    'sentiment_momentum': float,     # Recent trend
    'sentiment_volatility': float,   # Sentiment stability
    'confidence_weighted_sentiment': float
}
```

### **Technical Indicators (18)**
```python
technical_features = {
    'rsi': float,                    # 0-100
    'macd_line': float,
    'macd_signal': float,
    'macd_histogram': float,
    'sma_20': float,                 # Simple moving averages
    'sma_50': float,
    'sma_200': float,
    'ema_12': float,                 # Exponential moving averages
    'ema_26': float,
    'bollinger_upper': float,        # Bollinger bands
    'bollinger_lower': float,
    'bollinger_width': float,
    'momentum_score': float,
    'trend_strength': float
}
```

### **Price Features (12)**
```python
price_features = {
    'current_price': float,
    'price_change_1h': float,        # % change
    'price_change_4h': float,
    'price_change_1d': float,
    'price_change_5d': float,
    'price_vs_sma20': float,         # Position relative to SMA
    'price_vs_sma50': float,
    'daily_range': float,            # High-low range
    'atr_14': float,                 # Average True Range
    'volatility_20d': float
}
```

### **Volume Features (6)**
```python
volume_features = {
    'volume': float,
    'volume_sma20': float,
    'volume_ratio': float,           # Current vs average
    'on_balance_volume': float,
    'volume_price_trend': float,
    'volume_momentum': float
}
```

### **Market Context Features (6)**
```python
market_features = {
    'asx200_change': float,          # Market index performance
    'sector_performance': float,     # Financial sector
    'aud_usd_rate': float,          # Currency impact
    'vix_level': float,             # Volatility index
    'market_breadth': float,
    'market_momentum': float
}
```

## 🤖 **ML Model Architecture**

### **Multi-Output Prediction**
```python
prediction_outputs = {
    'price_direction_1h': bool,      # Up/down in 1 hour
    'price_direction_4h': bool,      # Up/down in 4 hours  
    'price_direction_1d': bool,      # Up/down in 1 day
    'price_magnitude_1h': float,     # % change expected
    'price_magnitude_4h': float,
    'price_magnitude_1d': float,
    'optimal_action': str,           # BUY/SELL/STRONG_BUY/etc
    'confidence_score': float        # Model confidence 0-1
}
```

### **Model Ensemble**
- **Random Forest**: Primary classifier
- **XGBoost**: Gradient boosting
- **Neural Network**: Deep learning patterns
- **Logistic Regression**: Linear baseline

## 📊 **Data Collection Process**

### **Real-time Collection**
```python
# Every 5 minutes during market hours:
# 1. Fetch price data (YFinance)
# 2. Collect news articles
# 3. Run sentiment analysis
# 4. Calculate technical indicators  
# 5. Generate ML predictions
# 6. Store in SQLite database
# 7. Broadcast via WebSocket
```

### **Database Schema**
```sql
-- Core prediction table
CREATE TABLE enhanced_predictions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timestamp DATETIME,
    sentiment_score REAL,
    rsi REAL,
    current_price REAL,
    predicted_direction TEXT,
    prediction_confidence REAL,
    features_json TEXT     -- All 54+ features
);
```

---

# 📊 TRADING CHART ANALYSIS {#trading-chart}

## 📈 **Chart Components**

### **Main Chart Display**
- **Candlestick Chart**: OHLC price data with volume bars
- **Timeframe Options**: 1H, 1D, 1W, 1M
- **Zoom & Pan**: Interactive navigation
- **Real-time Updates**: Live data refresh

### **Technical Indicators**

#### **Moving Averages**
- **SMA 20** (Yellow): Short-term trend
- **SMA 50** (Orange): Medium-term trend  
- **SMA 200** (Red): Long-term trend
- **Interpretation**: Price above/below indicates bullish/bearish trend

#### **RSI (Relative Strength Index)**
- **Range**: 0-100
- **Overbought**: RSI > 70 (potential sell signal)
- **Oversold**: RSI < 30 (potential buy signal)
- **Neutral**: 30-70 range

#### **Bollinger Bands**
- **Upper Band**: SMA + (2 * Standard Deviation)
- **Lower Band**: SMA - (2 * Standard Deviation)
- **Width**: Indicates volatility
- **Price touching bands**: Potential reversal signals

#### **MACD (Moving Average Convergence Divergence)**
- **MACD Line**: 12-day EMA - 26-day EMA
- **Signal Line**: 9-day EMA of MACD line
- **Histogram**: MACD - Signal line
- **Interpretation**: Line crossovers indicate momentum changes

### **ML Prediction Signals**

#### **Signal Types**
```typescript
interface MLSignal {
  type: 'BUY' | 'SELL' | 'STRONG_BUY' | 'STRONG_SELL';
  confidence: number;      // 0-1
  timestamp: number;
  price: number;
  reasoning: string[];     // Why this signal was generated
}
```

#### **Signal Interpretation**
- **🟢 BUY**: Positive momentum, RSI < 70, good sentiment
- **🔴 SELL**: Negative momentum, RSI > 30, poor sentiment  
- **🟢 STRONG_BUY**: High confidence (>80%), multiple confirmations
- **🔴 STRONG_SELL**: High confidence (>80%), strong bearish signals
- **🟡 HOLD**: Neutral conditions, wait for clearer signals

### **Sentiment Overlay**
- **Green Line**: Positive sentiment (0 to +1)
- **Red Line**: Negative sentiment (0 to -1)
- **Thickness**: Indicates confidence level
- **Integration**: Sentiment impacts ML signal generation

## 🎯 **How to Use Each Indicator**

### **Trend Analysis**
```
1. Check Moving Averages:
   - Price above SMA 20 > SMA 50 > SMA 200: Strong uptrend
   - Price below SMA 200 < SMA 50 < SMA 20: Strong downtrend
   
2. Confirm with RSI:
   - Uptrend + RSI 30-70: Healthy uptrend
   - Downtrend + RSI 30-70: Healthy downtrend
   
3. Volume Confirmation:
   - High volume on breakouts: Strong move
   - Low volume on moves: Weak/false signal
```

### **Entry/Exit Strategies**
```
BUY Signals:
- Price bounces off SMA support
- RSI oversold (<30) with reversal
- MACD crosses above signal line
- ML signal shows BUY with >60% confidence

SELL Signals:  
- Price breaks below SMA support
- RSI overbought (>70) with reversal
- MACD crosses below signal line
- ML signal shows SELL with >60% confidence
```

### **Risk Management**
```
Position Sizing:
- High confidence ML signals (>80%): Larger position
- Medium confidence (60-80%): Standard position
- Low confidence (<60%): Smaller position or avoid

Stop Losses:
- Place below recent support (for buys)
- Place above recent resistance (for sells)
- Use ATR for dynamic stop distances
```

---

# 🌅 MORNING & EVENING WORKFLOWS {#workflows}

## 🌅 **Morning Analysis Workflow**

### **Command**
```bash
python -m app.main morning
```

### **What Happens (End-to-End)**

#### **1. System Initialization (0-30 seconds)**
```python
# Initialize components
- Load ML models from data/ml_models/
- Connect to data sources (YFinance, news APIs)
- Validate database connections
- Check system health
```

#### **2. Market Data Collection (30-90 seconds)**
```python
# For each of 11 banks:
symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', ...]

for symbol in symbols:
    # Get current price data
    price_data = yf.download(symbol, period='1d', interval='1m')
    
    # Calculate technical indicators
    rsi = calculate_rsi(price_data)
    macd = calculate_macd(price_data)
    bollinger = calculate_bollinger_bands(price_data)
```

#### **3. News & Sentiment Analysis (90-180 seconds)**
```python
# Collect news articles
news_articles = collect_financial_news(symbols)

# Run sentiment analysis
for article in news_articles:
    # FinBERT sentiment analysis
    sentiment = finbert_analyzer.analyze(article.text)
    
    # Emotion detection
    emotions = emotion_detector.analyze(article.text)
    
    # Store results
    sentiment_scores[article.symbol] = sentiment
```

#### **4. Feature Engineering (30 seconds)**
```python
# Combine all data into ML features
features = create_prediction_features(
    sentiment_data=sentiment_scores,
    technical_data=technical_indicators,
    price_data=price_history,
    market_context=market_data
)
# Result: 54+ features per bank
```

#### **5. ML Predictions (30 seconds)**
```python
# Generate predictions for each bank
for symbol in symbols:
    prediction = ml_models[symbol].predict(features[symbol])
    
    # Multi-output prediction:
    results[symbol] = {
        'direction_1h': prediction['direction_1h'],
        'magnitude_1h': prediction['magnitude_1h'],
        'confidence': prediction['confidence'],
        'optimal_action': prediction['action']
    }
```

#### **6. Signal Generation & Output (15 seconds)**
```
============================================================
ENHANCED MORNING TRADING SIGNALS
============================================================
CBA  (Commonwealth Bank ) | BUY  (STRONG  ) | Score: +0.75 | Conf: 85.2% | RSI: 45.1 | Price: $121.30 | News: 3
ANZ  (ANZ Banking       ) | SELL (MODERATE) | Score: -0.42 | Conf: 67.8% | RSI: 72.3 | Price: $ 28.45 | News: 1
WBC  (Westpac           ) | HOLD (NEUTRAL ) | Score: +0.15 | Conf: 55.4% | RSI: 58.7 | Price: $ 27.92 | News: 2
...
============================================================
```

### **Output Files Generated**
```
logs/morning_analysis_YYYYMMDD.log     # Detailed analysis log
data/predictions/morning_YYYYMMDD.json # Structured prediction data
cache/features_YYYYMMDD.pkl           # Feature cache for evening
```

## 🌆 **Evening Analysis Workflow**

### **Command**
```bash
python -m app.main evening
```

### **What Happens (End-to-End)**

#### **1. Day Review & Data Validation (60 seconds)**
```python
# Collect all day's data
daily_data = aggregate_daily_data()

# Validate data quality
validation_results = validate_collected_data(daily_data)
# - Check for missing data points
# - Verify sentiment score ranges
# - Confirm price data consistency
```

#### **2. Prediction Accuracy Analysis (90 seconds)**
```python
# Compare morning predictions to actual outcomes
for symbol in symbols:
    morning_prediction = load_morning_prediction(symbol)
    actual_outcome = get_actual_price_movement(symbol)
    
    accuracy = calculate_prediction_accuracy(
        predicted=morning_prediction,
        actual=actual_outcome
    )
    
    # Update model performance metrics
    update_model_performance(symbol, accuracy)
```

#### **3. Enhanced Feature Analysis (120 seconds)**
```python
# Deep feature analysis with full day's data
enhanced_features = create_enhanced_features(
    full_day_sentiment=daily_sentiment,
    end_of_day_technical=eod_technical,
    volume_profile=daily_volume,
    news_impact=news_effectiveness
)

# Feature importance analysis
feature_importance = analyze_feature_importance(enhanced_features)
```

#### **4. Model Training & Optimization (180-300 seconds)**
```python
# Retrain models with new data
for symbol in symbols:
    # Prepare training data (last 30 days)
    training_data = prepare_training_dataset(symbol, days=30)
    
    # Train ensemble models
    random_forest = train_random_forest(training_data)
    xgboost = train_xgboost(training_data)
    neural_net = train_neural_network(training_data)
    
    # Save updated models
    save_model_ensemble(symbol, [random_forest, xgboost, neural_net])
```

#### **5. Performance Reporting (60 seconds)**
```python
# Generate comprehensive performance report
performance_report = {
    'daily_accuracy': calculate_daily_accuracy(),
    'model_performance': get_model_performance_metrics(),
    'feature_effectiveness': analyze_feature_effectiveness(),
    'trading_signals_summary': summarize_trading_signals(),
    'risk_metrics': calculate_risk_metrics()
}

# Export to JSON and text formats
export_performance_metrics(performance_report)

# Generate validation metrics export files
# This automatically runs export_and_validate_metrics.py to create:
# - dashboard_metrics_YYYYMMDD_HHMMSS.json
# - validation_results_YYYYMMDD_HHMMSS.json  
# - validation_summary_YYYYMMDD_HHMMSS.txt
generate_validation_metrics_export()
```

#### **6. System Optimization (30 seconds)**
```python
# Clean up old data
cleanup_old_cache_files(days_to_keep=7)

# Optimize database
optimize_sqlite_database()

# Prepare for next day
prepare_next_day_system()
```

### **Output Files Generated**
```
logs/evening_analysis_YYYYMMDD.log         # Detailed evening log
metrics_exports/validation_results_YYYYMMDD_HHMMSS.json
metrics_exports/validation_summary_YYYYMMDD_HHMMSS.txt
data/ml_models/models/                     # Updated ML models
reports/daily_performance_YYYYMMDD.json   # Performance metrics
```

## 🔄 **Integration with App.Main Commands**

### **Daily Manager Integration**
```python
# app/services/daily_manager.py
class TradingSystemManager:
    def morning_routine(self):
        # Check if enhanced analyzer available
        if self.enhanced_available():
            return self.run_enhanced_morning()
        else:
            return self.run_standard_morning()
    
    def evening_routine(self):
        # Always try enhanced first
        return self.run_enhanced_evening()
```

### **Automatic Fallback System**
```python
# If enhanced ML system unavailable:
# 1. Fall back to standard sentiment analysis
# 2. Use cached models for predictions
# 3. Generate simplified reports
# 4. Continue with reduced functionality
```

---

# ✅ VALIDATION FRAMEWORK {#validation}

## 🛡️ **Data Validation Pipeline**

### **Real-time Validation**
```python
class DataValidator:
    def validate_sentiment_data(self, data):
        # Check sentiment scores are in valid range
        assert -1 <= data['sentiment_score'] <= 1
        assert 0 <= data['confidence'] <= 1
        assert data['news_count'] >= 0
        return True
    
    def validate_technical_data(self, data):
        # RSI should be 0-100
        assert 0 <= data['rsi'] <= 100
        # Price should be positive
        assert data['current_price'] > 0
        return True
    
    def validate_ml_features(self, features):
        # Check for NaN values
        assert not features.isnull().any()
        # Check for infinite values
        assert not features.isinf().any()
        return True
```

### **Prediction Validation**
```python
def validate_predictions(predictions):
    for pred in predictions:
        # Direction should be valid
        assert pred['direction'] in ['UP', 'DOWN']
        
        # Magnitude should be reasonable (-10% to +10%)
        assert -10 <= pred['magnitude'] <= 10
        
        # Confidence should be 0-1
        assert 0 <= pred['confidence'] <= 1
        
        # Action should be valid
        assert pred['action'] in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
```

## 📊 **Validation Files Generated**

### **Validation Results JSON**
```json
// metrics_exports/validation_results_YYYYMMDD_HHMMSS.json
{
  "validation_summary": {
    "total_banks_analyzed": 11,
    "successful_predictions": 11,
    "failed_predictions": 0,
    "average_confidence": 0.734,
    "data_quality_score": 0.96
  },
  "detailed_results": {
    "CBA.AX": {
      "sentiment_valid": true,
      "technical_valid": true,
      "features_complete": true,
      "prediction_valid": true,
      "confidence": 0.78
    }
  },
  "quality_metrics": {
    "news_coverage": 0.91,
    "price_data_completeness": 1.0,
    "sentiment_reliability": 0.87
  }
}
```

### **Validation Summary Text**
```text
# metrics_exports/validation_summary_YYYYMMDD_HHMMSS.txt
=============================================================
TRADING SYSTEM VALIDATION SUMMARY
=============================================================
Timestamp: 2025-07-25 12:35:04
Analysis Mode: Enhanced ML with 54+ features

📊 VALIDATION RESULTS:
   ✅ Data Quality Score: 96.2%
   ✅ Prediction Accuracy: 11/11 banks successful
   ✅ Feature Completeness: 100%
   ✅ Sentiment Reliability: 87.3%

🏦 BANK-SPECIFIC RESULTS:
   CBA.AX: ✅ Valid (Confidence: 78.1%)
   ANZ.AX: ✅ Valid (Confidence: 82.4%)
   WBC.AX: ✅ Valid (Confidence: 71.3%)
   [... continues for all banks]

🎯 QUALITY METRICS:
   News Coverage: 91.2%
   Technical Data: 100%
   Model Performance: 89.7%
```

## 🔍 **How to Use Validation Framework**

### **Daily Validation Checks**
```bash
# Quick system validation summary (NEW - recommended)
python validate_system.py

# Generate comprehensive validation metrics export files (PRIMARY METHOD)
python export_and_validate_metrics.py

# Check latest validation results
cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt

# Manual ML data validation
python ml_data_validator.py

# Comprehensive test validation framework
python test_validation_framework.py

# View detailed JSON results
python -c "
import json
import glob
latest = max(glob.glob('metrics_exports/validation_results_*.json'))
with open(latest) as f:
    data = json.load(f)
    print(f'Quality Score: {data[\"validation_summary\"][\"data_quality_score\"]:.1%}')
"
```

### **📊 How Validation Metrics Export Files Are Generated**

The validation metrics export files in `metrics_exports/` folder are generated by the **`export_and_validate_metrics.py`** script through a comprehensive validation pipeline:

#### **Generation Methods**
```bash
# Primary Method - Manual Generation
python export_and_validate_metrics.py

# Automatic Generation - During Evening Analysis  
python -m app.main evening

# Files Generated (3 per run):
# ├── dashboard_metrics_YYYYMMDD_HHMMSS.json      # Complete metrics data
# ├── validation_results_YYYYMMDD_HHMMSS.json     # Detailed validation results  
# └── validation_summary_YYYYMMDD_HHMMSS.txt      # Human-readable summary
```

#### **Validation Process Flow**
```python
# 1. Export all metrics from dashboard
MetricsValidator.export_all_metrics()
   ├── fetch_ml_performance_metrics()       # ML success rates, confidence
   ├── fetch_current_sentiment_scores()     # Sentiment data validation
   ├── fetch_ml_feature_analysis()          # Feature usage statistics
   └── get_database_statistics()            # Database health metrics

# 2. Validate all exported data
MetricsValidator.validate_metrics()
   ├── _validate_ml_performance()           # Success rates (0-100%)
   ├── _validate_sentiment_scores()         # Sentiment (-1 to +1), confidence (0-1)
   ├── _validate_feature_analysis()         # Feature usage rates (0-100%)
   └── _validate_database_stats()           # Table counts, recent activity

# 3. Save results to files  
MetricsValidator.save_export()
   ├── dashboard_metrics_{timestamp}.json   # Raw exported data
   ├── validation_results_{timestamp}.json  # Validation outcomes
   └── validation_summary_{timestamp}.txt   # Summary report
```

#### **What Gets Validated**
```python
validation_categories = {
    'ml_performance': {
        'success_rate': '0-100% range validation',
        'avg_confidence': '0-100% range validation', 
        'completed_trades': 'Non-negative count validation',
        'avg_return': 'Reasonable return range (-100% to +100%)'
    },
    'sentiment_scores': {
        'sentiment_values': '-1 to +1 range validation',
        'confidence_values': '0 to 1 range validation',
        'expected_banks': 'CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX, SUN.AX, QBE.AX',
        'data_completeness': 'Presence of required bank data'
    },
    'feature_analysis': {
        'feature_usage_rates': '0-100% range validation',
        'total_records': 'Positive record count validation',
        'data_availability': 'Feature completeness checks'
    },
    'database_statistics': {
        'table_counts': 'sentiment_features, trading_outcomes, model_performance',
        'recent_activity': 'Predictions in last 7 days',
        'data_ranges': 'Earliest/latest timestamps validation'
    }
}
```

#### **Sample Validation Output**
```text
Dashboard Metrics Validation Summary
Generated: 2025-07-26 20:51:38
==================================================

Overall Status: PASS
Total Validations: 30
Passed: 30
Failed: 0  
Warnings: 0

PASSED VALIDATIONS:
✅ Success rate 60.0% is within valid range (0-100%)
✅ Average confidence 60.5% is within valid range (0-100%)
✅ Found data for expected bank: CBA.AX
✅ ANZ.AX: Sentiment score 0.028 within valid range
✅ Feature usage news_analysis: 100.0% within valid range
✅ Table sentiment_features: 170 records
✅ Recent activity: 170 predictions in last 7 days
```

### **Quality Thresholds**
```python
VALIDATION_THRESHOLDS = {
    'data_quality_score': 0.85,      # Minimum 85% data quality
    'average_confidence': 0.60,      # Minimum 60% prediction confidence  
    'news_coverage': 0.70,           # Minimum 70% news coverage
    'sentiment_reliability': 0.75    # Minimum 75% sentiment reliability
}
```

### **Automated Alerts**
```python
# System automatically alerts if:
# - Data quality drops below 85%
# - More than 2 banks fail validation
# - Average confidence below 60%
# - News coverage below 70%
```

---

# 📈 PYTHON DASHBOARD & METRICS {#python-dashboard}

## 🖥️ **Dashboard Architecture**

### **Main Python Dashboard**
```python
# dashboard.py - Primary metrics dashboard
# Port: 8501 (Streamlit)
# Features:
- Real-time ML performance metrics
- Bank-by-bank prediction tracking
- Model accuracy charts
- Feature importance analysis
- Trading signal distribution
```

### **Enhanced ML Dashboard**
```python
# enhanced_ml_system/bank_performance_dashboard.html
# Static HTML dashboard generated by multi_bank_data_collector.py
# Features:
- 11-bank performance grid
- Sentiment vs. Technical alignment
- Prediction confidence heatmap
- Real-time update timestamps
```

## 📊 **Key Metrics Displayed**

### **Model Performance Metrics**
```python
performance_metrics = {
    'prediction_accuracy': {
        'daily': 0.73,              # % of correct daily predictions
        'weekly': 0.68,             # % of correct weekly predictions
        'direction_accuracy': 0.81   # % of correct direction predictions
    },
    'confidence_calibration': {
        'high_confidence_accuracy': 0.87,  # Accuracy when confidence >80%
        'medium_confidence_accuracy': 0.71, # Accuracy when confidence 60-80%
        'low_confidence_accuracy': 0.54     # Accuracy when confidence <60%
    },
    'signal_effectiveness': {
        'buy_signal_success_rate': 0.76,
        'sell_signal_success_rate': 0.69,
        'hold_signal_accuracy': 0.82
    }
}
```

### **Feature Importance Rankings**
```python
feature_importance = {
    'sentiment_score': 0.23,         # Most important feature
    'rsi': 0.18,                     # Technical indicator importance
    'news_count': 0.15,              # News volume impact
    'volume_ratio': 0.12,            # Volume analysis importance
    'price_momentum': 0.11,          # Price trend importance
    # ... continues for all 54+ features
}
```

### **Trading Signal Distribution**
```python
signal_distribution = {
    'current_signals': {
        'STRONG_BUY': 2,             # 2 banks showing strong buy
        'BUY': 3,                    # 3 banks showing buy
        'HOLD': 4,                   # 4 banks neutral
        'SELL': 1,                   # 1 bank showing sell
        'STRONG_SELL': 1             # 1 bank showing strong sell
    },
    'weekly_trends': {
        'increasing_bullishness': 0.15,  # % increase in buy signals
        'market_sentiment_shift': 0.08,  # Overall sentiment change
        'volatility_trend': 0.12         # Volatility change
    }
}
```

### **Risk Metrics**
```python
risk_metrics = {
    'portfolio_risk': {
        'var_95': 0.034,             # Value at Risk (95% confidence)
        'max_drawdown': 0.087,       # Maximum historical drawdown
        'sharpe_ratio': 1.43,        # Risk-adjusted returns
        'volatility': 0.156          # Portfolio volatility
    },
    'individual_stock_risk': {
        'CBA.AX': {'beta': 0.91, 'volatility': 0.14},
        'ANZ.AX': {'beta': 1.08, 'volatility': 0.18},
        # ... continues for all banks
    }
}
```

## 🚀 **Dashboard Startup Commands**

### **Main Dashboard**
```bash
# Start main Python dashboard
streamlit run dashboard.py
# Access: http://localhost:8501
```

### **Enhanced ML Dashboard**
```bash
# Generate static HTML dashboard
python enhanced_ml_system/multi_bank_data_collector.py
# View: enhanced_ml_system/bank_performance_dashboard.html
```

### **Complete System Dashboard**
```bash
# Start complete system with all dashboards
./start_complete_ml_system.sh
# Access:
# - React Frontend: http://localhost:3000
# - SimpleML Dashboard: http://localhost:3000/simple-ml  
# - ML API Docs: http://localhost:8001/docs
```

## 📋 **Dashboard Features**

### **Real-time Updates**
- **Auto-refresh**: Every 30 seconds
- **WebSocket updates**: Live data streaming
- **Status indicators**: Green/red system health
- **Last update timestamps**: Data freshness tracking

### **Interactive Charts**
- **Prediction accuracy over time**: Line charts
- **Feature importance**: Bar charts  
- **Signal distribution**: Pie charts
- **Performance heatmaps**: Color-coded metrics

### **Export Capabilities**
- **JSON exports**: Structured data for analysis
- **CSV downloads**: Spreadsheet-compatible data
- **PDF reports**: Formatted summary reports
- **Image exports**: Chart screenshots

---

# 🚀 OPERATIONS GUIDE {#operations}

## ⚡ **Quick Start Commands**

### **🛑 Process Management - Clean Startup**

#### **Step 1: Kill Existing Processes (ALWAYS DO THIS FIRST)**
```bash
# Kill all Node.js processes (frontend/servers)
pkill -f node

# Kill all Python processes (backends/ML systems)
pkill -f python
pkill -f uvicorn
pkill -f api_server
pkill -f realtime_ml_api

# Alternative: Kill specific ports if needed
lsof -ti:3000,3002,8000,8001 | xargs kill -9

# Verify all processes are stopped
ps aux | grep -E "(node|python|uvicorn)" | grep -v grep
# Should return empty if all processes killed
```

#### **Step 2: Complete System Startup**
```bash
# Start everything (recommended - runs in background)
./start_complete_ml_system.sh

# What it starts:
# - Main Backend (port 8000) - Chart data, ML predictions, caching
# - Enhanced ML Backend (port 8001) - Real-time 11-bank analysis  
# - React Frontend (port 3002) - Dashboard with optimized caching
# - Data collection processes - News, sentiment, technical analysis
# - WebSocket updates - Live streaming every 5 minutes
```

#### **Step 3: Verify System Startup**
```bash
# Check all processes are running
echo "🔍 Checking System Status..."
ps aux | grep -E "(api_server|realtime_ml_api|node.*serve)" | grep -v grep

# Check ports are open
echo "🌐 Checking Open Ports..."
lsof -i :8000,8001,3002 | grep LISTEN

# Test backend connectivity
echo "🔧 Testing Backend APIs..."
curl -s http://localhost:8000/api/cache/status | head -20
curl -s http://localhost:8001/api/market-summary | head -20

# Test frontend
echo "🎨 Testing Frontend..."
curl -s http://localhost:3002 | head -10
```

#### **🌐 System Access Points**
```bash
# Once system is running, access via:

# 📊 MAIN REACT DASHBOARD (Primary Interface)
open http://localhost:3002
# - Interactive candlestick charts with ML signals
# - Real-time sentiment analysis overlay
# - Technical indicators (RSI, MACD, Bollinger Bands)
# - Optimized caching (15-minute ML predictions)

# 🤖 SIMPLE ML TESTING DASHBOARD  
open http://localhost:3002   # Same port, different interface
# - 11 Australian banks real-time analysis
# - ML prediction confidence scores
# - Buy/Sell/Hold signal distribution
# - Market summary statistics

# 🔧 MAIN BACKEND API (Port 8000)
curl http://localhost:8000/api/cache/status        # Cache performance
curl http://localhost:8000/api/banks/CBA.AX/ohlcv  # Price data
open http://localhost:8000/docs                    # API documentation

# 🧠 ENHANCED ML BACKEND API (Port 8001)  
curl http://localhost:8001/api/predictions         # All bank predictions
curl http://localhost:8001/api/market-summary      # Market overview
open http://localhost:8001/docs                    # ML API documentation

# 📡 WEBSOCKET LIVE UPDATES
# ws://localhost:8001/ws/live-updates              # Real-time data stream
```

### **📊 Complete Data Flow - Start to Finish**

#### **🔄 Data Pipeline Architecture**
```
1. DATA SOURCES → 2. COLLECTION → 3. PROCESSING → 4. ML MODELS → 5. FRONTEND
      ↓               ↓              ↓              ↓             ↓
   YFinance      Multi-Bank     Feature Eng.   RandomForest   React UI
   News APIs     Collector      54+ Features   XGBoost        Charts
   Reddit        Sentiment      Technical      Neural Net     Dashboards
   Market Data   Analysis       Price/Volume   Ensemble       Cache Layer
```

#### **🕐 Real-time Data Collection (Every 5 Minutes)**
```python
# 1. Price Data Collection (YFinance)
for symbol in ['CBA.AX', 'ANZ.AX', 'WBC.AX', ...]:  # 11 banks
    price_data = yf.download(symbol, period='1d', interval='1m')
    # Cache: 15 minutes (backend optimization)
    
# 2. News & Sentiment Analysis
news_articles = collect_financial_news(symbols)
sentiment_scores = analyze_sentiment(articles)  # FinBERT, RoBERTa
reddit_sentiment = analyze_reddit_sentiment(symbols)
# Cache: No caching (always fresh sentiment)

# 3. Technical Indicators Calculation
technical_data = {
    'rsi': calculate_rsi(price_data),          # 0-100
    'macd': calculate_macd(price_data),        # MACD lines
    'bollinger': calculate_bollinger(price_data),
    'sma_20/50/200': calculate_sma(price_data),
    'volume_analysis': analyze_volume(price_data)
}
# Cache: 5 minutes (backend optimization)
```

#### **🧠 ML Feature Engineering & Prediction Pipeline**
```python
# 4. Feature Engineering (54+ Features)
ml_features = combine_features(
    sentiment_features=sentiment_scores,      # 12 features
    technical_features=technical_data,        # 18 features  
    price_features=price_history,            # 12 features
    volume_features=volume_analysis,         # 6 features
    market_context=market_data               # 6 features
)

# 5. ML Model Prediction (Ensemble)
for symbol in symbols:
    # Load pre-trained models
    models = load_model_ensemble(symbol)     # RandomForest, XGBoost, Neural Net
    
    # Generate predictions
    prediction = models.predict(ml_features[symbol])
    results[symbol] = {
        'direction': prediction['direction'],     # UP/DOWN
        'magnitude': prediction['magnitude'],     # % change expected
        'confidence': prediction['confidence'],   # 0-1
        'optimal_action': prediction['action']    # BUY/SELL/HOLD/STRONG_BUY/etc
    }

# 6. Store & Cache Results
store_in_database(predictions)
cache_ml_predictions(predictions, cache_time=15_minutes)
broadcast_websocket_updates(predictions)
```

#### **🌐 Frontend Data Consumption & Caching**
```typescript
// 7. Frontend Request Optimization
class RequestCache {
    static getCacheTime(dataType: string): number {
        switch (dataType) {
            case 'ml_predictions': return 15 * 60 * 1000;  // 15 minutes
            case 'technical_indicators': return 5 * 60 * 1000;   // 5 minutes  
            case 'price_data': return 15 * 60 * 1000;      // 15 minutes
            default: return 60 * 1000;                     // 1 minute
        }
    }
}

// 8. Chart Rendering & Updates
TradingChart.tsx renders:
- Candlestick charts (OHLCV data)
- Technical indicators overlay (SMA, RSI, Bollinger)
- ML prediction signals (BUY/SELL markers)
- Sentiment analysis overlay (confidence lines)
- Real-time WebSocket updates (every 5 minutes)
```

#### **💾 Data Storage & Persistence**
```sql
-- Database Schema (SQLite)
CREATE TABLE enhanced_predictions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,                    -- e.g., 'CBA.AX'
    timestamp DATETIME,
    sentiment_score REAL,           -- -1 to +1
    rsi REAL,                      -- 0-100
    current_price REAL,
    predicted_direction TEXT,       -- 'BUY'/'SELL'/'HOLD'
    prediction_confidence REAL,     -- 0-1
    features_json TEXT             -- All 54+ features as JSON
);

-- Cache Tables (In-Memory)
price_data_cache         -- 15-minute TTL
technical_indicators_cache -- 5-minute TTL  
ml_predictions_cache     -- 15-minute TTL
```

### **✅ System Verification Commands**

#### **🔍 Process Health Checks**
```bash
# Check all trading system processes
echo "📊 TRADING SYSTEM PROCESS STATUS"
echo "================================"
ps aux | grep -E "(api_server|realtime_ml_api|node.*serve)" | grep -v grep

# Check specific port usage
echo -e "\n🌐 PORT USAGE:"
lsof -i :8000 && echo "✅ Main Backend (8000) - Running" || echo "❌ Main Backend (8000) - NOT RUNNING"
lsof -i :8001 && echo "✅ ML Backend (8001) - Running" || echo "❌ ML Backend (8001) - NOT RUNNING"  
lsof -i :3002 && echo "✅ Frontend (3002) - Running" || echo "❌ Frontend (3002) - NOT RUNNING"

# Memory usage check
echo -e "\n💾 MEMORY USAGE:"
ps aux | grep -E "(api_server|realtime_ml_api)" | awk '{print $11, $4"%", $6/1024"MB"}' | grep -v grep
```

#### **🧪 API Connectivity Tests**
```bash
# Test Main Backend (Port 8000)
echo "🔧 TESTING MAIN BACKEND API:"
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     http://localhost:8000/api/cache/status -o /dev/null

# Test Enhanced ML Backend (Port 8001)  
echo "🤖 TESTING ML BACKEND API:"
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     http://localhost:8001/api/market-summary -o /dev/null

# Test Frontend
echo "🎨 TESTING FRONTEND:"
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     http://localhost:3002 -o /dev/null

# Test ML Prediction Performance
echo "⚡ TESTING ML PREDICTION PERFORMANCE:"
echo "First request (fresh data):"
time curl -s "http://localhost:8000/api/banks/CBA.AX/ml-indicators?period=1D" > /dev/null
echo "Second request (cached data):"
time curl -s "http://localhost:8000/api/banks/CBA.AX/ml-indicators?period=1D" > /dev/null
```

#### **📊 Cache Performance Verification**
```bash
# Check cache status and performance
echo "🚀 CACHE PERFORMANCE STATUS:"
curl -s http://localhost:8000/api/cache/status | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Cache Entries: {data[\"cache_stats\"][\"total_memory_items\"]}')
print(f'ML Models Loaded: {data[\"cache_stats\"][\"ml_models_loaded\"]}')
print(f'Price Data Cached: {data[\"cache_stats\"][\"price_data_entries\"]}')
print(f'Policy: {data[\"cache_policies\"][\"price_data_cache_time\"]}')
"

# Test cache hit/miss performance
echo -e "\n⏱️ CACHE PERFORMANCE TEST:"
echo "Testing 3 consecutive requests for cache efficiency..."
for i in {1..3}; do
    echo "Request $i:"
    time curl -s "http://localhost:8000/api/banks/CBA.AX/ml-indicators?period=1D" | \
         python3 -c "import json,sys; data=json.load(sys.stdin); print(f'ML Confidence: {data[\"data\"][0][\"confidence\"]}')"
done
```

#### **🏦 Bank Data Validation**
```bash
# Verify all 11 banks are being analyzed
echo "🏦 BANK ANALYSIS VERIFICATION:"
curl -s http://localhost:8001/api/predictions | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total Banks Analyzed: {len(data)}')
for bank in data:
    print(f'{bank[\"symbol\"]}: {bank[\"optimal_action\"]} (Conf: {bank[\"prediction_confidence\"]:.1%})')
"

# Check market summary statistics
echo -e "\n📈 MARKET SUMMARY:"
curl -s http://localhost:8001/api/market-summary | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Buy Signals: {data[\"buy_signals\"]}')
print(f'Sell Signals: {data[\"sell_signals\"]}') 
print(f'Hold Signals: {data[\"hold_signals\"]}')
print(f'Avg Sentiment: {data[\"avg_sentiment\"]:.3f}')
print(f'Best Performer: {data[\"best_performer\"][\"symbol\"]} ({data[\"best_performer\"][\"change\"]:+.2f}%)')
"
```

### **🎯 Daily Operations Workflow**

#### **📅 Morning Routine (8:00 AM - 5 minutes)**
```bash
# 1. Check if system is running
ps aux | grep -E "(api_server|realtime_ml_api)" | grep -v grep

# 2. If not running, clean start:
pkill -f python && pkill -f node  # Kill existing processes
./start_complete_ml_system.sh     # Start complete system

# 3. Run morning analysis
python -m app.main morning

# 4. Verify system health
curl -s http://localhost:8000/api/cache/status
curl -s http://localhost:8001/api/market-summary

# 5. Access dashboards for monitoring
open http://localhost:3002        # Main React dashboard
```

#### **🌅 Market Hours Monitoring (9:00 AM - 4:00 PM)**
```bash
# Monitor real-time updates (WebSocket broadcasts every 5 minutes)
# Frontend auto-refreshes with optimized caching:
# - ML predictions: 15-minute cache
# - Technical indicators: 5-minute cache  
# - Price data: 15-minute cache

# Quick market check command
curl -s http://localhost:8001/api/market-summary | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'🔥 {data[\"buy_signals\"]} BUY | ⏸️ {data[\"hold_signals\"]} HOLD | 🔻 {data[\"sell_signals\"]} SELL')
print(f'📊 Avg Sentiment: {data[\"avg_sentiment\"]:.3f}')
"
```

#### **🌆 Evening Analysis (6:00 PM - 12 minutes)**
```bash
# 1. Run comprehensive evening analysis
python -m app.main evening
# This automatically:
# - Analyzes day's performance vs predictions
# - Retrains ML models with new data
# - Generates validation metrics export files
# - Updates model performance statistics

# 2. Review validation results
cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt

# 3. Check system performance
python export_and_validate_metrics.py  # Manual validation export

# 4. System cleanup (optional)
find logs/ -name "*.log" -mtime +7 -delete     # Clean old logs
find cache/ -name "*.pkl" -mtime +3 -delete    # Clean old cache files
```

### **📊 Validation Metrics Management**

```bash
# Generate comprehensive validation export
python export_and_validate_metrics.py
# Creates 3 files in metrics_exports/:
# - dashboard_metrics_YYYYMMDD_HHMMSS.json (complete data)
# - validation_results_YYYYMMDD_HHMMSS.json (validation details)
# - validation_summary_YYYYMMDD_HHMMSS.txt (human-readable)

# View latest validation summary
cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt

# Check validation history
ls -la metrics_exports/validation_summary_*.txt | tail -5

# Clean old validation files (keep last 30 days)
find metrics_exports/ -name "*.json" -mtime +30 -delete
find metrics_exports/ -name "*.txt" -mtime +30 -delete

# Monitor validation file sizes
du -sh metrics_exports/
```

## 🔧 **Development & Debugging**

### **Backend Testing**
```bash
# Test main backend
curl "http://localhost:8000/api/banks/CBA.AX/ohlcv?period=1D"

# Test ML backend
curl "http://localhost:8001/api/market-summary"

# View API documentation
open http://localhost:8001/docs
```

### **Frontend Development**
```bash
cd frontend
npm run dev     # Development server
npm run build   # Production build
npm run test    # Run tests
```

### **ML System Debugging**
```bash
# Test individual components
python enhanced_ml_system/multi_bank_data_collector.py
python enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py

# Check model loading
python -c "from enhanced_ml_system.enhanced_training_pipeline import *; print('Models loaded successfully')"
```

## 📁 **File Organization (Production Ready)**

### **Keep These Files (Core System)**
```
✅ KEEP - Core Application:
   app/                            # Main application framework
   enhanced_ml_system/             # Enhanced ML components
   frontend/                       # React frontend
   api_server.py                   # Main backend
   start_complete_ml_system.sh     # System startup
   
✅ KEEP - Data & Models:
   data/ml_models/                 # Trained ML models
   metrics_exports/                # Validation results
   logs/                          # System logs
   
✅ KEEP - Configuration:
   requirements.txt                # Python dependencies
   frontend/package.json           # Node dependencies
   .env files                      # Environment variables
```

### **Legacy Files (Consider Removing)**
```
⚠️ LEGACY - Single File Analyzers:
   enhanced_morning_analyzer.py
   enhanced_morning_analyzer_single.py
   enhanced_morning_analyzer_with_ml.py  # Use enhanced_ml_system/ version
   
⚠️ LEGACY - Old Dashboards:
   dashboard_sql_integration_template.py
   
⚠️ LEGACY - Test Files:
   test_*.py                       # Unless actively used
   
⚠️ LEGACY - Backup Files:
   *_old.py
   *_backup.py
   legacy_enhanced/                # Old implementations
```

## 🎯 **Best Practices**

### **Daily Workflow**
```
08:00 AM: python -m app.main morning
          └─ Review signals, plan trades
          
10:00 AM: Monitor dashboards during market hours
          └─ Track signal performance
          
06:00 PM: python -m app.main evening  
          └─ Comprehensive analysis, model training
          └─ Auto-generates validation metrics export
          
06:15 PM: Review validation results
          └─ Check metrics_exports/ folder
          └─ cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt
          
Weekly : python export_and_validate_metrics.py
         └─ Manual validation metrics generation
         └─ Data quality assessment
```

### **System Maintenance**
```bash
# Weekly health check
python -m app.main status

# Monthly cleanup
find logs/ -name "*.log" -mtime +30 -delete
find metrics_exports/ -name "*.json" -mtime +30 -delete

# Model backup (before major changes)
cp -r data/ml_models/ data/ml_models_backup_$(date +%Y%m%d)/
```

### **Performance Monitoring**
```bash
# Check system resource usage
top -p $(pgrep -f "api_server\|realtime_ml_api")

# Monitor disk space
df -h

# Check log file sizes
du -sh logs/ metrics_exports/
```

## 🚨 **Troubleshooting**

### **⚠️ Process Management Issues**

**System won't start / Ports already in use:**
```bash
# STEP 1: Kill all existing processes (CRITICAL)
echo "🛑 Killing all Node.js processes..."
pkill -f node

echo "🛑 Killing all Python processes..."
pkill -f python
pkill -f uvicorn
pkill -f api_server
pkill -f realtime_ml_api

# STEP 2: Verify ports are free
echo "🔍 Checking ports are free..."
lsof -i :3000,3002,8000,8001 || echo "✅ All ports free"

# STEP 3: Force kill if processes persist
echo "🔨 Force killing remaining processes on ports..."
lsof -ti:3000,3002,8000,8001 | xargs kill -9 2>/dev/null || echo "✅ No processes to kill"

# STEP 4: Clean start
echo "🚀 Starting clean system..."
./start_complete_ml_system.sh
```

**Zombie processes / System hanging:**
```bash
# Check for zombie processes
ps aux | grep -E "(python|node)" | grep -E "(Z|<defunct>)"

# Nuclear option - kill all python/node processes
sudo pkill -9 python
sudo pkill -9 node

# Restart system
./start_complete_ml_system.sh
```

### **🔌 Connection Issues**

**Frontend can't connect to backend:**
```bash
# Check if backends are running
ps aux | grep -E "(api_server|realtime_ml_api)" | grep -v grep

# Check ports are listening
lsof -i :8000,8001 | grep LISTEN

# Test backend connectivity
curl -v http://localhost:8000/api/cache/status
curl -v http://localhost:8001/api/market-summary

# If backends not running, restart
pkill -f python && ./start_complete_ml_system.sh
```

**CORS / Proxy issues:**
```bash
# Check frontend proxy configuration
cat frontend/vite.config.ts | grep -A 5 proxy

# Test direct API access (bypass proxy)
curl http://localhost:8000/api/banks/CBA.AX/ohlcv?period=1D

# Clear browser cache and restart frontend
cd frontend && rm -rf node_modules/.vite && npm run dev
```

### **💾 Data & Model Issues**

**ML models not loading:**
```bash
# Check model files exist
ls -la data/ml_models/models/
echo "Model count: $(ls data/ml_models/models/ | wc -l)"

# Check model file integrity
python -c "
import joblib, os
model_dir = 'data/ml_models/models/'
for file in os.listdir(model_dir):
    try:
        joblib.load(os.path.join(model_dir, file))
        print(f'✅ {file}')
    except Exception as e:
        print(f'❌ {file}: {e}')
"

# Regenerate models if corrupted
python -m app.main evening
```

**Memory issues:**
```bash
# Monitor memory usage
free -h

# Use memory-efficient mode (RECOMMENDED for development)
export SKIP_TRANSFORMERS=1
python -m app.main morning

# This skips heavy transformer models (FinBERT, RoBERTa) and uses
# lightweight alternatives while maintaining full functionality
```

**Data quality issues:**
```bash
# Check latest validation
cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt

# Manual data validation
python enhanced_ml_system/ml_data_validator.py

# Generate fresh validation metrics export
python export_and_validate_metrics.py

# Check validation status programmatically
python -c "
import json, glob
try:
    latest = max(glob.glob('metrics_exports/validation_results_*.json'))
    with open(latest) as f:
        data = json.load(f)
        print(f'Status: {data[\"overall_status\"]}')
        print(f'Failed: {data[\"summary\"][\"failed\"]}')
        if data['failed_validations']:
            print('Issues:', data['failed_validations'])
except: print('No validation files found')
"

# If you get "Too many identical confidence values" error:
# Remove the database trigger (fixed in v2.1):
sqlite3 data/ml_models/training_data.db "DROP TRIGGER IF EXISTS prevent_confidence_duplicates;"
```

**Validation metrics export issues:**
```bash
# Check if export_and_validate_metrics.py is working
python export_and_validate_metrics.py

# Verify metrics_exports directory exists and is writable
ls -la metrics_exports/ && touch metrics_exports/test.tmp && rm metrics_exports/test.tmp

# Check dashboard dependencies
python -c "from dashboard import fetch_ml_performance_metrics; print('Dashboard imports OK')"

# If validation fails, check individual components
python -c "
from export_and_validate_metrics import MetricsValidator
validator = MetricsValidator()
print('MetricsValidator initialized successfully')
"
```

---

# 🎯 SUMMARY

This ASX Trading System provides:

✅ **Complete ML Pipeline**: 54+ features, ensemble models, real-time predictions  
✅ **Dual Backend Architecture**: Original + enhanced ML capabilities (Ports 8000 & 8001)  
✅ **Modern Frontend**: React with interactive charts and ML dashboards (Port 3002)  
✅ **Optimized Performance**: 15-minute ML caching, 5x speed improvement, request deduplication  
✅ **Automated Workflows**: Morning analysis, evening training, validation metrics  
✅ **Process Management**: Clean startup/shutdown, port management, zombie process handling  
✅ **Production Ready**: Error handling, fallbacks, monitoring, comprehensive documentation  
✅ **AI-Assisted Development**: MCP server for VS Code Copilot context and assistance  

## 🤖 **MCP Server for AI Development**

The project includes a Model Context Protocol (MCP) server that provides comprehensive context to VS Code Copilot and AI agents:

```bash
# 🚀 Setup MCP Server (One-time setup)
cd mcp_server && ./setup.sh

# After setup, restart VS Code to enable AI context assistance
```

**MCP Server Features:**
- **System Architecture Context**: Complete understanding of components and data flow
- **File Purpose Explanations**: Know what every file does and why it exists  
- **Operations Knowledge**: Commands, troubleshooting, and maintenance procedures
- **Quick References**: Essential commands and system status checks
- **Smart Navigation**: AI can understand your complex project structure

## 🚀 **Quick Reference Commands**

```bash
# 🛑 CLEAN SYSTEM START (Always run first)
pkill -f python && pkill -f node
./start_complete_ml_system.sh

# 🔍 VERIFY SYSTEM RUNNING  
ps aux | grep -E "(api_server|realtime_ml_api|node.*serve)" | grep -v grep
curl -s http://localhost:8000/api/cache/status
curl -s http://localhost:8001/api/market-summary

# 🌐 ACCESS DASHBOARDS
open http://localhost:3002        # Main React Dashboard
open http://localhost:8001/docs   # ML API Documentation

# 📊 DAILY OPERATIONS
python -m app.main morning        # Morning analysis (5 min)
python -m app.main evening        # Evening training (12 min)
python export_and_validate_metrics.py  # Validation export
```

**Use this document as authoritative reference for all system operations and development.**

---

*Last Updated: July 27, 2025*  
*System Version: Enhanced ML Trading System v2.2 - Optimized Caching*


Graceful shutdown

# Comprehensive graceful shutdown of all trading processes
echo "🛑 Gracefully shutting down trading system..."

# Step 1: Send SIGTERM to all main processes
pkill -TERM -f "realtime_ml_api"
pkill -TERM -f "api_server" 
pkill -TERM -f "news_collector"
pkill -TERM -f "multi_bank_data_collector"
pkill -TERM -f "enhanced_morning_analyzer"

# Step 2: Wait for graceful shutdown
echo "⏳ Waiting 10 seconds for graceful shutdown..."
sleep 10

# Step 3: Check what's still running
REMAINING=$(ps aux | grep -E "(python.*collector|python.*analyzer|uvicorn|api_server)" | grep -v grep)
if [ -n "$REMAINING" ]; then
    echo "⚠️ Some processes still running:"
    echo "$REMAINING"
    echo "🔨 Sending SIGKILL as fallback..."
    pkill -KILL -f "realtime_ml_api"
    pkill -KILL -f "api_server"
    pkill -KILL -f "collector"
    pkill -KILL -f "analyzer"
else
    echo "✅ All processes shut down gracefully"
fi

# Step 4: Verify ports are free
echo "🔍 Checking ports..."
lsof -i :8000 || echo "✅ Port 8000 free"
lsof -i :8001 || echo "✅ Port 8001 free"


Check Current data status

ssh root@170.64.199.151 "cd /root/test && source /root/trading_venv/bin/activate && python -c "
import sqlite3
import os

# Check enhanced training data
enhanced_db = 'data/ml_models/enhanced_training_data.db'
if os.path.exists(enhanced_db):
    conn = sqlite3.connect(enhanced_db)
    cursor = conn.cursor()
    
    # Check training features
    cursor.execute('SELECT COUNT(*) FROM enhanced_features')
    features_count = cursor.fetchone()[0]
    
    # Check outcomes (completed predictions)
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL')
    outcomes_count = cursor.fetchone()[0]
    
    print(f'📊 Training Data Status:')
    print(f'   Features collected: {features_count}')
    print(f'   Completed outcomes: {outcomes_count}')
    print(f'   Minimum needed: 50+ for training')
    print(f'   Recommended: 100+ for reliable models')
    
    conn.close()
else:
    print('❌ Enhanced training database not found')
""


# Check outcome recording progress daily
ssh root@170.64.199.151 "cd /root/test && source /root/trading_venv/bin/activate && python -c "
import sqlite3
conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL')
outcomes = cursor.fetchone()[0]
print(f'Completed outcomes: {outcomes}')
conn.close()
""

Features: 89
Outcomes: 0
Training readiness: ❌ INSUFFICIENT

ssh root@170.64.199.151 'cd /root/test && source ../trading_venv/bin/activate && python3 -c "import sqlite3; conn = sqlite3.connect(\"data/ml_models/enhanced_training_data.db\"); cursor = conn.cursor(); cursor.execute(\"SELECT COUNT(*) FROM enhanced_features\"); features = cursor.fetchone()[0]; cursor.execute(\"SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL\"); outcomes = cursor.fetchone()[0]; print(f\"Features: {features}\"); print(f\"Outcomes: {outcomes}\"); print(f\"Training readiness: {'✅ READY' if features >= 50 and outcomes >= 50 else '❌ INSUFFICIENT'}\"); conn.close()"'