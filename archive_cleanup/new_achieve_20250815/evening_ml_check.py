#!/usr/bin/env python3
"""
Evening ML Model Performance Check
Run this script after market close (5:00 PM AEST) to get a comprehensive daily report
of your ML trading model performance.

Usage:
    python3 evening_ml_check.py
    
Or with SSH to remote server:
    ssh root@170.64.199.151 "cd /root/test && python3 evening_ml_check.py"
"""

import sqlite3
import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def check_model_status():
    """Check if ML models exist and get their metadata"""
    print_section("1. MODEL STATUS CHECK")
    
    models_dir = Path("data/ml_models/models")
    
    # Check if models exist
    direction_model = models_dir / "current_direction_model.pkl"
    magnitude_model = models_dir / "current_magnitude_model.pkl"
    metadata_file = models_dir / "current_enhanced_metadata.json"
    
    if direction_model.exists():
        print("✅ Direction model: FOUND")
        print(f"   Size: {direction_model.stat().st_size / 1024:.1f} KB")
        print(f"   Modified: {datetime.fromtimestamp(direction_model.stat().st_mtime)}")
    else:
        print("❌ Direction model: MISSING")
        return False
    
    if magnitude_model.exists():
        print("✅ Magnitude model: FOUND") 
        print(f"   Size: {magnitude_model.stat().st_size / 1024:.1f} KB")
        print(f"   Modified: {datetime.fromtimestamp(magnitude_model.stat().st_mtime)}")
    else:
        print("❌ Magnitude model: MISSING")
        return False
    
    # Check metadata
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            print("✅ Model metadata: FOUND")
            print(f"   Version: {metadata.get('version', 'Unknown')}")
            print(f"   Training Date: {metadata.get('training_date', 'Unknown')}")
            print(f"   Features: {len(metadata.get('feature_columns', []))}")
        except Exception as e:
            print(f"⚠️  Model metadata: ERROR reading file ({e})")
    else:
        print("❌ Model metadata: MISSING")
    
    return True

def check_database_connection():
    """Check if we can connect to the database"""
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_records = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database: Connected ({total_records:,} total records)")
        return True
    except Exception as e:
        print(f"❌ Database: Connection failed ({e})")
        return False

def check_todays_performance():
    """Check today's trading performance"""
    print_section("2. TODAY'S PERFORMANCE")
    
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        
        # Today's performance by action
        today_query = """
        SELECT 
            optimal_action,
            COUNT(*) as trades,
            ROUND(AVG(return_pct), 3) as avg_return,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as wins,
            ROUND(MIN(return_pct), 3) as min_return,
            ROUND(MAX(return_pct), 3) as max_return
        FROM enhanced_outcomes 
        WHERE DATE(prediction_timestamp) = DATE('now')
        GROUP BY optimal_action
        ORDER BY trades DESC
        """
        
        cursor = conn.cursor()
        results = cursor.execute(today_query).fetchall()
        
        if results:
            print("Action      Trades  Avg Return  Win Rate  Confidence  Min/Max Return")
            print("-" * 70)
            
            total_trades = 0
            total_wins = 0
            weighted_return = 0
            
            for row in results:
                action, trades, avg_ret, confidence, wins, min_ret, max_ret = row
                win_rate = (wins / trades * 100) if trades > 0 else 0
                
                print(f"{action:<10} {trades:>6}  {avg_ret:>8.3f}%  {win_rate:>6.1f}%  {confidence:>9.3f}  {min_ret:>6.3f}%/{max_ret:>6.3f}%")
                
                total_trades += trades
                total_wins += wins
                weighted_return += avg_ret * trades
            
            if total_trades > 0:
                overall_win_rate = total_wins / total_trades * 100
                overall_avg_return = weighted_return / total_trades
                print("-" * 70)
                print(f"{'TOTAL':<10} {total_trades:>6}  {overall_avg_return:>8.3f}%  {overall_win_rate:>6.1f}%")
        else:
            print("No trades recorded for today")
        
        # Check for any prediction errors
        error_query = """
        SELECT COUNT(*) as error_count
        FROM enhanced_outcomes 
        WHERE DATE(prediction_timestamp) = DATE('now')
        AND (confidence_score = 0 OR confidence_score IS NULL)
        """
        
        error_count = cursor.execute(error_query).fetchone()[0]
        if error_count > 0:
            print(f"\n⚠️  WARNING: {error_count} predictions with zero/null confidence detected!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking today's performance: {e}")

def check_weekly_trends():
    """Check 7-day performance trends"""
    print_section("3. WEEKLY PERFORMANCE TRENDS")
    
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        
        # 7-day performance by action
        weekly_query = """
        SELECT 
            optimal_action,
            COUNT(*) as trades,
            ROUND(AVG(return_pct), 3) as avg_return,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM enhanced_outcomes 
        WHERE prediction_timestamp >= datetime('now', '-7 days')
        AND return_pct IS NOT NULL
        GROUP BY optimal_action
        ORDER BY trades DESC
        """
        
        results = conn.execute(weekly_query).fetchall()
        
        if results:
            print("7-DAY PERFORMANCE BY ACTION:")
            print("Action      Trades  Avg Return  Win Rate  Confidence")
            print("-" * 55)
            
            for row in results:
                action, trades, avg_ret, confidence, win_rate = row
                status = "✅" if win_rate > 55 else "⚠️" if win_rate > 45 else "❌"
                print(f"{status} {action:<10} {trades:>6}  {avg_ret:>8.3f}%  {win_rate:>6.1f}%  {confidence:>9.3f}")
        
        # Daily breakdown
        daily_query = """
        SELECT 
            DATE(prediction_timestamp) as date,
            COUNT(*) as trades,
            ROUND(AVG(return_pct), 3) as avg_return,
            SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM enhanced_outcomes 
        WHERE prediction_timestamp >= datetime('now', '-7 days')
        AND return_pct IS NOT NULL
        GROUP BY DATE(prediction_timestamp)
        ORDER BY date DESC
        """
        
        daily_results = conn.execute(daily_query).fetchall()
        
        if daily_results:
            print(f"\nDAILY BREAKDOWN (Last 7 Days):")
            print("Date       Trades  Avg Return  Win Rate")
            print("-" * 40)
            
            for row in daily_results:
                date, trades, avg_ret, win_rate = row
                status = "✅" if win_rate > 55 else "⚠️" if win_rate > 45 else "❌"
                print(f"{status} {date}  {trades:>6}  {avg_ret:>8.3f}%  {win_rate:>6.1f}%")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking weekly trends: {e}")

def check_data_quality():
    """Check training data quality and bias"""
    print_section("4. DATA QUALITY ASSESSMENT")
    
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        
        # Check for training data bias
        bias_query = """
        SELECT 
            AVG(CASE WHEN price_direction_1h = 1 THEN 1.0 ELSE 0.0 END) * 100 as bullish_1h,
            AVG(CASE WHEN price_direction_4h = 1 THEN 1.0 ELSE 0.0 END) * 100 as bullish_4h,
            AVG(CASE WHEN price_direction_1d = 1 THEN 1.0 ELSE 0.0 END) * 100 as bullish_1d,
            COUNT(*) as total_samples
        FROM enhanced_outcomes 
        WHERE created_at >= datetime('now', '-7 days')
        """
        
        row = conn.execute(bias_query).fetchone()
        
        if row and row[3] > 0:  # If we have samples
            bullish_1h, bullish_4h, bullish_1d, total_samples = row
            
            print(f"Training Data (Last 7 Days): {total_samples:,} samples")
            print(f"Bullish Prediction Bias:")
            print(f"  1h: {bullish_1h:.1f}% {'✅' if 40 <= bullish_1h <= 60 else '⚠️'}")
            print(f"  4h: {bullish_4h:.1f}% {'✅' if 40 <= bullish_4h <= 60 else '⚠️'}")
            print(f"  1d: {bullish_1d:.1f}% {'✅' if 40 <= bullish_1d <= 60 else '⚠️'}")
            print("Healthy range: 40-60% bullish")
            
            # Warnings for extreme bias
            if bullish_1h < 20 or bullish_1h > 80:
                print("❌ CRITICAL: Extreme bias in 1h predictions!")
            if bullish_4h < 20 or bullish_4h > 80:
                print("❌ CRITICAL: Extreme bias in 4h predictions!")
            if bullish_1d < 20 or bullish_1d > 80:
                print("❌ CRITICAL: Extreme bias in 1d predictions!")
        
        # Check data freshness
        freshness_query = """
        SELECT 
            MIN(created_at) as oldest,
            MAX(created_at) as newest,
            COUNT(*) as total
        FROM enhanced_outcomes 
        WHERE created_at >= datetime('now', '-1 days')
        """
        
        fresh_row = conn.execute(freshness_query).fetchone()
        if fresh_row:
            oldest, newest, count = fresh_row
            print(f"\nData Freshness (Last 24h): {count} new samples")
            if newest:
                newest_time = datetime.fromisoformat(newest.replace('Z', '+00:00'))
                hours_ago = (datetime.now() - newest_time).total_seconds() / 3600
                print(f"Most recent: {hours_ago:.1f} hours ago {'✅' if hours_ago < 12 else '⚠️'}")
        
        # Check for missing features
        feature_query = """
        SELECT 
            SUM(CASE WHEN sentiment_score IS NULL THEN 1 ELSE 0 END) as missing_sentiment,
            SUM(CASE WHEN confidence IS NULL THEN 1 ELSE 0 END) as missing_confidence,
            SUM(CASE WHEN rsi IS NULL THEN 1 ELSE 0 END) as missing_rsi,
            COUNT(*) as total
        FROM enhanced_features ef
        JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.created_at >= datetime('now', '-7 days')
        """
        
        feature_row = conn.execute(feature_query).fetchone()
        if feature_row and feature_row[3] > 0:
            missing_sent, missing_conf, missing_rsi, total = feature_row
            missing_pct = (missing_sent + missing_conf + missing_rsi) / (total * 3) * 100
            print(f"\nFeature Completeness: {100-missing_pct:.1f}% {'✅' if missing_pct < 5 else '⚠️'}")
            if missing_pct > 5:
                print(f"  Missing sentiment: {missing_sent}/{total} ({missing_sent/total*100:.1f}%)")
                print(f"  Missing confidence: {missing_conf}/{total} ({missing_conf/total*100:.1f}%)")
                print(f"  Missing RSI: {missing_rsi}/{total} ({missing_rsi/total*100:.1f}%)")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking data quality: {e}")

def check_model_predictions():
    """Test if models can make predictions"""
    print_section("5. MODEL PREDICTION TEST")
    
    try:
        # Try to import and test the prediction pipeline
        sys.path.append('.')
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        
        pipeline = EnhancedMLTrainingPipeline()
        
        # Test with dummy sentiment data
        dummy_sentiment = {
            'overall_sentiment': 0.2,
            'confidence': 0.7,
            'news_count': 5,
            'reddit_sentiment': {'average_sentiment': 0.1},
            'sentiment_components': {'events': 0.3}
        }
        
        # Test prediction for a common ASX stock
        test_symbol = "CBA.AX"
        result = pipeline.predict_enhanced(dummy_sentiment, test_symbol)
        
        if 'error' in result:
            print(f"❌ Prediction test FAILED: {result['error']}")
            if 'requires_manual_analysis' in result:
                print("   → Missing model files detected")
            elif 'requires_model_retraining' in result:
                print("   → Model corruption detected")
        else:
            print(f"✅ Prediction test PASSED for {test_symbol}")
            print(f"   Action: {result.get('optimal_action', 'Unknown')}")
            print(f"   Confidence: {result.get('confidence_scores', {}).get('average', 0):.3f}")
            
            # Check if we're getting reasonable values
            avg_conf = result.get('confidence_scores', {}).get('average', 0)
            if avg_conf > 0.3:
                print("   → Model confidence looks healthy")
            else:
                print("   → ⚠️ Low model confidence detected")
        
    except ImportError as e:
        print(f"❌ Cannot import ML pipeline: {e}")
    except Exception as e:
        print(f"❌ Prediction test error: {e}")

def check_training_logs():
    """Check recent training activity in logs"""
    print_section("6. TRAINING ACTIVITY CHECK")
    
    log_files = ["logs/app.log", "app.log", "trading.log"]
    found_logs = False
    
    for log_file in log_files:
        if os.path.exists(log_file):
            found_logs = True
            print(f"Checking {log_file}...")
            
            try:
                # Check last 100 lines for training activity
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                
                training_mentions = 0
                error_mentions = 0
                
                for line in recent_lines:
                    if any(keyword in line.lower() for keyword in ['training', 'enhanced.*trained', 'evening']):
                        training_mentions += 1
                        # Print recent training activity
                        if training_mentions <= 3:  # Show last 3 training mentions
                            print(f"   {line.strip()}")
                    
                    if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                        error_mentions += 1
                
                if training_mentions > 0:
                    print(f"✅ Training activity found ({training_mentions} mentions)")
                else:
                    print("⚠️ No recent training activity found")
                
                if error_mentions > 0:
                    print(f"⚠️ {error_mentions} errors/exceptions in recent logs")
                
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
            
            break
    
    if not found_logs:
        print("⚠️ No log files found")

def generate_summary():
    """Generate an overall system health summary"""
    print_section("7. SYSTEM HEALTH SUMMARY")
    
    # This is a simple health check based on what we've observed
    health_score = 0
    max_score = 6
    
    # Check 1: Model files exist
    models_dir = Path("data/ml_models/models")
    if (models_dir / "current_direction_model.pkl").exists() and (models_dir / "current_magnitude_model.pkl").exists():
        health_score += 1
        print("✅ Model files: Present")
    else:
        print("❌ Model files: Missing")
    
    # Check 2: Database accessible
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        conn.execute("SELECT 1 FROM enhanced_outcomes LIMIT 1")
        conn.close()
        health_score += 1
        print("✅ Database: Accessible")
    except:
        print("❌ Database: Inaccessible")
    
    # Check 3: Recent data
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        result = conn.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE created_at >= datetime('now', '-24 hours')").fetchone()
        if result[0] > 0:
            health_score += 1
            print("✅ Data freshness: Recent data available")
        else:
            print("❌ Data freshness: No recent data")
        conn.close()
    except:
        print("❌ Data freshness: Cannot check")
    
    # Check 4: Model prediction capability
    try:
        sys.path.append('.')
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        pipeline = EnhancedMLTrainingPipeline()
        dummy_sentiment = {'overall_sentiment': 0.1, 'confidence': 0.5, 'news_count': 1, 'reddit_sentiment': {'average_sentiment': 0}, 'sentiment_components': {'events': 0}}
        result = pipeline.predict_enhanced(dummy_sentiment, "CBA.AX")
        if 'error' not in result:
            health_score += 1
            print("✅ Predictions: Working")
        else:
            print("❌ Predictions: Failing")
    except:
        print("❌ Predictions: Cannot test")
    
    # Check 5: Performance quality (if we have recent data)
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        result = conn.execute("""
            SELECT AVG(CASE WHEN return_pct > 0 THEN 1.0 ELSE 0.0 END) * 100 
            FROM enhanced_outcomes 
            WHERE prediction_timestamp >= datetime('now', '-7 days') 
            AND return_pct IS NOT NULL
        """).fetchone()
        
        if result[0] is not None and result[0] > 45:
            health_score += 1
            print(f"✅ Performance: {result[0]:.1f}% win rate")
        elif result[0] is not None:
            print(f"⚠️ Performance: {result[0]:.1f}% win rate (below 45%)")
        else:
            print("❓ Performance: No recent data to assess")
        conn.close()
    except:
        print("❌ Performance: Cannot assess")
    
    # Check 6: Training data balance
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        result = conn.execute("""
            SELECT AVG(CASE WHEN price_direction_1d = 1 THEN 1.0 ELSE 0.0 END) * 100 
            FROM enhanced_outcomes 
            WHERE created_at >= datetime('now', '-7 days')
        """).fetchone()
        
        if result[0] is not None and 40 <= result[0] <= 60:
            health_score += 1
            print(f"✅ Data balance: {result[0]:.1f}% bullish (healthy)")
        elif result[0] is not None:
            print(f"⚠️ Data balance: {result[0]:.1f}% bullish (biased)")
        else:
            print("❓ Data balance: No recent data")
        conn.close()
    except:
        print("❌ Data balance: Cannot check")
    
    # Overall assessment
    health_percentage = (health_score / max_score) * 100
    
    print(f"\nOVERALL SYSTEM HEALTH: {health_score}/{max_score} ({health_percentage:.0f}%)")
    
    if health_percentage >= 80:
        print("🟢 EXCELLENT: System operating normally")
    elif health_percentage >= 60:
        print("🟡 GOOD: Minor issues detected")
    elif health_percentage >= 40:
        print("🟠 FAIR: Several issues need attention")
    else:
        print("🔴 POOR: Major issues require immediate attention")

def main():
    """Main function to run all checks"""
    print_header(f"ML TRADING SYSTEM - EVENING REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print(f"Report for: {datetime.now().strftime('%A, %B %d, %Y')}")
    
    # Run all checks
    if not check_database_connection():
        print("\n❌ Cannot continue - database connection failed")
        return
    
    if not check_model_status():
        print("\n❌ Critical: Model files missing - system cannot make predictions")
    
    check_todays_performance()
    check_weekly_trends()
    check_data_quality()
    check_model_predictions()
    check_training_logs()
    generate_summary()
    
    print_header("REPORT COMPLETE")
    print("Next steps:")
    print("• Review any warnings (⚠️) or errors (❌) above")
    print("• If health score <60%, investigate issues before trading")
    print("• Check again tomorrow evening for trends")
    print("• Full guide available in: ML_MODEL_TESTING_GUIDE.md")

if __name__ == "__main__":
    main()
