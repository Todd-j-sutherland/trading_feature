#!/usr/bin/env python3
"""
Prediction Validation Tool - Diagnose Morning Run Issues
"""

import sys
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta
import json

def check_recent_predictions():
    """Analyze recent predictions for issues"""
    print("🔍 ANALYZING RECENT PREDICTIONS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('/root/test/data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Get today's predictions
        today = datetime.now().date()
        cursor.execute('''
        SELECT symbol, prediction_timestamp, predicted_action, action_confidence, 
               predicted_direction, predicted_magnitude, model_version
        FROM predictions 
        WHERE date(prediction_timestamp) = ?
        ORDER BY prediction_timestamp DESC
        ''', (today,))
        
        today_predictions = cursor.fetchall()
        
        if not today_predictions:
            print("❌ No predictions found for today")
            return False
        
        print(f"📊 Found {len(today_predictions)} predictions for today")
        
        # Analyze for issues
        issues = []
        unique_actions = set()
        unique_confidences = set()
        unique_timestamps = set()
        
        for pred in today_predictions:
            symbol, timestamp, action, confidence, direction, magnitude, model_version = pred
            unique_actions.add(action)
            unique_confidences.add(confidence)
            unique_timestamps.add(timestamp)
            
            print(f"  {symbol}: {action} (conf: {confidence:.3f}, dir: {direction}, mag: {magnitude})")
        
        # Check for issues
        if len(unique_actions) == 1:
            issues.append(f"⚠️ All predictions have same action: {list(unique_actions)[0]}")
        
        if len(unique_confidences) == 1 and 0.5 in unique_confidences:
            issues.append("⚠️ All predictions have default confidence: 0.5")
        
        if len(unique_timestamps) == 1:
            issues.append("⚠️ All predictions have identical timestamp")
        
        # Check for default/fallback values
        default_confidence_count = sum(1 for pred in today_predictions if pred[3] == 0.5)
        if default_confidence_count > 0:
            issues.append(f"⚠️ {default_confidence_count}/{len(today_predictions)} predictions use default confidence (0.5)")
        
        if issues:
            print(f"\n🚨 ISSUES DETECTED:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print(f"\n✅ Predictions look normal")
            return True
            
    except Exception as e:
        print(f"❌ Error analyzing predictions: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_data_sources():
    """Check if data sources are working"""
    print("\n🔍 CHECKING DATA SOURCES")
    print("=" * 40)
    
    checks = {}
    
    # Test yfinance
    try:
        import yfinance as yf
        ticker = yf.Ticker("CBA.AX")
        info = ticker.info
        if info and 'regularMarketPrice' in info:
            print(f"  ✅ yfinance: CBA.AX price = ${info['regularMarketPrice']}")
            checks['yfinance'] = True
        else:
            print(f"  ❌ yfinance: No price data")
            checks['yfinance'] = False
    except Exception as e:
        print(f"  ❌ yfinance: {e}")
        checks['yfinance'] = False
    
    # Test transformers
    try:
        from transformers import pipeline
        classifier = pipeline("sentiment-analysis", return_all_scores=True)
        result = classifier("The market outlook is positive")
        print(f"  ✅ transformers: Sentiment working")
        checks['transformers'] = True
    except Exception as e:
        print(f"  ❌ transformers: {e}")
        checks['transformers'] = False
    
    # Test database connection
    try:
        conn = sqlite3.connect('/root/test/data/trading_predictions.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions")
        count = cursor.fetchone()[0]
        print(f"  ✅ database: {count} total predictions")
        checks['database'] = True
        conn.close()
    except Exception as e:
        print(f"  ❌ database: {e}")
        checks['database'] = False
    
    return checks

def check_morning_routine_logs():
    """Check logs from morning routine"""
    print("\n🔍 CHECKING MORNING ROUTINE LOGS")
    print("=" * 40)
    
    log_files = [
        '/root/test/logs/morning_cron.log',
        '/root/test/logs/market_hours.log',
        '/root/test/logs/enhanced_morning_analysis.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📄 {os.path.basename(log_file)}:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Show last few lines
                        for line in lines[-5:]:
                            print(f"    {line.strip()}")
                    else:
                        print("    (empty)")
            except Exception as e:
                print(f"    Error reading: {e}")
        else:
            print(f"❌ Missing: {log_file}")

def check_market_hours_status():
    """Check if market hours detection is working"""
    print("\n🔍 CHECKING MARKET HOURS STATUS")
    print("=" * 40)
    
    try:
        import pytz
        from datetime import time
        
        # Australian Eastern Time
        aet = pytz.timezone('Australia/Sydney')
        now_aet = datetime.now(aet)
        
        # Market hours: Monday-Friday, 10:00 AM - 4:00 PM AEST/AEDT
        market_open = time(10, 0)
        market_close = time(16, 0)
        
        is_weekday = now_aet.weekday() < 5
        is_market_hours = market_open <= now_aet.time() <= market_close
        market_is_open = is_weekday and is_market_hours
        
        print(f"🕐 Current AET: {now_aet.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 Weekday: {'✅' if is_weekday else '❌'} (day {now_aet.weekday()})")
        print(f"⏰ Market Hours: {'✅' if is_market_hours else '❌'}")
        print(f"🏦 Market Open: {'✅' if market_is_open else '❌'}")
        
        return market_is_open
        
    except Exception as e:
        print(f"❌ Error checking market hours: {e}")
        return False

def validate_prediction_logic():
    """Test if prediction logic is working correctly"""
    print("\n🔍 TESTING PREDICTION LOGIC")
    print("=" * 40)
    
    try:
        # Try to run a quick test prediction
        test_command = '''
cd /root/test
export PYTHONPATH=/root/test
/root/trading_venv/bin/python3 -c "
import sys
sys.path.append('/root/test')
try:
    from app.core.sentiment.news_analyzer import NewsTradingAnalyzer
    analyzer = NewsTradingAnalyzer()
    result = analyzer.analyze_single_bank('CBA.AX', detailed=False)
    print(f'Test analysis result: {type(result)}')
    if result and 'overall_sentiment' in result:
        print(f'Sentiment: {result[\"overall_sentiment\"]:.3f}')
    else:
        print('No sentiment result')
except Exception as e:
    print(f'Test failed: {e}')
"
'''
        
        result = subprocess.run(test_command, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Prediction logic test:")
            print(f"    {result.stdout.strip()}")
            return True
        else:
            print("❌ Prediction logic test failed:")
            print(f"    Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Could not test prediction logic: {e}")
        return False

def main():
    """Main validation routine"""
    print("🔍 PREDICTION VALIDATION & DIAGNOSIS")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all checks
    checks = {
        "Recent Predictions": check_recent_predictions(),
        "Data Sources": all(check_data_sources().values()),
        "Market Hours": check_market_hours_status(),
        "Prediction Logic": validate_prediction_logic()
    }
    
    # Check logs
    check_morning_routine_logs()
    
    # Summary
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 30)
    
    passed = 0
    for check_name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}")
        if status:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(checks)} checks passed")
    
    if passed < len(checks):
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print("1. Check if morning routine ran successfully")
        print("2. Verify data sources are accessible")
        print("3. Ensure ML models are loaded correctly") 
        print("4. Check for any error logs")
        
        if not checks["Recent Predictions"]:
            print("5. ⚠️ CRITICAL: All predictions identical - system may be in fallback mode")
    
    return passed == len(checks)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
