#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/trading_predictions.db')
cursor = conn.cursor()

today = datetime.now().strftime('%Y-%m-%d')

print('🔍 PREDICTION PRICE STATUS VERIFICATION')
print('=' * 42)

# Check predictions with zero prices
cursor.execute('SELECT COUNT(*) FROM predictions WHERE entry_price = 0.0 AND DATE(prediction_timestamp) = ?', (today,))
zero_count = cursor.fetchone()[0]

# Check predictions with valid prices  
cursor.execute('SELECT COUNT(*) FROM predictions WHERE entry_price > 0 AND DATE(prediction_timestamp) = ?', (today,))
valid_count = cursor.fetchone()[0]

print(f'❌ Predictions with zero prices: {zero_count}')
print(f'✅ Predictions with valid prices: {valid_count}')

# Show recent predictions
print()
print('📊 RECENT PREDICTIONS WITH PRICES:')
print('-' * 35)

cursor.execute('''
    SELECT symbol, predicted_action, entry_price, action_confidence, prediction_timestamp
    FROM predictions 
    WHERE DATE(prediction_timestamp) = ?
    ORDER BY prediction_timestamp DESC
    LIMIT 10
''', (today,))

for symbol, action, price, conf, timestamp in cursor.fetchall():
    price_status = '✅' if price > 0 else '❌'
    time_str = timestamp.split('T')[1][:8]  # Just HH:MM:SS
    print(f'   {price_status} {symbol}: {action} @ ${price:.2f} ({time_str})')

conn.close()
