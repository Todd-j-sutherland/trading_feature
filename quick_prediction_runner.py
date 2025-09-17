#!/usr/bin/env python3
"""
Quick Prediction Runner - Simple version for immediate results
"""

import sqlite3
import json
import uuid
from datetime import datetime
import yfinance as yf
import sys
import signal

# Set up timeout handler
def timeout_handler(signum, frame):
    print("❌ Script timed out!")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second timeout

def quick_prediction():
    """Generate quick predictions for ASX bank stocks"""
    print(f"🚀 Quick Prediction System: {datetime.now()}")
    
    # ASX bank symbols
    symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
    
    db_path = "/root/test/data/trading_predictions.db"
    
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        predictions_made = 0
        
        for symbol in symbols:
            try:
                print(f"📊 Processing {symbol}...")
                
                # Get current price
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d', interval='1h')
                
                if len(hist) < 2:
                    print(f"❌ No data for {symbol}")
                    continue
                
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                
                # Simple prediction logic
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                if price_change > 0.5:
                    action = 'BUY'
                    confidence = min(0.8, 0.5 + abs(price_change) / 10)
                elif price_change < -0.5:
                    action = 'SELL'
                    confidence = min(0.8, 0.5 + abs(price_change) / 10)
                else:
                    action = 'HOLD'
                    confidence = 0.7
                
                # Generate prediction ID
                timestamp = datetime.now().isoformat()
                prediction_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_quick"
                
                # Insert prediction
                cursor.execute("""
                    INSERT INTO predictions (
                        prediction_id, symbol, prediction_timestamp,
                        predicted_action, action_confidence, entry_price,
                        prediction_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_id,
                    symbol,
                    timestamp,
                    action,
                    confidence,
                    current_price,
                    json.dumps({
                        'price_change_pct': round(price_change, 2),
                        'method': 'quick_prediction',
                        'current_price': current_price,
                        'prev_price': prev_price
                    })
                ))
                
                predictions_made += 1
                print(f"✅ {symbol}: {action} (conf: {confidence:.2f}, price: ${current_price:.2f})")
                
            except Exception as e:
                print(f"❌ Error with {symbol}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"🎯 Generated {predictions_made} quick predictions!")
        return predictions_made
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return 0

if __name__ == "__main__":
    try:
        count = quick_prediction()
        print(f"✅ Quick prediction complete: {count} predictions made")
    except Exception as e:
        print(f"❌ Script failed: {e}")
    finally:
        signal.alarm(0)  # Cancel alarm
