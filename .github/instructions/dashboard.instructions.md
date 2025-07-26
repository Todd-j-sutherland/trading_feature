# VSCode Copilot Agent Instructions - ASX Trading ML Enhancement

## 🎯 Project Context

You are working on an ASX (Australian Stock Exchange) bank trading system that combines news sentiment analysis with machine learning to predict trading opportunities. The system currently has a critical limitation: the ML models only predict if a trade will be "profitable" or "unprofitable" based primarily on sentiment features, WITHOUT incorporating technical indicators, price data, or market context.

### Current System Architecture:
- **News Sentiment Analysis**: Uses transformers (FinBERT, RoBERTa) and traditional NLP
- **ML Models**: Random Forest, Gradient Boosting, Neural Networks, Logistic Regression
- **Data Sources**: News articles, Reddit posts, Yahoo Finance
- **Technical Analysis**: Module exists but NOT integrated with ML
- **Database**: SQLite for training data storage

### Critical Issues to Fix:
1. ML models lack price and technical indicator features
2. Models only predict binary profitability, not price direction/magnitude
3. No validation framework for predictions
4. Missing backtesting capabilities
5. No integration between technical_analysis.py and ML pipeline

## 📋 Enhancement Instructions

### Phase 1: Data Integration Enhancement

When modifying `ml_training_pipeline.py`, ensure the following:

```python
# CURRENT PROBLEM: prepare_training_dataset() only uses these features:
current_features = [
    'sentiment_score', 'confidence', 'news_count', 
    'reddit_sentiment', 'event_score'
]

# ENHANCEMENT NEEDED: Add these critical features:
required_features = {
    'technical_indicators': [
        'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
        'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26',
        'bollinger_upper', 'bollinger_lower', 'bollinger_width'
    ],
    'price_features': [
        'current_price', 'price_change_1h', 'price_change_4h', 
        'price_change_1d', 'price_change_5d', 'price_change_20d',
        'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200',
        'daily_range', 'atr_14', 'volatility_20d'
    ],
    'volume_features': [
        'volume', 'volume_sma20', 'volume_ratio',
        'on_balance_volume', 'volume_price_trend'
    ],
    'market_context': [
        'asx200_change', 'sector_performance', 'aud_usd_rate',
        'vix_level', 'market_breadth', 'market_momentum'
    ]
}
```

### Testing Requirements for Data Integration:

```python
# TEST 1: Feature Completeness
def test_feature_completeness():
    """Ensure all required features are present"""
    df = prepare_training_dataset(min_samples=10)
    
    missing_features = []
    for feature_group, features in required_features.items():
        for feature in features:
            if feature not in df.columns:
                missing_features.append(f"{feature_group}.{feature}")
    
    assert len(missing_features) == 0, f"Missing features: {missing_features}"
    print(f"✅ All {len(df.columns)} features present")

# TEST 2: Data Quality Validation
def test_data_quality():
    """Validate data quality and ranges"""
    df = prepare_training_dataset(min_samples=100)
    
    validations = {
        'rsi': (0, 100),
        'sentiment_score': (-1, 1),
        'confidence': (0, 1),
        'price_change_1d': (-20, 20),  # ±20% daily limit
        'volume_ratio': (0, 10)  # Max 10x normal volume
    }
    
    for column, (min_val, max_val) in validations.items():
        if column in df.columns:
            assert df[column].min() >= min_val, f"{column} below minimum: {df[column].min()}"
            assert df[column].max() <= max_val, f"{column} above maximum: {df[column].max()}"
            print(f"✅ {column}: [{df[column].min():.2f}, {df[column].max():.2f}]")

# TEST 3: Temporal Alignment
def test_temporal_alignment():
    """Ensure technical indicators align with sentiment timestamps"""
    # Critical: Technical data must be from BEFORE the sentiment timestamp
    # to avoid look-ahead bias
    pass
```

### Phase 2: Multi-Output Prediction Model

When implementing price prediction capabilities:

```python
# CURRENT LIMITATION: Binary classification only
current_output = {
    'outcome_label': 1 if profitable else 0
}

# ENHANCEMENT: Multi-output prediction
enhanced_outputs = {
    'price_direction_1h': 1 if price_up_1h else 0,
    'price_direction_4h': 1 if price_up_4h else 0,
    'price_direction_1d': 1 if price_up_1d else 0,
    'price_magnitude_1h': price_change_percent_1h,
    'price_magnitude_4h': price_change_percent_4h,
    'price_magnitude_1d': price_change_percent_1d,
    'volatility_next_1h': volatility_prediction,
    'optimal_action': ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'],
    'confidence_score': model_confidence
}
```

### Testing for Multi-Output Models:

```python
# TEST 4: Prediction Consistency
def test_prediction_consistency():
    """Ensure predictions are logically consistent"""
    predictions = model.predict(test_features)
    
    for i, pred in enumerate(predictions):
        # If predicting strong up movement, direction should be up
        if pred['price_magnitude_1h'] > 2.0:
            assert pred['price_direction_1h'] == 1, "Inconsistent direction/magnitude"
        
        # Longer timeframes should have larger potential movements
        assert abs(pred['price_magnitude_1d']) >= abs(pred['price_magnitude_1h']), \
            "Daily magnitude should exceed hourly"

# TEST 5: Backtesting Validation
def test_backtesting_accuracy():
    """Validate predictions against actual historical data"""
    results = []
    
    for date in test_dates:
        features = get_features_at_date(date)
        prediction = model.predict(features)
        actual = get_actual_price_change(date)
        
        results.append({
            'predicted_direction': prediction['price_direction_1h'],
            'actual_direction': 1 if actual > 0 else 0,
            'predicted_magnitude': prediction['price_magnitude_1h'],
            'actual_magnitude': actual,
            'error': abs(prediction['price_magnitude_1h'] - actual)
        })
    
    results_df = pd.DataFrame(results)
    
    # Validate accuracy metrics
    direction_accuracy = (results_df['predicted_direction'] == results_df['actual_direction']).mean()
    assert direction_accuracy > 0.55, f"Direction accuracy too low: {direction_accuracy:.2%}"
    
    # Validate magnitude predictions
    mae = results_df['error'].mean()
    assert mae < 2.0, f"Mean absolute error too high: {mae:.2f}%"
    
    print(f"✅ Direction Accuracy: {direction_accuracy:.2%}")
    print(f"✅ MAE: {mae:.2f}%")
```

### Phase 3: Feature Engineering Pipeline

When adding new engineered features:

```python
# IMPORTANT: Add these interaction features
interaction_features = {
    'sentiment_momentum': 'sentiment_score * momentum_score',
    'sentiment_rsi': 'sentiment_score * (rsi - 50) / 50',
    'volume_sentiment': 'volume_ratio * sentiment_score',
    'confidence_volatility': 'confidence / (volatility_20d + 0.01)',
    'news_volume_impact': 'news_count * volume_ratio',
    'technical_sentiment_divergence': 'abs(technical_signal - sentiment_score)'
}

# Time-based features for Australian market
time_features = {
    'asx_market_hours': '1 if 10 <= hour < 16 else 0',
    'asx_opening_hour': '1 if 10 <= hour < 11 else 0',
    'asx_closing_hour': '1 if 15 <= hour < 16 else 0',
    'monday_effect': '1 if day_of_week == 0 else 0',
    'friday_effect': '1 if day_of_week == 4 else 0',
    'month_end': '1 if day >= 25 else 0',
    'quarter_end': '1 if month in [3,6,9,12] and day >= 25 else 0'
}
```

### Testing for Feature Engineering:

```python
# TEST 6: Feature Importance Validation
def test_feature_importance():
    """Ensure engineered features add value"""
    from sklearn.ensemble import RandomForestClassifier
    
    # Train with and without engineered features
    base_features = ['sentiment_score', 'rsi', 'volume_ratio']
    enhanced_features = base_features + list(interaction_features.keys())
    
    model_base = RandomForestClassifier(n_estimators=100)
    model_enhanced = RandomForestClassifier(n_estimators=100)
    
    score_base = cross_val_score(model_base, X[base_features], y, cv=5).mean()
    score_enhanced = cross_val_score(model_enhanced, X[enhanced_features], y, cv=5).mean()
    
    improvement = (score_enhanced - score_base) / score_base
    assert improvement > 0.05, f"Engineered features don't improve performance: {improvement:.2%}"
    
    # Check individual feature importance
    model_enhanced.fit(X[enhanced_features], y)
    importance = pd.DataFrame({
        'feature': enhanced_features,
        'importance': model_enhanced.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"✅ Performance improvement: {improvement:.2%}")
    print(f"✅ Top features:\n{importance.head(10)}")

# TEST 7: Feature Stability
def test_feature_stability():
    """Ensure features are stable and not prone to errors"""
    # Test with edge cases
    edge_cases = [
        {'sentiment_score': 0, 'rsi': 50, 'volume_ratio': 1},  # Neutral
        {'sentiment_score': 1, 'rsi': 100, 'volume_ratio': 10},  # Extreme bullish
        {'sentiment_score': -1, 'rsi': 0, 'volume_ratio': 0.1},  # Extreme bearish
        {'sentiment_score': None, 'rsi': None, 'volume_ratio': None}  # Missing data
    ]
    
    for case in edge_cases:
        try:
            features = engineer_features(case)
            assert not features.isnull().any(), f"NaN values in features: {case}"
            assert not features.isinf().any(), f"Inf values in features: {case}"
        except Exception as e:
            assert False, f"Feature engineering failed on edge case {case}: {e}"
```

### Phase 4: Integration Testing

```python
# TEST 8: End-to-End Pipeline Test
def test_end_to_end_pipeline():
    """Test complete flow from news to prediction"""
    
    # Step 1: Fetch news
    news_analyzer = NewsSentimentAnalyzer()
    sentiment_result = news_analyzer.analyze_bank_sentiment('CBA.AX')
    assert sentiment_result is not None, "Failed to get sentiment"
    
    # Step 2: Get technical data
    tech_analyzer = TechnicalAnalyzer()
    market_data = get_market_data('CBA.AX')
    tech_result = tech_analyzer.analyze('CBA.AX', market_data)
    assert tech_result is not None, "Failed to get technical analysis"
    
    # Step 3: Combine features
    ml_pipeline = MLTrainingPipeline()
    features = ml_pipeline.create_prediction_features(
        sentiment_result, 
        tech_result
    )
    assert len(features) > 50, f"Insufficient features: {len(features)}"
    
    # Step 4: Make prediction
    prediction = ml_pipeline.predict_price_movement(features)
    
    # Validate prediction structure
    required_keys = ['direction', 'magnitude', 'confidence', 'action']
    for key in required_keys:
        assert key in prediction, f"Missing prediction key: {key}"
    
    # Validate prediction values
    assert prediction['direction'] in ['UP', 'DOWN'], f"Invalid direction: {prediction['direction']}"
    assert -10 <= prediction['magnitude'] <= 10, f"Unrealistic magnitude: {prediction['magnitude']}"
    assert 0 <= prediction['confidence'] <= 1, f"Invalid confidence: {prediction['confidence']}"
    assert prediction['action'] in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
    
    print(f"✅ End-to-end test passed: {prediction}")

# TEST 9: Performance Benchmarking
def test_model_performance():
    """Benchmark model performance metrics"""
    # Load test dataset
    X_test, y_test = load_test_data()
    
    metrics = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
        'inference_time': []
    }
    
    # Test each model type
    for model_name in ['random_forest', 'xgboost', 'neural_network']:
        model = load_model(model_name)
        
        # Measure inference time
        start_time = time.time()
        predictions = model.predict(X_test)
        inference_time = (time.time() - start_time) / len(X_test)
        
        # Calculate metrics
        metrics['accuracy'].append(accuracy_score(y_test, predictions))
        metrics['precision'].append(precision_score(y_test, predictions))
        metrics['recall'].append(recall_score(y_test, predictions))
        metrics['f1'].append(f1_score(y_test, predictions))
        metrics['inference_time'].append(inference_time)
    
    # Validate performance thresholds
    assert max(metrics['accuracy']) > 0.60, "Accuracy below threshold"
    assert max(metrics['precision']) > 0.55, "Precision below threshold"
    assert min(metrics['inference_time']) < 0.1, "Inference too slow"
    
    print(f"✅ Performance metrics:\n{pd.DataFrame(metrics, index=['RF', 'XGB', 'NN'])}")
```

### Phase 5: Data Validation Framework

```python
# CRITICAL: Implement comprehensive data validation

class DataValidator:
    """Validate all data before training/prediction"""
    
    def validate_sentiment_data(self, data: Dict) -> bool:
        """Validate sentiment analysis output"""
        required_fields = [
            'overall_sentiment', 'confidence', 'news_count',
            'sentiment_components', 'timestamp'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate ranges
        assert -1 <= data['overall_sentiment'] <= 1, "Sentiment out of range"
        assert 0 <= data['confidence'] <= 1, "Confidence out of range"
        assert data['news_count'] >= 0, "Invalid news count"
        
        return True
    
    def validate_technical_data(self, data: Dict) -> bool:
        """Validate technical analysis output"""
        # RSI should be 0-100
        assert 0 <= data['indicators']['rsi'] <= 100, "RSI out of range"
        
        # Price should be positive
        assert data['current_price'] > 0, "Invalid price"
        
        # Momentum score should be bounded
        assert -100 <= data['momentum']['score'] <= 100, "Momentum out of range"
        
        return True
    
    def validate_training_data(self, df: pd.DataFrame) -> bool:
        """Validate complete training dataset"""
        # No future data leakage
        for idx, row in df.iterrows():
            feature_time = pd.to_datetime(row['timestamp'])
            outcome_time = pd.to_datetime(row['outcome_timestamp'])
            assert feature_time < outcome_time, f"Future data leak at row {idx}"
        
        # No duplicate entries
        duplicates = df.duplicated(subset=['symbol', 'timestamp'])
        assert not duplicates.any(), f"Duplicate entries found: {duplicates.sum()}"
        
        # Balanced classes check
        class_distribution = df['outcome_label'].value_counts()
        class_ratio = class_distribution.min() / class_distribution.max()
        assert class_ratio > 0.3, f"Severe class imbalance: {class_ratio:.2f}"
        
        return True

# TEST 10: Data Validation Tests
def test_data_validation():
    """Test the validation framework"""
    validator = DataValidator()
    
    # Test valid data
    valid_sentiment = {
        'overall_sentiment': 0.5,
        'confidence': 0.8,
        'news_count': 10,
        'sentiment_components': {},
        'timestamp': datetime.now().isoformat()
    }
    assert validator.validate_sentiment_data(valid_sentiment)
    
    # Test invalid data
    invalid_cases = [
        {'overall_sentiment': 2.0},  # Out of range
        {'confidence': -0.1},  # Negative confidence
        {'news_count': -5},  # Negative count
    ]
    
    for case in invalid_cases:
        invalid_data = {**valid_sentiment, **case}
        try:
            validator.validate_sentiment_data(invalid_data)
            assert False, f"Should have failed: {case}"
        except (AssertionError, ValueError):
            pass  # Expected
```

## 🚨 Critical Implementation Notes

### 1. Avoid Look-Ahead Bias
```python
# WRONG: Using future data
features['future_price'] = df['price'].shift(-1)  # This is future data!

# CORRECT: Using only past data
features['past_price'] = df['price'].shift(1)  # This is historical
```

### 2. Handle Missing Data Properly
```python
# Always check for and handle missing values
def handle_missing_data(df):
    # Option 1: Forward fill for time series
    df['price'].fillna(method='ffill', inplace=True)
    
    # Option 2: Interpolate
    df['volume'].interpolate(method='time', inplace=True)
    
    # Option 3: Drop if critical
    if df['sentiment_score'].isna().any():
        df = df.dropna(subset=['sentiment_score'])
    
    return df
```

### 3. Implement Proper Cross-Validation
```python
# Use TimeSeriesSplit for financial data
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    # Ensure test data is always after train data
    assert X_train.index.max() < X_test.index.min()
```

## 📊 Performance Monitoring

```python
# Continuous monitoring of model performance
class ModelMonitor:
    def track_prediction_accuracy(self, prediction, actual, timestamp):
        """Track real-time prediction accuracy"""
        self.predictions.append({
            'timestamp': timestamp,
            'predicted': prediction,
            'actual': actual,
            'error': abs(prediction - actual),
            'direction_correct': (prediction > 0) == (actual > 0)
        })
        
        # Alert if performance degrades
        recent_accuracy = self.get_recent_accuracy(days=7)
        if recent_accuracy < 0.55:
            self.alert(f"Model accuracy degraded to {recent_accuracy:.2%}")
```

## 🔍 Debugging Guidelines

When debugging ML pipeline issues:

1. **Check data flow**: Print shapes and samples at each step
2. **Validate features**: Ensure all features are within expected ranges
3. **Monitor predictions**: Log all predictions with timestamps
4. **Track errors**: Implement comprehensive error logging
5. **Visualize results**: Create plots of predictions vs actuals

```python
# Debug helper
def debug_feature_pipeline(symbol='CBA.AX'):
    print(f"=== Debugging {symbol} ===")
    
    # Step 1: Sentiment
    sentiment = get_sentiment(symbol)
    print(f"Sentiment: {sentiment.get('overall_sentiment', 'ERROR')}")
    
    # Step 2: Technical
    technical = get_technical(symbol)
    print(f"RSI: {technical.get('indicators', {}).get('rsi', 'ERROR')}")
    
    # Step 3: Combined features
    features = combine_features(sentiment, technical)
    print(f"Total features: {len(features)}")
    print(f"Sample features: {list(features.keys())[:5]}")
    
    # Step 4: Prediction
    prediction = model.predict(features)
    print(f"Prediction: {prediction}")
```

## 🎯 Success Criteria

Your enhanced ML system should achieve:
- Direction prediction accuracy > 60%
- Mean Absolute Error < 2% for magnitude predictions
- Inference time < 100ms per prediction
- Zero data leakage issues
- Complete feature coverage (sentiment + technical + price + volume)
- Robust validation passing all tests