#!/usr/bin/env python3
"""
Evening ML Model Performance Check with Historical Tracking
Stores results in JSON format for trend analysis.

Usage:
    python3 evening_ml_check_with_history.py
    
Or with SSH to remote server:
    ssh root@170.64.199.151 "cd /root/test && python3 evening_ml_check_with_history.py"
"""

import sqlite3
import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
RESULTS_DIR = Path("data/ml_performance_history")
RESULTS_FILE = RESULTS_DIR / "daily_performance.json"

def ensure_results_directory():
    """Create results directory if it doesn't exist"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_historical_results():
    """Load existing historical results"""
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load historical results: {e}")
            return {}
    return {}

def save_results(results):
    """Save results to JSON file"""
    ensure_results_directory()
    
    # Load existing results
    historical_data = load_historical_results()
    
    # Add today's results
    today = datetime.now().strftime('%Y-%m-%d')
    historical_data[today] = results
    
    # Keep only last 30 days to prevent file from growing too large
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    historical_data = {date: data for date, data in historical_data.items() if date >= cutoff_date}
    
    # Save to file
    try:
        with open(RESULTS_FILE, 'w') as f:
            json.dump(historical_data, f, indent=2, default=str)
        print(f"\n📊 Results saved to: {RESULTS_FILE}")
    except Exception as e:
        print(f"Error saving results: {e}")

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
    status = {
        "models_exist": False,
        "direction_model_size_kb": 0,
        "magnitude_model_size_kb": 0,
        "model_version": "unknown",
        "training_date": "unknown",
        "feature_count": 0
    }
    
    # Check if models exist
    direction_model = models_dir / "current_direction_model.pkl"
    magnitude_model = models_dir / "current_magnitude_model.pkl"
    metadata_file = models_dir / "current_enhanced_metadata.json"
    
    if direction_model.exists():
        print("✅ Direction model: FOUND")
        status["direction_model_size_kb"] = round(direction_model.stat().st_size / 1024, 1)
        print(f"   Size: {status['direction_model_size_kb']} KB")
        print(f"   Modified: {datetime.fromtimestamp(direction_model.stat().st_mtime)}")
    else:
        print("❌ Direction model: MISSING")
        return status
    
    if magnitude_model.exists():
        print("✅ Magnitude model: FOUND") 
        status["magnitude_model_size_kb"] = round(magnitude_model.stat().st_size / 1024, 1)
        print(f"   Size: {status['magnitude_model_size_kb']} KB")
        print(f"   Modified: {datetime.fromtimestamp(magnitude_model.stat().st_mtime)}")
        status["models_exist"] = True
    else:
        print("❌ Magnitude model: MISSING")
        return status
    
    # Check metadata
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            print("✅ Model metadata: FOUND")
            status["model_version"] = metadata.get('version', 'Unknown')
            status["training_date"] = metadata.get('training_date', 'Unknown')
            status["feature_count"] = len(metadata.get('feature_columns', []))
            print(f"   Version: {status['model_version']}")
            print(f"   Training Date: {status['training_date']}")
            print(f"   Features: {status['feature_count']}")
        except Exception as e:
            print(f"⚠️  Model metadata: ERROR reading file ({e})")
    else:
        print("❌ Model metadata: MISSING")
    
    return status

def check_database_connection():
    """Check if we can connect to the database"""
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_records = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database: Connected ({total_records:,} total records)")
        return True, total_records
    except Exception as e:
        print(f"❌ Database: Connection failed ({e})")
        return False, 0

def check_todays_performance():
    """Check today's trading performance"""
    print_section("2. TODAY'S PERFORMANCE")
    
    performance = {
        "total_trades": 0,
        "overall_win_rate": 0.0,
        "overall_avg_return": 0.0,
        "actions": {},
        "error_predictions": 0
    }
    
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
                
                # Store in performance dict
                performance["actions"][action] = {
                    "trades": trades,
                    "avg_return": float(avg_ret) if avg_ret is not None else 0.0,
                    "win_rate": float(win_rate),
                    "confidence": float(confidence) if confidence is not None else 0.0,
                    "min_return": float(min_ret) if min_ret is not None else 0.0,
                    "max_return": float(max_ret) if max_ret is not None else 0.0
                }
                
                total_trades += trades
                total_wins += wins
                weighted_return += (avg_ret or 0) * trades
            
            if total_trades > 0:
                performance["total_trades"] = total_trades
                performance["overall_win_rate"] = round(total_wins / total_trades * 100, 1)
                performance["overall_avg_return"] = round(weighted_return / total_trades, 3)
                
                print("-" * 70)
                print(f"{'TOTAL':<10} {total_trades:>6}  {performance['overall_avg_return']:>8.3f}%  {performance['overall_win_rate']:>6.1f}%")
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
        performance["error_predictions"] = error_count
        if error_count > 0:
            print(f"\n⚠️  WARNING: {error_count} predictions with zero/null confidence detected!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking today's performance: {e}")
    
    return performance

def check_weekly_trends():
    """Check 7-day performance trends"""
    print_section("3. WEEKLY PERFORMANCE TRENDS")
    
    weekly_performance = {
        "actions": {},
        "daily_breakdown": {}
    }
    
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
                
                # Store weekly performance
                weekly_performance["actions"][action] = {
                    "trades": trades,
                    "avg_return": float(avg_ret) if avg_ret is not None else 0.0,
                    "win_rate": float(win_rate),
                    "confidence": float(confidence) if confidence is not None else 0.0
                }
        
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
                
                # Store daily breakdown
                weekly_performance["daily_breakdown"][date] = {
                    "trades": trades,
                    "avg_return": float(avg_ret) if avg_ret is not None else 0.0,
                    "win_rate": float(win_rate)
                }
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking weekly trends: {e}")
    
    return weekly_performance

def check_data_quality():
    """Check training data quality and bias"""
    print_section("4. DATA QUALITY ASSESSMENT")
    
    data_quality = {
        "bias_1h": 0.0,
        "bias_4h": 0.0,
        "bias_1d": 0.0,
        "total_samples_7d": 0,
        "new_samples_24h": 0,
        "hours_since_last_data": 0.0,
        "feature_completeness": 100.0,
        "bias_warnings": []
    }
    
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
            
            data_quality.update({
                "bias_1h": round(bullish_1h, 1),
                "bias_4h": round(bullish_4h, 1),
                "bias_1d": round(bullish_1d, 1),
                "total_samples_7d": total_samples
            })
            
            print(f"Training Data (Last 7 Days): {total_samples:,} samples")
            print(f"Bullish Prediction Bias:")
            print(f"  1h: {bullish_1h:.1f}% {'✅' if 40 <= bullish_1h <= 60 else '⚠️'}")
            print(f"  4h: {bullish_4h:.1f}% {'✅' if 40 <= bullish_4h <= 60 else '⚠️'}")
            print(f"  1d: {bullish_1d:.1f}% {'✅' if 40 <= bullish_1d <= 60 else '⚠️'}")
            print("Healthy range: 40-60% bullish")
            
            # Check for warnings
            if bullish_1h < 20 or bullish_1h > 80:
                warning = "Extreme bias in 1h predictions"
                data_quality["bias_warnings"].append(warning)
                print(f"❌ CRITICAL: {warning}!")
            if bullish_4h < 20 or bullish_4h > 80:
                warning = "Extreme bias in 4h predictions"
                data_quality["bias_warnings"].append(warning)
                print(f"❌ CRITICAL: {warning}!")
            if bullish_1d < 20 or bullish_1d > 80:
                warning = "Extreme bias in 1d predictions"
                data_quality["bias_warnings"].append(warning)
                print(f"❌ CRITICAL: {warning}!")
        
        # Check data freshness
        freshness_query = """
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as newest
        FROM enhanced_outcomes 
        WHERE created_at >= datetime('now', '-1 days')
        """
        
        fresh_row = conn.execute(freshness_query).fetchone()
        if fresh_row:
            count, newest = fresh_row
            data_quality["new_samples_24h"] = count
            print(f"\nData Freshness (Last 24h): {count} new samples")
            if newest:
                try:
                    newest_time = datetime.fromisoformat(newest.replace('Z', '+00:00'))
                    hours_ago = (datetime.now() - newest_time).total_seconds() / 3600
                    data_quality["hours_since_last_data"] = round(hours_ago, 1)
                    print(f"Most recent: {hours_ago:.1f} hours ago {'✅' if hours_ago < 12 else '⚠️'}")
                except:
                    print(f"Most recent: {newest}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking data quality: {e}")
    
    return data_quality

def generate_health_summary():
    """Generate an overall system health summary"""
    print_section("5. SYSTEM HEALTH SUMMARY")
    
    health_metrics = {
        "health_score": 0,
        "max_score": 6,
        "status": "unknown",
        "checks": {}
    }
    
    health_score = 0
    max_score = 6
    
    # Check 1: Model files exist
    models_dir = Path("data/ml_models/models")
    if (models_dir / "current_direction_model.pkl").exists() and (models_dir / "current_magnitude_model.pkl").exists():
        health_score += 1
        health_metrics["checks"]["model_files"] = "present"
        print("✅ Model files: Present")
    else:
        health_metrics["checks"]["model_files"] = "missing"
        print("❌ Model files: Missing")
    
    # Check 2: Database accessible
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        conn.execute("SELECT 1 FROM enhanced_outcomes LIMIT 1")
        conn.close()
        health_score += 1
        health_metrics["checks"]["database"] = "accessible"
        print("✅ Database: Accessible")
    except:
        health_metrics["checks"]["database"] = "inaccessible"
        print("❌ Database: Inaccessible")
    
    # Check 3: Recent data
    try:
        conn = sqlite3.connect("data/trading_unified.db")
        result = conn.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE created_at >= datetime('now', '-24 hours')").fetchone()
        if result[0] > 0:
            health_score += 1
            health_metrics["checks"]["data_freshness"] = "recent"
            print("✅ Data freshness: Recent data available")
        else:
            health_metrics["checks"]["data_freshness"] = "stale"
            print("❌ Data freshness: No recent data")
        conn.close()
    except:
        health_metrics["checks"]["data_freshness"] = "error"
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
            health_metrics["checks"]["predictions"] = "working"
            print("✅ Predictions: Working")
        else:
            health_metrics["checks"]["predictions"] = "failing"
            print("❌ Predictions: Failing")
    except:
        health_metrics["checks"]["predictions"] = "error"
        print("❌ Predictions: Cannot test")
    
    # Check 5: Performance quality
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
            health_metrics["checks"]["performance"] = f"{result[0]:.1f}%"
            print(f"✅ Performance: {result[0]:.1f}% win rate")
        elif result[0] is not None:
            health_metrics["checks"]["performance"] = f"{result[0]:.1f}%_low"
            print(f"⚠️ Performance: {result[0]:.1f}% win rate (below 45%)")
        else:
            health_metrics["checks"]["performance"] = "no_data"
            print("❓ Performance: No recent data to assess")
        conn.close()
    except:
        health_metrics["checks"]["performance"] = "error"
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
            health_metrics["checks"]["data_balance"] = f"{result[0]:.1f}%_healthy"
            print(f"✅ Data balance: {result[0]:.1f}% bullish (healthy)")
        elif result[0] is not None:
            health_metrics["checks"]["data_balance"] = f"{result[0]:.1f}%_biased"
            print(f"⚠️ Data balance: {result[0]:.1f}% bullish (biased)")
        else:
            health_metrics["checks"]["data_balance"] = "no_data"
            print("❓ Data balance: No recent data")
        conn.close()
    except:
        health_metrics["checks"]["data_balance"] = "error"
        print("❌ Data balance: Cannot check")
    
    # Overall assessment
    health_percentage = (health_score / max_score) * 100
    
    health_metrics.update({
        "health_score": health_score,
        "health_percentage": round(health_percentage, 0)
    })
    
    print(f"\nOVERALL SYSTEM HEALTH: {health_score}/{max_score} ({health_percentage:.0f}%)")
    
    if health_percentage >= 80:
        status = "EXCELLENT"
        print("🟢 EXCELLENT: System operating normally")
    elif health_percentage >= 60:
        status = "GOOD"
        print("🟡 GOOD: Minor issues detected")
    elif health_percentage >= 40:
        status = "FAIR"
        print("🟠 FAIR: Several issues need attention")
    else:
        status = "POOR"
        print("🔴 POOR: Major issues require immediate attention")
    
    health_metrics["status"] = status
    return health_metrics

def main():
    """Main function to run all checks and save results"""
    print_header(f"ML TRADING SYSTEM - EVENING REPORT WITH HISTORY")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print(f"Report for: {datetime.now().strftime('%A, %B %d, %Y')}")
    
    # Initialize results structure
    results = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "report_version": "2.0"
    }
    
    # Run all checks and collect data
    db_connected, total_records = check_database_connection()
    if not db_connected:
        print("\n❌ Cannot continue - database connection failed")
        return
    
    results["database_records"] = total_records
    results["model_status"] = check_model_status()
    results["todays_performance"] = check_todays_performance()
    results["weekly_performance"] = check_weekly_trends()
    results["data_quality"] = check_data_quality()
    results["health_summary"] = generate_health_summary()
    
    # Save results to JSON
    save_results(results)
    
    print_header("REPORT COMPLETE")
    print("Results saved to JSON for historical tracking!")
    print("Next steps:")
    print("• Review any warnings (⚠️) or errors (❌) above")
    print("• If health score <60%, investigate issues before trading")
    print("• Check trends with: python3 view_ml_trends.py")
    print("• Full guide available in: ML_MODEL_TESTING_GUIDE.md")

if __name__ == "__main__":
    main()
