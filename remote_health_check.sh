#!/bin/bash
# Remote Data Health Check for Live Market Hours
# Run this on the remote server during ASX market hours

echo "🌐 REMOTE TRADING SYSTEM DATA HEALTH CHECK"
echo "=========================================="

# Get Australian time
export TZ="Australia/Sydney"
CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S %Z')
CURRENT_HOUR=$(date '+%H')
CURRENT_DOW=$(date '+%u')  # 1=Monday, 7=Sunday

echo "📅 Current Time: $CURRENT_TIME"

# Check if market hours (10 AM - 4 PM AEST, Monday-Friday)
MARKET_OPEN=0
if [ "$CURRENT_DOW" -le 5 ] && [ "$CURRENT_HOUR" -ge 10 ] && [ "$CURRENT_HOUR" -lt 16 ]; then
    MARKET_OPEN=1
    echo "🟢 Market Status: OPEN (Live Trading Hours)"
else
    echo "🔴 Market Status: CLOSED"
fi

echo ""
echo "🔍 ACTIVATING REMOTE ENVIRONMENT..."
echo "====================================="

# Navigate to remote directory and activate environment
cd test/
source trading_venv/bin/activate

echo "✅ Remote environment activated"
echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $(which python)"

echo ""
echo "🏥 RUNNING DATA HEALTH DIAGNOSTICS..."
echo "====================================="

# Create and run health check script
cat > live_data_health_check.py << 'EOF'
#!/usr/bin/env python3
"""
Live Data Health Check for Remote Trading System
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json

def check_remote_data_health():
    """Check data health on remote system"""
    
    print("📊 REMOTE DATA HEALTH ANALYSIS")
    print("-" * 50)
    
    # Database paths (adjust for remote system)
    db_paths = [
        "data/trading_predictions.db",
        "../data/trading_predictions.db", 
        "trading_predictions.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No trading database found!")
        print("   Searched paths:")
        for path in db_paths:
            print(f"   - {path}")
        return
    
    print(f"✅ Database found: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Available tables ({len(tables)}):")
        for table in sorted(tables):
            print(f"   - {table}")
        
        print()
        
        # Check today's data status
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"🗓️  CHECKING TODAY'S DATA ({today}):")
        print("-" * 40)
        
        # 1. Morning Analysis Data
        if 'enhanced_morning_analysis' in tables:
            cursor.execute("""
                SELECT COUNT(*), MAX(timestamp), market_hours 
                FROM enhanced_morning_analysis 
                WHERE DATE(timestamp) = ?
            """, (today,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                print(f"✅ Morning Analysis: {result[0]} runs today")
                print(f"   Latest: {result[1]}")
                print(f"   Market Hours: {'Yes' if result[2] else 'No'}")
            else:
                print("❌ Morning Analysis: No runs today")
        
        # 2. Volume Data
        if 'daily_volume_data' in tables:
            cursor.execute("""
                SELECT COUNT(*), MAX(data_timestamp) 
                FROM daily_volume_data 
                WHERE analysis_date = ?
            """, (today,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                print(f"✅ Volume Data: {result[0]} symbols today")
                print(f"   Latest: {result[1]}")
                
                # Show volume details
                cursor.execute("""
                    SELECT symbol, latest_volume, volume_ratio, market_hours
                    FROM daily_volume_data 
                    WHERE analysis_date = ?
                    ORDER BY volume_ratio DESC
                """, (today,))
                
                volumes = cursor.fetchall()
                print(f"   📊 Volume Summary:")
                for symbol, vol, ratio, mh in volumes[:5]:  # Top 5
                    status = "Live" if mh else "EOD"
                    print(f"      {symbol}: {vol:,.0f} ({ratio:.2f}x) [{status}]")
            else:
                print("❌ Volume Data: No data today")
        
        # 3. Predictions
        if 'predictions' in tables:
            cursor.execute("""
                SELECT COUNT(*), MAX(prediction_timestamp) 
                FROM predictions 
                WHERE DATE(prediction_timestamp) = ?
            """, (today,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                print(f"✅ Predictions: {result[0]} predictions today")
                print(f"   Latest: {result[1]}")
                
                # Show prediction summary
                cursor.execute("""
                    SELECT predicted_action, COUNT(*) 
                    FROM predictions 
                    WHERE DATE(prediction_timestamp) = ?
                    GROUP BY predicted_action
                """, (today,))
                
                actions = cursor.fetchall()
                print(f"   📈 Action Summary:")
                for action, count in actions:
                    print(f"      {action}: {count}")
            else:
                print("❌ Predictions: No predictions today")
        
        # 4. Evening Analysis
        if 'enhanced_evening_analysis' in tables:
            cursor.execute("""
                SELECT COUNT(*), MAX(timestamp) 
                FROM enhanced_evening_analysis 
                WHERE DATE(timestamp) = ?
            """, (today,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                print(f"✅ Evening Analysis: {result[0]} runs today")
                print(f"   Latest: {result[1]}")
            else:
                print("❌ Evening Analysis: No runs today")
        
        print()
        
        # 5. Data Freshness Analysis
        print("🕐 DATA FRESHNESS ANALYSIS:")
        print("-" * 40)
        
        # Check most recent data across all tables
        data_freshness = []
        
        for table in ['enhanced_morning_analysis', 'daily_volume_data', 'predictions', 'enhanced_evening_analysis']:
            if table in tables:
                # Try different timestamp column names
                timestamp_cols = ['timestamp', 'prediction_timestamp', 'data_timestamp', 'created_at']
                
                for col in timestamp_cols:
                    try:
                        cursor.execute(f"SELECT MAX({col}) FROM {table}")
                        result = cursor.fetchone()
                        if result and result[0]:
                            latest = result[0]
                            # Calculate hours ago
                            try:
                                latest_dt = datetime.fromisoformat(latest.replace('Z', '+00:00'))
                                hours_ago = (datetime.now() - latest_dt.replace(tzinfo=None)).total_seconds() / 3600
                                data_freshness.append((table, latest, hours_ago))
                                break
                            except:
                                data_freshness.append((table, latest, -1))
                                break
                    except:
                        continue
        
        for table, latest, hours_ago in data_freshness:
            if hours_ago >= 0:
                if hours_ago < 1:
                    status = "🟢 Very Fresh"
                elif hours_ago < 6:
                    status = "🟡 Fresh"
                elif hours_ago < 24:
                    status = "🟠 Stale"
                else:
                    status = "🔴 Very Stale"
                print(f"   {table}: {status} ({hours_ago:.1f}h ago)")
            else:
                print(f"   {table}: {latest}")
        
        print()
        
        # 6. System Health Score
        print("🏥 SYSTEM HEALTH SCORE:")
        print("-" * 40)
        
        health_score = 0
        max_score = 100
        
        # Morning analysis (25 points)
        if 'enhanced_morning_analysis' in tables:
            cursor.execute(f"SELECT COUNT(*) FROM enhanced_morning_analysis WHERE DATE(timestamp) = '{today}'")
            if cursor.fetchone()[0] > 0:
                health_score += 25
                print("✅ Morning Analysis: +25 points")
            else:
                print("❌ Morning Analysis: +0 points")
        
        # Volume data (25 points)
        if 'daily_volume_data' in tables:
            cursor.execute(f"SELECT COUNT(*) FROM daily_volume_data WHERE analysis_date = '{today}'")
            if cursor.fetchone()[0] >= 4:  # At least 4 banks
                health_score += 25
                print("✅ Volume Data: +25 points")
            else:
                print("❌ Volume Data: +0 points")
        
        # Recent predictions (25 points)
        if 'predictions' in tables:
            cursor.execute(f"SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = '{today}'")
            if cursor.fetchone()[0] > 0:
                health_score += 25
                print("✅ Predictions: +25 points")
            else:
                print("❌ Predictions: +0 points")
        
        # Data freshness (25 points)
        fresh_tables = sum(1 for _, _, hours in data_freshness if hours >= 0 and hours < 6)
        if fresh_tables >= 2:
            health_score += 25
            print("✅ Data Freshness: +25 points")
        else:
            print("❌ Data Freshness: +0 points")
        
        print()
        print(f"🏥 OVERALL HEALTH SCORE: {health_score}/{max_score}")
        
        if health_score >= 80:
            print("🟢 System Status: EXCELLENT")
        elif health_score >= 60:
            print("🟡 System Status: GOOD")
        elif health_score >= 40:
            print("🟠 System Status: FAIR")
        else:
            print("🔴 System Status: POOR")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_remote_data_health()
EOF

# Run the health check
echo "🚀 Executing health check..."
python live_data_health_check.py

echo ""
echo "📊 MARKET DATA COLLECTION TEST..."
echo "================================="

# Test live market data collection during market hours
if [ "$MARKET_OPEN" -eq 1 ]; then
    echo "🟢 Market is OPEN - Testing live data collection..."
    
    cat > test_live_market_data.py << 'EOF'
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
EOF

    python test_live_market_data.py
else
    echo "🔴 Market is CLOSED - Skipping live data test"
fi

echo ""
echo "✅ REMOTE HEALTH CHECK COMPLETE"
echo "==============================="
echo "💡 Run this script on the remote server during market hours for live analysis"

# Deactivate environment
deactivate
