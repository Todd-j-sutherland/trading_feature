#!/usr/bin/env python3
"""
Demonstration of Volume Data Availability Issues When Running in Evening
Shows how market hours detection affects volume data availability
"""

import pytz
from datetime import datetime
import yfinance as yf

def get_australian_time():
    """Get current time in Australian timezone (AEST/AEDT)"""
    try:
        australian_tz = pytz.timezone('Australia/Sydney')
        return datetime.now(australian_tz)
    except:
        return datetime.now()

def is_market_hours() -> bool:
    """Check if during ASX market hours (10 AM - 4 PM AEST)"""
    now = get_australian_time()
    if now.weekday() >= 5:  # Weekend
        return False
    return 10 <= now.hour < 16

def check_volume_data_availability():
    """Check if volume data is available when running in evening"""
    
    print("🕐 EVENING VOLUME DATA AVAILABILITY CHECK")
    print("=" * 60)
    
    # Current time info
    now = get_australian_time()
    print(f"📅 Current Australian Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"📊 Market Hours Status: {'✅ OPEN' if is_market_hours() else '❌ CLOSED'}")
    print(f"🌙 Running in Evening: {'✅ YES' if now.hour >= 16 or now.hour < 10 else '❌ NO'}")
    
    print(f"\n🏦 TESTING VOLUME DATA FOR ASX BANKS:")
    print("-" * 40)
    
    banks = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX"]
    
    for symbol in banks:
        print(f"\n📊 {symbol}:")
        
        try:
            # Test current price availability (what the analyzer tries to get)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            
            # Test recent trading data
            hist_1d = ticker.history(period="1d", interval="1m")
            hist_recent = ticker.history(period="5d", interval="1h") 
            
            print(f"   💰 Current Price: ${current_price:.2f}")
            print(f"   📈 Today's Data Points: {len(hist_1d)}")
            print(f"   📊 Recent 5-day Data: {len(hist_recent)} hours")
            
            if not hist_1d.empty:
                latest_data = hist_1d.index[-1]
                latest_volume = hist_1d['Volume'].iloc[-1]
                hours_old = (datetime.now(pytz.timezone('Australia/Sydney')) - latest_data.tz_convert('Australia/Sydney')).total_seconds() / 3600
                
                print(f"   🕐 Latest Data: {latest_data.strftime('%H:%M')} ({hours_old:.1f} hours ago)")
                print(f"   📊 Latest Volume: {latest_volume:,.0f}")
                
                # Check if volume data is "stale" 
                if hours_old > 8:  # More than 8 hours old
                    print(f"   ⚠️  STALE DATA: Volume is {hours_old:.1f} hours old!")
                else:
                    print(f"   ✅ FRESH DATA: Volume is recent")
                    
            else:
                print(f"   ❌ NO INTRADAY DATA AVAILABLE")
                
            # Evening-specific analysis
            if not is_market_hours():
                print(f"   🌙 EVENING ISSUE: Market closed, volume data reflects last trading session")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n🔍 VOLUME ASSESSMENT IMPLICATIONS:")
    print("-" * 40)
    
    if is_market_hours():
        print("✅ DURING MARKET HOURS:")
        print("   - Volume data is live and current")
        print("   - has_volume_data = True makes sense") 
        print("   - Volume quality assessment works as designed")
    else:
        print("❌ OUTSIDE MARKET HOURS (EVENING):")
        print("   - Volume data reflects previous trading session")
        print("   - Data may be 1-16 hours old depending on timing")
        print("   - has_volume_data logic may be inappropriate")
        print("   - Volume quality assessment may be misleading")
    
    print(f"\n💡 RECOMMENDATIONS FOR EVENING RUNS:")
    print("-" * 40)
    print("1. 📊 Adjust volume assessment logic for market hours")
    print("2. 🕐 Use different thresholds for stale vs fresh data")
    print("3. 🌙 Consider 'end-of-day volume summary' instead of 'live volume'")
    print("4. ⚖️  Reduce volume weight in quality score when market closed")
    print("5. 📈 Focus more on daily/weekly volume patterns vs intraday")

if __name__ == "__main__":
    check_volume_data_availability()
