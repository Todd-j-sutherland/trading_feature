#!/usr/bin/env python3
"""
Remote System Status Checker
Check prediction generation status and recent activity
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
import os
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_recent_predictions(db_path="data/trading_predictions.db"):
    """Check for recent prediction activity"""
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Database not found: {db_path}")
        return False
    
    logger.info("🔍 Checking recent prediction activity...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current time and 30 minutes ago
        now = datetime.now()
        thirty_min_ago = now - timedelta(minutes=30)
        
        print(f"📊 RECENT PREDICTION ANALYSIS")
        print(f"   Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Checking since: {thirty_min_ago.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Check legacy predictions table
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE prediction_timestamp > ?
        """, (thirty_min_ago.isoformat(),))
        
        recent_legacy = cursor.fetchone()[0]
        print(f"📋 Legacy predictions (last 30 min): {recent_legacy}")
        
        if recent_legacy > 0:
            cursor.execute("""
                SELECT symbol, predicted_action, action_confidence, prediction_timestamp, model_version
                FROM predictions 
                WHERE prediction_timestamp > ?
                ORDER BY prediction_timestamp DESC
                LIMIT 5
            """, (thirty_min_ago.isoformat(),))
            
            for row in cursor.fetchall():
                print(f"   {row[3]}: {row[0]} {row[1]} ({row[2]:.1%}) - {row[4]}")
        
        # 2. Check market-aware predictions table
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM market_aware_predictions 
                WHERE timestamp > ?
            """, (thirty_min_ago.isoformat(),))
            
            recent_market_aware = cursor.fetchone()[0]
            print(f"📋 Market-aware predictions (last 30 min): {recent_market_aware}")
            
            if recent_market_aware > 0:
                cursor.execute("""
                    SELECT symbol, recommended_action, confidence, timestamp, model_used
                    FROM market_aware_predictions 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, (thirty_min_ago.isoformat(),))
                
                for row in cursor.fetchall():
                    print(f"   {row[3]}: {row[0]} {row[1]} ({row[2]:.1%}) - {row[4]}")
                    
        except sqlite3.OperationalError:
            print(f"📋 Market-aware predictions: Table not found")
            recent_market_aware = 0
        
        print()
        
        # 3. Check last prediction times
        cursor.execute("""
            SELECT MAX(prediction_timestamp) FROM predictions
        """)
        last_legacy = cursor.fetchone()[0]
        
        try:
            cursor.execute("""
                SELECT MAX(timestamp) FROM market_aware_predictions
            """)
            last_market_aware = cursor.fetchone()[0]
        except:
            last_market_aware = None
        
        print(f"🕒 LAST PREDICTION TIMES:")
        print(f"   Legacy system: {last_legacy}")
        print(f"   Market-aware system: {last_market_aware}")
        
        # 4. Check if prediction systems are running
        print()
        print(f"🔍 SYSTEM STATUS CHECK:")
        
        # Check for running prediction processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            prediction_processes = []
            for line in processes.split('\n'):
                if any(keyword in line.lower() for keyword in ['predict', 'trading', 'market_aware', 'enhanced']):
                    if 'python' in line.lower():
                        prediction_processes.append(line.strip())
            
            if prediction_processes:
                print(f"   ✅ Found {len(prediction_processes)} potential prediction processes:")
                for proc in prediction_processes[:5]:  # Show first 5
                    print(f"      {proc}")
            else:
                print(f"   ⚠️ No prediction processes found running")
                
        except Exception as e:
            print(f"   ❌ Could not check processes: {e}")
        
        # 5. Check cron jobs
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                cron_jobs = result.stdout
                prediction_crons = [line for line in cron_jobs.split('\n') if 'predict' in line.lower() or 'trading' in line.lower()]
                
                if prediction_crons:
                    print(f"   ✅ Found {len(prediction_crons)} prediction cron jobs:")
                    for cron in prediction_crons:
                        print(f"      {cron}")
                else:
                    print(f"   ⚠️ No prediction cron jobs found")
            else:
                print(f"   ❌ Could not access crontab")
        except Exception as e:
            print(f"   ❌ Could not check crontab: {e}")
        
        # 6. Analysis summary
        total_recent = recent_legacy + recent_market_aware
        print()
        print(f"🎯 ANALYSIS SUMMARY:")
        print(f"   Total recent predictions: {total_recent}")
        
        if total_recent == 0:
            print(f"   ❌ NO RECENT PREDICTIONS - Investigation needed")
            print(f"   🔍 Possible causes:")
            print(f"      - Prediction services stopped")
            print(f"      - Cron jobs not running") 
            print(f"      - Market hours (check if predictions run during market close)")
            print(f"      - System errors or crashes")
            print(f"      - Database connection issues")
        else:
            print(f"   ✅ Recent prediction activity detected")
        
        conn.close()
        return total_recent > 0
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return False

def check_prediction_system_health():
    """Check if prediction systems are healthy"""
    
    print()
    print(f"🏥 PREDICTION SYSTEM HEALTH CHECK:")
    
    # Check key prediction scripts exist
    prediction_files = [
        'enhanced_efficient_system_market_aware.py',
        'enhanced_efficient_system_market_aware_integrated.py',
        'market_aware_daily_manager.py',
        'market-aware-paper-trading/market_aware_prediction_system.py',
        'predictions_paper_trading_executor_v2.py'
    ]
    
    for file in prediction_files:
        if os.path.exists(file):
            print(f"   ✅ {file}: Present")
        else:
            print(f"   ❌ {file}: Missing")
    
    # Check data sources
    data_files = [
        'data/trading_predictions.db',
        'data/news_data.db',
        'data/market_data.db'
    ]
    
    for file in data_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024*1024)  # MB
            print(f"   ✅ {file}: Present ({size:.1f} MB)")
        else:
            print(f"   ❌ {file}: Missing")
            
    # Check if main prediction system can be imported
    print()
    print(f"🔧 PREDICTION SYSTEM IMPORT TEST:")
    try:
        import subprocess
        result = subprocess.run([
            'python3', '-c', 
            'import sys; sys.path.append("."); from enhanced_efficient_system_market_aware import *; print("✅ Main prediction system imports successfully")'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ enhanced_efficient_system_market_aware.py: Import successful")
        else:
            print(f"   ❌ enhanced_efficient_system_market_aware.py: Import failed")
            print(f"      Error: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")

def main():
    """Main execution"""
    print("🚀 REMOTE PREDICTION SYSTEM STATUS CHECK")
    print("=" * 45)
    
    # Change to correct directory if needed
    if os.path.exists('/path/to/trading_feature'):
        os.chdir('/path/to/trading_feature')
    elif os.path.exists('../trading_feature'):
        os.chdir('../trading_feature')
    
    print(f"📂 Working directory: {os.getcwd()}")
    print()
    
    # Run status checks
    has_recent = check_recent_predictions()
    check_prediction_system_health()
    
    if not has_recent:
        print()
        print("🔧 RECOMMENDED ACTIONS:")
        print("1. Check if prediction services are running")
        print("2. Restart prediction cron jobs")
        print("3. Check system logs for errors")
        print("4. Verify market data feeds are working")
        print("5. Test manual prediction generation")

if __name__ == "__main__":
    main()
