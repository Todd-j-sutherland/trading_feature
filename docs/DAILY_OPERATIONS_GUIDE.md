# 📅 Daily Operations Guide

## Overview
Your trading analysis system has been designed with sophisticated daily, evening, and continuous data collection routines. This guide explains what each operation does and how they work together.

## 🌅 Morning Routine (`python -m app.main morning`)

### What It Does
The morning routine prepares your system for the trading day by:

1. **System Health Check**
   - Verifies all AI components are operational
   - Checks data feed connections
   - Validates ML model availability

2. **Data Initialization**
   - Initializes ASX data feeds for real-time market data
   - Starts smart news collector for continuous monitoring
   - Loads latest ML models and configurations

3. **Market Overview Analysis**
   - Analyzes current market conditions for major indices (ASX200, ALL_ORDS)
   - Performs sentiment analysis for all major bank stocks
   - Calculates overnight sentiment shifts

4. **AI Pattern Recognition Setup**
   - Runs pattern detection on overnight price movements
   - Identifies any significant technical pattern changes
   - Prepares pattern alerts for the day

5. **Risk Assessment Initialization**
   - Calculates current market volatility
   - Updates risk parameters based on overnight developments
   - Sets position sizing guidelines for the day

6. **Smart Data Collection Activation**
   - **Automatically starts continuous news collection**
   - Begins Reddit sentiment monitoring
   - Initializes technical data streaming

### Key Features
- **✅ Real-time data collection starts automatically**
- **✅ No separate command needed for continuous monitoring**
- **✅ Sets up all AI systems for the day**

## 🌆 Evening Routine (`python -m app.main evening`)

### What It Does
The evening routine performs comprehensive end-of-day analysis and ML training:

1. **Comprehensive Data Analysis**
   - Analyzes all collected news and sentiment data from the day
   - Performs detailed sentiment analysis for all bank stocks
   - Reviews social media sentiment trends

2. **Advanced ML Processing**
   - **Trains ML models with the day's data (87+ samples)**
   - Updates transformer ensemble models
   - Optimizes prediction algorithms

3. **Pattern Recognition Analysis**
   - Comprehensive pattern analysis with 3-month historical data
   - Identifies daily pattern formations
   - Updates pattern confidence scores

4. **Anomaly Detection Report**
   - Analyzes the day for any market anomalies
   - Generates severity assessments
   - Provides recommendations for the next day

5. **Position Sizing Optimization**
   - Reviews and optimizes position sizing strategies
   - Updates risk parameters based on daily performance
   - Calculates optimal positions for current market conditions

6. **Paper Trading Performance**
   - Reviews virtual trading performance
   - Updates win rates and performance metrics
   - Generates performance reports

7. **ML Model Training & Optimization**
   - **This replaces your old weekend routine**
   - Trains models with the latest data
   - Optimizes algorithms for better performance
   - Updates prediction thresholds

### Key Features
- **✅ Includes your weekend ML training functionality**
- **✅ Comprehensive model optimization**
- **✅ Performance tracking and reporting**

## 🔄 Continuous Data Collection

### Automatic Collection (Started by Morning Routine)
The morning routine automatically starts:

1. **Smart News Collector**
   - Continuously monitors 7+ news sources
   - Real-time sentiment analysis
   - Automatic relevance filtering

2. **Technical Data Streaming**
   - Real-time price updates
   - Volume and volatility monitoring
   - Technical indicator calculations

3. **Social Media Monitoring**
   - Reddit sentiment tracking
   - Social media trend analysis
   - Real-time social sentiment scores

### Manual Collection Commands
If you need to run specific collection tasks:

```bash
# Force news collection for all banks
python -m app.main news --all

# Continuous news monitoring (if not already running)
python -m app.main news --continuous

# Specific bank analysis
python -m app.main news --symbol CBA.AX
```

## 📊 Data Flow Architecture

```
Morning Routine
     ↓
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   News Data     │    │  Technical Data  │    │  Social Media   │
│   Collection    │    │   Streaming      │    │   Monitoring    │
│   (Continuous)  │    │   (Real-time)    │    │   (Continuous)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
     ↓                          ↓                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Data Storage & Processing                    │
│          (sentiment_history/, ml_models/, cache/)               │
└─────────────────────────────────────────────────────────────────┘
     ↓
Evening Routine
     ↓
┌─────────────────────────────────────────────────────────────────┐
│              ML Training & Model Optimization                   │
│        (Replaces weekend routine - happens daily)              │
└─────────────────────────────────────────────────────────────────┘
```

## 🤖 Machine Learning Training Schedule

### Daily Training (Evening Routine)
- **Frequency**: Every evening
- **Data**: Previous 24-48 hours of market activity
- **Purpose**: Fine-tune models with latest market conditions

### Weekly Optimization (Automated)
- **Frequency**: Every 7 days (tracked automatically)
- **Data**: Full week of trading data
- **Purpose**: Major model architecture updates

### Model Types Trained
1. **Sentiment Models**: News and social media sentiment prediction
2. **Pattern Recognition**: Technical pattern identification
3. **Anomaly Detection**: Market anomaly identification
4. **Position Sizing**: Optimal position calculation models

## 📈 Performance Tracking

### Current Status
- **87 training samples** collected and ready
- **ML models optimized** with latest data
- **453 sentiment records** loaded for analysis

### Data Sources
- **News**: 7+ Australian financial news sources
- **Social Media**: Reddit (AusFinance, ASX_Bets, etc.)
- **Technical**: Real-time ASX market data
- **Fundamental**: Company financial data

## 🎯 Recommended Daily Workflow

### 1. Start Your Day
```bash
python -m app.main morning
```
- Runs comprehensive morning analysis
- **Automatically starts all continuous data collection**
- Sets up AI systems for the day

### 2. Monitor During Day
- Check dashboard: `python -m app.main dashboard`
- Review alerts and recommendations
- Monitor real-time data (collected automatically)

### 3. End Your Day
```bash
python -m app.main evening
```
- Comprehensive analysis of the day's data
- **ML model training and optimization**
- Performance review and optimization

### 4. Weekly Health Check
```bash
python -m app.main status
```
- Verify all systems are operational
- Check data collection statistics

## ⚠️ Important Notes

### What Changed From Your Original Setup
1. **Weekend ML Training** → Now happens daily in evening routine
2. **Manual Data Collection** → Now automatic with morning routine
3. **Separate Commands** → Integrated into morning/evening workflows

### No Additional Commands Needed
- ✅ Morning routine starts all continuous collection
- ✅ Evening routine includes ML training
- ✅ Dashboard shows real-time data automatically
- ✅ All AI systems work together seamlessly

### Data Storage Locations
- **Sentiment History**: `data/sentiment_history/`
- **ML Models**: `data/ml_models/`
- **Market Data**: `data/historical/`
- **Reports**: `reports/`

Your system is now fully automated and requires only the morning and evening commands to maintain optimal performance!
