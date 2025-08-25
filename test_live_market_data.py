#!/usr/bin/env python3
"""
Test live market data collection during market hours
"""
import yfinance as yf
from datetime import datetime

def test_live_data():
    print("📈 LIVE MARKET DATA TEST")
    print("-" * 30)
    
    banks = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX"]
    
    for symbol in banks:
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current info
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # Get recent trading data
            hist_1d = ticker.history(period="1d", interval="1m")
            
            if not hist_1d.empty:
                latest_data = hist_1d.index[-1]
                latest_volume = hist_1d['Volume'].iloc[-1]
                latest_price = hist_1d['Close'].iloc[-1]
                
                # Calculate how fresh the data is
                from datetime import datetime
                import pytz
                
                australia_tz = pytz.timezone('Australia/Sydney')
                now_au = datetime.now(australia_tz)
                
                # Convert latest_data to Australia timezone
                latest_au = latest_data.tz_convert('Australia/Sydney')
                minutes_ago = (now_au - latest_au).total_seconds() / 60
                
                print(f"📊 {symbol}:")
                print(f"   Current Price: ${current_price:.2f}")
                print(f"   Latest Trade: ${latest_price:.2f}")
                print(f"   Volume: {latest_volume:,.0f}")
                print(f"   Data Age: {minutes_ago:.1f} minutes ago")
                
                if minutes_ago < 5:
                    print(f"   Status: 🟢 LIVE")
                elif minutes_ago < 15:
                    print(f"   Status: 🟡 RECENT")
                else:
                    print(f"   Status: 🔴 STALE")
            else:
                print(f"📊 {symbol}: ❌ No intraday data")
                
        except Exception as e:
            print(f"📊 {symbol}: ❌ Error - {e}")

if __name__ == "__main__":
    test_live_data()
