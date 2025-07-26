# Enhanced Analyzers

This folder contains the enhanced morning and evening analyzers with full ML integration.

## Files

### `enhanced_morning_analyzer_with_ml.py`
- **Purpose**: Comprehensive morning market analysis with enhanced ML features
- **Features**: 54+ ML features, sentiment analysis, technical indicators
- **Integration**: Works with `app.main morning` command
- **Key Method**: `run_enhanced_morning_analysis()`

### `enhanced_evening_analyzer_with_ml.py`  
- **Purpose**: End-of-day analysis with ML validation and performance tracking
- **Features**: Model performance validation, prediction accuracy tracking
- **Integration**: Works with `app.main evening` command
- **Key Method**: `run_enhanced_evening_analysis()`

## Usage

These analyzers are automatically detected and used by the daily manager when you run:
```bash
python app.main morning  # Uses enhanced_morning_analyzer_with_ml.py
python app.main evening  # Uses enhanced_evening_analyzer_with_ml.py
```

## Dependencies
- Enhanced ML Pipeline: `app/core/ml/enhanced_training_pipeline.py`
- Technical Analysis: `app/core/analysis/technical.py`
- Sentiment Analysis: `app/core/sentiment/news_analyzer.py`
- Settings: `app/config/settings.py`

## Features
- Comprehensive sentiment analysis with transformers
- Technical indicator integration  
- Multi-output ML predictions
- Data validation and quality scoring
- Australian market-specific features
- Graceful fallback when ML models unavailable
