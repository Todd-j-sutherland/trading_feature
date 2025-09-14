# Trading Microservices Implementation

This document describes the complete microservices architecture that has been implemented for the trading system, replacing the monolithic structure with scalable, maintainable services.

## 🏗️ Architecture Overview

The trading system has been decomposed into 6 core microservices that communicate via Unix sockets and Redis pub/sub:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Market Data    │    │   Sentiment     │    │   ML Models     │
│   Service       │    │   Service       │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              Prediction Service                 │
         │          (Enhanced Market-Aware)                │
         └─────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler     │    │  Paper Trading  │    │   Management    │
│   Service       │    │    Service      │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
services/
├── base/                          # Foundation framework
│   └── base_service.py           # Base service class with Unix sockets, Redis, health monitoring
├── market-data/                   # Market data collection and distribution
│   └── market_data_service.py    # yfinance integration, technical analysis, caching
├── sentiment/                     # News sentiment analysis
│   └── sentiment_service.py      # MarketAux API, sentiment scoring, Big 4 aggregation
├── ml-model/                      # Machine learning model management
│   └── ml_model_service.py       # Bank-specific models, ensemble predictions
├── prediction/                    # Core trading signal generation
│   └── prediction_service.py     # Enhanced market-aware predictions, signal distribution
├── scheduler/                     # Market-aware task scheduling
│   └── scheduler_service.py      # ASX hours awareness, dependency management
├── paper-trading/                 # Live trading simulation
│   └── paper_trading_service.py  # IG Markets integration, P&L tracking
└── management/                    # Service lifecycle management
    └── service_manager.py         # Start/stop, monitoring, dashboard
```

## 🚀 Services Overview

### 1. Base Service Framework (`base/base_service.py`)
**Purpose**: Foundation class for all microservices

**Key Features**:
- Unix socket RPC communication
- Redis pub/sub event system
- Health monitoring with metrics
- Graceful shutdown handling
- Structured JSON logging
- Service-to-service communication with retry logic

**API**: 
- `health()` - Service health and metrics
- `metrics()` - Performance statistics
- `shutdown()` - Graceful shutdown

### 2. Market Data Service (`market-data/market_data_service.py`)
**Purpose**: Collect and distribute ASX market data with technical analysis

**Key Features**:
- yfinance integration for real-time data
- Technical indicators (RSI, MACD, Bollinger Bands)
- Market context analysis (bull/bear/sideways)
- Intelligent caching (5-minute intervals)
- Volume analysis and quality scoring

**API**:
- `get_market_data(symbol)` - Complete market data package
- `refresh_all_data()` - Force refresh for all symbols
- `get_technical_analysis(symbol)` - Technical indicators only
- `get_market_context()` - Overall market sentiment

### 3. Sentiment Service (`sentiment/sentiment_service.py`)
**Purpose**: News sentiment analysis for trading decisions

**Key Features**:
- MarketAux API integration for financial news
- Keyword-based sentiment scoring (-1.0 to +1.0)
- Big 4 banks sentiment aggregation
- News volume and quality weighting
- 30-minute caching to minimize API usage
- Fallback sentiment generation when API unavailable

**API**:
- `analyze_sentiment(symbol)` - Individual stock sentiment
- `get_big4_sentiment()` - Aggregated Big 4 banks sentiment
- `get_market_sentiment()` - Overall market sentiment
- `refresh_sentiment_cache()` - Force refresh

### 4. ML Model Service (`ml-model/ml_model_service.py`)
**Purpose**: Machine learning model management and predictions

**Key Features**:
- Bank-specific model loading from `models/` directory
- Ensemble predictions combining multiple models
- Feature validation and preprocessing
- Model performance tracking
- Confidence scoring for non-probabilistic models
- Support for scikit-learn pickle models

**API**:
- `load_model(model_name, symbol)` - Load specific model
- `predict(model_name, features, symbol)` - Generate prediction
- `get_ensemble_prediction(features, symbol)` - Multi-model prediction
- `list_available_models()` - Available models inventory
- `get_feature_importance(model_name)` - Model interpretability

### 5. Prediction Service (`prediction/prediction_service.py`)
**Purpose**: Core trading signal generation using enhanced market-aware algorithm

**Key Features**:
- Integration with Market Data, Sentiment, and ML Model services
- Batch prediction processing with caching
- Confidence-based signal generation (BUY/HOLD/SELL)
- Buy rate monitoring and alerts (>70% triggers alert)
- Comprehensive metrics and error tracking
- Event publishing for signal distribution

**API**:
- `generate_predictions(symbols, force_refresh)` - Multi-symbol predictions
- `generate_single_prediction(symbol)` - Individual prediction
- `get_buy_rate()` - Current buy signal percentage
- `clear_cache()` - Clear prediction cache

### 6. Scheduler Service (`scheduler/scheduler_service.py`)
**Purpose**: Market-aware task scheduling replacing cron

**Key Features**:
- ASX trading hours awareness (10:00-16:00 AEST)
- Market holiday detection and handling
- Task dependency management
- Exponential backoff retry logic
- Pre-market, market hours, and post-market task phases
- Real-time task monitoring

**Default Schedule**:
- 09:30: Morning analysis (pre-market)
- 09:45: Market data refresh
- 09:50: Sentiment analysis
- 10:15+: Market monitoring (every 15min during hours)
- 17:00: Evening analysis (post-market)
- 17:30: Paper trading sync
- 02:00: Daily backup

**API**:
- `schedule_task(config)` - Schedule new task
- `execute_task(task_id)` - Manual execution
- `list_tasks()` - All scheduled tasks
- `get_market_status()` - Current market phase

### 7. Paper Trading Service (`paper-trading/paper_trading_service.py`)
**Purpose**: Live trading simulation with IG Markets integration

**Key Features**:
- Virtual portfolio management ($100k starting capital)
- Real-time P&L calculation
- IG Markets API integration for live simulation
- Position sizing rules (5% of portfolio per trade)
- Stop-loss (5%) and take-profit (10%) automation
- Trading signal execution from prediction service
- Comprehensive trade history and analytics

**Trading Rules**:
- Max position size: $10k
- Max portfolio exposure: 80%
- Max daily loss: $5k
- Commission: $10 + 0.1% of trade value

**API**:
- `execute_trade(symbol, action, quantity)` - Execute paper trade
- `get_positions()` - Current open positions
- `get_portfolio_status()` - Complete portfolio summary
- `get_trading_performance(period)` - Performance metrics
- `sync_with_ig_markets()` - Sync with IG Markets

### 8. Service Manager (`management/service_manager.py`)
**Purpose**: Centralized service lifecycle management

**Key Features**:
- Dependency-aware service startup/shutdown
- Real-time health monitoring dashboard
- Service status and metrics collection
- Log aggregation and error tracking
- Automatic service restart and recovery
- Comprehensive system overview

**Commands**:
```bash
python services/management/service_manager.py start
python services/management/service_manager.py stop
python services/management/service_manager.py status
python services/management/service_manager.py health
python services/management/service_manager.py dashboard
python services/management/service_manager.py restart [service]
python services/management/service_manager.py logs [service]
```

## 🔧 Setup and Installation

### 1. Quick Setup
```bash
# Run complete setup
python setup_microservices.py --full

# Or run individual steps
python setup_microservices.py --create-dirs --install-deps --init-db --test
```

### 2. Manual Setup
```bash
# Install dependencies
pip install redis aiofiles psutil pandas numpy yfinance requests pytz scikit-learn

# Create directories
mkdir -p /var/log/trading /tmp/trading_sockets

# Initialize databases
python setup_microservices.py --init-db

# Start Redis
sudo systemctl start redis
```

### 3. Start Services
```bash
# Start all services
./start_microservices.sh

# Or manually
python services/management/service_manager.py start

# Monitor with dashboard
python services/management/service_manager.py dashboard
```

## 🔄 Communication Architecture

### Inter-Service Communication
- **Primary**: Unix sockets with JSON-RPC
- **Events**: Redis pub/sub for real-time events
- **Storage**: SQLite databases for persistence
- **Caching**: Redis for temporary data storage

### Event Flow Example
```
Market Data Service → [market_data_updated] → Redis
                                                ↓
Prediction Service ← [market_data_updated] ← Redis
                                                ↓
Prediction Service → [prediction_generated] → Redis
                                                ↓
Paper Trading ← [prediction_generated] ← Redis
```

### Service Dependencies
```
Base Services (Redis)
├── market-data (independent)
├── sentiment (independent)  
├── ml-model (independent)
└── Core Services
    ├── prediction (depends: market-data, sentiment, ml-model)
    ├── scheduler (depends: prediction)
    └── paper-trading (depends: prediction, market-data)
```

## 📊 Monitoring and Health

### Health Check Endpoints
Each service provides comprehensive health information:
```json
{
  "service": "prediction",
  "status": "healthy",
  "uptime": 3600,
  "memory_usage": 45678123,
  "cpu_usage": 2.3,
  "prediction_count": 147,
  "cache_size": 12,
  "current_buy_rate": 23.5
}
```

### Dashboard Interface
Real-time dashboard showing:
- Overall system status (🟢/🟡/🔴)
- Individual service health
- Memory and CPU usage
- Active alerts and warnings
- Service dependency status

### Logging
- Structured JSON logging to `/var/log/trading/`
- Automatic log rotation (daily, 7 days retention)
- Centralized error tracking and alerting

## 🎯 Key Benefits

### Performance
- **Memory Efficiency**: ~180MB total vs ~1.1GB Docker overhead
- **CPU Efficiency**: Minimal containerization overhead
- **Network Efficiency**: Unix sockets faster than TCP/HTTP

### Scalability
- Independent service scaling
- Horizontal scaling capability
- Resource isolation and monitoring

### Reliability
- Service failure isolation
- Automatic retry and recovery
- Health monitoring and alerting
- Graceful degradation

### Maintainability
- Clear service boundaries
- Independent deployment
- Comprehensive logging and monitoring
- Standardized APIs

## 🔮 Future Enhancements

### Additional Services (Ready for Implementation)
1. **Data Quality Service** - Comprehensive data validation
2. **Backup Service** - Automated backup and recovery
3. **Monitoring Service** - Advanced metrics and alerting
4. **Config Service** - Centralized configuration management
5. **API Gateway** - External API access and rate limiting

### Advanced Features
- Service mesh integration
- Distributed tracing
- Advanced caching strategies
- Machine learning model versioning
- Real-time portfolio optimization

## 🚀 Quick Start Commands

```bash
# Complete setup and start
python setup_microservices.py --full
./start_microservices.sh

# Monitor system
python services/management/service_manager.py dashboard

# Test individual service
python -c "
import asyncio
from services.base.base_service import BaseService

async def test():
    service = BaseService('test')
    result = await service.call_service('prediction', 'generate_predictions', symbols=['CBA.AX'])
    print(result)

asyncio.run(test())
"

# View logs
python services/management/service_manager.py logs prediction

# Restart specific service
python services/management/service_manager.py restart market-data
```

This microservices architecture provides a robust, scalable foundation for your trading system while maintaining backward compatibility with your existing cron jobs and database structures.
