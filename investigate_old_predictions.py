#!/usr/bin/env python3
"""
Investigate old predictions in the database
"""

import sqlite3
from datetime import datetime, timedelta

def investigate_old_predictions():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()

    print('🔍 INVESTIGATING OLD PREDICTIONS')
    print('=' * 40)

    # Check the date range of all predictions
    cursor.execute('SELECT MIN(DATE(prediction_timestamp)), MAX(DATE(prediction_timestamp)), COUNT(*) FROM predictions')
    date_range = cursor.fetchone()
    print(f'📅 Prediction date range: {date_range[0]} to {date_range[1]} ({date_range[2]} total)')

    print()
    print('📊 PREDICTIONS BY DATE:')
    print('-' * 25)

    cursor.execute('''
        SELECT DATE(prediction_timestamp) as pred_date, COUNT(*) as count
        FROM predictions 
        GROUP BY DATE(prediction_timestamp)
        ORDER BY pred_date DESC
        LIMIT 10
    ''')

    date_counts = cursor.fetchall()
    for date, count in date_counts:
        print(f'   {date}: {count} predictions')

    print()
    print('🗓️  JULY 24TH PREDICTIONS DETAILS:')
    print('-' * 35)

    cursor.execute('''
        SELECT symbol, prediction_timestamp, predicted_action, action_confidence, entry_price
        FROM predictions 
        WHERE DATE(prediction_timestamp) = '2025-07-24'
        ORDER BY prediction_timestamp DESC
        LIMIT 15
    ''')

    july_preds = cursor.fetchall()
    print(f'Found {len(july_preds)} predictions from July 24th:')
    for symbol, timestamp, action, conf, price in july_preds:
        if ' ' in timestamp:
            time_part = timestamp.split(' ')[1]
        else:
            time_part = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
        print(f'   {symbol}: {action} @ ${price:.2f} (conf: {conf:.3f}) [{time_part}]')

    print()
    print('⚠️  ANALYSIS:')
    print('-' * 12)

    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = ?', (today,))
    today_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) != ?', (today,))
    old_count = cursor.fetchone()[0]

    print(f'✅ Today ({today}): {today_count} predictions')
    print(f'❌ Old dates: {old_count} predictions')

    if old_count > 0:
        print()
        print('🚨 RECOMMENDATION: Clean up old predictions!')
        print('   These July predictions should probably be deleted.')
        
        print()
        print('🗑️  CLEANUP OPTIONS:')
        print('   1. Delete all predictions older than 7 days')
        print('   2. Delete all predictions older than 30 days') 
        print('   3. Keep only today\'s predictions')

    conn.close()

if __name__ == '__main__':
    investigate_old_predictions()
