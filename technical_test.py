#!/usr/bin/env python3
import yfinance as yf
from datetime import datetime, timedelta

def test_technical():
    try:
        # Test getting data for CBA
        symbol = "CBA.AX"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if not hist.empty:
            prices = hist["Close"].tolist()
            print(f"✅ Got {len(prices)} prices for {symbol}")
            print(f"Latest price: ${prices[-1]:.2f}")
            
            # Simple RSI calculation
            if len(prices) >= 15:
                deltas = [prices[i] - prices[i-1] for i in range(1, 15)]
                gains = [d if d > 0 else 0 for d in deltas]
                losses = [-d if d < 0 else 0 for d in deltas]
                
                avg_gain = sum(gains) / len(gains)
                avg_loss = sum(losses) / len(losses)
                
                if avg_loss > 0:
                    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
                else:
                    rsi = 100
                    
                print(f"RSI: {rsi:.1f}")
            
            return True
        else:
            print("❌ No data received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_technical()
