# Trading System Components Documentation

## 📋 Overview

This document maps all the key files and components that contribute to the three main pillars of the trading application:

1. **Predictions** - Generate trading signals
2. **Outcomes** - Evaluate prediction performance
3. **Machine Learning** - Train and improve models

---

## 🔮 PREDICTIONS - Trading Signal Generation

### Core Prediction Engines

#### 1. **Enhanced Efficient Prediction System** ⭐

- **File**: `enhanced_efficient_system_news_volume_clean.py`
- **Purpose**: Main production prediction engine with technical analysis
- **Features**: 53 technical features, RSI, MACD, moving averages, volume analysis
- **Schedule**: Every 30 minutes during market hours (10 AM - 4 PM AEST)
- **Output**: BUY/SELL/HOLD signals with confidence scores
- **Key Class**: `EnhancedEfficientPredictionSystem`

#### 2. **Fixed Price Mapping System** ⭐

- **File**: `production/cron/fixed_price_mapping_system.py`
- **Purpose**: Scheduled prediction generation via cron
- **Schedule**: `*/30 0-5 * * 1-5` (Every 30 min, weekdays, 00:00-05:59 UTC)
- **Integration**: Calls enhanced efficient system
- **Database**: Stores predictions in `trading_predictions.db`

#### 3. **Market-Aware Prediction System**

- **File**: `paper-trading-app/app/core/ml/prediction/market_aware_predictor.py`
- **Class**: `MarketAwarePricePredictor`
- **Purpose**: ML-based predictions with market context
- **Features**: Volume trends, news sentiment, market regime detection
- **Special**: Implements ML HOLD bias fixes and volume validation

#### 4. **True Prediction Engine**

- **File**: `data_quality_system/core/true_prediction_engine.py`
- **Class**: `TruePredictionEngine`
- **Purpose**: Rule-based fallback when ML models unavailable
- **Logic**: RSI, MACD, sentiment, volume ratio analysis

### Prediction Components & Features

#### **Technical Analysis Engine**

- **File**: `enhanced_efficient_system_news_volume_clean.py` (internal class)
- **Features**: RSI, MACD, Bollinger Bands, moving averages, momentum
- **Data Source**: Yahoo Finance via yfinance
- **Output**: Technical scores, feature vectors

#### **ML Price Predictor**

- **File**: `paper-trading-app/app/core/ml/prediction/predictor.py`
- **Class**: `PricePredictor`
- **Purpose**: Core ML prediction logic
- **Methods**: `predict_price()`, `predict_portfolio()`, confidence calculation

#### **Market Context Managers**

- **File**: `app/services/market_aware_daily_manager.py`
- **File**: `market_aware_daily_manager.py`
- **Class**: `MarketAwareTradingManager`
- **Purpose**: Generate market-aware trading signals with context

### Database Integration

#### **Predictions Table Schema**

```sql
CREATE TABLE predictions (
    prediction_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    prediction_timestamp DATETIME NOT NULL,
    predicted_action TEXT NOT NULL,        -- BUY/SELL/HOLD
    action_confidence REAL NOT NULL,       -- 0.0-1.0
    predicted_direction INTEGER,           -- 1=UP, 0=DOWN
    predicted_magnitude REAL,              -- Expected % change
    feature_vector TEXT,                   -- Technical features
    model_version TEXT,
    entry_price REAL
);
```

---

## 📊 OUTCOMES - Prediction Performance Evaluation

### Core Outcome Evaluators

#### 1. **Fixed Outcome Evaluator** ⭐

- **File**: `fixed_outcome_evaluator.py`
- **Class**: `FixedOutcomeEvaluator`
- **Purpose**: Evaluate prediction success/failure using current market prices
- **Schedule**: Hourly via cron (`0 * * * *`)
- **Key Features**:
  - Timezone-aware SQL queries (fixed timezone bug)
  - Minute-level price data for accuracy
  - 4-hour delay before evaluation (allows market movement)
  - Success criteria: BUY=price up, SELL=price down, HOLD=<1% change

#### 2. **Evaluation Cron Script**

- **File**: `evaluate_predictions_comprehensive.sh`
- **Purpose**: Automated outcome evaluation wrapper
- **Schedule**: Every hour
- **Logs**: `logs/evaluation.log`

### Outcome Processing Logic

#### **Price Fetching**

- **Method**: `fetch_current_price()` in `FixedOutcomeEvaluator`
- **Data Source**: Yahoo Finance with 1-minute intervals
- **Timeframe**: Last 5 days of minute data for current pricing
- **Fallback**: Historical data if current unavailable

#### **Success Determination**

```python
# Success criteria in calculate_outcome()
if predicted_action == 'BUY' and actual_direction == 1:
    success = True
elif predicted_action == 'SELL' and actual_direction == 0:
    success = True
elif predicted_action == 'HOLD' and abs(actual_return) < 1.0:
    success = True
```

#### **Outcome Storage**

- **Table**: `outcomes`
- **Key Fields**: actual_return, actual_direction, entry_price, exit_price
- **Metadata**: evaluation_timestamp, outcome_details (JSON)

### Database Schema

#### **Outcomes Table**

```sql
CREATE TABLE outcomes (
    outcome_id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    actual_return REAL NOT NULL,           -- Actual % change
    actual_direction INTEGER NOT NULL,     -- 1=UP, 0=DOWN
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    evaluation_timestamp DATETIME NOT NULL,
    outcome_details TEXT,                  -- JSON metadata
    performance_metrics TEXT,              -- JSON metrics
    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
);
```

---

## 🤖 MACHINE LEARNING - Model Training & Improvement

### Core ML Components

#### 1. **Enhanced Training Pipeline** ⭐

- **File**: `app/core/ml/enhanced_training_pipeline.py`
- **Purpose**: Train ML models using prediction outcomes
- **Features**: Direction prediction, magnitude prediction, ensemble methods
- **Performance**: 100% direction accuracy, 91.6% magnitude R²

#### 2. **Enhanced Evening Analyzer** ⭐

- **File**: `enhanced_evening_analyzer_with_ml.py`
- **Purpose**: Daily ML training and sentiment analysis
- **Schedule**: Daily at 08:00 UTC (18:00 AEST)
- **Features**: News sentiment, ML model training, performance reports

#### 3. **Enhanced Morning Analyzer**

- **File**: `enhanced_morning_analyzer_with_ml.py`
- **Purpose**: Morning market analysis with ML
- **Schedule**: Daily at 07:00 UTC (17:00 AEST)

### ML Model Types & Storage

#### **Model Files** (in `/models/` directory)

- `action_model.pkl` - Trading action classification
- `direction_model.pkl` - Price direction prediction
- `magnitude_model.pkl` - Price magnitude prediction
- `current_direction_model.pkl` - Current direction model
- `current_magnitude_model.pkl` - Current magnitude model

#### **Symbol-Specific Models**

- `models/ANZ.AX/` - ANZ-specific models
- `models/CBA.AX/` - CBA-specific models
- `models/MQG.AX/` - Macquarie-specific models
- `models/NAB.AX/` - NAB-specific models
- `models/WBC.AX/` - Westpac-specific models

### ML Training Components

#### **ML Trading Manager**

- **File**: `app/core/ml/trading_manager.py`
- **Purpose**: Central orchestrator for ML operations
- **Integration**: Coordinates sentiment, technical, and ML components

#### **ML Trading Scorer**

- **File**: `app/core/ml/trading_scorer.py`
- **Purpose**: Calculate comprehensive ML scores
- **Components**: 6-factor scoring system (sentiment, confidence, economic, divergence, technical, ML prediction)

#### **Ensemble Predictor**

- **File**: `app/core/ml/ensemble_predictor.py`
- **Purpose**: Combine multiple ML models for better predictions

#### **LSTM Neural Network**

- **File**: `app/core/ml/lstm_neural_network.py`
- **Purpose**: Deep learning for time series prediction

#### **ML Backtester**

- **File**: `paper-trading-app/app/core/ml/prediction/backtester.py`
- **Class**: `MLBacktester`
- **Purpose**: Backtest ML model predictions against historical data

### Training Data Sources

#### **Enhanced Outcomes Database**

- **File**: `data/enhanced_outcomes.db`
- **Purpose**: Enhanced outcome tracking with additional metrics
- **Integration**: Multi-timeframe analysis, advanced performance metrics

#### **Features & Labels**

- **Features**: Technical indicators (53 features), sentiment scores, volume metrics
- **Labels**: Direction (up/down), magnitude (% change), action (BUY/SELL/HOLD)
- **Source**: Generated from `predictions` + `outcomes` tables

---

## 🔄 INTEGRATION & DATA FLOW

### Prediction → Outcome → ML Cycle

```
1. PREDICTION GENERATION
   ├── enhanced_efficient_system_news_volume_clean.py
   ├── production/cron/fixed_price_mapping_system.py
   └── Stores in: predictions table

2. OUTCOME EVALUATION
   ├── fixed_outcome_evaluator.py (hourly cron)
   ├── evaluate_predictions_comprehensive.sh
   └── Stores in: outcomes table

3. ML TRAINING
   ├── enhanced_evening_analyzer_with_ml.py (daily)
   ├── app/core/ml/enhanced_training_pipeline.py
   └── Updates: model files in /models/
```

### Key Cron Schedule

```bash
# Predictions: Every 30 min during market hours
*/30 0-5 * * 1-5 cd /root/test && python production/cron/fixed_price_mapping_system.py

# Outcomes: Every hour
0 * * * * cd /root/test && bash evaluate_predictions_comprehensive.sh

# ML Training: Daily evening
0 8 * * * cd /root/test && python enhanced_evening_analyzer_with_ml.py

# Morning Analysis: Daily morning
0 7 * * 1-5 cd /root/test && python enhanced_morning_analyzer_with_ml.py
```

---

## 📈 DASHBOARD & MONITORING

### Visualization Components

#### **Comprehensive Table Dashboard**

- **File**: `comprehensive_table_dashboard.py`
- **Purpose**: Web dashboard for prediction/outcome visualization
- **Schedule**: Every 4 hours via cron
- **Features**: Streamlit-based UI, performance metrics

#### **Independent ML Dashboard**

- **File**: `independent_ml_dashboard.py`
- **Purpose**: ML-specific performance dashboard

#### **Simple ML Success Dashboard**

- **File**: `simple_ml_success_dashboard.py`
- **Purpose**: Basic ML success rate visualization

### Log Files & Monitoring

- `logs/prediction_fixed.log` - Prediction generation logs
- `logs/evaluation.log` - Outcome evaluation logs
- `logs/evening_ml_training.log` - ML training logs
- `logs/dashboard_updates.log` - Dashboard update logs

---

## 🔧 UTILITIES & HELPERS

### Support Files

#### **Market Hours & Timing**

- **Integration**: Built into prediction engines
- **Logic**: ASX market hours (10 AM - 4 PM AEST), timezone handling

#### **Database Utilities**

- **Files**: Various SQLite integration throughout system
- **Databases**: `trading_predictions.db`, `enhanced_outcomes.db`
- **Maintenance**: Daily VACUUM and REINDEX via cron

#### **Configuration Files**

- **Crontab**: Stored in system crontab with full schedule
- **Environment**: Python virtual environment at `/root/trading_venv/`

---

## 📝 RECENT FIXES & IMPROVEMENTS

### Critical Bug Fixes

1. **Timezone Bug** (Sept 10, 2025)

   - **Issue**: SQL timezone mismatch preventing outcome evaluation
   - **Fix**: Updated `FixedOutcomeEvaluator.get_pending_predictions()` SQL query
   - **Impact**: Automated evaluation system now working correctly

2. **ML HOLD Bias** (Previous)

   - **Issue**: 100% HOLD predictions due to conservative thresholds
   - **Fix**: Volume pipeline improvements, threshold adjustments
   - **Files**: Multiple prediction engines updated

3. **YFinance Data Staleness**
   - **Issue**: Using hourly data instead of minute data for current prices
   - **Fix**: Changed to minute-level data in outcome evaluator
   - **Impact**: More accurate price evaluation for outcomes

---

## 📊 CURRENT SYSTEM STATUS

### Database Statistics (as of Sept 10, 2025)

- **Total Predictions**: 958
- **Total Outcomes**: 937
- **Evaluation Coverage**: 97.8%
- **Pending Evaluations**: 21 (within 4-hour window or outside 72-hour limit)

### Active Components

- ✅ Prediction Generation: Working (every 30 min during market hours)
- ✅ Outcome Evaluation: Working (hourly, timezone bug fixed)
- ✅ ML Training: Working (daily evening analysis)
- ✅ Dashboards: Active (multiple visualization options)

---

This documentation provides a complete map of all files contributing to predictions, outcomes, and machine learning in your trading system. Each component is categorized by its primary function and includes the key classes, purposes, and integration points.
