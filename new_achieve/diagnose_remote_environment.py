#!/usr/bin/env python3
"""
Remote Environment Diagnostic Script
Comprehensive analysis of remote vs local environment differences
"""

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

def diagnose_remote_environment():
    """
    Comprehensive diagnostic of remote environment issues
    """
    print("🔍 REMOTE ENVIRONMENT DIAGNOSTIC")
    print("=" * 50)
    
    # Check database file existence and permissions
    db_path = "data/ml_models/enhanced_training_data.db"
    print(f"\n📁 Database File Analysis:")
    print(f"   Path: {db_path}")
    print(f"   Exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        print(f"   Size: {stat.st_size:,} bytes")
        print(f"   Modified: {datetime.fromtimestamp(stat.st_mtime)}")
        print(f"   Permissions: {oct(stat.st_mode)[-3:]}")
    
    # Database structure analysis
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 Database Structure Analysis:")
        
        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tables found: {[table[0] for table in tables]}")
        
        # Enhanced features analysis
        cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        total_features = cursor.fetchone()[0]
        print(f"\n📈 Enhanced Features Table:")
        print(f"   Total records: {total_features}")
        
        if total_features > 0:
            # Date range analysis
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM enhanced_features")
            min_date, max_date = cursor.fetchone()
            print(f"   Date range: {min_date} to {max_date}")
            
            # Symbol distribution
            cursor.execute("SELECT symbol, COUNT(*) FROM enhanced_features GROUP BY symbol ORDER BY COUNT(*) DESC")
            symbol_counts = cursor.fetchall()
            print(f"   Symbol distribution:")
            for symbol, count in symbol_counts:
                print(f"     {symbol}: {count} records")
            
            # Recent data analysis
            cursor.execute("""
                SELECT COUNT(*) FROM enhanced_features 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            recent_features = cursor.fetchone()[0]
            print(f"   Recent features (7 days): {recent_features}")
            
            # Feature completeness check
            cursor.execute("""
                SELECT 
                    AVG(CASE WHEN sentiment_score IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100 as sentiment_pct,
                    AVG(CASE WHEN rsi IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100 as rsi_pct,
                    AVG(CASE WHEN news_count IS NOT NULL AND news_count > 0 THEN 1.0 ELSE 0.0 END) * 100 as news_pct,
                    AVG(CASE WHEN confidence IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100 as confidence_pct
                FROM enhanced_features
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            completeness = cursor.fetchone()
            if completeness[0] is not None:
                print(f"   Feature completeness (recent):")
                print(f"     Sentiment: {completeness[0]:.1f}%")
                print(f"     RSI: {completeness[1]:.1f}%") 
                print(f"     News: {completeness[2]:.1f}%")
                print(f"     Confidence: {completeness[3]:.1f}%")
        
        # Enhanced outcomes analysis
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_outcomes = cursor.fetchone()[0]
        print(f"\n📉 Enhanced Outcomes Table:")
        print(f"   Total records: {total_outcomes}")
        
        if total_outcomes > 0:
            # Outcomes with actual price data
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN exit_price_1h IS NOT NULL THEN 1 END) as has_1h_exit,
                    COUNT(CASE WHEN exit_price_4h IS NOT NULL THEN 1 END) as has_4h_exit,
                    COUNT(CASE WHEN exit_price_1d IS NOT NULL THEN 1 END) as has_1d_exit,
                    COUNT(CASE WHEN return_pct IS NOT NULL THEN 1 END) as has_return
                FROM enhanced_outcomes
            """)
            outcome_stats = cursor.fetchone()
            print(f"   Outcomes with exit prices:")
            print(f"     1-hour exits: {outcome_stats[1]}/{outcome_stats[0]}")
            print(f"     4-hour exits: {outcome_stats[2]}/{outcome_stats[0]}")
            print(f"     1-day exits: {outcome_stats[3]}/{outcome_stats[0]}")
            print(f"     Return calculated: {outcome_stats[4]}/{outcome_stats[0]}")
            
            # Recent outcomes
            cursor.execute("""
                SELECT COUNT(*) FROM enhanced_outcomes 
                WHERE prediction_timestamp >= datetime('now', '-7 days')
            """)
            recent_outcomes = cursor.fetchone()[0]
            print(f"   Recent outcomes (7 days): {recent_outcomes}")
        
        # Training readiness assessment
        print(f"\n🎯 Training Readiness Assessment:")
        training_ready = total_features >= 50 and total_outcomes >= 50
        print(f"   Features requirement: {total_features}/50 {'✅' if total_features >= 50 else '❌'}")
        print(f"   Outcomes requirement: {total_outcomes}/50 {'✅' if total_outcomes >= 50 else '❌'}")
        print(f"   Overall status: {'✅ READY' if training_ready else '❌ INSUFFICIENT'}")
        
        # Data quality issues
        print(f"\n⚠️ Potential Issues:")
        issues = []
        
        if total_features < 371:
            missing_features = 371 - total_features
            issues.append(f"Missing {missing_features} features compared to local environment")
        
        if total_outcomes < 50:
            issues.append(f"Insufficient outcomes for ML training ({total_outcomes}/50)")
        
        if recent_features == 0:
            issues.append("No recent feature data (past 7 days)")
        
        if recent_outcomes == 0:
            issues.append("No recent outcome data (past 7 days)")
        
        # Check for data staleness
        if total_features > 0:
            cursor.execute("SELECT MAX(timestamp) FROM enhanced_features")
            latest_feature = cursor.fetchone()[0]
            if latest_feature:
                latest_dt = datetime.fromisoformat(latest_feature.replace('Z', '+00:00'))
                days_old = (datetime.now() - latest_dt.replace(tzinfo=None)).days
                if days_old > 1:
                    issues.append(f"Feature data is {days_old} days old")
        
        if issues:
            for issue in issues:
                print(f"   ❌ {issue}")
        else:
            print(f"   ✅ No obvious data quality issues detected")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Environment analysis
    print(f"\n🌍 Environment Analysis:")
    print(f"   Python version: {os.sys.version}")
    print(f"   Working directory: {os.getcwd()}")
    print(f"   Environment variables:")
    
    # Check for important environment variables
    env_vars = ['PYTHONPATH', 'MARKET_API_KEY', 'REDDIT_CLIENT_ID', 'OPENAI_API_KEY']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive data
            if 'KEY' in var or 'SECRET' in var:
                masked = value[:8] + '...' + value[-4:] if len(value) > 12 else 'SET'
                print(f"     {var}: {masked}")
            else:
                print(f"     {var}: {value}")
        else:
            print(f"     {var}: ❌ NOT SET")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if total_features < 371:
        print("   1. 🔄 Run enhanced morning analyzer to populate missing features")
        print("      Command: python -m app.main morning")
    
    if total_outcomes < 50:
        print("   2. ⏰ Wait for more trading outcomes to accumulate")
        print("      Or run historical backfill if available")
    
    if recent_features == 0:
        print("   3. 📊 Verify data collection processes are running")
        print("      Check news feeds, Reddit API, and technical analysis")
    
    print("   4. 🔍 Compare with local environment:")
    print("      Run this same diagnostic locally to identify differences")
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic Complete")

if __name__ == "__main__":
    diagnose_remote_environment()
