#!/usr/bin/env python3
"""
Simple emergency traditional signals runner
"""

import sqlite3
import yfinance as yf
from datetime import datetime

def run_simple_emergency_signals():
    """Run simple traditional signals"""
    
    print('🚨 SIMPLE EMERGENCY TRADITIONAL SIGNALS')
    print('=' * 42)
    
    banks = {
        'CBA.AX': 'Commonwealth Bank',
        'WBC.AX': 'Westpac Banking Corporation', 
        'ANZ.AX': 'Australia and New Zealand Banking Group',
        'NAB.AX': 'National Australia Bank'
    }
    
    conn = sqlite3.connect("data/trading_predictions.db")
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    saved_count = 0
    
    for symbol, name in banks.items():
        try:
            print(f'\\n🏦 {symbol} ({name})')
            
            # Get current price - simple method
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            
            if hist.empty:
                print(f'   ❌ No data for {symbol}')
                continue
                
            current_price = float(hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
            
            # Simple price momentum
            price_change_pct = ((current_price - prev_price) / prev_price) * 100
            
            print(f'   💰 Price: ${current_price:.2f} (change: {price_change_pct:+.1f}%)')
            
            # Very simple traditional rules
            action = "HOLD"  # Default
            confidence = 0.6
            
            # Simple BUY/SELL logic based on momentum and price level
            if price_change_pct > 2.0:  # Strong positive momentum
                action = "BUY"
                confidence = 0.7
                reasoning = f"Strong positive momentum ({price_change_pct:+.1f}%)"
            elif price_change_pct < -2.0:  # Strong negative momentum  
                action = "SELL"
                confidence = 0.7
                reasoning = f"Strong negative momentum ({price_change_pct:+.1f}%)"
            elif price_change_pct > 0.5:  # Moderate positive
                action = "BUY"
                confidence = 0.65
                reasoning = f"Moderate positive momentum ({price_change_pct:+.1f}%)"
            else:
                reasoning = f"Neutral momentum ({price_change_pct:+.1f}%)"
            
            print(f'   🎯 Signal: {action} (conf: {confidence:.2f})')
            print(f'   💭 {reasoning}')
            
            # Save to database
            prediction_id = f"simple_emergency_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            predicted_direction = 1 if action == "BUY" else (-1 if action == "SELL" else 0)
            magnitude = abs(price_change_pct) / 100
            
            cursor.execute("""
                INSERT INTO predictions 
                (prediction_id, symbol, prediction_timestamp, predicted_action, 
                 action_confidence, predicted_direction, predicted_magnitude, 
                 model_version, entry_price, optimal_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id, symbol, timestamp, action,
                float(confidence), predicted_direction, float(magnitude),
                "simple_emergency_v1", current_price, action
            ))
            
            saved_count += 1
            print(f'   ✅ Saved to database')
            
        except Exception as e:
            print(f'   ❌ Error: {e}')
    
    conn.commit()
    conn.close()
    
    print(f'\\n🏁 EMERGENCY RUN COMPLETE: {saved_count} predictions saved')
    
    # Show results
    conn = sqlite3.connect("data/trading_predictions.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT predicted_action, COUNT(*) as count
        FROM predictions 
        WHERE model_version = 'simple_emergency_v1'
        GROUP BY predicted_action
    """)
    
    results = cursor.fetchall()
    total = sum(count for _, count in results)
    
    print(f'\\n📊 EMERGENCY SIGNALS DISTRIBUTION:')
    for action, count in results:
        pct = (count / total) * 100 if total > 0 else 0
        print(f'   {action}: {count} ({pct:.1f}%)')
    
    conn.close()

if __name__ == '__main__':
    run_simple_emergency_signals()
