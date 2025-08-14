# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive **AI-powered trading analysis platform** for Australian Stock Exchange (ASX) securities, featuring sentiment analysis, ML predictions, technical analysis, and automated trading capabilities. The system follows a professional Python package architecture with two-stage memory-optimized ML analysis.

## Common Development Commands

### Daily Operations
```bash
# Morning analysis (Stage 1 - lightweight sentiment analysis)
python -m app.main morning

# Evening analysis (Stage 1+2 - full ML analysis with FinBERT)
python -m app.main evening

# Quick system health check
python -m app.main status

# Launch interactive dashboard
python -m app.main dashboard
```

### ML Trading System
```bash
# Display current ML trading scores for all banks
python -m app.main ml-scores

# Run comprehensive ML trading session (dry run by default)
python -m app.main ml-trading

# Execute actual trades (use --execute flag)
python -m app.main ml-trading --execute

# Show trading history and performance
python -m app.main trading-history
```

### Testing and Development
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v        # Unit tests (19 tests)
python -m pytest tests/integration/ -v # Integration tests (44+ tests)

# Code formatting and linting
black app/ tests/
flake8 app/ tests/
```

### Dashboard Operations
```bash
# Launch SQL-based dashboard (RECOMMENDED - fastest performance)
streamlit run app/dashboard/sql_dashboard.py --server.port 8501

# Launch enhanced dashboard (fallback)
streamlit run app/dashboard/enhanced_main.py --server.port 8502

# Start frontend development server
cd frontend && npm start

# Launch ML trading dashboard
python -m app.main ml-dashboard
```

## High-Level Architecture

### Core Components

1. **Two-Stage Sentiment System** (`app/core/sentiment/two_stage_analyzer.py`)
   - Stage 1: TextBlob + VADER (~100MB memory) - Always running
   - Stage 2: FinBERT + advanced models (~800MB memory) - On-demand enhancement
   - Automatic memory management and quality escalation (70% → 95% accuracy)

2. **ML Trading Pipeline** (`app/core/ml/`)
   - `enhanced_pipeline.py` - Main ML orchestration
   - `trading_manager.py` - Trading session management
   - `trading_scorer.py` - Bank scoring and recommendations
   - Uses ensemble models with backtesting and confidence scoring

3. **Daily Operations Manager** (`app/services/daily_manager.py`)
   - Orchestrates morning/evening routines
   - Coordinates data collection, analysis, and reporting
   - Handles system health monitoring

4. **Interactive Dashboard** (`app/dashboard/enhanced_main.py`)
   - Streamlit-based professional interface
   - Real-time sentiment tracking, ML predictions, trading signals
   - Economic context and risk assessment

### Data Flow Architecture

```
News Collection → Sentiment Analysis → ML Feature Engineering → 
Trading Signals → Risk Assessment → Position Management → 
Performance Tracking → Unified SQL Database → Dashboard Visualization
```

**IMPORTANT**: The system now uses a **unified SQL database** (`data/trading_unified.db`) instead of scattered JSON files. All data operations go through `app/core/data/sql_manager.py` for better performance and consistency.

### Key Directories

- `app/core/sentiment/` - Multi-stage sentiment analysis engine
- `app/core/ml/` - Machine learning models and trading logic  
- `app/core/trading/` - Alpaca integration, paper trading, risk management
- `app/dashboard/` - Web interface and visualization components
- `app/services/` - Business logic orchestration
- `data/` - SQLite databases, ML models, cached data
- `tests/` - Comprehensive test suite (63+ tests)

## Environment Configuration

### Two-Stage Analysis Control
```bash
# Enable intelligent two-stage analysis (recommended)
export USE_TWO_STAGE_ANALYSIS=1

# Memory-constrained mode (Stage 1 only)
export SKIP_TRANSFORMERS=1

# Full quality mode (Stage 1+2)
export SKIP_TRANSFORMERS=0

# FinBERT-only mode (balanced memory/quality)
export FINBERT_ONLY=1
```

### Remote Server Operations
```bash
# Connect to remote server
ssh -i ~/.ssh/id_rsa root@170.64.199.151

# Remote environment setup
cd test
source ../trading_venv/bin/activate
export PYTHONPATH=/root/test

# Remote dashboard access
# Main: http://170.64.199.151:8501
# Debug: http://170.64.199.151:8502
```

## Development Guidelines

### Code Organization
- All business logic in `app/core/` with clear module separation
- Services layer in `app/services/` for orchestration
- Configuration centralized in `app/config/settings.py`
- Comprehensive logging with rotation in `logs/`

### Memory Management
- System automatically switches between Stage 1 (100MB) and Stage 2 (800MB) analysis
- Use environment variables to control transformer loading
- ML models are cached and reused efficiently

### Testing Standards
- 63+ tests across unit and integration categories
- All critical paths have test coverage
- Use `pytest` with clear test organization

### Data Architecture (Updated August 2025)

**PRIMARY DATABASE:**
- **`data/trading_unified.db`** - Main system database (ALL operations)
  - `enhanced_features` - ML features, sentiment data, technical indicators
  - `enhanced_outcomes` - Trading results, predictions, position outcomes
  - `enhanced_morning_analysis` / `enhanced_evening_analysis` - Daily routine results
  - `positions` - Trading positions and history
  - `sentiment_data` - Historical sentiment analysis
  - `predictions` - ML predictions and confidence scores
  - `ml_training_history` - Training metrics and model performance
  - `news_sentiment_analysis` - News analysis results
  - `bank_performance` - Bank-specific performance metrics

**LEGACY DATABASES (Backed up, still referenced by some components):**
- `data/trading_data.db` - Legacy morning/evening analysis (80KB)
- `data/ml_models/training_data.db` - Legacy ML training data (40KB)
- `data/ml_models/enhanced_training_data.db` - Empty legacy file (0KB)

**CACHING:**
- JSON caching for API responses (`data/cache/`)
- ML model versioning (`data/ml_models/models/`)

**IMPORTANT**: The system has been consolidated to primarily use `trading_unified.db` for all functionality. Morning/evening routines, dashboard, ML training, and trading operations all use this unified database.

## Complete Database Audit - trading_unified.db (August 2025)

### **Database Overview**
- **Location**: `data/trading_unified.db`
- **Size**: 1.5MB (actively used)
- **Total Tables**: 13 tables
- **Total Records**: 6,061 records across all tables

### **Core Data Tables (High Volume)**

#### 1. **bank_performance** (1,318 records) 🏦
- **Purpose**: Real-time bank stock performance metrics
- **Key Fields**: symbol, current_price, rsi, macd_signal, sma_20/50, bollinger_position
- **Used By**: Dashboard price displays, technical analysis
- **Data Source**: Live market data collection
- **Sample**: CBA.AX, $172.87, RSI 40.03, HOLD signals

#### 2. **news_sentiment_analysis** (3,954 records) 📰
- **Purpose**: News headlines and sentiment scoring
- **Key Fields**: symbol, headline, sentiment_score, confidence, category, source
- **Used By**: Morning/evening sentiment analysis, dashboard news metrics
- **Data Source**: News collection and FinBERT analysis
- **Sample**: "Commonwealth Bank increases dividend" → 0.517 sentiment, 0.693 confidence

#### 3. **enhanced_features** (367 records) 🎯
- **Purpose**: ML feature engineering - combines sentiment, technical, and market data
- **Key Fields**: 50+ features including sentiment_score, rsi, macd_line, price ratios, volume metrics
- **Used By**: All ML training and prediction pipelines
- **Data Source**: Consolidated from all analysis engines
- **Critical**: This is the main ML training dataset

#### 4. **enhanced_outcomes** (178 records) 📊
- **Purpose**: Trading position outcomes and ML prediction results
- **Key Fields**: feature_id (FK), optimal_action, confidence_score, entry_price, exit_price, return_pct
- **Used By**: Dashboard position tables, ML performance tracking
- **Data Source**: Trading execution and position management
- **Relationships**: Links to enhanced_features via feature_id

### **Analysis & Tracking Tables (Medium Volume)**

#### 5. **enhanced_morning_analysis** (20 records) 🌅
- **Purpose**: Results of morning routine analysis
- **Key Fields**: timestamp, banks_analyzed, ml_predictions, technical_signals, recommendations
- **Used By**: Morning routine (`python -m app.main morning`)
- **Data Source**: `app/services/daily_manager.py` morning routine
- **Complex JSON**: Stores detailed analysis results as JSON

#### 6. **enhanced_evening_analysis** (22 records) 🌆
- **Purpose**: Results of evening routine analysis  
- **Key Fields**: timestamp, model_training, backtesting, next_day_predictions, model_comparison
- **Used By**: Evening routine (`python -m app.main evening`)
- **Data Source**: `app/services/daily_manager.py` evening routine
- **Complex JSON**: Stores ML training and backtesting results

#### 7. **sentiment_features** (74 records) 📈
- **Purpose**: Processed sentiment features for ML
- **Key Fields**: symbol, sentiment_score, confidence, news_count, reddit_sentiment
- **Used By**: Legacy ML training components
- **Status**: Being phased out in favor of enhanced_features

#### 8. **predictions** (17 records) 🔮
- **Purpose**: Discrete trading predictions and signals
- **Key Fields**: date, symbol, signal, confidence, sentiment_score, status, outcome
- **Used By**: Dashboard predictions display
- **Data Source**: ML prediction generation

### **ML Performance & Model Tables (Low Volume)**

#### 9. **model_performance_enhanced** (13 records) 🤖
- **Purpose**: Enhanced ML model performance metrics
- **Key Fields**: model_version, direction_accuracy_1h/4h/1d, magnitude_mae, training_samples
- **Used By**: Dashboard ML summary, model evaluation
- **Data Source**: `app/core/ml/enhanced_training_pipeline.py`
- **Critical**: Tracks ML model quality over time

#### 10. **Empty/Unused Tables** (0 records each):
- **positions**: Trading positions (not actively used - data in enhanced_outcomes)
- **sentiment_data**: Legacy sentiment storage
- **technical_scores**: Legacy technical analysis
- **trading_outcomes**: Legacy trading results
- **model_performance**: Legacy model tracking
- **ml_performance_tracking**: Unused performance tracking

### **Database Usage by Component**

#### **Core Systems Using trading_unified.db:**
1. **Dashboard** (`dashboard.py`, `enhanced_main.py`)
   - Reads: enhanced_features, enhanced_outcomes, model_performance_enhanced
   - Purpose: Real-time position tracking, ML performance display

2. **ML Training Pipeline** (`enhanced_training_pipeline.py`)
   - Reads/Writes: enhanced_features, enhanced_outcomes, model_performance_enhanced
   - Purpose: Feature engineering, model training, outcome recording

3. **Daily Manager** (`daily_manager.py`)
   - Writes: enhanced_morning_analysis, enhanced_evening_analysis
   - Purpose: Morning/evening routine result storage

4. **SQL Data Manager** (`sql_manager.py`)
   - Manages: All table operations
   - Purpose: Centralized database operations

5. **Backtesting** (`comprehensive_backtester.py`, `simple_backtester.py`)
   - Reads: enhanced_morning_analysis, enhanced_evening_analysis, sentiment_data
   - Purpose: Historical analysis and strategy testing

6. **ML Components** (`ensemble_predictor.py`, `lstm_neural_network.py`)
   - Reads/Writes: enhanced_features, enhanced_outcomes
   - Purpose: Prediction generation and outcome tracking

#### **Data Flow Architecture:**
```
Market Data → News Collection → Sentiment Analysis → 
enhanced_features (ML Features) → ML Training/Prediction → 
enhanced_outcomes (Position Results) → Dashboard Visualization
```

#### **Key Relationships:**
- **enhanced_features.id** → **enhanced_outcomes.feature_id** (1:1)
- **enhanced_features** serves as the master feature record
- **enhanced_outcomes** tracks what happened after predictions
- **Morning/evening analysis** tables store routine results
- **Model performance** tables track ML system quality

### **Critical Database Operations:**
1. **Feature Engineering**: `enhanced_features` table population (daily)
2. **Outcome Recording**: `enhanced_outcomes` updates (when positions close)
3. **Performance Tracking**: `model_performance_enhanced` updates (when models retrain)
4. **Routine Logging**: `enhanced_morning/evening_analysis` inserts (daily)

## Important Implementation Details

1. **Main Entry Point**: `app/main.py` - CLI with argparse for all commands
2. **Bank Symbols**: CBA.AX, WBC.AX, ANZ.AX, NAB.AX, MQG.AX, QBE.AX, SUN.AX
3. **ML Pipeline**: Enhanced ensemble with XGBoost, Random Forest, and neural networks
4. **Paper Trading**: Integrated Alpaca simulator for safe strategy testing
5. **Economic Context**: Market regime detection and economic sentiment analysis
6. **Performance Tracking**: Complete position outcome database with P&L analysis

## Remote Server Deployment

The system runs on a DigitalOcean droplet with automated cron jobs:
- **8 AM**: Pre-market analysis (`premarket_analysis.log`)
- **10 AM-4 PM**: Market monitoring (`market_hours.log`) 
- **6 PM**: ML training and analysis (`evening_ml_cron.log`)

Dashboard accessible at http://170.64.199.151:8501 with live data updates.