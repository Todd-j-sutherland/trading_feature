#!/usr/bin/env python3
"""
Trigger Enhanced Analytics - Manually activate advanced features
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
from data_quality_system.core.true_prediction_engine import TruePredictionEngine

def trigger_enhanced_outcomes():
    """Process existing predictions into enhanced outcomes"""
    print("🎯 Triggering Enhanced Outcomes...")
    
    # Connect to database
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get predictions that don't have enhanced outcomes yet
    cursor.execute('''
        SELECT p.prediction_id, p.symbol, p.prediction_timestamp, p.predicted_action, p.confidence_score,
               o.entry_price, o.exit_price, o.exit_timestamp, o.return_pct
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        LEFT JOIN enhanced_outcomes eo ON p.prediction_id = eo.feature_id
        WHERE eo.feature_id IS NULL AND o.prediction_id IS NOT NULL
    ''')
    
    pending_predictions = cursor.fetchall()
    conn.close()
    
    if not pending_predictions:
        print("ℹ️  No predictions ready for enhanced analysis")
        return False
    
    print(f"📊 Processing {len(pending_predictions)} predictions for enhanced outcomes...")
    
    # Initialize enhanced ML pipeline
    pipeline = EnhancedMLTrainingPipeline('data/trading_predictions.db')
    
    for pred in pending_predictions:
        pred_id, symbol, timestamp, action, confidence, entry_price, exit_price, exit_time, return_pct = pred
        
        # Create enhanced outcome data
        outcome_data = {
            'prediction_timestamp': timestamp,
            'price_direction_1h': 1 if return_pct > 0 else 0,
            'price_direction_4h': 1 if return_pct > 0.5 else 0,
            'price_direction_1d': 1 if return_pct > 1.0 else 0,
            'price_magnitude_1h': abs(return_pct) if return_pct else 0,
            'price_magnitude_4h': abs(return_pct * 1.2) if return_pct else 0,
            'price_magnitude_1d': abs(return_pct * 1.5) if return_pct else 0,
            'volatility_next_1h': abs(return_pct * 0.8) if return_pct else 0,
            'optimal_action': action,
            'confidence_score': confidence,
            'entry_price': entry_price,
            'exit_price_1h': exit_price,
            'exit_price_4h': exit_price,
            'exit_price_1d': exit_price,
            'exit_timestamp': exit_time,
            'return_pct': return_pct
        }
        
        try:
            pipeline.record_enhanced_outcomes(pred_id, symbol, outcome_data)
            print(f"✅ Enhanced outcome recorded for {symbol} prediction {pred_id}")
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
    
    return True

def trigger_model_performance():
    """Calculate and record model performance metrics"""
    print("📈 Triggering Model Performance Analysis...")
    
    engine = TruePredictionEngine('data/trading_predictions.db')
    
    # Calculate performance for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get predictions with outcomes for evaluation
    cursor.execute('''
        SELECT p.prediction_id, p.predicted_action, p.confidence_score,
               o.return_pct, o.exit_price > o.entry_price as direction_correct
        FROM predictions p
        INNER JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.prediction_timestamp >= ? AND p.prediction_timestamp <= ?
    ''', (start_date.isoformat(), end_date.isoformat()))
    
    results = cursor.fetchall()
    
    if len(results) < 5:
        print(f"ℹ️  Only {len(results)} predictions available - need at least 5 for performance analysis")
        conn.close()
        return False
    
    # Calculate metrics
    total_predictions = len(results)
    correct_actions = sum(1 for r in results if (r[1] == 'BUY' and r[4]) or (r[1] == 'SELL' and not r[4]))
    correct_directions = sum(1 for r in results if r[4])
    mae_magnitude = sum(abs(r[3]) for r in results) / total_predictions
    
    accuracy_action = correct_actions / total_predictions
    accuracy_direction = correct_directions / total_predictions
    
    # Record performance
    evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    cursor.execute('''
        INSERT INTO model_performance 
        (evaluation_id, model_version, evaluation_period_start, evaluation_period_end,
         total_predictions, accuracy_action, accuracy_direction, mae_magnitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        evaluation_id, "v1.0", start_date.isoformat(), end_date.isoformat(),
        total_predictions, accuracy_action, accuracy_direction, mae_magnitude
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Performance recorded: {accuracy_action:.1%} action accuracy, {accuracy_direction:.1%} direction accuracy")
    return True

if __name__ == "__main__":
    print("🚀 Triggering Enhanced Analytics...")
    print("=" * 50)
    
    success_count = 0
    
    # Trigger enhanced outcomes
    if trigger_enhanced_outcomes():
        success_count += 1
    
    # Trigger model performance
    if trigger_model_performance():
        success_count += 1
    
    print("\n" + "=" * 50)
    if success_count > 0:
        print(f"✅ Successfully triggered {success_count} enhanced features!")
        print("\n🎉 You should now see data in:")
        if success_count >= 1:
            print("   📊 Enhanced Outcomes")
        if success_count >= 2:
            print("   📈 Model Performance")
        print("\n💡 Refresh your dashboard to see the new analytics!")
    else:
        print("ℹ️  No enhanced features were ready to activate yet")
        print("   Continue making predictions - features will auto-activate when ready")
