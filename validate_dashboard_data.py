#!/usr/bin/env python3
"""
Final Dashboard Data Validation
Tests the complete data flow to ensure dashboard shows correct information
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

def main():
    print("🎯 FINAL DASHBOARD DATA VALIDATION")
    print("=" * 50)
    
    # Load prediction history (what dashboard uses)
    pred_file = Path("data/ml_performance/prediction_history.json")
    
    if not pred_file.exists():
        print("❌ Prediction history file not found!")
        return
    
    with open(pred_file, 'r') as f:
        predictions = json.load(f)
    
    print(f"📊 PREDICTION HISTORY ANALYSIS:")
    print(f"   Total records: {len(predictions)}")
    
    # Filter today's records
    today = "2025-07-22"
    today_predictions = [p for p in predictions if p['timestamp'].startswith(today)]
    
    print(f"   Today's records: {len(today_predictions)}")
    
    if not today_predictions:
        print("⚠️ No predictions for today found!")
        return
    
    # Analyze confidence distribution
    confidences = [p['prediction']['confidence'] for p in today_predictions]
    unique_confidences = sorted(set(confidences))
    
    print(f"\n📈 CONFIDENCE ANALYSIS:")
    print(f"   Unique confidence values: {len(unique_confidences)}")
    print(f"   Range: {min(confidences):.1%} to {max(confidences):.1%}")
    print(f"   Values: {[f'{c:.1%}' for c in unique_confidences]}")
    
    # Check for uniform values (the original problem)
    if len(unique_confidences) == 1:
        print(f"   🚨 WARNING: All confidence values are identical ({unique_confidences[0]:.1%})")
    elif len(unique_confidences) <= 2:
        print(f"   ⚠️ CAUTION: Very low diversity ({len(unique_confidences)} unique values)")
    else:
        print(f"   ✅ GOOD: Diverse confidence values ({len(unique_confidences)} unique)")
    
    # Analyze signals
    signals = [p['prediction']['signal'] for p in today_predictions]
    signal_counts = Counter(signals)
    
    print(f"\n🎯 SIGNAL ANALYSIS:")
    for signal, count in signal_counts.items():
        print(f"   {signal}: {count} predictions")
    
    # Analyze timestamps 
    timestamps = [p['timestamp'] for p in today_predictions]
    times = [t.split('T')[1][:5] for t in timestamps]  # Extract HH:MM
    
    print(f"\n⏰ TIME DISTRIBUTION:")
    print(f"   Time range: {min(times)} to {max(times)}")
    print(f"   All times: {times}")
    
    # Check for duplicates (another original problem)
    time_counts = Counter(times)
    duplicated_times = {time: count for time, count in time_counts.items() if count > 1}
    
    if duplicated_times:
        print(f"   🚨 DUPLICATE TIMESTAMPS FOUND:")
        for time, count in duplicated_times.items():
            print(f"      {time}: {count} predictions")
    else:
        print(f"   ✅ No duplicate timestamps")
    
    # Display sample records for verification
    print(f"\n📋 SAMPLE PREDICTIONS (Dashboard Format):")
    print("   Date       Time   Symbol    Signal  Confidence  Sentiment   Status")
    print("   " + "-" * 65)
    
    for pred in today_predictions[:10]:  # Show first 10
        date = pred['timestamp'][:10]
        time = pred['timestamp'][11:16]
        symbol = pred['symbol']
        signal = pred['prediction']['signal']
        confidence = pred['prediction']['confidence']
        sentiment = pred['prediction'].get('sentiment_score', 0)
        status = pred['status']
        
        print(f"   {date}    {time}   {symbol:8} {signal:6}  {confidence:8.1%}    {sentiment:+.3f}   {status}")
    
    # Final assessment
    print(f"\n🏆 FINAL ASSESSMENT:")
    
    issues = []
    
    if len(unique_confidences) == 1:
        issues.append("All confidence values are identical")
    
    if duplicated_times:
        issues.append("Duplicate timestamps found")
    
    if all(s == 'HOLD' for s in signals):
        issues.append("All signals are HOLD (may be expected)")
    
    if issues:
        print("   ⚠️ POTENTIAL ISSUES:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ ALL CHECKS PASSED")
    
    print(f"\n🎯 DASHBOARD READINESS:")
    if len(unique_confidences) > 2 and not duplicated_times:
        print("   ✅ READY - Dashboard should show diverse, correct data")
    else:
        print("   ⚠️ NEEDS ATTENTION - Some data quality issues remain")
    
    # Instructions for dashboard testing
    print(f"\n📱 TESTING INSTRUCTIONS:")
    print("   1. Start dashboard: python -m streamlit run app/dashboard/enhanced_main.py")
    print("   2. Check 'Trading Performance' section")
    print("   3. Verify confidence values are diverse (not all 61%)")
    print("   4. Confirm no duplicate entries for same time/symbol")
    print("   5. Look for today's predictions with correct timestamps")

if __name__ == "__main__":
    main()
