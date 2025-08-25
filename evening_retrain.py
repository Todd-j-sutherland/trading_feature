#!/usr/bin/env python3
"""
Evening ML Retraining Script
Runs automatically in the evening to retrain models
"""

import sys
import os
sys.path.append('.')

from datetime import datetime
import logging

def evening_retrain():
    """Evening retraining routine"""
    
    print(f'🌅 EVENING RETRAINING - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('=' * 50)
    
    # Import here to avoid issues if run during market hours
    from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
    
    pipeline = EnhancedMLPipeline()
    
    # Check if retraining is needed
    bias_detected = check_prediction_bias()
    
    if bias_detected:
        print('🚨 Bias detected - starting emergency retraining')
        accuracies = pipeline.train_models(min_samples=30)
        
        if accuracies:
            print('✅ Emergency retraining complete')
            # Auto-enable if accuracies are good
            min_accuracy = min(accuracies.values())
            if min_accuracy > 0.6:
                enable_retrained_models()
        else:
            print('❌ Emergency retraining failed - keeping traditional signals')
    else:
        print('✅ No bias detected - models performing well')

def check_prediction_bias():
    """Check if current predictions show bias"""
    
    import sqlite3
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Check last 50 predictions
    cursor.execute("""
        SELECT predicted_action, COUNT(*) as count
        FROM predictions 
        WHERE prediction_timestamp >= datetime('now', '-3 days')
        AND model_version NOT LIKE '%emergency%'
        GROUP BY predicted_action
    """)
    
    results = cursor.fetchall()
    total = sum(count for _, count in results)
    
    if total < 20:
        return False  # Not enough data
    
    # Check for severe bias (>80% one action, 0% another)
    action_counts = {action: count for action, count in results}
    buy_pct = (action_counts.get('BUY', 0) / total) * 100
    sell_pct = (action_counts.get('SELL', 0) / total) * 100
    
    # Bias if one action >80% or any action 0%
    severe_bias = (buy_pct > 80 or sell_pct > 80) or (buy_pct == 0 or sell_pct == 0)
    
    conn.close()
    return severe_bias

if __name__ == '__main__':
    evening_retrain()
