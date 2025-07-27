# 🧠 Integrated ML Dashboard - Complete Guide

## 🎯 Overview

The **Integrated ML Dashboard** connects your complete ML workflow in a single interface:

```
Morning Data Collection → Evening ML Training → Real-time Dashboard Predictions
```

This dashboard shows **real ML predictions** using the models trained by your `app.main evening` processes, unlike the Simple ML Dashboard which uses simulated data.

---

## 🔄 How the Integration Works

### **1. Morning Data Collection (`app.main morning`)**
```bash
python -m app.main morning
```

**What happens:**
- Collects real market data for ASX banks
- Gathers news sentiment from multiple sources
- Calculates technical indicators (RSI, MACD, Bollinger Bands)
- Stores training features in `data/ml_models/enhanced_training_data.db`

**Output:** 54+ features per bank stored for ML training

### **2. Evening ML Training (`app.main evening`)**
```bash
python -m app.main evening
```

**What happens:**
- Loads morning-collected data
- Trains ensemble ML models (Random Forest, XGBoost, Neural Networks)
- Validates model performance with backtesting
- Saves trained models to `data/ml_models/models/`
- Generates performance metrics and feature importance

**Output:** Trained ML models ready for real-time predictions

### **3. Real-time Dashboard Integration**

The Integrated ML Dashboard connects to your trained models via:

```typescript
// Frontend calls main backend
GET /api/ml/enhanced-predictions
GET /api/ml/training-status

// Backend uses your trained models
EnhancedMLTrainingPipeline.predict_enhanced(sentiment_data, symbol)
```

---

## 🚀 Quick Start

### **Start the Complete System**
```bash
./start_integrated_ml_system.sh
```

This starts:
- **Main Backend** (Port 8000) - API server with ML endpoints
- **Enhanced ML Backend** (Port 8001) - Original ML system 
- **Frontend** (Port 3000) - React dashboard with 3 tabs

### **Access the Dashboard**
1. Open browser: `http://localhost:3000`
2. Click the **"🧠 Integrated ML"** tab
3. View real ML predictions from your trained models

---

## 📊 Dashboard Features

### **Training Status Panel**
- **Model Status**: PASSED/FAILED validation
- **Direction Accuracy**: 1H/4H/1D prediction accuracy percentages
- **Training Data**: Number of samples used for training
- **Top Feature**: Most important feature from your ML pipeline

### **Bank Prediction Cards**
Each bank shows:
- **Current Market Data**: Price, 1D change, RSI
- **ML Direction Predictions**: 📈/📉 for 1H, 4H, 1D timeframes
- **Confidence Scores**: ML model confidence per timeframe
- **Optimal Action**: BUY/SELL/HOLD/STRONG_BUY/STRONG_SELL
- **Sentiment & Technical**: Input features used by ML model

### **Feature Importance**
- Top 5 most important features from your trained models
- Visual importance percentages
- Updates after each evening training session

---

## 🗄️ Data Flow Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  app.main morning   │    │   ML Training       │    │  Integrated ML      │
│                     │    │   Pipeline          │    │  Dashboard          │
│ • Market data       │───▶│                     │───▶│                     │
│ • News sentiment    │    │ • Feature eng.      │    │ • Real predictions  │
│ • Technical calc.   │    │ • Model training    │    │ • Training status   │
│                     │    │ • Validation        │    │ • Performance metrics│
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ enhanced_training   │    │ Trained ML Models   │    │ Frontend Display    │
│ _data.db           │    │ (Random Forest,     │    │ (React Components)  │
│                     │    │  XGBoost, NN)      │    │                     │
│ • 54+ features      │    │                     │    │ • Live updates      │
│ • Historical data   │    │ • .pkl model files  │    │ • Interactive UI    │
│ • Validation data   │    │ • Metadata JSON     │    │ • Error handling    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 🔧 Technical Implementation

### **API Endpoints**

#### `/api/ml/enhanced-predictions`
```json
{
  "predictions": [
    {
      "symbol": "CBA.AX",
      "bank_name": "Commonwealth Bank",
      "features": {
        "sentiment_score": 0.234,
        "rsi": 68.2,
        "current_price": 121.30,
        "volume_ratio": 1.15
      },
      "direction_predictions": {
        "1h": true,   // Predicts UP
        "4h": false,  // Predicts DOWN  
        "1d": true    // Predicts UP
      },
      "confidence_scores": {
        "1h": 0.78,   // 78% confidence
        "4h": 0.65,   // 65% confidence
        "1d": 0.81    // 81% confidence
      },
      "optimal_action": "BUY",
      "overall_confidence": 0.75
    }
  ]
}
```

#### `/api/ml/training-status`
```json
{
  "last_training_run": "2025-07-27T18:30:00",
  "model_accuracy": {
    "direction_accuracy_1h": 0.72,  // 72% accuracy
    "direction_accuracy_4h": 0.68,  // 68% accuracy  
    "direction_accuracy_1d": 0.75   // 75% accuracy
  },
  "training_samples": 2847,
  "feature_importance": [
    {"feature": "sentiment_score", "importance": 0.18},
    {"feature": "rsi", "importance": 0.15},
    {"feature": "price_vs_sma20", "importance": 0.12}
  ],
  "validation_status": "PASSED"
}
```

### **ML Integration Code**
```python
# Backend integration with your ML pipeline
from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline

ml_pipeline = EnhancedMLTrainingPipeline()

# Get latest sentiment data
sentiment_data = get_latest_sentiment_data(symbol)

# Use your trained models for prediction
prediction_result = ml_pipeline.predict_enhanced(sentiment_data, symbol)

# Returns multi-timeframe predictions with confidence scores
```

---

## 🎯 Comparison: Simple ML vs Integrated ML

| Feature | Simple ML Dashboard | Integrated ML Dashboard |
|---------|-------------------|----------------------|
| **Data Source** | Simulated sentiment | Real morning collection |
| **ML Models** | Mock predictions | Your trained models |
| **Training** | No training | Evening ML pipeline |
| **Predictions** | Generated scenarios | Real ML outputs |
| **Accuracy** | N/A | Actual backtested metrics |
| **Features** | Basic sentiment | 54+ engineered features |
| **Updates** | Independent process | Connected to your workflow |

---

## 🔍 Troubleshooting

### **Dashboard Shows Mock Data**
If you see "Mock Data Mode ⚠️":
1. Run evening training: `python -m app.main evening`
2. Check if models exist: `ls data/ml_models/models/`
3. Verify API connectivity: `curl http://localhost:8000/api/ml/training-status`

### **No Predictions Available**
1. Run morning data collection: `python -m app.main morning`
2. Run evening training: `python -m app.main evening`
3. Check database: `ls data/ml_models/enhanced_training_data.db`

### **Low Model Accuracy**
1. Collect more training data (run morning/evening for several days)
2. Check feature quality in dashboard
3. Review validation metrics in evening analysis

---

## 📈 Usage Workflow

### **Daily Operation**
```bash
# 1. Morning - Collect data
python -m app.main morning

# 2. During day - Monitor dashboard
# Open http://localhost:3000 → Integrated ML tab

# 3. Evening - Train models
python -m app.main evening

# 4. Next day - View updated predictions
# Dashboard automatically shows new model results
```

### **Development Workflow**
```bash
# 1. Start integrated system
./start_integrated_ml_system.sh

# 2. Generate training data
python -m app.main morning
python -m app.main evening

# 3. Test dashboard integration
# Open browser → Integrated ML tab

# 4. Verify real predictions
# Check that dashboard shows trained model results, not mock data
```

---

## 🎉 Benefits

1. **Real ML Integration**: Uses your actual trained models, not simulations
2. **Complete Workflow**: Connects morning → evening → dashboard
3. **Live Updates**: Dashboard refreshes with new model predictions
4. **Performance Tracking**: Shows actual model accuracy and feature importance
5. **Multiple Timeframes**: 1H, 4H, 1D predictions with separate confidence scores
6. **Actionable Insights**: BUY/SELL recommendations based on trained models

The Integrated ML Dashboard bridges the gap between your ML training pipeline and real-time decision making, providing a complete end-to-end trading system visualization.

---

*This dashboard represents the full realization of your ML trading system architecture.*
