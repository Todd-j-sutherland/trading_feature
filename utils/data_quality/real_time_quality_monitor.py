#!/usr/bin/env python3
"""
Real-Time Trading System Quality Monitor
========================================

Monitor data quality metrics while the remote trading system is running.
Provides real-time insights into sentiment confidence, data freshness, 
technical indicators, and ML model performance.
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
import subprocess
import os

class RealTimeQualityMonitor:
    def __init__(self, remote_host="root@170.64.199.151", remote_path="/root/test"):
        self.remote_host = remote_host
        self.remote_path = remote_path
        
    def run_remote_query(self, query):
        """Execute SQL query on remote database"""
        cmd = f"ssh {self.remote_host} 'cd {self.remote_path} && sqlite3 data/trading_predictions.db \"{query}\"'"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Exception: {e}"
    
    def get_latest_quality_metrics(self):
        """Get the latest data quality metrics"""
        
        # Latest enhanced features (sentiment quality)
        features_query = """
        SELECT 
            symbol, 
            timestamp, 
            sentiment_score, 
            confidence, 
            news_count,
            current_price,
            rsi,
            volume_ratio,
            volatility_20d
        FROM enhanced_features 
        ORDER BY timestamp DESC 
        LIMIT 7;
        """
        
        # Latest morning analysis summary
        morning_query = """
        SELECT 
            timestamp,
            banks_analyzed,
            overall_sentiment,
            data_quality_scores
        FROM enhanced_morning_analysis 
        ORDER BY timestamp DESC 
        LIMIT 1;
        """
        
        # Enhanced outcomes quality
        outcomes_query = """
        SELECT COUNT(*) as total_outcomes,
               AVG(CASE WHEN exit_timestamp > prediction_timestamp THEN 1 ELSE 0 END) as temporal_quality
        FROM enhanced_outcomes;
        """
        
        features_data = self.run_remote_query(features_query)
        morning_data = self.run_remote_query(morning_query)
        outcomes_data = self.run_remote_query(outcomes_query)
        
        return {
            'features': features_data,
            'morning_analysis': morning_data,
            'outcomes_quality': outcomes_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_health(self):
        """Check overall system health"""
        
        health_query = """
        SELECT 
            'enhanced_features' as table_name,
            COUNT(*) as record_count,
            MAX(timestamp) as latest_record
        FROM enhanced_features
        UNION ALL
        SELECT 
            'enhanced_morning_analysis' as table_name,
            COUNT(*) as record_count,
            MAX(timestamp) as latest_record
        FROM enhanced_morning_analysis
        UNION ALL
        SELECT 
            'enhanced_outcomes' as table_name,
            COUNT(*) as record_count,
            MAX(timestamp) as latest_record
        FROM enhanced_outcomes;
        """
        
        return self.run_remote_query(health_query)
    
    def check_temporal_guard_status(self):
        """Check if temporal guard is passing"""
        
        guard_cmd = f"ssh {self.remote_host} 'cd {self.remote_path} && python3 morning_temporal_guard.py 2>&1 | grep -E \"PASSED|FAILED|ERROR\"'"
        try:
            result = subprocess.run(guard_cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error checking guard: {e}"
    
    def display_quality_dashboard(self):
        """Display a real-time quality dashboard"""
        
        print("🔍 REAL-TIME TRADING SYSTEM QUALITY MONITOR")
        print("=" * 60)
        print(f"⏰ Monitor Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # System Health
        print("🏥 SYSTEM HEALTH")
        print("-" * 30)
        health = self.get_system_health()
        for line in health.split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) == 3:
                    table, count, latest = parts
                    print(f"  {table:25} {count:>6} records (latest: {latest})")
        print()
        
        # Temporal Guard Status
        print("🛡️ TEMPORAL PROTECTION")
        print("-" * 30)
        guard_status = self.check_temporal_guard_status()
        if "PASSED" in guard_status:
            print("  ✅ All temporal checks PASSED")
        elif "FAILED" in guard_status:
            print("  ❌ Temporal checks FAILED")
        else:
            print(f"  ⚠️ Guard status: {guard_status}")
        print()
        
        # Latest Quality Metrics
        print("📊 LATEST QUALITY METRICS")
        print("-" * 30)
        metrics = self.get_latest_quality_metrics()
        
        if metrics['morning_analysis']:
            morning_parts = metrics['morning_analysis'].split('|')
            if len(morning_parts) >= 4:
                timestamp, banks, sentiment, quality_scores = morning_parts[:4]
                print(f"  Last Analysis: {timestamp}")
                print(f"  Banks Analyzed: {len(eval(banks))}")
                print(f"  Overall Sentiment: {float(sentiment):.4f}")
                
                # Parse quality scores
                try:
                    quality_dict = eval(quality_scores)
                    avg_quality = sum(quality_dict.values()) / len(quality_dict)
                    print(f"  Average Quality: {avg_quality:.1f}%")
                except:
                    print(f"  Quality Scores: {quality_scores}")
        print()
        
        # Latest Features Quality
        print("🔬 SENTIMENT & TECHNICAL QUALITY")
        print("-" * 30)
        if metrics['features']:
            print("  Symbol   Confidence  News  RSI     Vol Ratio  Sentiment")
            print("  " + "-" * 54)
            for line in metrics['features'].split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 8:
                        symbol, ts, sentiment, conf, news, price, rsi, vol_ratio = parts[:8]
                        print(f"  {symbol:8} {float(conf):>8.3f}  {news:>4}  {float(rsi):>6.1f}  {float(vol_ratio):>8.2f}  {float(sentiment):>8.4f}")
        print()
        
        # Outcomes Quality
        print("🎯 OUTCOMES QUALITY")
        print("-" * 30)
        if metrics['outcomes_quality']:
            outcomes_parts = metrics['outcomes_quality'].split('|')
            if len(outcomes_parts) >= 2:
                total, temporal = outcomes_parts[:2]
                print(f"  Total Outcomes: {total}")
                if temporal and temporal.strip():
                    try:
                        print(f"  Temporal Quality: {float(temporal):.1%}")
                    except ValueError:
                        print(f"  Temporal Quality: {temporal}")
                else:
                    print("  Temporal Quality: No data")
            else:
                print("  No outcomes data available")
        print()
    
    def monitor_continuous(self, interval_seconds=30):
        """Run continuous monitoring"""
        print("🚀 Starting continuous quality monitoring...")
        print(f"📡 Remote: {self.remote_host}:{self.remote_path}")
        print(f"🔄 Update interval: {interval_seconds} seconds")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                # Clear screen (works on Unix/Linux/Mac)
                os.system('clear')
                self.display_quality_dashboard()
                print(f"⏱️ Next update in {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
    
    def single_check(self):
        """Run a single quality check"""
        self.display_quality_dashboard()

def main():
    import sys
    
    monitor = RealTimeQualityMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = 30
        if len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
            except ValueError:
                print("Invalid interval, using 30 seconds")
        monitor.monitor_continuous(interval)
    else:
        print("📋 SINGLE QUALITY CHECK")
        print("=" * 60)
        monitor.single_check()
        print()
        print("💡 For continuous monitoring, run:")
        print("   python3 real_time_quality_monitor.py --continuous [seconds]")

if __name__ == "__main__":
    main()
