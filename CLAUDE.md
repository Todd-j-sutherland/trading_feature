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

### Data Persistence
- SQLite databases for structured data (`data/*.db`)
- JSON caching for API responses (`data/cache/`)
- ML model versioning (`data/ml_models/models/`)

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