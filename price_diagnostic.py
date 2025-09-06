#!/usr/bin/env python3
"""
Price Data Diagnostic Script
Check where the incorrect entry prices are coming from
"""

import sys
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta

sys.path.insert(0, '/root/test')

def check_current_prices():
    """Check current market prices vs stored entry prices"""
    
    symbols = ['CSL.AX', 'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
    
    print("🔍 PRICE DIAGNOSTIC REPORT")
    print("=" * 60)
    
    # Get current market prices
    print("\n📈 Current Market Prices (yfinance):")
    current_prices = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d', interval='1h')
            if len(hist) > 0:
                current_price = round(float(hist['Close'].iloc[-1]), 2)
                current_prices[symbol] = current_price
                print(f"   {symbol}: ${current_price}")
            else:
                print(f"   {symbol}: No data")
        except Exception as e:
            print(f"   {symbol}: Error - {e}")
    
    # Check stored entry prices in predictions
    print("\n💾 Recent Entry Prices in Database:")
    conn = sqlite3.connect('/root/test/data/trading_predictions.db')
    cursor = conn.cursor()
    
    for symbol in symbols:
        cursor.execute("""
            SELECT prediction_id, entry_price, prediction_timestamp 
            FROM predictions 
            WHERE symbol = ? 
            ORDER BY prediction_timestamp DESC 
            LIMIT 3
        """, (symbol,))
        
        results = cursor.fetchall()
        print(f"\n   {symbol}:")
        for pred_id, entry_price, timestamp in results:
            current_market = current_prices.get(symbol, 0)
            diff = abs(current_market - entry_price) if current_market > 0 else 0
            diff_pct = (diff / current_market * 100) if current_market > 0 else 0
            
            status = "✅ GOOD" if diff_pct < 5 else "❌ BAD"
            print(f"     {timestamp}: ${entry_price} vs ${current_market} ({diff_pct:.1f}% diff) {status}")
    
    # Check problematic outcomes
    print("\n🚨 Problematic Outcomes (unrealistic returns):")
    cursor.execute("""
        SELECT o.prediction_id, o.entry_price, o.exit_price, o.actual_return,
               p.symbol, p.prediction_timestamp
        FROM outcomes o
        JOIN predictions p ON o.prediction_id = p.prediction_id
        WHERE o.actual_return > 100 OR o.actual_return < -90
        ORDER BY o.actual_return DESC
        LIMIT 10
    """)
    
    problematic = cursor.fetchall()
    for pred_id, entry, exit, ret, symbol, timestamp in problematic:
        current_market = current_prices.get(symbol, 0)
        print(f"   {symbol}: Entry=${entry}, Exit=${exit}, Return={ret:.1f}%, Market=${current_market}")
        print(f"     Prediction: {timestamp}")
        
        # Calculate what return should be if entry price was correct
        if current_market > 0:
            correct_return = ((exit - current_market) / current_market) * 100
            print(f"     Correct return if entry=${current_market}: {correct_return:.2f}%")
        print()
    
    conn.close()
    
    print("\n📊 SUMMARY:")
    print("- Entry prices in predictions table are often incorrect")
    print("- This causes unrealistic returns in outcomes table")
    print("- Need to fix the price fetching in prediction generation")

if __name__ == "__main__":
    check_current_prices()
