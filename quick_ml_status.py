#!/usr/bin/env python3
"""
Quick ML Status Check - Works without heavy dependencies
"""
import json
import os
from datetime import datetime, timedelta

def check_ml_status():
    print("🧠 QUICK ML STATUS CHECK")
    print("="*50)
    
    # Check for ML performance data
    performance_file = "data_v2/data/ml_performance/ml_performance_history.json"
    metrics_file = "data_v2/data/ml_performance/model_metrics_history.json"
    
    if os.path.exists(performance_file):
        try:
            with open(performance_file, 'r') as f:
                data = json.load(f)
            
            print(f"📊 Performance Records: {len(data)} found")
            
            # Get latest performance
            if data:
                latest = data[-1]
                date = latest.get('date', 'Unknown')
                trades = latest.get('total_trades', 0)
                success = latest.get('successful_trades', 0)
                rate = latest.get('success_rate', 0)
                confidence = latest.get('avg_confidence', 0)
                
                print(f"📅 Latest: {date}")
                print(f"🎯 Trades: {trades} | Success: {success} | Rate: {rate:.1f}%")
                print(f"🔮 Confidence: {confidence:.1f}%")
                
                # Weekly summary
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                recent_trades = [d for d in data if d.get('date', '') >= week_ago]
                
                if recent_trades:
                    total_trades = sum(d.get('total_trades', 0) for d in recent_trades)
                    total_success = sum(d.get('successful_trades', 0) for d in recent_trades)
                    weekly_rate = (total_success / total_trades * 100) if total_trades > 0 else 0
                    
                    print(f"📈 This Week: {total_trades} trades, {weekly_rate:.1f}% success")
                
        except Exception as e:
            print(f"❌ Error reading performance data: {e}")
    else:
        print("❌ No ML performance data found")
    
    # Check for model metrics
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            
            print(f"🎯 Model Training Sessions: {len(metrics)}")
            
            if metrics:
                latest_model = metrics[-1]
                accuracy = latest_model.get('validation_accuracy', 0)
                cv_score = latest_model.get('cv_score', 0)
                samples = latest_model.get('training_samples', 0)
                
                print(f"🧠 Latest Model Accuracy: {accuracy:.2f}%")
                print(f"✅ Cross-Validation: {cv_score:.2f}%")
                print(f"📚 Training Samples: {samples}")
                
        except Exception as e:
            print(f"❌ Error reading model metrics: {e}")
    else:
        print("❌ No model metrics found")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    check_ml_status()
