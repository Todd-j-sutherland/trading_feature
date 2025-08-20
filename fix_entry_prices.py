#!/usr/bin/env python3
"""
Fix entry prices in predictions table
"""

import sqlite3
import yfinance as yf

def fix_entry_prices():
    """Update predictions with zero entry prices using current market data"""
    
    # Connect to database
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get predictions with zero entry prices
    cursor.execute('SELECT DISTINCT symbol FROM predictions WHERE entry_price = 0.0')
    symbols = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(symbols)} symbols with zero entry prices: {symbols}")
    
    updated_count = 0
    for symbol in symbols:
        try:
            # Get current price
            print(f"Getting price for {symbol}...")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            if current_price and current_price > 0:
                # Update all predictions for this symbol with zero entry price
                cursor.execute('''
                    UPDATE predictions 
                    SET entry_price = ? 
                    WHERE symbol = ? AND entry_price = 0.0
                ''', (float(current_price), symbol))
                
                rows_updated = cursor.rowcount
                updated_count += rows_updated
                print(f'✅ Updated {rows_updated} predictions for {symbol} with price ${current_price:.2f}')
            else:
                print(f'❌ Could not get valid price for {symbol}')
                
        except Exception as e:
            print(f'❌ Error updating {symbol}: {e}')
    
    conn.commit()
    conn.close()
    print(f'\n🎉 Total predictions updated: {updated_count}')

if __name__ == '__main__':
    fix_entry_prices()
