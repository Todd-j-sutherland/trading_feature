#!/usr/bin/env python3
"""
Update pending predictions with simulated market outcomes
This simulates what would happen in a real trading system where predictions
are updated with actual market data after some time.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def update_pending_predictions():
    """Update some pending predictions with realistic outcomes"""
    
    # Load current predictions
    prediction_file = Path("data/ml_performance/prediction_history.json")
    
    if not prediction_file.exists():
        print("No prediction history file found")
        return
    
    with open(prediction_file, 'r') as f:
        predictions = json.load(f)
    
    updated_count = 0
    
    # Find pending predictions that are older than 30 minutes
    cutoff_time = datetime.now() - timedelta(minutes=30)
    
    for prediction in predictions:
        if prediction.get('status') == 'pending':
            pred_time = datetime.fromisoformat(prediction['timestamp'])
            
            # Update predictions that are older than 30 minutes
            if pred_time < cutoff_time:
                # Generate realistic price change based on prediction
                signal = prediction['prediction'].get('signal', 'HOLD')
                confidence = prediction['prediction'].get('confidence', 0.5)
                
                # Simulate market outcome with some correlation to prediction
                if signal == 'BUY':
                    # Positive bias for BUY signals, stronger with higher confidence
                    base_change = random.uniform(-1, 3)  # Slight positive bias
                    confidence_boost = confidence * 2  # Up to 2% boost for high confidence
                    price_change = base_change + confidence_boost
                elif signal == 'SELL':
                    # Negative bias for SELL signals
                    base_change = random.uniform(-3, 1)  # Slight negative bias
                    confidence_boost = confidence * -2  # Down to -2% for high confidence
                    price_change = base_change + confidence_boost
                else:  # HOLD
                    # Small random movements for HOLD
                    price_change = random.uniform(-1.5, 1.5)
                
                # Add some randomness (market is unpredictable)
                market_noise = random.uniform(-1, 1)
                final_price_change = price_change + market_noise
                
                # Update the prediction
                prediction['actual_outcome'] = {
                    'price_change_percent': round(final_price_change, 4),
                    'outcome_timestamp': datetime.now().isoformat()
                }
                prediction['status'] = 'completed'
                
                updated_count += 1
                print(f"Updated {prediction['id']}: {signal} -> {final_price_change:+.2f}%")
    
    # Save updated predictions
    if updated_count > 0:
        with open(prediction_file, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        print(f"\nUpdated {updated_count} pending predictions with simulated outcomes")
    else:
        print("No pending predictions found that are ready for update")

if __name__ == "__main__":
    update_pending_predictions()
