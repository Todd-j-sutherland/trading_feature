# GitHub Copilot Instructions - Premium ASX Trading System

## 🏆 System Overview

You're working with a sophisticated ASX trading system that combines 53-feature ML models, real-time sentiment analysis, IG Markets integration, and automated paper trading. This is a production system currently managing $100K in paper trading positions with 44.92% success rate.

**Current Branch Context**: `major1/saturday-working` - Service-based architecture transformation in progress (maintain backwards compatibility)

## 🚀 Quick System Context

### Core Architecture
```
Trading System Components:
├── Main ML Pipeline: enhanced_morning_analyzer_with_ml.py (53 features, 7 banks)
├── Market-Aware System: app/core/ml/prediction/market_aware_predictor.py (NEW)
├── IG Markets Integration: ig_markets_paper_trading/ ($5K-$15K positions)
├── Database: data/trading_predictions.db (SQLite with WAL mode)
├── Cron Automation: Every 30min during market hours
└── Dashboard: comprehensive_table_dashboard.py (Streamlit)
```

### Remote Production System
- **Server**: `ssh root@170.64.199.151`
- **Environment**: `source ../trading_venv/bin/activate`
- **Logs**: `/root/test/logs/`
- **Database**: `/root/test/data/trading_predictions.db`

## 🎯 Current Service Architecture Transformation

### Phase 1: Services-Rich Architecture (In Progress)
The system is transitioning from a monolithic structure (717 files) to microservices:

```
services/
├── trading_service.py (Port 8001)     # Position management, risk validation
├── sentiment_service.py (Port 8002)   # News collection, sentiment analysis
├── orchestrator_service.py (Port 8000) # Service coordination
└── shared/
    ├── models/     # TradingSignal, SentimentScore data structures
    ├── utils/      # Service clients, logging utilities
    └── config/     # Configuration management
```

**CRITICAL**: Maintain backwards compatibility during transformation. Existing cron jobs and production systems must continue working.

## 🧠 ML System Architecture

### 53-Feature Enhanced System
```python
# Core ML Components (PRODUCTION)
enhanced_morning_analyzer_with_ml.py    # Primary ML prediction engine
enhanced_evening_analyzer_with_ml.py    # Daily model training
app/core/ml/prediction/market_aware_predictor.py  # Market context integration

# Feature Categories (53 total):
sentiment_features = 15      # FinBERT, news volume, Reddit sentiment
technical_features = 20      # RSI, MACD, Bollinger, moving averages
price_features = 10          # Price momentum, volatility, ranges
volume_features = 6          # Volume ratios, OBV, trends
market_features = 2          # ASX 200 context, sector performance
```

### Market-Aware Enhancement (NEW)
```python
# Dynamic market context system
market_contexts = {
    'BEARISH': {'multiplier': 0.7, 'buy_threshold': 80},  # ASX 200 down >2%
    'NEUTRAL': {'multiplier': 1.0, 'buy_threshold': 70},  # ASX 200 -2% to +2%
    'BULLISH': {'multiplier': 1.1, 'buy_threshold': 65}   # ASX 200 up >2%
}
```

## 📊 Database Schema (Critical)

### Core Tables
```sql
-- Main predictions (legacy, keep for compatibility)
predictions: prediction_id, symbol, prediction_timestamp, action, confidence, entry_price

-- Enhanced outcomes (corrected evaluation system)
outcomes: outcome_id, prediction_id, evaluation_timestamp, success_rate, actual_return

-- Market-aware predictions (NEW)
market_aware_predictions: prediction_id, symbol, market_context, buy_threshold_used, confidence

-- IG Markets paper trading
positions: position_id, symbol, shares, entry_price, stop_loss, profit_target, status, pnl
```

## 🔧 Essential Commands

### System Operations
```bash
# Remote system health check
ssh root@170.64.199.151 "cd /root/test && python3 -c 'import sqlite3; conn=sqlite3.connect(\"data/trading_predictions.db\"); print(f\"Recent predictions: {conn.execute(\"SELECT COUNT(*) FROM predictions WHERE prediction_timestamp > datetime(\\\"now\\\", \\\"-24 hours\\\")\").fetchone()[0]}\"); conn.close()'"

# Manual prediction generation
ssh root@170.64.199.151 "cd /root/test && python3 enhanced_morning_analyzer_with_ml.py"

# Market-aware system testing
ssh root@170.64.199.151 "cd /root/test && python3 -m app.main_enhanced market-status"

# IG Markets paper trading status
ssh root@170.64.199.151 "cd /root/test/ig_markets_paper_trading && python3 verify_config.py"
```

### Development Workflows
```bash
# Local development (dashboard environment)
source dashboard_env/bin/activate

# Test services architecture (NEW)
python test_services_architecture.py

# Start services (Phase 1)
./services/start_services.sh
```

## 🎯 Critical Development Patterns

### 1. ML Model Integration
```python
# ALWAYS use 53-feature system for production predictions
from enhanced_ml_system.enhanced_training_pipeline import EnhancedMLTrainingPipeline

# Market-aware prediction pattern
from app.core.ml.prediction.market_aware_predictor import create_market_aware_predictor
predictor = create_market_aware_predictor()
prediction = predictor.generate_market_aware_prediction(symbol, features)
```

### 2. Database Operations (WAL Mode Required)
```python
# ALWAYS use WAL mode for database connections
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn
```

### 3. Service Integration Pattern (NEW)
```python
# Service-based approach (maintain backwards compatibility)
from shared.utils.service_client import ServiceClient

# Use services when available, fall back to legacy
try:
    sentiment_client = ServiceClient("http://localhost:8002")
    sentiment_data = sentiment_client.get_sentiment(symbol)
except:
    # Fall back to legacy sentiment analysis
    sentiment_data = legacy_sentiment_analyzer(symbol)
```

### 4. Position Sizing (IG Markets)
```python
# Optimized position sizes to overcome spread costs
position_config = {
    'min_position_size': 5000,   # $5K minimum
    'max_position_size': 15000,  # $15K maximum  
    'max_risk_per_trade': 0.15,  # 15% max risk
    'stop_loss_percentage': 2.0  # 2% stop loss
}
```

## 🚨 Critical System Knowledge

### 1. Cron Job Dependencies
```bash
# Production cron jobs (DO NOT BREAK)
*/30 0-5 * * 1-5    # Market predictions every 30min
0 * * * *           # Hourly outcome evaluation  
0 8 * * *           # Daily ML training
0 7 * * 1-5         # Market-aware morning routine (NEW)
```

### 2. Database Integrity Issues (RESOLVED)
- **Legacy Issue**: Entry prices were wrong (CBA stored as $60 vs actual $168)
- **Solution**: `corrected_outcome_evaluator.py` fixes bad entry prices
- **Current Status**: 82 predictions corrected, realistic returns achieved

### 3. ML Training Status
- **Status**: ✅ FULLY OPERATIONAL (after fixing empty file issue)
- **Performance**: 92.2% direction accuracy with 703 training samples
- **Models**: All 7 bank stocks updated daily at 08:00 UTC

### 4. Market-Aware System (NEW)
```python
# Check market context before making predictions
market_context = predictor.get_cached_market_context()
if market_context['context'] == 'BEARISH':
    # Apply stricter criteria
    buy_threshold = 80  # vs 70 in neutral markets
    confidence_multiplier = 0.7
```

## 🔄 Service Migration Guidelines

### Phase 1 Implementation Rules
1. **Backwards Compatibility**: Existing files must continue working
2. **Gradual Migration**: Move functionality piece by piece
3. **Testing**: Use `test_services_architecture.py` for validation
4. **Fallback**: Always provide legacy fallback options

### Service Development Pattern
```python
# When creating new services, follow this pattern:
from fastapi import FastAPI
from shared.models.trading_models import TradingSignal
from shared.utils.logging_utils import setup_logging

app = FastAPI(title="Trading Service", version="1.0.0")

@app.post("/trading/analyze", response_model=TradingSignal)
async def analyze_trading_opportunity(request: AnalysisRequest):
    # Service implementation
    return TradingSignal(...)

# Health check endpoint (REQUIRED)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trading"}
```

## 📈 Performance Monitoring

### Key Metrics to Track
```python
# System health indicators
health_metrics = {
    'prediction_success_rate': 44.92,      # Current system performance
    'recent_predictions_24h': 20-30,       # Expected daily volume
    'ml_model_accuracy': 92.2,             # Direction prediction accuracy
    'paper_trading_positions': 'varies',    # Active IG Markets positions
    'database_size_mb': 15.2               # SQLite database size
}
```

### Performance Validation
```bash
# Check system performance
ssh root@170.64.199.151 "cd /root/test && python3 comprehensive_table_dashboard.py --stats-only"

# Validate market-aware performance
ssh root@170.64.199.151 "cd /root/test && python3 -c 'from app.core.ml.prediction.market_aware_predictor import create_market_aware_predictor; predictor = create_market_aware_predictor(); print(predictor.get_cached_market_context())'"
```

## 🎯 Development Priorities

### Immediate Focus
1. **Service Migration**: Complete Phase 1 services implementation
2. **Backwards Compatibility**: Ensure legacy systems continue working
3. **Testing**: Comprehensive validation of service architecture
4. **Documentation**: Update service-specific documentation

### Code Quality Standards
- **Type Safety**: Use Pydantic models for data structures
- **Error Handling**: Implement retry logic and graceful degradation
- **Logging**: Comprehensive logging for debugging
- **Testing**: Unit tests for each service component

## 🔍 Debugging Common Issues

### ML Model Loading Failures
```python
# Check if models exist and are loadable
import os
model_path = "data/ml_models/models/"
if not os.path.exists(model_path):
    print("❌ ML models directory missing - run evening training")
```

### Database Lock Issues
```python
# Use WAL mode and retry logic
def safe_db_operation(operation, retries=3):
    for attempt in range(retries):
        try:
            return operation()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries-1:
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

### Service Communication Failures
```python
# Always implement fallback mechanisms
try:
    response = requests.get(f"http://localhost:8002/sentiment/{symbol}", timeout=5)
    sentiment_data = response.json()
except requests.RequestException:
    # Fall back to legacy method
    sentiment_data = legacy_sentiment_analysis(symbol)
```

---

**Remember**: This is a production trading system with real money implications (even in paper trading). Always test changes thoroughly and maintain backwards compatibility during the service architecture transformation.
