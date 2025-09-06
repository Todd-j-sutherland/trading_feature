#!/usr/bin/env python3
"""
Remote Prediction Status Checker
Check for predictions needing outcome evaluation on remote server
"""

import sqlite3
from datetime import datetime, timedelta

def check_remote_predictions():
    """Check for predictions needing outcomes"""
    
    try:
        conn = sqlite3.connect('/root/test/data/trading_predictions.db')
        cursor = conn.cursor()
        
        print('🔍 REMOTE PREDICTIONS NEEDING OUTCOMES')
        print('=' * 50)
        
        # Check recent predictions without outcomes
        cursor.execute('''
        SELECT 
            p.symbol,
            p.prediction_timestamp,
            p.predicted_action,
            p.entry_price,
            p.predicted_direction,
            p.predicted_magnitude,
            p.action_confidence,
            p.prediction_id
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE o.prediction_id IS NULL
        AND p.prediction_timestamp > datetime("now", "-7 days")
        ORDER BY p.prediction_timestamp DESC
        LIMIT 20
        ''')
        
        predictions = cursor.fetchall()
        print(f'Found {len(predictions)} recent predictions without outcomes:')
        print()
        
        if predictions:
            for pred in predictions:
                symbol, pred_time, action, entry_price, direction, magnitude, confidence, pred_id = pred
                print(f'{symbol}: {pred_time} | Action: {action} | Entry: ${entry_price:.2f} | Dir: {direction} | Mag: {magnitude:.4f} | Conf: {confidence:.3f}')
        else:
            print('✅ All recent predictions have outcomes!')
        
        print()
        print('📊 TOTAL PREDICTIONS VS OUTCOMES:')
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM outcomes')
        total_outcomes = cursor.fetchone()[0]
        
        print(f'Total Predictions: {total_predictions}')
        print(f'Total Outcomes: {total_outcomes}')
        print(f'Missing Outcomes: {total_predictions - total_outcomes}')
        
        # Check most recent predictions
        print()
        print('📅 MOST RECENT PREDICTIONS:')
        cursor.execute('''
        SELECT symbol, prediction_timestamp, predicted_action, entry_price
        FROM predictions 
        ORDER BY prediction_timestamp DESC 
        LIMIT 5
        ''')
        
        recent = cursor.fetchall()
        for pred in recent:
            symbol, pred_time, action, entry_price = pred
            print(f'{symbol}: {pred_time} | {action} | ${entry_price:.2f}')
            
        # Check when last outcome was evaluated
        print()
        print('🕐 LAST OUTCOME EVALUATION:')
        cursor.execute('''
        SELECT MAX(evaluation_timestamp) FROM outcomes
        ''')
        
        last_eval = cursor.fetchone()[0]
        if last_eval:
            print(f'Last evaluation: {last_eval}')
        else:
            print('No evaluations found')
        
        conn.close()
        
        return len(predictions)
        
    except Exception as e:
        print(f'❌ Error checking remote predictions: {e}')
        return -1

if __name__ == "__main__":
    missing_count = check_remote_predictions()
    
    if missing_count > 0:
        print()
        print('💡 TO FORCE OUTCOME EVALUATION:')
        print('   bash evaluate_predictions.sh')
        print('   OR')
        print('   python3 fixed_outcome_evaluator.py')
    elif missing_count == 0:
        print()
        print('✅ All predictions have outcomes - system is up to date!')
