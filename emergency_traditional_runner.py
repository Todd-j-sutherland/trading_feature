#!/usr/bin/env python3
"""
Emergency traditional signals runner - bypass ML entirely
"""

import sqlite3
import yfinance as yf
from datetime import datetime
import logging

def run_emergency_traditional_signals():
    """Run traditional signals to replace biased ML predictions"""
    
    print('🚨 EMERGENCY TRADITIONAL SIGNALS RUN')
    print('=' * 40)
    
    # Bank symbols
    banks = {
        'CBA.AX': 'Commonwealth Bank',
        'WBC.AX': 'Westpac Banking Corporation', 
        'ANZ.AX': 'Australia and New Zealand Banking Group',
        'NAB.AX': 'National Australia Bank'
    }
    
    db_path = "data/trading_predictions.db"
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    saved_count = 0
    
    for symbol, name in banks.items():
        try:
            print(f'\\n🏦 Analyzing {symbol} ({name})')
            
            # Get current price
            ticker = yf.Ticker(symbol)
            
            # Try multiple methods to get current price
            current_price = 0
            try:
                # Method 1: Recent history
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    print(f'   💰 Current price: ${current_price:.2f} (from history)')
            except:
                pass
            
            if current_price == 0:
                try:
                    # Method 2: Info
                    info = ticker.info
                    current_price = info.get('currentPrice', 0)
                    if current_price > 0:
                        print(f'   💰 Current price: ${current_price:.2f} (from info)')
                except:
                    pass
            
            if current_price == 0:
                print(f'   ❌ Could not get price for {symbol}')
                continue
            
            # Get technical data for traditional signals
            data = yf.download(symbol, period="30d", interval="1d", progress=False)
            
            if data.empty:
                print(f'   ❌ No historical data for {symbol}')
                continue
            
            # Calculate traditional indicators
            close_prices = data['Close']
            volume = data['Volume']
            
            # Simple RSI calculation
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
            
            # Moving averages
            sma_5 = close_prices.rolling(window=5).mean().iloc[-1]
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            
            # Price momentum
            price_change = ((current_price - close_prices.iloc[-6]) / close_prices.iloc[-6]) * 100 if len(close_prices) > 5 else 0
            
            # Volume analysis
            avg_volume = volume.rolling(window=10).mean().iloc[-1]
            volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0
            
            # Traditional trading rules (BALANCED for BUY/SELL/HOLD)
            action = "HOLD"  # Default
            confidence = 0.6
            reasoning = ""
            
            # BUY conditions (encourage BUY signals) - fix pandas Series comparison
            if (current_rsi < 35) and (float(sma_5) > float(sma_20)) and (volume_ratio > 1.2):
                action = "BUY"
                confidence = 0.75
                reasoning = f"Oversold RSI ({current_rsi:.1f}) + upward momentum + volume spike"
            elif (current_rsi < 40) and (price_change > 1.5):
                action = "BUY" 
                confidence = 0.7
                reasoning = f"Low RSI ({current_rsi:.1f}) + positive momentum ({price_change:.1f}%)"
            elif (current_rsi < 45) and (float(sma_5) > float(sma_20) * 1.01):
                action = "BUY"
                confidence = 0.65
                reasoning = f"Moderate RSI + clear upward trend"
            
            # SELL conditions (more conservative)
            elif (current_rsi > 70) and (float(sma_5) < float(sma_20)):
                action = "SELL"
                confidence = 0.75
                reasoning = f"Overbought RSI ({current_rsi:.1f}) + downward momentum"
            elif (current_rsi > 75):
                action = "SELL"
                confidence = 0.7
                reasoning = f"Very overbought RSI ({current_rsi:.1f})"
            
            # HOLD (default for neutral conditions)
            else:
                reasoning = f"Neutral conditions (RSI: {current_rsi:.1f}, Change: {price_change:.1f}%)"
            
            print(f'   📊 RSI: {current_rsi:.1f}, Price change: {price_change:.1f}%, Volume ratio: {volume_ratio:.1f}x')
            print(f'   🎯 Traditional signal: {action} (confidence: {confidence:.2f})')
            print(f'   💭 Reasoning: {reasoning}')
            
            # Save to database
            prediction_id = f"traditional_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            predicted_direction = 1 if action == "BUY" else (-1 if action == "SELL" else 0)
            magnitude = abs(price_change) / 100  # Convert to decimal
            
            cursor.execute("""
                INSERT OR REPLACE INTO predictions 
                (prediction_id, symbol, prediction_timestamp, predicted_action, 
                 action_confidence, predicted_direction, predicted_magnitude, 
                 model_version, entry_price, optimal_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id,
                symbol,
                timestamp,
                action,
                float(confidence),
                predicted_direction,
                float(magnitude),
                "traditional_emergency_v1",
                current_price,
                action
            ))
            
            saved_count += 1
            print(f'   ✅ Saved traditional prediction to database')
            
        except Exception as e:
            print(f'   ❌ Error processing {symbol}: {e}')
    
    conn.commit()
    conn.close()
    
    print(f'\\n🏁 EMERGENCY RUN COMPLETE!')
    print(f'✅ Saved {saved_count} traditional predictions')
    print(f'⏰ Timestamp: {timestamp}')
    
    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT predicted_action, COUNT(*) as count
        FROM predictions 
        WHERE model_version = 'traditional_emergency_v1'
        GROUP BY predicted_action
        ORDER BY count DESC
    """)
    
    traditional_results = cursor.fetchall()
    total_traditional = sum(count for _, count in traditional_results)
    
    print(f'\\n📊 TRADITIONAL SIGNALS DISTRIBUTION:')
    for action, count in traditional_results:
        percentage = (count / total_traditional) * 100 if total_traditional > 0 else 0
        print(f'   {action}: {count} predictions ({percentage:.1f}%)')
    
    conn.close()
    
    return saved_count

if __name__ == '__main__':
    run_emergency_traditional_signals()
