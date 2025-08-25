#!/usr/bin/env python3
"""
Investigate new price errors in predictions
"""

import sqlite3
from datetime import datetime

def investigate_price_errors():
    print('🔍 INVESTIGATING NEW PRICE ERRORS')
    print('=' * 40)

    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    # Check recent predictions with zero prices
    cursor.execute('''
        SELECT symbol, prediction_timestamp, predicted_action, entry_price, action_confidence
        FROM predictions 
        WHERE entry_price = 0.0 
        AND DATE(prediction_timestamp) = ?
        ORDER BY prediction_timestamp DESC
        LIMIT 20
    ''', (today,))

    zero_price_preds = cursor.fetchall()

    print(f'📊 Found {len(zero_price_preds)} predictions with zero prices today:')
    for symbol, timestamp, action, price, conf in zero_price_preds:
        time_part = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
        print(f'   {symbol}: {action} @ ${price:.2f} (conf: {conf:.3f}) [{time_part}]')

    print()
    print('📈 Recent predictions with VALID prices:')
    cursor.execute('''
        SELECT symbol, prediction_timestamp, predicted_action, entry_price, action_confidence
        FROM predictions 
        WHERE entry_price > 0 
        AND DATE(prediction_timestamp) = ?
        ORDER BY prediction_timestamp DESC
        LIMIT 10
    ''', (today,))

    valid_preds = cursor.fetchall()
    for symbol, timestamp, action, price, conf in valid_preds:
        time_part = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
        print(f'   {symbol}: {action} @ ${price:.2f} (conf: {conf:.3f}) [{time_part}]')

    print()
    print('🕐 TIMELINE ANALYSIS:')
    print('-' * 20)

    cursor.execute('''
        SELECT substr(prediction_timestamp, 12, 8) as time_slot,
               COUNT(*) as total,
               SUM(CASE WHEN entry_price = 0 THEN 1 ELSE 0 END) as zero_prices,
               SUM(CASE WHEN entry_price > 0 THEN 1 ELSE 0 END) as valid_prices
        FROM predictions 
        WHERE DATE(prediction_timestamp) = ?
        GROUP BY time_slot
        ORDER BY time_slot DESC
    ''', (today,))

    timeline = cursor.fetchall()
    for time_slot, total, zero, valid in timeline:
        status = '❌' if zero > 0 else '✅'
        print(f'   {status} {time_slot}: {total} total ({zero} zero, {valid} valid)')

    print()
    print('🚨 ISSUE PATTERN:')
    print('-' * 17)
    if len(zero_price_preds) > 0:
        latest_failure = zero_price_preds[0][1]
        print(f'   Latest price failure: {latest_failure}')
        print(f'   This suggests the price fetching logic is failing intermittently')
        print(f'   Likely cause: Yahoo Finance API timeouts or rate limiting')
    
    conn.close()

if __name__ == '__main__':
    investigate_price_errors()
