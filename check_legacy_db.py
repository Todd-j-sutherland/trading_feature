#!/usr/bin/env python3
"""
Check legacy predictions.db for July data
"""

import sqlite3
import os

def check_legacy_db():
    print('🔍 CHECKING LEGACY DATABASE FILES')
    print('=' * 40)

    # Check the main predictions.db file
    if os.path.exists('predictions.db'):
        print('📊 Checking predictions.db:')
        try:
            conn = sqlite3.connect('predictions.db')
            cursor = conn.cursor()
            
            # Check table structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f'   Tables: {tables}')
            
            if 'predictions' in tables:
                cursor.execute('SELECT MIN(DATE(prediction_timestamp)), MAX(DATE(prediction_timestamp)), COUNT(*) FROM predictions')
                result = cursor.fetchone()
                print(f'   Date range: {result[0]} to {result[1]} ({result[2]} total)')
                
                # Check for July 24th specifically
                cursor.execute("SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = '2025-07-24'")
                july_count = cursor.fetchone()[0]
                print(f'   July 24th predictions: {july_count}')
                
                if july_count > 0:
                    print('   🎯 FOUND THE JULY 24TH DATA!')
                    cursor.execute("SELECT symbol, prediction_timestamp, predicted_action, entry_price FROM predictions WHERE DATE(prediction_timestamp) = '2025-07-24' LIMIT 10")
                    july_preds = cursor.fetchall()
                    for symbol, timestamp, action, price in july_preds:
                        print(f'      {symbol}: {action} @ ${price:.2f} [{timestamp}]')
                
                # Show recent data too
                print('   📅 Recent predictions:')
                cursor.execute("SELECT DATE(prediction_timestamp), COUNT(*) FROM predictions GROUP BY DATE(prediction_timestamp) ORDER BY DATE(prediction_timestamp) DESC LIMIT 5")
                recent = cursor.fetchall()
                for date, count in recent:
                    print(f'      {date}: {count} predictions')
            
            conn.close()
        except Exception as e:
            print(f'   Error: {e}')
    else:
        print('   predictions.db not found')

    print()
    print('📂 SUMMARY:')
    print('-' * 12)
    print('   data/trading_predictions.db: Current active database (Aug 12-21)')
    print('   predictions.db: Legacy database (may contain July data)')

if __name__ == '__main__':
    check_legacy_db()
