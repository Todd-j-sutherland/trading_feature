#!/usr/bin/env python3
"""
Demo script to show ML Performance Metrics that will be displayed in Enhanced Dashboard
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def load_ml_performance_data():
    """Load ML performance data from JSON files"""
    data_dir = Path("data/ml_performance")
    
    # Load performance history
    perf_file = data_dir / "ml_performance_history.json"
    model_file = data_dir / "model_metrics_history.json"
    
    performance_data = []
    model_metrics = []
    
    if perf_file.exists():
        with open(perf_file, 'r') as f:
            performance_data = json.load(f)
    
    if model_file.exists():
        with open(model_file, 'r') as f:
            model_metrics = json.load(f)
    
    return performance_data, model_metrics

def analyze_ml_performance():
    """Analyze and display ML performance metrics"""
    print("🧠 MACHINE LEARNING PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    performance_data, model_metrics = load_ml_performance_data()
    
    if not performance_data:
        print("❌ No ML performance data found")
        return
    
    # === ACCURACY & CONFIDENCE PROGRESSION ===
    print("\n📈 ACCURACY & CONFIDENCE PROGRESSION")
    print("-" * 40)
    
    recent_data = performance_data[-30:]  # Last 30 days
    
    print("Date          | Accuracy | Success Rate | Model Confidence | Predictions")
    print("-" * 75)
    
    total_accuracy = 0
    total_success = 0
    total_confidence = 0
    total_predictions = 0
    
    for entry in recent_data[-10:]:  # Show last 10 days
        date = entry['date']
        accuracy = entry.get('accuracy_metrics', {}).get('accuracy', 0) * 100
        success_rate = (entry['successful_trades'] / entry['total_trades']) * 100 if entry['total_trades'] > 0 else 0
        confidence = entry.get('model_confidence', 0) * 100
        predictions = entry.get('predictions_made', 0)
        
        print(f"{date} | {accuracy:6.1f}%  | {success_rate:9.1f}%  | {confidence:13.1f}%  | {predictions:10}")
        
        total_accuracy += accuracy
        total_success += success_rate
        total_confidence += confidence
        total_predictions += predictions
    
    # Calculate averages
    num_entries = len(recent_data[-10:])
    avg_accuracy = total_accuracy / num_entries if num_entries > 0 else 0
    avg_success = total_success / num_entries if num_entries > 0 else 0
    avg_confidence = total_confidence / num_entries if num_entries > 0 else 0
    
    print("-" * 75)
    print(f"{'AVERAGES':<13} | {avg_accuracy:6.1f}%  | {avg_success:9.1f}%  | {avg_confidence:13.1f}%  | {total_predictions:10}")
    
    # === MODEL TRAINING PROGRESS ===
    print("\n🎯 MODEL TRAINING PROGRESS")
    print("-" * 40)
    
    if model_metrics:
        print("Training Date | Validation Acc | Cross-Val Score | Training Samples")
        print("-" * 70)
        
        for entry in model_metrics[-5:]:  # Last 5 training sessions
            date = entry['timestamp'][:10]
            val_acc = entry.get('validation_accuracy', 0) * 100
            cv_score = entry.get('cross_validation_score', 0) * 100
            samples = entry.get('training_samples', 0)
            
            print(f"{date}   | {val_acc:12.2f}%  | {cv_score:13.2f}%  | {samples:14,}")
        
        # Latest model metrics
        latest_model = model_metrics[-1]
        print(f"\n🏆 Latest Model Performance:")
        print(f"   Validation Accuracy: {latest_model.get('validation_accuracy', 0) * 100:.2f}%")
        print(f"   Cross-Validation Score: {latest_model.get('cross_validation_score', 0) * 100:.2f}%")
        print(f"   Training Samples: {latest_model.get('training_samples', 0):,}")
        print(f"   Model Version: {latest_model.get('model_version', 'N/A')}")
    else:
        print("❌ No model training metrics found")
    
    # === TRADING PERFORMANCE ANALYSIS ===
    print("\n💹 TRADING PERFORMANCE ANALYSIS")
    print("-" * 40)
    
    # Overall statistics
    total_trades = sum(entry['total_trades'] for entry in performance_data)
    successful_trades = sum(entry['successful_trades'] for entry in performance_data)
    overall_success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
    
    print(f"📊 Overall Performance:")
    print(f"   Total Trades: {total_trades:,}")
    print(f"   Successful Trades: {successful_trades:,}")
    print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
    
    # Recent performance comparison
    recent_7days = performance_data[-7:]
    recent_trades = sum(entry['total_trades'] for entry in recent_7days)
    recent_successful = sum(entry['successful_trades'] for entry in recent_7days)
    recent_success_rate = (recent_successful / recent_trades * 100) if recent_trades > 0 else 0
    
    print(f"\n📈 Recent Performance (Last 7 Days):")
    print(f"   Recent Trades: {recent_trades:,}")
    print(f"   Recent Successful: {recent_successful:,}")
    print(f"   Recent Success Rate: {recent_success_rate:.1f}%")
    print(f"   Performance Change: {recent_success_rate - overall_success_rate:+.1f}%")
    
    # === DETAILED PERFORMANCE LOG ===
    print("\n📋 DETAILED PERFORMANCE LOG (Last 7 Days)")
    print("-" * 40)
    print("Date       | Predictions | Trades | Success | Rate  | Accuracy | Confidence")
    print("-" * 75)
    
    for entry in performance_data[-7:]:
        date = entry['date']
        predictions = entry.get('predictions_made', 0)
        trades = entry['total_trades']
        successful = entry['successful_trades']
        rate = (successful / trades * 100) if trades > 0 else 0
        accuracy = entry.get('accuracy_metrics', {}).get('accuracy', 0) * 100
        confidence = entry.get('model_confidence', 0) * 100
        
        print(f"{date} | {predictions:10} | {trades:6} | {successful:7} | {rate:4.1f}% | {accuracy:7.1f}% | {confidence:9.1f}%")

def show_dashboard_features():
    """Show what features are available in the enhanced dashboard"""
    print("\n🎨 ENHANCED DASHBOARD FEATURES")
    print("=" * 60)
    
    print("\n📊 Available in Enhanced Dashboard:")
    print("   ✅ Interactive Plotly Charts")
    print("      - Accuracy & Confidence Progression")
    print("      - Model Training Evolution")
    print("      - Performance Trends Over Time")
    
    print("\n   ✅ Real-time Metrics Cards")
    print("      - Current Accuracy with delta")
    print("      - Success Rate with trend")
    print("      - Model Confidence progression")
    print("      - 7-Day Prediction count")
    
    print("\n   ✅ Training Progress Visualization")
    print("      - Validation accuracy over time")
    print("      - Cross-validation scores")
    print("      - Training sample counts")
    print("      - Model version tracking")
    
    print("\n   ✅ Performance Analysis")
    print("      - Overall vs Recent comparison")
    print("      - Week-over-week trends")
    print("      - Success rate breakdown")
    print("      - Detailed performance logs")
    
    print("\n   ✅ Interactive Tables")
    print("      - Sortable performance data")
    print("      - Filterable by date range")
    print("      - Downloadable reports")

if __name__ == "__main__":
    try:
        analyze_ml_performance()
        show_dashboard_features()
        
        print("\n" + "=" * 60)
        print("💡 To see these metrics in the Enhanced Dashboard:")
        print("   1. Run: streamlit run app/dashboard/enhanced_main.py")
        print("   2. Navigate to the 'Learning Metrics' tab")
        print("   3. View interactive charts and real-time updates")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
