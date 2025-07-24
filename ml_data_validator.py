#!/usr/bin/env python3
"""
ML Data Validation and Testing Script
Identifies and fixes issues with ML prediction data, model validation, and accuracy calculations
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from typing import Dict, List

def load_json_file(file_path: str) -> List[Dict]:
    """Load and validate JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return []

def validate_prediction_data():
    """Validate prediction history data"""
    print("🔍 Validating ML Prediction Data...")
    
    pred_file = "data/ml_performance/prediction_history.json"
    if not os.path.exists(pred_file):
        print(f"❌ Prediction file not found: {pred_file}")
        return
    
    predictions = load_json_file(pred_file)
    print(f"📊 Total predictions: {len(predictions)}")
    
    # Analyze prediction status
    pending_count = sum(1 for p in predictions if p.get('status') == 'pending')
    completed_count = sum(1 for p in predictions if p.get('status') == 'completed')
    
    print(f"⏳ Pending predictions: {pending_count}")
    print(f"✅ Completed predictions: {completed_count}")
    
    if pending_count > completed_count * 2:
        print("⚠️  WARNING: Too many pending predictions - actual outcomes not being updated!")
    
    # Check for data quality issues
    issues = []
    
    for i, pred in enumerate(predictions):
        # Check for invalid timestamps
        try:
            timestamp = datetime.fromisoformat(pred['timestamp'])
            hour = timestamp.hour
            if hour > 23 or hour < 0:
                issues.append(f"Invalid hour {hour} in prediction {pred.get('id', i)}")
        except Exception as e:
            issues.append(f"Invalid timestamp in prediction {pred.get('id', i)}: {e}")
        
        # Check for repeated confidence values
        conf = pred.get('prediction', {}).get('confidence', 0)
        if conf == 0.61:  # The suspicious repeated value
            issues.append(f"Suspicious repeated confidence 61% in {pred.get('id', i)}")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} data quality issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"   • {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
    
    return {
        'total': len(predictions),
        'pending': pending_count,
        'completed': completed_count,
        'issues': len(issues)
    }

def validate_model_metrics():
    """Validate model metrics data"""
    print("\n🔍 Validating ML Model Metrics...")
    
    metrics_file = "data/ml_performance/model_metrics_history.json"
    if not os.path.exists(metrics_file):
        print(f"❌ Model metrics file not found: {metrics_file}")
        return
    
    metrics = load_json_file(metrics_file)
    print(f"📊 Total model metrics entries: {len(metrics)}")
    
    if not metrics:
        print("❌ No model metrics found - models not being trained/validated!")
        return {'total': 0, 'zero_accuracy': 0}
    
    # Check for zero accuracy
    zero_accuracy_count = sum(1 for m in metrics if m.get('validation_accuracy', 0) == 0)
    
    print(f"🎯 Validation accuracy records: {len(metrics) - zero_accuracy_count}")
    print(f"❌ Zero accuracy records: {zero_accuracy_count}")
    
    if zero_accuracy_count > len(metrics) * 0.5:
        print("⚠️  WARNING: Most model metrics have 0% validation accuracy!")
    
    # Show recent accuracy values
    recent_metrics = sorted(metrics, key=lambda x: x.get('timestamp', ''))[-5:]
    print("\n📈 Recent validation accuracies:")
    for m in recent_metrics:
        acc = m.get('validation_accuracy', 0) * 100
        timestamp = m.get('timestamp', 'Unknown')[:16]
        print(f"   {timestamp}: {acc:.1f}%")
    
    return {
        'total': len(metrics),
        'zero_accuracy': zero_accuracy_count
    }

def validate_performance_history():
    """Validate performance history data"""
    print("\n🔍 Validating Performance History...")
    
    perf_file = "data/ml_performance/ml_performance_history.json"
    if not os.path.exists(perf_file):
        print(f"❌ Performance history file not found: {perf_file}")
        return
    
    performance = load_json_file(perf_file)
    print(f"📊 Total performance entries: {len(performance)}")
    
    # Check for realistic success rates
    unrealistic_rates = []
    for p in performance[-10:]:  # Check last 10 entries
        success_rate = p.get('success_rate', 0)
        total_trades = p.get('total_trades', 0)
        
        if success_rate == 0 and total_trades > 0:
            unrealistic_rates.append(f"0% success with {total_trades} trades")
        elif success_rate > 0.95:  # > 95% success
            unrealistic_rates.append(f"{success_rate*100:.1f}% success (too high)")
    
    if unrealistic_rates:
        print(f"⚠️  Unrealistic success rates found:")
        for rate in unrealistic_rates:
            print(f"   • {rate}")
    
    return {'total': len(performance), 'unrealistic': len(unrealistic_rates)}

def create_test_data_with_outcomes():
    """Create realistic test data with proper outcomes"""
    print("\n🔧 Creating realistic test predictions with outcomes...")
    
    test_predictions = []
    symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX']
    
    # Generate 20 test predictions with realistic outcomes
    for i in range(20):
        timestamp = datetime.now() - timedelta(hours=24-i)
        symbol = symbols[i % len(symbols)]
        
        # Generate realistic prediction
        confidence = np.random.uniform(0.55, 0.92)  # Varied confidence
        signal_prob = np.random.random()
        
        if signal_prob < 0.4:
            signal = 'BUY'
            # BUY signals should be more successful when price goes up
            price_change = np.random.uniform(-2.5, 4.0)  # Slight positive bias
        elif signal_prob < 0.7:
            signal = 'SELL'
            # SELL signals should be more successful when price goes down  
            price_change = np.random.uniform(-4.0, 2.5)  # Slight negative bias
        else:
            signal = 'HOLD'
            # HOLD signals should have smaller movements
            price_change = np.random.uniform(-1.5, 1.5)  # Small movements
        
        # Add some market noise
        price_change += np.random.normal(0, 0.5)
        
        prediction = {
            'id': f'TEST_{symbol}_{timestamp.strftime("%Y%m%d_%H%M%S")}',
            'timestamp': timestamp.isoformat(),
            'symbol': symbol,
            'prediction': {
                'signal': signal,
                'confidence': round(confidence, 4),
                'sentiment_score': round(np.random.uniform(-0.3, 0.3), 4),
                'pattern_strength': round(confidence * 0.8, 4)
            },
            'actual_outcome': {
                'price_change_percent': round(price_change, 4),
                'outcome_timestamp': (timestamp + timedelta(hours=6)).isoformat()
            },
            'status': 'completed'
        }
        
        test_predictions.append(prediction)
    
    # Save test predictions
    test_file = "data/ml_performance/test_predictions_with_outcomes.json"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w') as f:
        json.dump(test_predictions, f, indent=2)
    
    print(f"✅ Created {len(test_predictions)} test predictions with outcomes")
    print(f"💾 Saved to: {test_file}")
    
    # Calculate test success rate
    successful = 0
    for p in test_predictions:
        signal = p['prediction']['signal']
        price_change = p['actual_outcome']['price_change_percent']
        
        if signal == 'BUY' and price_change > 0:
            successful += 1
        elif signal == 'SELL' and price_change < 0:
            successful += 1
        elif signal == 'HOLD' and abs(price_change) < 2:
            successful += 1
    
    success_rate = (successful / len(test_predictions)) * 100
    print(f"📊 Test data success rate: {success_rate:.1f}%")
    
    return test_predictions

def create_realistic_model_metrics():
    """Create realistic model validation metrics"""
    print("\n🔧 Creating realistic model validation metrics...")
    
    metrics = []
    
    # Generate 30 days of realistic model training metrics
    for i in range(30):
        timestamp = datetime.now() - timedelta(days=29-i)
        
        # Simulate improving model over time
        base_accuracy = 0.45 + (i / 30) * 0.25  # 45% to 70% over time
        accuracy = base_accuracy + np.random.normal(0, 0.03)  # Add noise
        accuracy = max(0.35, min(0.85, accuracy))  # Realistic bounds
        
        metrics.append({
            'timestamp': timestamp.isoformat(),
            'model_type': 'random_forest',
            'metrics': {
                'accuracy': accuracy,
                'precision': accuracy + np.random.uniform(-0.05, 0.05),
                'recall': accuracy + np.random.uniform(-0.05, 0.05),
                'f1_score': accuracy + np.random.uniform(-0.03, 0.03)
            },
            'validation_accuracy': accuracy,
            'training_samples': np.random.randint(800, 1200),
            'features_used': np.random.randint(8, 15)
        })
    
    # Save model metrics
    metrics_file = "data/ml_performance/test_model_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    latest_acc = metrics[-1]['validation_accuracy'] * 100
    print(f"✅ Created {len(metrics)} realistic model metrics")
    print(f"📈 Latest validation accuracy: {latest_acc:.1f}%")
    print(f"💾 Saved to: {metrics_file}")
    
    return metrics

def run_comprehensive_validation():
    """Run complete validation of ML data"""
    print("🚀 Starting Comprehensive ML Data Validation\n")
    
    # Validate current data
    pred_results = validate_prediction_data()
    model_results = validate_model_metrics()
    perf_results = validate_performance_history()
    
    # Create test data if needed
    if model_results['zero_accuracy'] > 5:
        print("\n⚠️  Creating realistic model metrics due to zero accuracy issue...")
        create_realistic_model_metrics()
    
    if pred_results['pending'] > pred_results['completed']:
        print("\n⚠️  Creating test predictions with outcomes due to too many pending...")
        create_test_data_with_outcomes()
    
    # Summary
    print("\n" + "="*50)
    print("📋 VALIDATION SUMMARY")
    print("="*50)
    print(f"Predictions: {pred_results['total']} total, {pred_results['issues']} issues")
    print(f"Model Metrics: {model_results['total']} total, {model_results['zero_accuracy']} zero accuracy")
    print(f"Performance: {perf_results['total']} entries")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if pred_results['pending'] > pred_results['completed']:
        print("• Set up process to update pending predictions with actual outcomes")
    
    if model_results['zero_accuracy'] > 0:
        print("• Fix model training/validation pipeline")
    
    if pred_results['issues'] > 0:
        print("• Clean up data quality issues (invalid timestamps, repeated values)")
    
    print("\n✨ Run this script regularly to maintain data quality!")

if __name__ == "__main__":
    run_comprehensive_validation()
