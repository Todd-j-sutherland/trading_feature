# ASX Trading System - Architecture Overview

## 🏗️ System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ASX Trading Application                               │
│                        Server: root@170.64.199.151                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CRON SCHEDULER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Market Hours (00:00-06:00 UTC): Enhanced Predictions (Every 30 min)           │
│ Evening (08:00 UTC): ML Training & Analysis (Daily)                           │
│ Hourly: Outcome Evaluation (Every hour)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CORE PREDICTION ENGINE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                    enhanced_efficient_system.py                               │
│                                                                               │
│ • Technical Analysis (RSI, Moving Averages, Momentum)                        │
│ • Market Context Analysis                                                     │
│ • 53 Feature Vector Generation                                               │
│ • Multi-Symbol Processing (CBA, ANZ, WBC, NAB, MQG, SUN, QBE)               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DATA COLLECTION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │
│  │   NEWS DATA     │  │  REDDIT DATA    │  │  MARKET DATA    │               │
│  │                 │  │                 │  │                 │               │
│  │ • Financial     │  │ • r/AusFinance  │  │ • Price Data    │               │
│  │   News APIs     │  │ • r/fiaustralia │  │ • Volume Data   │               │
│  │ • Market News   │  │ • Sentiment     │  │ • Technical     │               │
│  │ • Sentiment     │  │   Analysis      │  │   Indicators    │               │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘               │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MACHINE LEARNING PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                    Enhanced ML Training Pipeline                        │  │
│  │                app/core/ml/enhanced_training_pipeline.py               │  │
│  │                                                                         │  │
│  │ • Feature Engineering (53 features)                                    │  │
│  │ • Multi-Output Targets (Direction + Magnitude: 1h/4h/1d)              │  │
│  │ • RandomForest Models (Direction: 100%, Magnitude: 91.6% accuracy)    │  │
│  │ • Training Data: 21 samples with enhanced outcomes                     │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                      Simple ML Training                                 │  │
│  │                      simple_ml_training.py                             │  │
│  │                                                                         │  │
│  │ • Symbol-Specific Models (5 symbols trained)                           │  │
│  │ • High Accuracy (85-93% direction prediction)                          │  │
│  │ • Model Bridging (bridge_models.py)                                   │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                   SQLite: data/trading_predictions.db                         │
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │
│  │   predictions   │  │    outcomes     │  │enhanced_features│               │
│  │   (126 records) │  │   (130 records) │  │   (28 records)  │               │
│  │                 │  │                 │  │                 │               │
│  │ • Predictions   │  │ • Actual        │  │ • 53 Feature    │               │
│  │ • Confidence    │  │   Outcomes      │  │   Vectors       │               │
│  │ • Timestamps    │  │ • Evaluation    │  │ • Technical     │               │
│  │ • Symbols       │  │   Results       │  │   Analysis      │               │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘               │
│                                                                               │
│  ┌─────────────────┐                                                          │
│  │enhanced_outcomes│                                                          │
│  │   (21 records)  │                                                          │
│  │                 │                                                          │
│  │ • ML Training   │                                                          │
│  │   Targets       │                                                          │
│  │ • Multi-Output  │                                                          │
│  │   Labels        │                                                          │
│  └─────────────────┘                                                          │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LOGGING & MONITORING                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Prediction Logs │  │ Training Logs   │  │  System Logs    │               │
│  │                 │  │                 │  │                 │               │
│  │ • cron_         │  │ • evening_ml_   │  │ • Error Logs    │               │
│  │   prediction.   │  │   training.log  │  │ • Performance   │               │
│  │   log           │  │ • Model         │  │   Monitoring    │               │
│  │ • Real-time     │  │   Performance   │  │ • System        │               │
│  │   Monitoring    │  │   Metrics       │  │   Health        │               │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘               │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

```
1. MARKET HOURS (Every 30 minutes)
   ├── enhanced_efficient_system.py
   ├── Collect Technical Indicators
   ├── Generate 53 Feature Vectors
   ├── Store in enhanced_features table
   └── Generate Predictions → predictions table

2. HOURLY
   ├── evaluate_predictions.sh
   ├── Compare predictions vs actual market movement
   └── Store results → outcomes table

3. DAILY EVENING (08:00 UTC)
   ├── enhanced_evening_analyzer_with_ml.py
   ├── Link enhanced_features ↔ outcomes → enhanced_outcomes
   ├── Train ML models (Direction + Magnitude)
   ├── Validate model performance
   └── Update prediction algorithms

4. ON-DEMAND
   ├── Manual prediction generation
   ├── Model retraining
   └── Performance analysis
```

## 🎯 Key Components

### Core Prediction Engine
- **File**: `enhanced_efficient_system.py`
- **Function**: Generates predictions every 30 minutes during market hours
- **Features**: 53 technical analysis features per prediction
- **Output**: Stored in `predictions` table

### ML Training Pipeline
- **File**: `app/core/ml/enhanced_training_pipeline.py`
- **Function**: Trains models using enhanced features and outcomes
- **Data**: 21 training samples with 6 target types
- **Performance**: 100% direction accuracy, 91.6% magnitude R²

### Evening Analysis
- **File**: `enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py`
- **Function**: Comprehensive sentiment analysis and ML training
- **Schedule**: Daily at 18:00 AEST (08:00 UTC)
- **Output**: Enhanced ML models and performance reports

### Data Storage
- **Database**: SQLite (`data/trading_predictions.db`)
- **Tables**: predictions, outcomes, enhanced_features, enhanced_outcomes
- **Backup**: Automated daily backups

## 📈 Performance Metrics

| Component | Current Status | Target |
|-----------|----------------|---------|
| **Prediction Generation** | ✅ Every 30 min | Every 30 min |
| **ML Model Accuracy** | ✅ 85-93% | >70% |
| **Feature Completeness** | ✅ 53/53 features | 53/53 features |
| **System Uptime** | ✅ ~100% | >99% |
| **Training Data** | ✅ 21 samples | >20 samples |

## 🔧 Maintenance Points

1. **Database Optimization**: Weekly VACUUM and REINDEX
2. **Log Rotation**: Automated cleanup of old log files
3. **Model Retraining**: Daily automated with enhanced pipeline
4. **Performance Monitoring**: Real-time accuracy tracking
5. **Backup Strategy**: Daily database backups

---

**System Status**: ✅ FULLY OPERATIONAL  
**Last Updated**: August 25, 2025  
**Version**: 5.0 - Post-Fix Implementation
