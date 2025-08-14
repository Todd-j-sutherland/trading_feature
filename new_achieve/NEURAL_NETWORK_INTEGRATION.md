# Neural Network Integration with App.Main Processes

## Current System Architecture

Your trading system has a well-structured command-line interface via `app/main.py` with several key processes:

### 🌅 **Morning Routine** (`python -m app.main morning`)
**Current:** Data collection, market analysis, news sentiment
**With Neural Networks:** Enhanced predictions for day trading opportunities

### 🌆 **Evening Routine** (`python -m app.main evening`)  
**Current:** ML training, performance analysis, next-day preparation
**With Neural Networks:** LSTM model training and ensemble optimization

### 🧠 **ML Trading Commands**
- `ml-scores` - Display current ML scores
- `ml-trading` - Execute ML-based trades
- `pre-trade` - Pre-trade analysis for specific symbol
- `trading-history` - Show trading performance

## Integration Points for Neural Network Ensemble

### 1. Enhanced ML Training Pipeline Integration

**File:** `app/core/commands/ml_trading.py`

The neural network ensemble integrates at multiple levels:

```python
# Current MLTradingCommand class will be enhanced
class MLTradingCommand:
    def __init__(self):
        # Existing components
        self.ml_scorer = MLTradingScorer()
        self.alpaca_simulator = AlpacaTradingSimulator()
        
        # NEW: Neural network ensemble
        from app.core.ml.ensemble_predictor import create_ensemble_predictor
        self.ensemble_predictor = create_ensemble_predictor()
        
    def run_ml_analysis_before_trade(self):
        # Enhanced with ensemble predictions
        for symbol in symbols:
            # Existing sentiment analysis
            sentiment_data = self.news_analyzer.analyze_single_bank(symbol)
            
            # NEW: Ensemble prediction
            ensemble_prediction = self.ensemble_predictor.predict_ensemble(
                sentiment_data, symbol
            )
            
            # Combine results for final decision
```

### 2. Evening Routine Enhancement

**File:** `app/services/daily_manager.py` (evening_routine method)

```python
def evening_routine(self):
    """Enhanced evening routine with neural network training"""
    
    # Existing ML training
    self.train_enhanced_models()
    
    # NEW: Neural network training (when TensorFlow available remotely)
    if self.neural_networks_enabled:
        print("🧠 Training LSTM Neural Networks...")
        from app.core.ml.lstm_neural_network import train_lstm_model
        lstm_results = train_lstm_model()
        
        # Update ensemble weights based on performance
        from app.core.ml.ensemble_predictor import create_ensemble_predictor
        ensemble = create_ensemble_predictor()
        ensemble.update_ensemble_weights(lstm_results)
    
    # Performance comparison
    self.compare_model_performance()
```

### 3. Real-Time Prediction Enhancement

**Integration Flow:**
1. **Morning Analysis** → Neural networks predict day-trading opportunities
2. **Pre-Trade Checks** → Ensemble validates individual trades  
3. **Evening Training** → Models retrain with latest market data
4. **Performance Tracking** → Compare RF vs LSTM vs Ensemble results

## Command Integration Examples

### Current vs Enhanced Commands

#### `ml-scores` Command Enhancement
```python
# BEFORE (RandomForest only)
def run_ml_scores_display():
    manager = MLTradingManager()
    manager.display_ml_scores_summary()

# AFTER (Neural Network Ensemble)
def run_ml_scores_display():
    manager = MLTradingManager()
    
    # Display traditional ML scores
    manager.display_ml_scores_summary()
    
    # NEW: Display ensemble predictions
    from app.core.ml.ensemble_predictor import create_ensemble_predictor
    ensemble = create_ensemble_predictor()
    
    print("\n🧠 Neural Network Ensemble Predictions:")
    for symbol in ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']:
        sentiment_data = get_latest_sentiment(symbol)
        prediction = ensemble.predict_ensemble(sentiment_data, symbol)
        
        action = prediction.get('optimal_action', 'HOLD')
        confidence = prediction.get('confidence_scores', {}).get('average', 0)
        models_used = prediction.get('models_used', [])
        
        print(f"   {symbol}: {action} (conf: {confidence:.1%}, models: {', '.join(models_used)})")
```

#### `evening` Command Neural Network Integration
```python
def evening_routine(self):
    print("🌆 EVENING ROUTINE - Enhanced with Neural Networks")
    
    # Step 1: Standard data collection
    self.collect_market_data()
    self.process_news_sentiment()
    
    # Step 2: Train RandomForest models (existing)
    self.train_traditional_ml_models()
    
    # Step 3: NEW - Neural Network Training
    if self.check_remote_training_available():
        print("🧠 Training LSTM Neural Networks (Remote)...")
        self.train_neural_networks_remote()
    else:
        print("⚠️ Neural networks training locally unavailable")
        
    # Step 4: Ensemble optimization
    self.optimize_ensemble_weights()
    
    # Step 5: Performance comparison
    self.compare_all_models()  # RF vs LSTM vs Ensemble
```

## Data Flow Architecture

```
Morning Routine:
├── Collect Market Data
├── News Sentiment Analysis  
├── Economic Context Analysis
└── Neural Network Predictions → Trading Opportunities

Intraday:
├── Pre-Trade Analysis
│   ├── RandomForest Prediction
│   ├── LSTM Sequence Analysis  
│   └── Ensemble Decision
└── Trade Execution (if confidence > threshold)

Evening Routine:
├── Data Consolidation
├── Model Training
│   ├── RandomForest Retraining
│   ├── LSTM Neural Network Training (remote)
│   └── Ensemble Weight Optimization
├── Performance Analysis
└── Next Day Preparation
```

## Database Integration

The ensemble system leverages your existing `trading_unified.db`:

```sql
-- Existing tables used by neural networks
enhanced_features      -- Sequential data for LSTM
enhanced_outcomes      -- Training targets
positions             -- Trading history for performance tracking

-- New table for ensemble tracking
CREATE TABLE ensemble_predictions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timestamp TEXT,
    model_type TEXT,  -- 'random_forest', 'lstm', 'ensemble'
    prediction_data TEXT,  -- JSON with predictions
    actual_outcome REAL,   -- Actual price movement for accuracy tracking
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Command Line Usage Examples

```bash
# Standard ML analysis (RandomForest only)
python -m app.main ml-scores

# Enhanced ensemble analysis (RF + LSTM when available)
python -m app.main ml-scores --ensemble

# Evening routine with neural network training
python -m app.main evening --neural-training

# Trading with ensemble predictions
python -m app.main ml-trading --use-ensemble

# Performance comparison across all models
python -m app.main ml-performance --compare-all
```

## Remote Training Integration

Since TensorFlow can't run locally, the system includes remote training capabilities:

### Cloud Training Workflow
```python
# app/core/ml/remote_training.py
class RemoteNeuralTrainer:
    def queue_training_job(self):
        """Queue LSTM training job for cloud execution"""
        
    def download_trained_models(self):
        """Download trained models for local inference"""
        
    def update_local_ensemble(self):
        """Update ensemble with new LSTM models"""
```

### Integration with Evening Routine
```python
def evening_routine(self):
    # Queue remote neural network training
    remote_trainer = RemoteNeuralTrainer()
    job_id = remote_trainer.queue_training_job()
    
    # Continue with local RandomForest training
    self.train_local_models()
    
    # Check if remote training completed
    if remote_trainer.is_job_complete(job_id):
        remote_trainer.download_trained_models()
        remote_trainer.update_local_ensemble()
```

## Performance Monitoring Integration

The system tracks ensemble performance across all models:

```python
# Performance tracking in evening routine
def compare_model_performance(self):
    """Compare RandomForest vs LSTM vs Ensemble performance"""
    
    performance = {
        'random_forest': self.get_rf_performance(),
        'lstm': self.get_lstm_performance(), 
        'ensemble': self.get_ensemble_performance()
    }
    
    # Display comparison
    print("\n📊 Model Performance Comparison:")
    for model, stats in performance.items():
        accuracy = stats.get('accuracy', 0)
        sharpe = stats.get('sharpe_ratio', 0)
        drawdown = stats.get('max_drawdown', 0)
        print(f"   {model.title()}: {accuracy:.1%} accuracy, {sharpe:.2f} Sharpe, {drawdown:.1%} max drawdown")
    
    # Update ensemble weights based on recent performance
    ensemble_predictor.update_ensemble_weights(performance)
```

## Next Steps for Full Integration

1. **Add ensemble flag** to existing ML commands
2. **Enhance evening routine** with neural network training checks
3. **Update performance tracking** to include all model types
4. **Create ensemble-specific commands** for advanced users
5. **Integrate with Alpaca trading** for live execution

The neural network ensemble seamlessly integrates with your existing command structure while maintaining backward compatibility and graceful fallback when TensorFlow isn't available.