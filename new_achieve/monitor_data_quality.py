#!/usr/bin/env python3
"""
Data Quality Monitoring Script
Tracks real vs synthetic data ratio and system health
"""

import sqlite3
from datetime import datetime

def monitor_data_quality():
    """Monitor the health and composition of training data"""
    conn = sqlite3.connect("data/ml_models/enhanced_training_data.db")
    cursor = conn.cursor()
    
    # Get synthetic vs real outcome ratio
    cursor.execute("""
        SELECT 
            COUNT(*) as total_outcomes,
            COUNT(CASE WHEN exit_timestamp = prediction_timestamp THEN 1 END) as synthetic_outcomes
        FROM enhanced_outcomes
    """)
    
    total, synthetic = cursor.fetchone()
    real_outcomes = total - synthetic
    synthetic_ratio = (synthetic / total * 100) if total > 0 else 0
    
    print(f"📊 Data Quality Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Total Outcomes: {total}")
    print(f"   Real Outcomes: {real_outcomes} ({100-synthetic_ratio:.1f}%)")
    print(f"   Synthetic Outcomes: {synthetic} ({synthetic_ratio:.1f}%)")
    
    # Check data availability by time horizon
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN price_direction_1h IS NOT NULL THEN 1 END) as with_1h,
            COUNT(CASE WHEN price_direction_4h IS NOT NULL THEN 1 END) as with_4h,
            COUNT(CASE WHEN price_direction_1d IS NOT NULL THEN 1 END) as with_1d
        FROM enhanced_outcomes
    """)
    
    h1_count, h4_count, d1_count = cursor.fetchone()
    print(f"\n🕒 Time Horizon Coverage:")
    print(f"   1-Hour Data: {h1_count} outcomes ({h1_count/total*100:.1f}%)")
    print(f"   4-Hour Data: {h4_count} outcomes ({h4_count/total*100:.1f}%)")
    print(f"   1-Day Data: {d1_count} outcomes ({d1_count/total*100:.1f}%)")
    
    # Get latest model performance
    cursor.execute("""
        SELECT direction_accuracy_1h, direction_accuracy_4h, direction_accuracy_1d,
               magnitude_mae_1h, magnitude_mae_4h, magnitude_mae_1d, training_samples
        FROM model_performance_enhanced 
        ORDER BY created_at DESC LIMIT 1
    """)
    
    perf = cursor.fetchone()
    if perf:
        print(f"\n🎯 Latest Model Performance:")
        print(f"   Direction Accuracy:")
        print(f"     • 1-Hour: {perf[0]*100:.1f}% {'✅' if perf[0] >= 0.60 else '❌'}")
        print(f"     • 4-Hour: {perf[1]*100:.1f}% {'✅' if perf[1] >= 0.60 else '❌'}")
        print(f"     • 1-Day:  {perf[2]*100:.1f}% {'✅' if perf[2] >= 0.60 else '❌'}")
        print(f"   Magnitude MAE:")
        print(f"     • 1-Hour: {perf[3]*100:.2f}% {'✅' if perf[3] <= 0.02 else '❌'}")
        print(f"     • 4-Hour: {perf[4]*100:.2f}% {'✅' if perf[4] <= 0.02 else '❌'}")
        print(f"     • 1-Day:  {perf[5]*100:.2f}% {'✅' if perf[5] <= 0.02 else '❌'}")
        print(f"   Training Samples: {perf[6]} {'✅' if perf[6] >= 50 else '❌'}")
    
    # Health assessment
    if synthetic_ratio < 30:
        print("\n   Overall Status: ✅ HEALTHY - Majority real data")
    elif synthetic_ratio < 60:
        print("\n   Overall Status: 🟡 TRANSITIONAL - Mixed data composition")
    else:
        print("\n   Overall Status: ⚠️ SYNTHETIC HEAVY - Need more real data")
    
    conn.close()
    return synthetic_ratio < 50

if __name__ == "__main__":
    monitor_data_quality()
