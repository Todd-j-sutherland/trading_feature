#!/usr/bin/env python3
"""
Dashboard Data Verification Script
Identifies where dashboard data is coming from and validates against expected sources
"""

import json
import os
from datetime import datetime
from pathlib import Path

def main():
    print("🔍 DASHBOARD DATA VERIFICATION")
    print("=" * 50)
    
    # Check prediction history file (what dashboard reads)
    pred_file = "data/ml_performance/prediction_history.json"
    if os.path.exists(pred_file):
        with open(pred_file, 'r') as f:
            pred_data = json.load(f)
        
        print(f"\n📊 PREDICTION HISTORY ({pred_file}):")
        print(f"   Total records: {len(pred_data)}")
        
        # Find today's records
        today = "2025-07-22"
        today_records = [p for p in pred_data if p['timestamp'].startswith(today)]
        print(f"   Today's records: {len(today_records)}")
        
        if today_records:
            print("\n   Today's Predictions:")
            for record in today_records[-5:]:  # Last 5
                timestamp = record['timestamp'][:16]
                symbol = record['symbol']
                signal = record['prediction']['signal']
                confidence = record['prediction']['confidence']
                status = record['status']
                print(f"   {timestamp} | {symbol} | {signal} | {confidence:.1%} | {status}")
    else:
        print(f"\n❌ PREDICTION HISTORY NOT FOUND: {pred_file}")
    
    # Check active signals (alternative source)
    signals_file = "data/ml_models/active_signals.json"
    if os.path.exists(signals_file):
        with open(signals_file, 'r') as f:
            signals_data = json.load(f)
        print(f"\n📈 ACTIVE SIGNALS ({signals_file}):")
        print(f"   Data: {signals_data}")
    else:
        print(f"\n❌ ACTIVE SIGNALS NOT FOUND: {signals_file}")
    
    # Check sentiment history (what evening routine should create)
    sentiment_dir = Path("data/sentiment_history")
    if sentiment_dir.exists():
        print(f"\n📰 SENTIMENT HISTORY ({sentiment_dir}):")
        sentiment_files = list(sentiment_dir.glob("*.json"))
        print(f"   Files found: {len(sentiment_files)}")
        
        for file in sentiment_files[-3:]:  # Last 3 files
            try:
                with open(file, 'r') as f:
                    sent_data = json.load(f)
                if isinstance(sent_data, list):
                    today_sent = [s for s in sent_data if s.get('timestamp', '').startswith(today)]
                    print(f"   {file.name}: {len(sent_data)} total, {len(today_sent)} today")
                    
                    # Check for ML predictions in sentiment data
                    if today_sent:
                        recent = today_sent[-1]
                        ml_prediction = recent.get('ml_prediction')
                        if ml_prediction:
                            confidence = ml_prediction.get('confidence', 0)
                            signal = ml_prediction.get('signal', 'N/A')
                            print(f"      Latest ML: {signal} @ {confidence:.1%}")
                        else:
                            print(f"      No ML prediction in sentiment data")
            except Exception as e:
                print(f"   {file.name}: Error reading - {e}")
    else:
        print(f"\n❌ SENTIMENT HISTORY NOT FOUND: {sentiment_dir}")
    
    # Check for recent ML performance files
    ml_perf_dir = Path("data/ml_performance")
    if ml_perf_dir.exists():
        print(f"\n🧠 ML PERFORMANCE ({ml_perf_dir}):")
        perf_files = list(ml_perf_dir.glob("*.json"))
        for file in perf_files:
            size = file.stat().st_size
            modified = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"   {file.name}: {size} bytes, modified {modified}")
    
    # Summary and recommendations
    print(f"\n💡 VERIFICATION SUMMARY:")
    print("   1. Dashboard reads from: data/ml_performance/prediction_history.json")
    print("   2. Evening routine creates sentiment data but may not update prediction history")
    print("   3. Need to check if ML predictions are being properly recorded")
    
    print(f"\n🔧 NEXT STEPS:")
    print("   1. Run evening routine and check if new predictions are recorded")
    print("   2. Verify MLProgressionTracker is being called during analysis")
    print("   3. Check if there's a disconnect between analysis and recording")

if __name__ == "__main__":
    main()
