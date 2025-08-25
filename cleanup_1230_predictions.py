#!/usr/bin/env python3
"""
Clean up broken 12:30 predictions
"""

import sqlite3
from datetime import datetime

def cleanup_1230_predictions():
    print('🧹 CLEANING UP NEW PRICE ERRORS (12:30)')
    print('=' * 45)

    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()

    # Find 12:30 predictions with zero prices
    cursor.execute('''
        SELECT prediction_id, symbol, prediction_timestamp, predicted_action, entry_price
        FROM predictions 
        WHERE entry_price = 0.0 
        AND prediction_timestamp LIKE '%12:30:27%'
        AND DATE(prediction_timestamp) = ?
    ''', (datetime.now().strftime('%Y-%m-%d'),))

    broken_preds = cursor.fetchall()

    print(f'📊 Found {len(broken_preds)} broken 12:30 predictions:')
    for pred_id, symbol, timestamp, action, price in broken_preds:
        print(f'   {symbol}: {action} @ ${price:.2f} [{timestamp}]')

    if len(broken_preds) > 0:
        print()
        print('🗑️  Deleting broken 12:30 predictions...')
        
        for pred_id, symbol, timestamp, action, price in broken_preds:
            cursor.execute('DELETE FROM predictions WHERE prediction_id = ?', (pred_id,))
            print(f'   ✅ Deleted {symbol} prediction')
        
        conn.commit()
        print(f'🎯 Successfully deleted {len(broken_preds)} broken predictions')
    else:
        print('✅ No broken predictions found to clean up')

    conn.close()

if __name__ == '__main__':
    cleanup_1230_predictions()
