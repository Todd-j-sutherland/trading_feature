#!/usr/bin/env python3
"""
Monitor training data collection progress
"""

import sqlite3
from datetime import datetime

def check_training_progress():
    print(f"📊 TRAINING DATA PROGRESS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 40)
    
    conn = sqlite3.connect("data/trading_predictions.db")
    cursor = conn.cursor()
    
    # Check recent predictions (last 7 days)
    cursor.execute("""
        SELECT predicted_action, COUNT(*) as count, model_version
        FROM predictions 
        WHERE prediction_timestamp >= datetime('now', '-7 days')
        GROUP BY predicted_action, model_version
        ORDER BY model_version, predicted_action
    """)
    
    results = cursor.fetchall()
    
    # Summary by model
    model_stats = {}
    for action, count, model in results:
        if model not in model_stats:
            model_stats[model] = {}
        model_stats[model][action] = count
    
    total_recent = 0
    for model, actions in model_stats.items():
        model_total = sum(actions.values())
        total_recent += model_total
        print(f"\n{model} (last 7 days): {model_total} predictions")
        
        for action, count in actions.items():
            pct = (count / model_total) * 100 if model_total > 0 else 0
            print(f"   {action}: {count} ({pct:.1f}%)")
    
    print(f"\nTOTAL RECENT: {total_recent} predictions")
    
    # Check if ready for retraining
    emergency_total = model_stats.get('simple_emergency_v1', {})
    emergency_count = sum(emergency_total.values())
    
    if emergency_count >= 20:
        buy_count = emergency_total.get('BUY', 0)
        sell_count = emergency_total.get('SELL', 0) 
        hold_count = emergency_total.get('HOLD', 0)
        
        if buy_count > 0 and sell_count > 0 and hold_count > 0:
            print("\n✅ READY FOR RETRAINING!")
            print("📝 Run: python3 manual_retrain_models.py")
        else:
            print("\n⚠️  Need more balanced data")
    else:
        print(f"\n📈 Progress: {emergency_count}/20 balanced predictions needed")
    
    conn.close()

if __name__ == '__main__':
    check_training_progress()
