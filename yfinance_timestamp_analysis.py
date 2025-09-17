#!/usr/bin/env python3
"""
yfinance Timestamp Analysis for MQG.AX
Check exact timestamps and calculate real delay
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def analyze_yfinance_timestamps():
    """Analyze yfinance timestamps to determine exact delay"""
    print("🕐 YFINANCE TIMESTAMP ANALYSIS FOR MQG.AX")
    print("=" * 60)
    
    symbol = 'MQG.AX'
    
    # Get current time in different timezones
    utc_now = datetime.now(pytz.UTC)
    sydney_tz = pytz.timezone('Australia/Sydney')
    sydney_now = utc_now.astimezone(sydney_tz)
    
    print(f"Current time (Sydney): {sydney_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Current time (UTC): {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Check if market is open (ASX: 10:00-16:00 Sydney time, Mon-Fri)
    market_open = sydney_now.replace(hour=10, minute=0, second=0, microsecond=0)
    market_close = sydney_now.replace(hour=16, minute=0, second=0, microsecond=0)
    is_trading_day = sydney_now.weekday() < 5  # Monday = 0, Friday = 4
    is_market_hours = market_open <= sydney_now <= market_close and is_trading_day
    
    print(f"ASX Market Status: {'🟢 OPEN' if is_market_hours else '🔴 CLOSED'}")
    print(f"Next market open: {market_open if sydney_now < market_open else market_open + timedelta(days=1)}")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. Check ticker.info timestamps
        print(f"\n📊 TICKER.INFO ANALYSIS:")
        info = ticker.info
        
        # Look for timestamp fields
        timestamp_fields = ['regularMarketTime', 'postMarketTime', 'preMarketTime', 'quoteTimeInLong']
        
        for field in timestamp_fields:
            if field in info and info[field]:
                if isinstance(info[field], (int, float)):
                    # Convert Unix timestamp
                    timestamp = datetime.fromtimestamp(info[field], tz=pytz.UTC)
                    sydney_time = timestamp.astimezone(sydney_tz)
                    delay = (utc_now - timestamp).total_seconds() / 60
                    
                    print(f"  {field}:")
                    print(f"    Time: {sydney_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print(f"    Delay: {delay:.1f} minutes")
                    
                    if delay > 60:
                        print(f"    ⚠️ Data is over 1 hour old!")
                    elif delay > 20:
                        print(f"    ⚠️ Significant delay detected")
                else:
                    print(f"  {field}: {info[field]} (non-timestamp format)")
        
        # Current/regular market price info
        current_price = info.get('currentPrice')
        regular_price = info.get('regularMarketPrice')
        previous_close = info.get('previousClose')
        
        print(f"\n💰 PRICE DATA FROM INFO:")
        if current_price:
            print(f"  Current Price: ${current_price:.2f}")
        if regular_price:
            print(f"  Regular Market Price: ${regular_price:.2f}")
        if previous_close:
            print(f"  Previous Close: ${previous_close:.2f}")
        
        # 2. Check 1-minute historical data
        print(f"\n📈 1-MINUTE DATA ANALYSIS:")
        
        # Try different periods to see data availability
        periods = ['1d', '2d', '5d']
        
        for period in periods:
            try:
                data_1m = ticker.history(period=period, interval="1m")
                
                if not data_1m.empty:
                    latest_time = data_1m.index[-1]
                    latest_price = data_1m['Close'].iloc[-1]
                    latest_volume = data_1m['Volume'].iloc[-1] if 'Volume' in data_1m.columns else 0
                    
                    # Convert to Sydney time if needed
                    if latest_time.tz is None:
                        latest_time = latest_time.tz_localize('UTC')
                    
                    sydney_latest = latest_time.astimezone(sydney_tz)
                    delay = (utc_now - latest_time).total_seconds() / 60
                    
                    print(f"\n  Period: {period}")
                    print(f"    Latest timestamp: {sydney_latest.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print(f"    Latest price: ${latest_price:.2f}")
                    print(f"    Volume: {latest_volume:,.0f}")
                    print(f"    Data points: {len(data_1m)}")
                    print(f"    Delay: {delay:.1f} minutes")
                    
                    # Determine if it's today's data or last trading day
                    data_date = sydney_latest.date()
                    today_date = sydney_now.date()
                    
                    if data_date == today_date:
                        print(f"    📅 Data is from TODAY")
                        if is_market_hours and delay > 5:
                            print(f"    ⚠️ Market is open but data is {delay:.1f} min delayed")
                        elif not is_market_hours:
                            print(f"    ℹ️ Market is closed - last trade was today")
                    else:
                        days_old = (today_date - data_date).days
                        print(f"    📅 Data is from {days_old} day(s) ago ({data_date})")
                        print(f"    ⚠️ Using LAST TRADING DAY data!")
                    
                    # Check if this looks like real-time vs delayed
                    if delay < 5:
                        print(f"    ✅ Appears to be real-time data")
                    elif delay < 30:
                        print(f"    🟡 Short delay - normal for free data")
                    else:
                        print(f"    🔴 SIGNIFICANT DELAY - explains price discrepancy!")
                    
                    break  # Use first successful period
                else:
                    print(f"  Period {period}: No data available")
                    
            except Exception as e:
                print(f"  Period {period}: Error - {e}")
        
        # 3. Check daily data for comparison
        print(f"\n📊 DAILY DATA COMPARISON:")
        
        try:
            daily_data = ticker.history(period="5d", interval="1d")
            
            if not daily_data.empty:
                latest_daily = daily_data.index[-1]
                latest_daily_price = daily_data['Close'].iloc[-1]
                
                if latest_daily.tz is None:
                    latest_daily = latest_daily.tz_localize('UTC')
                
                sydney_daily = latest_daily.astimezone(sydney_tz)
                
                print(f"  Latest daily close: ${latest_daily_price:.2f}")
                print(f"  Daily timestamp: {sydney_daily.strftime('%Y-%m-%d %Z')}")
                
                # Compare with 1-minute data
                if 'latest_price' in locals():
                    price_diff = abs(latest_price - latest_daily_price)
                    print(f"  Difference (1m vs daily): ${price_diff:.2f}")
                    
                    if price_diff > 0.50:
                        print(f"  ⚠️ Significant difference - 1m data may be more current")
        
        except Exception as e:
            print(f"  Daily data error: {e}")
        
        # 4. Summary analysis
        print(f"\n📋 TIMESTAMP ANALYSIS SUMMARY:")
        
        if 'delay' in locals():
            if delay > 60:
                print(f"🔴 yfinance data is {delay:.1f} minutes old (>{delay/60:.1f} hours)")
                print(f"   This is definitely STALE data explaining the $1 difference")
            elif delay > 20:
                print(f"🟡 yfinance data is {delay:.1f} minutes old")
                print(f"   Moderate delay - could explain price discrepancy")
            elif delay > 5:
                print(f"🟢 yfinance data is {delay:.1f} minutes old")
                print(f"   Normal delay for free data source")
            else:
                print(f"✅ yfinance data appears current ({delay:.1f} min delay)")
        
        # Market context
        if not is_trading_day:
            print(f"ℹ️ Market is closed (weekend) - using last trading day data is normal")
        elif not is_market_hours:
            print(f"ℹ️ Market is closed today - after hours or pre-market")
        else:
            print(f"⚠️ Market is currently OPEN - any significant delay is problematic")
            
    except Exception as e:
        print(f"❌ Error analyzing yfinance data: {e}")

if __name__ == "__main__":
    analyze_yfinance_timestamps()
