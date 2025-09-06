#!/usr/bin/env python3
"""
Force Outcome Evaluation for Specific Predictions
Processes the 24 missing outcome evaluations from September 5th
"""

import sqlite3
import logging
import yfinance as yf
from datetime import datetime, timedelta
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_evaluate_missing_outcomes():
    """Force evaluation of the 24 missing outcomes"""
    
    try:
        # Connect to database
        db_path = '/root/test/data/trading_predictions.db'
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        
        print('🔧 FORCING OUTCOME EVALUATION FOR MISSING PREDICTIONS')
        print('=' * 60)
        
        # Get predictions without outcomes
        cursor.execute('''
        SELECT 
            p.prediction_id,
            p.symbol,
            p.prediction_timestamp,
            p.predicted_action,
            p.entry_price,
            p.predicted_direction,
            p.predicted_magnitude,
            p.action_confidence
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE o.prediction_id IS NULL
        AND p.prediction_timestamp > datetime("now", "-7 days")
        ORDER BY p.prediction_timestamp DESC
        ''')
        
        predictions = cursor.fetchall()
        
        if not predictions:
            print('✅ No predictions need evaluation!')
            return 0
        
        print(f'Found {len(predictions)} predictions needing evaluation')
        
        evaluated_count = 0
        
        for pred in predictions:
            pred_id, symbol, pred_time, action, entry_price, direction, magnitude, confidence = pred
            
            try:
                # Calculate outcome (simple version - just get current price)
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')
                
                if hist.empty:
                    print(f'⚠️ No price data for {symbol}')
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Calculate return
                price_return = (current_price - entry_price) / entry_price
                
                # Determine if prediction was correct
                predicted_up = direction == 1
                actual_up = price_return > 0
                direction_correct = predicted_up == actual_up
                
                # Insert outcome
                cursor.execute('''
                INSERT INTO outcomes (
                    outcome_id,
                    prediction_id,
                    actual_return,
                    actual_direction,
                    entry_price,
                    exit_price,
                    evaluation_timestamp,
                    outcome_details,
                    performance_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"outcome_{pred_id}_{int(datetime.now().timestamp())}",
                    pred_id,
                    price_return,
                    1 if actual_up else 0,
                    entry_price,
                    current_price,
                    datetime.now().isoformat(),
                    f"Direction: {'Correct' if direction_correct else 'Incorrect'}",
                    f"Accuracy: {0.8 if direction_correct else 0.2}"
                ))
                
                print(f'✅ {symbol}: ${entry_price:.2f} → ${current_price:.2f} ({price_return*100:+.2f}%) - {"✓" if direction_correct else "✗"}')
                evaluated_count += 1
                
            except Exception as e:
                print(f'❌ Failed to evaluate {symbol}: {e}')
                continue
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print(f'\n🎉 Successfully evaluated {evaluated_count} predictions!')
        return evaluated_count
        
    except Exception as e:
        print(f'❌ Error during force evaluation: {e}')
        return 0

if __name__ == "__main__":
    count = force_evaluate_missing_outcomes()
    print(f'\nProcessed {count} missing outcomes')
