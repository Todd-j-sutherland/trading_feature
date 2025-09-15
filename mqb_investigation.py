#!/usr/bin/env python3
"""
MQG.AX Investigation Script  
Investigate MQG.AX (Macquarie Group) prediction accuracy and price data sources
Focus: Confirm if IG Markets is working or system is using yfinance fallback
"""

import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
import os

def check_data_source_tracking():
    """Check if the system is tracking data sources and what it's using"""
    print("📊 DATA SOURCE TRACKING ANALYSIS")
    print("=" * 50)
    
    db_path = "data/trading_predictions.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            # Check table schema for source tracking
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(predictions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            print(f"Available columns: {', '.join(columns)}")
            
            # Look for source-related columns
            source_columns = [col for col in columns if 'source' in col.lower() or 'provider' in col.lower()]
            if source_columns:
                print(f"🎯 Data source columns found: {', '.join(source_columns)}")
                
                # Check recent MQG.AX predictions for source info
                for col in source_columns:
                    query = f"""
                    SELECT {col}, COUNT(*) as count, MAX(timestamp) as latest
                    FROM predictions 
                    WHERE symbol = 'MQG.AX' 
                    AND timestamp > datetime('now', '-48 hours')
                    AND {col} IS NOT NULL
                    GROUP BY {col}
                    ORDER BY count DESC
                    """
                    
                    results = pd.read_sql_query(query, conn)
                    if not results.empty:
                        print(f"\n🔍 {col} usage for MQG.AX (last 48h):")
                        for _, row in results.iterrows():
                            print(f"  {row[col]}: {row['count']} predictions (latest: {row['latest']})")
                            if 'yfinance' in str(row[col]).lower():
                                print(f"    ⚠️ YFINANCE FALLBACK CONFIRMED!")
                            elif 'ig' in str(row[col]).lower():
                                print(f"    ✅ IG Markets working")
                    else:
                        print(f"\n❌ No source data in {col} for recent MQG.AX predictions")
            else:
                print("❌ No data source tracking columns found")
                print("   System may not be logging which price source is used")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"❌ Database not found: {db_path}")

def test_ig_markets_vs_yfinance():
    """Test both IG Markets and yfinance to compare data sources"""
    print("\n\n🔬 IG MARKETS VS YFINANCE COMPARISON")
    print("=" * 50)
    
    symbol = 'MQG.AX'
    
    # Test yfinance (definitely available)
    print(f"\n📊 yfinance test for {symbol}:")
    try:
        ticker = yf.Ticker(symbol)
        
        # Multiple yfinance methods
        info = ticker.info
        info_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        data_1m = ticker.history(period="1d", interval="1m")
        if not data_1m.empty:
            minute_price = data_1m['Close'].iloc[-1]
            minute_time = data_1m.index[-1]
            
            # Calculate delay
            now = pd.Timestamp.now(tz=minute_time.tz)
            delay_minutes = (now - minute_time).total_seconds() / 60
            
            print(f"  Info price: ${info_price:.2f}" if info_price else "  Info price: N/A")
            print(f"  1-min price: ${minute_price:.2f} at {minute_time}")
            print(f"  Data delay: {delay_minutes:.1f} minutes")
            
            if delay_minutes > 20:
                print(f"  ⚠️ SIGNIFICANT DELAY - This explains price differences!")
                
    except Exception as e:
        print(f"  ❌ yfinance error: {e}")
    
    # Test IG Markets components if available
    print(f"\n🎯 IG Markets integration test:")
    try:
        # Try to import IG Markets components
        from real_time_price_fetcher import RealTimePriceFetcher
        
        fetcher = RealTimePriceFetcher()
        result = fetcher.get_current_price(symbol)
        
        if result:
            price, source, delay = result
            print(f"  IG Price: ${price:.2f}")
            print(f"  Source: {source}")
            print(f"  Delay: {delay} minutes")
            
            if 'yfinance' in source.lower():
                print(f"  🔴 IG MARKETS IS FALLING BACK TO YFINANCE!")
                print(f"      This confirms your suspicion")
            else:
                print(f"  ✅ IG Markets working properly")
        else:
            print(f"  ❌ IG Markets returned no data")
            
    except ImportError:
        print(f"  ❌ IG Markets components not available")
        print(f"      System is definitely using yfinance only")
    except Exception as e:
        print(f"  ❌ IG Markets error: {e}")
    
    # Test enhanced market data collector
    print(f"\n📈 Enhanced Market Data Collector test:")
    try:
        from app.core.data.collectors.enhanced_market_data_collector import market_data_collector
        
        price_data = market_data_collector.get_current_price(symbol)
        
        if price_data and price_data.get('success'):
            print(f"  Price: ${price_data['price']:.2f}")
            print(f"  Source: {price_data.get('source', 'Unknown')}")
            print(f"  Quality: {price_data.get('data_quality', 'Unknown')}")
            
            if 'yfinance' in price_data.get('source', '').lower():
                print(f"  🔴 ENHANCED COLLECTOR USING YFINANCE FALLBACK!")
            elif 'ig' in price_data.get('source', '').lower():
                print(f"  ✅ Enhanced collector using IG Markets")
        else:
            print(f"  ❌ Enhanced collector failed")
            
    except ImportError:
        print(f"  ❌ Enhanced market data collector not available")
    except Exception as e:
        print(f"  ❌ Enhanced collector error: {e}")

def analyze_yfinance_timestamps():
    """Analyze exact yfinance timestamps to determine data age"""
    print("\n\n� YFINANCE TIMESTAMP DETAILED ANALYSIS")
    print("=" * 50)
    
    symbol = 'MQG.AX'
    
    # Get current time info
    import pytz
    utc_now = datetime.now(pytz.UTC)
    sydney_tz = pytz.timezone('Australia/Sydney')
    sydney_now = utc_now.astimezone(sydney_tz)
    
    print(f"Current time (Sydney): {sydney_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Check ASX market hours (10:00-16:00 Sydney time)
    market_open = sydney_now.replace(hour=10, minute=0, second=0, microsecond=0)
    market_close = sydney_now.replace(hour=16, minute=0, second=0, microsecond=0)
    is_trading_day = sydney_now.weekday() < 5
    is_market_hours = market_open <= sydney_now <= market_close and is_trading_day
    
    print(f"ASX Market: {'🟢 OPEN' if is_market_hours else '🔴 CLOSED'}")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Check info timestamps
        info = ticker.info
        print(f"\n📊 INFO TIMESTAMPS:")
        
        if 'regularMarketTime' in info:
            reg_time = datetime.fromtimestamp(info['regularMarketTime'], tz=pytz.UTC)
            sydney_reg_time = reg_time.astimezone(sydney_tz)
            reg_delay = (utc_now - reg_time).total_seconds() / 60
            
            print(f"  Regular Market Time: {sydney_reg_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"  Delay: {reg_delay:.1f} minutes")
            
            # Check if it's today or last trading day
            reg_date = sydney_reg_time.date()
            today_date = sydney_now.date()
            
            if reg_date == today_date:
                print(f"  📅 Data is from TODAY")
            else:
                days_old = (today_date - reg_date).days
                print(f"  📅 Data is {days_old} day(s) old - LAST TRADING DAY")
        
        # Check 1-minute data timestamps
        print(f"\n📈 1-MINUTE DATA TIMESTAMPS:")
        
        data_1m = ticker.history(period="1d", interval="1m")
        if not data_1m.empty:
            latest_time = data_1m.index[-1]
            latest_price = data_1m['Close'].iloc[-1]
            
            # Handle timezone
            if latest_time.tz is None:
                latest_time = latest_time.tz_localize('UTC')
            
            sydney_latest = latest_time.astimezone(sydney_tz)
            minute_delay = (utc_now - latest_time).total_seconds() / 60
            
            print(f"  Latest 1m timestamp: {sydney_latest.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"  Latest 1m price: ${latest_price:.2f}")
            print(f"  1m data delay: {minute_delay:.1f} minutes")
            
            # Determine data freshness
            data_date = sydney_latest.date()
            today_date = sydney_now.date()
            
            if data_date == today_date:
                print(f"  📅 1-minute data is from TODAY")
                if is_market_hours and minute_delay > 20:
                    print(f"  🔴 SIGNIFICANT DELAY during market hours!")
                    print(f"      This explains the ~$1 MQG.AX discrepancy")
                elif minute_delay > 5:
                    print(f"  🟡 Moderate delay - normal for free yfinance")
            else:
                days_old = (today_date - data_date).days
                print(f"  📅 1-minute data is {days_old} day(s) old")
                print(f"  ⚠️ Using LAST TRADING DAY data!")
            
            # Show data age context
            if minute_delay > 60:
                hours_old = minute_delay / 60
                print(f"  ⏰ Data is {hours_old:.1f} hours old")
            elif minute_delay > 20:
                print(f"  ⏰ Data is significantly delayed ({minute_delay:.1f} min)")
            
            return {
                'timestamp': sydney_latest,
                'price': latest_price,
                'delay_minutes': minute_delay,
                'is_today': data_date == today_date,
                'market_hours': is_market_hours
            }
        else:
            print(f"  ❌ No 1-minute data available")
def check_environment_variables():
    """Check IG Markets environment variables"""
    print("\n\n🔐 IG MARKETS ENVIRONMENT CHECK")
    print("=" * 50)
    
    required_vars = ['IG_USERNAME', 'IG_PASSWORD', 'IG_API_KEY']
    optional_vars = ['IG_DEMO', 'IG_DISABLE']
    
    print("Required variables:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'IG_PASSWORD':
                print(f"  ✅ {var}: {'*' * min(len(value), 6)}...")
            elif var == 'IG_API_KEY':
                print(f"  ✅ {var}: {value[:8]}...")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
            missing_vars.append(var)
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        print(f"  {var}: {value if value else 'Not set'}")
    
    if missing_vars:
        print(f"\n🔴 MISSING VARIABLES: {', '.join(missing_vars)}")
        print("   This is likely why IG Markets is falling back to yfinance")
    else:
        print(f"\n✅ All required variables are set")
        print("   If still using yfinance, check network/API connectivity")
            
    except Exception as e:
        print(f"❌ Timestamp analysis error: {e}")
        return None

def check_database_mqg_data():
    """Check MQG.AX data in all available databases"""
    db_files = [
        "data/trading_predictions.db",
        "trading_predictions.db", 
        "predictions.db",
        "paper_trading.db"
    ]
    
    print("🔍 CHECKING MQG.AX DATA IN DATABASES")
    print("=" * 50)
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n📊 Database: {db_file}")
            try:
                conn = sqlite3.connect(db_file)
                
                # Get all tables
                tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                print(f"Tables: {', '.join(tables['name'].tolist())}")
                
                # Check for MQG.AX in predictions tables
                for table in tables['name']:
                    try:
                        if 'prediction' in table.lower():
                            mqg_data = pd.read_sql_query(f"SELECT * FROM {table} WHERE symbol = 'MQG.AX' ORDER BY timestamp DESC LIMIT 5", conn)
                            if not mqg_data.empty:
                                print(f"\n🎯 MQG.AX data in {table}:")
                                print(mqg_data[['symbol', 'timestamp', 'current_price', 'predicted_price', 'confidence'] if 'current_price' in mqg_data.columns else mqg_data.columns[:6]])
                    except Exception as e:
                        print(f"Error checking {table}: {e}")
                
                conn.close()
            except Exception as e:
                print(f"Error opening {db_file}: {e}")
        else:
            print(f"❌ {db_file} not found")

def check_yfinance_mqg_accuracy():
    """Check yfinance data accuracy for MQG.AX"""
    print("\n\n💰 YFINANCE MQG.AX PRICE VERIFICATION")
    print("=" * 50)
    
    symbol = 'MQG.AX'
    print(f"\n📈 Testing symbol: {symbol}")
    try:
        # Get current price
        ticker = yf.Ticker(symbol)
        
        # Get 1-minute data for today
        data_1m = ticker.history(period="1d", interval="1m")
        if not data_1m.empty:
            current_price = data_1m['Close'].iloc[-1]
            volume = data_1m['Volume'].iloc[-1] if 'Volume' in data_1m.columns else 0
            print(f"Current price (1m): ${current_price:.2f}")
            print(f"Volume: {volume:,} shares")
            print(f"Last update: {data_1m.index[-1]}")
            
            # Check recent price movement
            if len(data_1m) > 10:
                price_10min_ago = data_1m['Close'].iloc[-10]
                price_change = current_price - price_10min_ago
                print(f"Price change (10min): ${price_change:+.2f}")
            
        # Get 5-minute data
        data_5m = ticker.history(period="1d", interval="5m")
        if not data_5m.empty:
            current_price_5m = data_5m['Close'].iloc[-1]
            print(f"Current price (5m): ${current_price_5m:.2f}")
            
        # Get daily data
        data_daily = ticker.history(period="2d", interval="1d")
        if not data_daily.empty:
            current_price_daily = data_daily['Close'].iloc[-1]
            print(f"Current price (daily): ${current_price_daily:.2f}")
            
        # Check info
        info = ticker.info
        if info:
            print(f"Company: {info.get('longName', 'Unknown')}")
            print(f"Exchange: {info.get('exchange', 'Unknown')}")
            print(f"Currency: {info.get('currency', 'Unknown')}")
            if 'regularMarketPrice' in info:
                print(f"Regular market price: ${info['regularMarketPrice']:.2f}")
            if 'currentPrice' in info:
                print(f"Info current price: ${info['currentPrice']:.2f}")
                
        # Compare different data sources
        print(f"\n🔍 PRICE COMPARISON:")
        prices = {}
        if not data_1m.empty:
            prices['1min'] = data_1m['Close'].iloc[-1]
        if not data_5m.empty:
            prices['5min'] = data_5m['Close'].iloc[-1]
        if not data_daily.empty:
            prices['daily'] = data_daily['Close'].iloc[-1]
        if info.get('currentPrice'):
            prices['info'] = info['currentPrice']
        if info.get('regularMarketPrice'):
            prices['regular'] = info['regularMarketPrice']
            
        for source, price in prices.items():
            print(f"  {source:8}: ${price:.2f}")
            
        # Check for $1+ differences
        price_values = list(prices.values())
        if len(price_values) > 1:
            max_diff = max(price_values) - min(price_values)
            if max_diff >= 1.0:
                print(f"⚠️  LARGE PRICE DIFFERENCE DETECTED: ${max_diff:.2f}")
                
    except Exception as e:
        print(f"❌ Error getting data for {symbol}: {e}")

def compare_prediction_vs_live():
    """Compare database predictions with live prices"""
    print("\n\n⚖️ MQG.AX PREDICTION VS LIVE PRICE COMPARISON")
    print("=" * 50)
    
    # Check main database
    db_path = "data/trading_predictions.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            # Get recent MQG.AX predictions
            query = """
            SELECT * FROM predictions 
            WHERE symbol = 'MQG.AX' 
            AND timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC 
            LIMIT 5
            """
            
            predictions = pd.read_sql_query(query, conn)
            
            if not predictions.empty:
                print("Recent MQG.AX predictions:")
                for idx, row in predictions.iterrows():
                    symbol = row['symbol']
                    pred_time = row['timestamp']
                    if 'current_price' in row:
                        pred_price = row['current_price']
                    elif 'entry_price' in row:
                        pred_price = row['entry_price']
                    else:
                        pred_price = "Unknown"
                    
                    print(f"\n🔸 {symbol} at {pred_time}")
                    print(f"   Database price: ${pred_price}")
                    
                    # Get current live price
                    try:
                        ticker = yf.Ticker(symbol)
                        
                        # Try multiple methods to get current price
                        info = ticker.info
                        info_price = info.get('currentPrice') or info.get('regularMarketPrice')
                        
                        live_data = ticker.history(period="1d", interval="1m")
                        if not live_data.empty:
                            live_price = live_data['Close'].iloc[-1]
                            live_time = live_data.index[-1]
                            print(f"   Live price (1m): ${live_price:.2f} at {live_time}")
                            
                            if info_price:
                                print(f"   Info price: ${info_price:.2f}")
                                
                            if pred_price != "Unknown":
                                diff_live = abs(float(pred_price) - live_price)
                                print(f"   Difference (vs 1m): ${diff_live:.2f}")
                                if diff_live >= 1.0:
                                    print(f"   ⚠️ LARGE DIFFERENCE DETECTED (${diff_live:.2f})!")
                                    
                                if info_price:
                                    diff_info = abs(float(pred_price) - info_price)
                                    print(f"   Difference (vs info): ${diff_info:.2f}")
                                    
                    except Exception as e:
                        print(f"   Error getting live price: {e}")
            else:
                print("❌ No recent MQG.AX predictions found")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"❌ Database not found: {db_path}")

def check_1_minute_intervals():
    """Check if system is actually using 1-minute intervals for MQG.AX"""
    print("\n\n⏰ MQG.AX 1-MINUTE INTERVAL VERIFICATION")
    print("=" * 50)
    
    db_path = "data/trading_predictions.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            
            # Check prediction timestamps to see if they're actually 1-minute apart
            query = """
            SELECT symbol, timestamp 
            FROM predictions 
            WHERE symbol = 'MQG.AX'
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            
            predictions = pd.read_sql_query(query, conn)
            
            if not predictions.empty:
                print("Recent MQG.AX prediction timestamps:")
                prev_time = None
                for idx, row in predictions.iterrows():
                    current_time = pd.to_datetime(row['timestamp'])
                    print(f"{row['symbol']}: {current_time}")
                    
                    if prev_time:
                        diff = (prev_time - current_time).total_seconds() / 60
                        print(f"   Time diff: {diff:.1f} minutes")
                        
                        if abs(diff - 1.0) > 0.5:  # Not close to 1 minute
                            print(f"   ⚠️ NOT 1-minute interval!")
                    
                    prev_time = current_time
                    
                    if idx >= 5:  # Only show first 5 for brevity
                        break
            else:
                print("❌ No MQG.AX predictions found")
                
            # Also check market_aware_predictions table if it exists
            try:
                query_ma = """
                SELECT symbol, timestamp 
                FROM market_aware_predictions 
                WHERE symbol = 'MQG.AX'
                ORDER BY timestamp DESC 
                LIMIT 10
                """
                
                ma_predictions = pd.read_sql_query(query_ma, conn)
                if not ma_predictions.empty:
                    print(f"\nMarket-aware predictions found: {len(ma_predictions)}")
                    for idx, row in ma_predictions.head(3).iterrows():
                        print(f"  {row['symbol']}: {row['timestamp']}")
                        
            except Exception as e:
                print(f"No market_aware_predictions table: {e}")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"❌ Database not found: {db_path}")
        
    # Check yfinance 1-minute data availability
    print(f"\n📊 YFINANCE 1-MINUTE DATA CHECK:")
    try:
        ticker = yf.Ticker('MQG.AX')
        data_1m = ticker.history(period="1d", interval="1m")
        if not data_1m.empty:
            print(f"Available 1-minute data points: {len(data_1m)}")
            print(f"Latest timestamp: {data_1m.index[-1]}")
            print(f"Data span: {data_1m.index[0]} to {data_1m.index[-1]}")
            
            # Check if data is actually 1-minute intervals
            time_diffs = data_1m.index[1:] - data_1m.index[:-1]
            avg_diff = time_diffs.mean().total_seconds() / 60
            print(f"Average interval: {avg_diff:.1f} minutes")
        else:
            print("❌ No 1-minute data available")
    except Exception as e:
        print(f"Error checking yfinance data: {e}")

if __name__ == "__main__":
    print("🔍 MQG.AX PREDICTION ACCURACY INVESTIGATION")
    print("=" * 60)
    print("Focus: Verify if IG Markets is working or system is using yfinance fallback")
    print("Special Focus: Check exact yfinance timestamps and data age")
    
    check_environment_variables()
    timestamp_info = analyze_yfinance_timestamps()
    check_data_source_tracking()
    test_ig_markets_vs_yfinance()
    check_database_mqg_data()
    check_yfinance_mqg_accuracy()
    compare_prediction_vs_live()
    check_1_minute_intervals()
    
    print("\n✅ Investigation complete!")
    print("\n💡 KEY FINDINGS:")
    if timestamp_info:
        delay = timestamp_info['delay_minutes']
        is_today = timestamp_info['is_today']
        market_hours = timestamp_info['market_hours']
        
        print(f"📊 yfinance data delay: {delay:.1f} minutes")
        print(f"📅 Data date: {'Today' if is_today else 'Last trading day'}")
        print(f"🕐 Market status: {'Open' if market_hours else 'Closed'}")
        
        if delay > 20 and market_hours:
            print(f"🔴 CONCLUSION: {delay:.1f} minute yfinance delay explains the ~$1 MQG.AX difference!")
        elif not is_today:
            print(f"🔴 CONCLUSION: Using last trading day data explains the price difference!")
        else:
            print(f"🟢 yfinance delay is reasonable for free data")
    
    print("🔧 RECOMMENDATIONS:")
    print("1. Fix IG Markets integration for real-time ASX data")
    print("2. Monitor yfinance delay during market hours") 
    print("3. Add timestamp logging to track data freshness")
    print("4. Consider price tolerance based on data source delays")
