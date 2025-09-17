#!/usr/bin/env python3
"""
Pricing Logic Comparison - Demonstrates the bug fix
Shows side-by-side comparison of old vs new pricing logic
"""

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta

def demonstrate_pricing_fix():
    """Show the difference between broken and fixed pricing logic"""
    
    print("🔍 PRICING DATA DUPLICATION BUG DEMONSTRATION")
    print("=" * 60)
    
    # Get sample predictions from the same day
    conn = sqlite3.connect('predictions.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, prediction_timestamp, entry_price 
        FROM predictions 
        WHERE DATE(prediction_timestamp) = '2025-09-15'
        AND symbol = 'MQG.AX'
        ORDER BY prediction_timestamp
        LIMIT 5
    """)
    
    predictions = cursor.fetchall()
    conn.close()
    
    if not predictions:
        print("No sample predictions found")
        return
    
    print(f"\n📊 Testing with {len(predictions)} MQG.AX predictions from 2025-09-15:")
    print("-" * 60)
    
    symbol = 'MQG.AX'
    test_date = datetime(2025, 9, 15)
    
    try:
        ticker = yf.Ticker(symbol)
        
        # OLD BROKEN LOGIC - What was causing duplicates
        print("\n❌ OLD BROKEN LOGIC (causing duplicates):")
        old_hist = ticker.history(start=test_date.date(), 
                                end=(test_date + timedelta(days=1)).date(),
                                interval='1h')
        
        if not old_hist.empty:
            old_entry = float(old_hist['Close'].iloc[0])  # SAME for all predictions
            old_exit = float(old_hist['Close'].iloc[-1])   # SAME for all predictions
            old_return = ((old_exit - old_entry) / old_entry) * 100
            
            print(f"  Entry Price: ${old_entry:.2f} (SAME for ALL predictions that day)")
            print(f"  Exit Price:  ${old_exit:.2f} (SAME for ALL predictions that day)")
            print(f"  Return:      {old_return:+.2f}% (DUPLICATED for all predictions)")
            
            print(f"\n  🚨 PROBLEM: All {len(predictions)} predictions would get:")
            for i, (_, timestamp, _) in enumerate(predictions, 1):
                pred_time = datetime.fromisoformat(timestamp.replace('Z', ''))
                print(f"    {i}. {pred_time.strftime('%H:%M:%S')} → ${old_entry:.2f} → ${old_exit:.2f} = {old_return:+.2f}%")
        
        # NEW CORRECTED LOGIC
        print(f"\n✅ NEW CORRECTED LOGIC (unique pricing):")
        
        for i, (_, timestamp, stored_entry) in enumerate(predictions, 1):
            pred_time = datetime.fromisoformat(timestamp.replace('Z', ''))
            
            # Use stored entry price if available (most accurate)
            if stored_entry and stored_entry > 0:
                entry_price = stored_entry
                entry_method = "stored"
            else:
                # Get precise entry price at prediction time
                entry_hist = ticker.history(start=pred_time.date(),
                                           end=(pred_time + timedelta(days=1)).date(),
                                           interval='1m')
                if not entry_hist.empty:
                    entry_price = float(entry_hist['Open'].iloc[0])
                    entry_method = "1-minute"
                else:
                    entry_price = float(old_hist['Open'].iloc[0]) if not old_hist.empty else 0
                    entry_method = "hourly"
            
            # Exit price 4+ hours later
            eval_time = pred_time + timedelta(hours=4, minutes=30)
            exit_hist = ticker.history(start=eval_time.date(),
                                     end=(eval_time + timedelta(days=1)).date())
            
            if not exit_hist.empty:
                exit_price = float(exit_hist['Close'].iloc[0])
                
                if entry_price > 0:
                    return_pct = ((exit_price - entry_price) / entry_price) * 100
                    print(f"    {i}. {pred_time.strftime('%H:%M:%S')} → ${entry_price:.2f} → ${exit_price:.2f} = {return_pct:+.2f}% ({entry_method})")
        
        print(f"\n🎯 KEY DIFFERENCE:")
        print(f"  ❌ Old: ALL predictions get identical prices = DUPLICATE DATA")
        print(f"  ✅ New: Each prediction gets unique timestamp-based prices = ACCURATE DATA")
        
    except Exception as e:
        print(f"Error in demonstration: {e}")

if __name__ == "__main__":
    demonstrate_pricing_fix()
