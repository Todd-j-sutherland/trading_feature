#!/usr/bin/env python3
"""
Quick fix for ML model bias - use traditional signals when ML is heavily biased
"""

import sqlite3
from datetime import datetime, timedelta

def detect_ml_bias():
    """Detect if ML model is showing excessive bias"""
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Check last 3 days of predictions
    cursor.execute('''
        SELECT predicted_action, COUNT(*) as count
        FROM predictions 
        WHERE prediction_timestamp >= date('now', '-3 days')
        GROUP BY predicted_action
    ''')
    
    action_counts = dict(cursor.fetchall())
    total = sum(action_counts.values())
    
    if total == 0:
        return False, "No recent predictions"
    
    buy_pct = (action_counts.get('BUY', 0) / total) * 100
    sell_pct = (action_counts.get('SELL', 0) / total) * 100
    hold_pct = (action_counts.get('HOLD', 0) / total) * 100
    
    print(f"📊 Last 3 days action distribution:")
    print(f"   BUY: {buy_pct:.1f}% ({action_counts.get('BUY', 0)} predictions)")
    print(f"   SELL: {sell_pct:.1f}% ({action_counts.get('SELL', 0)} predictions)")
    print(f"   HOLD: {hold_pct:.1f}% ({action_counts.get('HOLD', 0)} predictions)")
    print(f"   Total: {total} predictions")
    
    # Detect bias - healthy model should have some BUY signals
    bias_detected = False
    bias_reasons = []
    
    if buy_pct == 0 and total > 20:
        bias_detected = True
        bias_reasons.append("Zero BUY signals")
    
    if sell_pct > 85:
        bias_detected = True
        bias_reasons.append(f"Excessive SELL bias ({sell_pct:.1f}%)")
    
    if buy_pct < 5 and sell_pct > 75:
        bias_detected = True
        bias_reasons.append("Severely unbalanced predictions")
    
    conn.close()
    
    return bias_detected, bias_reasons

def main():
    print("🔍 ML MODEL BIAS DETECTION")
    print("=" * 30)
    
    bias_detected, reasons = detect_ml_bias()
    
    if bias_detected:
        print("🚨 ML MODEL BIAS DETECTED!")
        print("Reasons:")
        for reason in reasons:
            print(f"   - {reason}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Use traditional signals as primary")
        print("   2. Retrain ML model with recent data")
        print("   3. Add bias monitoring to system")
        print("   4. Review sentiment analysis pipeline")
        
        print("\n⚠️  Consider disabling ML predictions until model is retrained")
        
    else:
        print("✅ ML model appears balanced")
        if isinstance(reasons, str):
            print(f"Note: {reasons}")

if __name__ == "__main__":
    main()
