#!/usr/bin/env python3
"""
Fix predictions with zero entry prices
"""

import sqlite3
import yfinance as yf
from datetime import datetime

def fix_zero_prices():
    print('🔍 FIXING PREDICTIONS WITH ZERO PRICES')
    print('=' * 40)

    # Connect to database
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()

    # Get recent predictions with zero prices
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT prediction_id, symbol, prediction_timestamp 
        FROM predictions 
        WHERE entry_price = 0.0 
        AND DATE(prediction_timestamp) = ?
        ORDER BY prediction_timestamp DESC
    ''', (today,))

    zero_price_preds = cursor.fetchall()
    print(f'Found {len(zero_price_preds)} predictions with zero prices')

    fixed_count = 0

    for pred_id, symbol, timestamp in zero_price_preds:
        try:
            # Get current price using yfinance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            
            if current_price > 0:
                # Update the prediction with the correct price
                cursor.execute('''
                    UPDATE predictions 
                    SET entry_price = ? 
                    WHERE prediction_id = ?
                ''', (current_price, pred_id))
                
                print(f'✅ Fixed {symbol}: ${current_price:.2f}')
                fixed_count += 1
            else:
                print(f'❌ Still no price for {symbol}')
                
        except Exception as e:
            print(f'❌ Error fixing {symbol}: {e}')

    conn.commit()
    conn.close()

    print(f'🎯 Fixed {fixed_count} predictions with correct prices!')
    
    # Show sample of fixed predictions
    print()
    print('📊 SAMPLE OF FIXED PREDICTIONS:')
    print('-' * 30)
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT symbol, predicted_action, entry_price, action_confidence
        FROM predictions 
        WHERE entry_price > 0
        AND DATE(prediction_timestamp) = ?
        ORDER BY prediction_timestamp DESC
        LIMIT 10
    ''', (today,))
    
    fixed_preds = cursor.fetchall()
    for symbol, action, price, confidence in fixed_preds:
        print(f'   {symbol}: {action} @ ${price:.2f} (conf: {confidence:.3f})')
    
    conn.close()

if __name__ == '__main__':
    fix_zero_prices()
