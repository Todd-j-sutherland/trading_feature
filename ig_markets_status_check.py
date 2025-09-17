#!/usr/bin/env python3
"""
IG Markets Integration Status Checker
Diagnose why IG Markets isn't working and confirm yfinance fallback
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

def check_ig_markets_status():
    """Check IG Markets integration status"""
    print("🔍 IG MARKETS INTEGRATION STATUS CHECK")
    print("=" * 60)
    
    # 1. Check environment variables
    print("\n🔐 ENVIRONMENT VARIABLES:")
    env_vars = ['IG_USERNAME', 'IG_PASSWORD', 'IG_API_KEY', 'IG_DEMO', 'IG_DISABLE']
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var in ['IG_PASSWORD', 'IG_API_KEY']:
                print(f"  ✅ {var}: {'*' * min(len(value), 8)}...")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # 2. Check .env file
    print(f"\n📄 .ENV FILE CHECK:")
    env_paths = ['.env', '../.env', '/root/test/.env']
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"  ✅ {env_path} exists")
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                    if 'IG_USERNAME' in content:
                        print(f"      Contains IG credentials")
                    else:
                        print(f"      No IG credentials found")
            except Exception as e:
                print(f"      Error reading: {e}")
        else:
            print(f"  ❌ {env_path} not found")
    
    # 3. Check IG Markets components
    print(f"\n🧩 IG MARKETS COMPONENTS:")
    components = [
        'real_time_price_fetcher.py',
        '../real_time_price_fetcher.py',
        '/root/test/real_time_price_fetcher.py',
        'ig_markets_asx_mapper.py',
        '../ig_markets_asx_mapper.py', 
        '/root/test/ig_markets_asx_mapper.py'
    ]
    
    ig_components_found = 0
    for component in components:
        if os.path.exists(component):
            print(f"  ✅ {component}")
            ig_components_found += 1
        else:
            print(f"  ❌ {component} not found")
    
    # 4. Test IG Markets imports
    print(f"\n📦 IMPORT TESTS:")
    
    try:
        from real_time_price_fetcher import RealTimePriceFetcher
        print("  ✅ RealTimePriceFetcher import successful")
        ig_available = True
    except ImportError as e:
        print(f"  ❌ RealTimePriceFetcher import failed: {e}")
        ig_available = False
    
    try:
        from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
        print("  ✅ EnhancedMarketDataCollector import successful")
    except ImportError as e:
        print(f"  ❌ EnhancedMarketDataCollector import failed: {e}")
    
    try:
        import yfinance as yf
        print("  ✅ yfinance import successful")
        yf_available = True
    except ImportError as e:
        print(f"  ❌ yfinance import failed: {e}")
        yf_available = False
    
    # 5. Test actual data fetching
    print(f"\n💰 PRICE FETCHING TEST:")
    
    if ig_available:
        try:
            fetcher = RealTimePriceFetcher()
            result = fetcher.get_current_price('MQG.AX')
            if result:
                price, source, delay = result
                print(f"  🎯 IG Markets test: ${price:.2f} from {source} (delay: {delay}min)")
                if 'yfinance' in source.lower():
                    print(f"      ⚠️ IG MARKETS FALLBACK TO YFINANCE DETECTED!")
                else:
                    print(f"      ✅ IG Markets working properly")
            else:
                print(f"  ❌ IG Markets test failed - no data returned")
        except Exception as e:
            print(f"  ❌ IG Markets test error: {e}")
    
    if yf_available:
        try:
            import yfinance as yf
            ticker = yf.Ticker('MQG.AX')
            info = ticker.info
            price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            print(f"  📊 yfinance test: ${price:.2f}")
            
            # Test 1-minute data
            data_1m = ticker.history(period="1d", interval="1m")
            if not data_1m.empty:
                recent_price = data_1m['Close'].iloc[-1]
                timestamp = data_1m.index[-1]
                print(f"      1-min data: ${recent_price:.2f} at {timestamp}")
                
                # Calculate delay
                now = pd.Timestamp.now(tz=timestamp.tz)
                delay_minutes = (now - timestamp).total_seconds() / 60
                print(f"      Data delay: {delay_minutes:.1f} minutes")
                
                if delay_minutes > 30:
                    print(f"      ⚠️ SIGNIFICANT DELAY - This explains the $1 difference!")
                
        except Exception as e:
            print(f"  ❌ yfinance test error: {e}")
    
    # 6. Check configuration
    print(f"\n⚙️ CONFIGURATION CHECK:")
    
    try:
        from config import IG_MARKETS_CONFIG, TRADING_CONFIG
        print(f"  ✅ Config imports successful")
        print(f"      IG_MARKETS_CONFIG enabled: {IG_MARKETS_CONFIG.get('enabled', False)}")
        print(f"      TRADING_CONFIG use_ig_markets: {TRADING_CONFIG.get('use_ig_markets', False)}")
    except ImportError as e:
        print(f"  ❌ Config import failed: {e}")
    except Exception as e:
        print(f"  ❌ Config error: {e}")
    
    # 7. Check database for source tracking
    print(f"\n💾 DATABASE SOURCE TRACKING:")
    
    db_paths = ["data/trading_predictions.db", "trading_predictions.db"]
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                
                # Check if source tracking exists
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(predictions)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'data_source' in columns:
                    print(f"  ✅ {db_path} has data_source column")
                    
                    # Check recent sources
                    cursor.execute("SELECT data_source, COUNT(*) FROM predictions WHERE symbol = 'MQG.AX' AND timestamp > datetime('now', '-24 hours') GROUP BY data_source")
                    sources = cursor.fetchall()
                    
                    if sources:
                        print(f"      Recent MQG.AX data sources:")
                        for source, count in sources:
                            print(f"        {source}: {count} predictions")
                    else:
                        print(f"      No recent MQG.AX predictions with source info")
                else:
                    print(f"  ❌ {db_path} missing data_source column")
                
                conn.close()
            except Exception as e:
                print(f"  ❌ Database error: {e}")
        else:
            print(f"  ❌ {db_path} not found")
    
    # 8. Summary and recommendations
    print(f"\n📋 DIAGNOSIS SUMMARY:")
    
    if not ig_available:
        print(f"  🔴 IG Markets integration is NOT working")
        print(f"     Reason: Missing components or import failures")
        print(f"     Solution: Install IG Markets components and credentials")
    elif ig_components_found == 0:
        print(f"  🔴 IG Markets components are missing")
        print(f"     Solution: Copy IG Markets files to correct locations")
    elif not os.getenv('IG_USERNAME'):
        print(f"  🔴 IG Markets credentials not configured")
        print(f"     Solution: Set IG_USERNAME, IG_PASSWORD, IG_API_KEY")
    else:
        print(f"  🟡 IG Markets may be configured but falling back to yfinance")
        print(f"     Solution: Check API credentials and network connectivity")
    
    print(f"\n  🔵 yfinance fallback is {'working' if yf_available else 'NOT working'}")
    if yf_available:
        print(f"     This explains the ~$1 MQG.AX price discrepancy")
        print(f"     yfinance has 15-20 minute delays on ASX data")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"1. Fix IG Markets integration for real-time prices")
    print(f"2. Add data source logging to track price sources") 
    print(f"3. Monitor yfinance delay vs live chart timing")
    print(f"4. Consider enabling IG Markets demo account")

if __name__ == "__main__":
    check_ig_markets_status()
