#!/usr/bin/env python3
"""
Remote ML Performance Metrics Analysis
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def load_ml_performance_data():
    """Load ML performance data from JSON files on remote server"""
    # Try different possible data directories
    possible_dirs = [
        Path("data_v2/data/ml_performance"),
        Path("data_temp/ml_performance"),
        Path("data/ml_performance")
    ]
    
    performance_data = []
    model_metrics = []
    
    for data_dir in possible_dirs:
        perf_file = data_dir / "ml_performance_history.json"
        model_file = data_dir / "model_metrics_history.json"
        
        if perf_file.exists():
            print(f"📊 Found performance data: {perf_file}")
            with open(perf_file, 'r') as f:
                performance_data = json.load(f)
            break
    
    for data_dir in possible_dirs:
        model_file = data_dir / "model_metrics_history.json"
        if model_file.exists():
            print(f"🎯 Found model metrics: {model_file}")
            with open(model_file, 'r') as f:
                model_metrics = json.load(f)
            break
    
    return performance_data, model_metrics

def analyze_remote_ml_performance():
    """Analyze ML performance on remote server"""
    print("🧠 REMOTE ML PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    performance_data, model_metrics = load_ml_performance_data()
    
    if not performance_data:
        print("❌ No ML performance data found")
        # Try to find what files exist
        print("\n🔍 Searching for ML data files...")
        import os
        for root, dirs, files in os.walk("."):
            for file in files:
                if "ml_performance" in file or "model_metrics" in file:
                    print(f"   Found: {os.path.join(root, file)}")
        return
    
    print(f"📈 Loaded {len(performance_data)} performance records")
    print(f"🎯 Loaded {len(model_metrics)} model training sessions")
    
    # === CURRENT STATUS ===
    print("\n📊 CURRENT ML STATUS")
    print("-" * 40)
    
    latest_perf = performance_data[-1]
    print(f"Latest Date: {latest_perf['date']}")
    print(f"Total Trades: {latest_perf['total_trades']}")
    print(f"Successful: {latest_perf['successful_trades']}")
    success_rate = (latest_perf['successful_trades'] / latest_perf['total_trades']) * 100 if latest_perf['total_trades'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Model Confidence: {latest_perf.get('model_confidence', 0) * 100:.1f}%")
    
    # === RECENT PERFORMANCE ===
    print("\n📈 RECENT PERFORMANCE (Last 7 Days)")
    print("-" * 50)
    
    recent_data = performance_data[-7:]
    print("Date       | Trades | Success | Rate  | Confidence")
    print("-" * 50)
    
    total_recent_trades = 0
    total_recent_success = 0
    
    for entry in recent_data:
        date = entry['date']
        trades = entry['total_trades']
        successful = entry['successful_trades']
        rate = (successful / trades * 100) if trades > 0 else 0
        confidence = entry.get('model_confidence', 0) * 100
        
        print(f"{date} | {trades:6} | {successful:7} | {rate:4.1f}% | {confidence:9.1f}%")
        
        total_recent_trades += trades
        total_recent_success += successful
    
    recent_success_rate = (total_recent_success / total_recent_trades * 100) if total_recent_trades > 0 else 0
    print("-" * 50)
    print(f"{'TOTALS':<10} | {total_recent_trades:6} | {total_recent_success:7} | {recent_success_rate:4.1f}%")
    
    # === MODEL TRAINING STATUS ===
    if model_metrics:
        print("\n🎯 MODEL TRAINING STATUS")
        print("-" * 40)
        
        latest_model = model_metrics[-1]
        print(f"Latest Training: {latest_model['timestamp'][:10]}")
        print(f"Validation Accuracy: {latest_model.get('validation_accuracy', 0) * 100:.2f}%")
        print(f"Cross-Validation: {latest_model.get('cross_validation_score', 0) * 100:.2f}%")
        print(f"Training Samples: {latest_model.get('training_samples', 0):,}")
        print(f"Model Version: {latest_model.get('model_version', 'N/A')}")
        
        print(f"\n📊 Training Sessions: {len(model_metrics)}")
        if len(model_metrics) >= 2:
            first_acc = model_metrics[0].get('validation_accuracy', 0) * 100
            latest_acc = latest_model.get('validation_accuracy', 0) * 100
            improvement = latest_acc - first_acc
            print(f"Accuracy Improvement: {improvement:+.2f}%")
    
    # === OVERALL STATISTICS ===
    print("\n💹 OVERALL STATISTICS")
    print("-" * 40)
    
    total_trades = sum(entry['total_trades'] for entry in performance_data)
    total_successful = sum(entry['successful_trades'] for entry in performance_data)
    overall_success_rate = (total_successful / total_trades * 100) if total_trades > 0 else 0
    
    print(f"Total Historical Trades: {total_trades:,}")
    print(f"Total Successful: {total_successful:,}")
    print(f"Overall Success Rate: {overall_success_rate:.1f}%")
    print(f"Data Period: {performance_data[0]['date']} to {performance_data[-1]['date']}")
    print(f"Days of Data: {len(performance_data)}")
    
    # === PERFORMANCE TRENDS ===
    print("\n📊 PERFORMANCE TRENDS")
    print("-" * 40)
    
    if len(performance_data) >= 14:
        week1_data = performance_data[-14:-7]
        week2_data = performance_data[-7:]
        
        week1_trades = sum(e['total_trades'] for e in week1_data)
        week1_success = sum(e['successful_trades'] for e in week1_data)
        week1_rate = (week1_success / week1_trades * 100) if week1_trades > 0 else 0
        
        week2_trades = sum(e['total_trades'] for e in week2_data)
        week2_success = sum(e['successful_trades'] for e in week2_data)
        week2_rate = (week2_success / week2_trades * 100) if week2_trades > 0 else 0
        
        trend_change = week2_rate - week1_rate
        trend_direction = "📈 Improving" if trend_change > 0 else "📉 Declining" if trend_change < 0 else "➡️ Stable"
        
        print(f"Week 1 (2 weeks ago): {week1_rate:.1f}% ({week1_success}/{week1_trades})")
        print(f"Week 2 (last week): {week2_rate:.1f}% ({week2_success}/{week2_trades})")
        print(f"Trend: {trend_direction} ({trend_change:+.1f}%)")

def check_ml_system_health():
    """Check if ML components are working properly"""
    print("\n🏥 ML SYSTEM HEALTH CHECK")
    print("=" * 60)
    
    # Check if ML tracker can be imported
    try:
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        print("✅ MLProgressionTracker: Available")
        
        # Try to initialize tracker
        tracker = MLProgressionTracker()
        print(f"✅ Tracker Initialized: {len(tracker.performance_history)} records")
        
        # Check if we can get progression summary
        summary = tracker.get_progression_summary(days=7)
        print(f"✅ Progression Summary: {len(summary)} metrics")
        
        return tracker
        
    except Exception as e:
        print(f"❌ ML Tracker Error: {e}")
        return None

def generate_remote_dashboard_command():
    """Generate command to run dashboard on remote server"""
    print("\n🚀 DASHBOARD DEPLOYMENT")
    print("=" * 60)
    
    print("To run the Enhanced Dashboard with ML metrics on this server:")
    print("")
    print("1. Install Streamlit (if not already installed):")
    print("   pip install streamlit plotly")
    print("")
    print("2. Run the Enhanced Dashboard:")
    print("   streamlit run app/dashboard/enhanced_main.py --server.port 8501 --server.address 0.0.0.0")
    print("")
    print("3. Access via browser:")
    print("   http://170.64.199.151:8501")
    print("")
    print("4. Navigate to 'Learning Metrics' tab for ML performance analysis")

if __name__ == "__main__":
    try:
        analyze_remote_ml_performance()
        ml_tracker = check_ml_system_health()
        generate_remote_dashboard_command()
        
        print("\n" + "=" * 60)
        print("✅ Remote ML Performance Analysis Complete")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
