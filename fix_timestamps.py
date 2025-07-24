#!/usr/bin/env python3
"""
Fix Duplicate Timestamps in Dashboard Data
Adjusts timestamps to ensure each prediction has a unique time
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def main():
    print("🔧 FIXING DUPLICATE TIMESTAMPS")
    print("=" * 40)
    
    # Load prediction history
    pred_file = Path("data/ml_performance/prediction_history.json")
    
    with open(pred_file, 'r') as f:
        predictions = json.load(f)
    
    # Find today's predictions
    today = "2025-07-22"
    today_predictions = [p for p in predictions if p['timestamp'].startswith(today)]
    other_predictions = [p for p in predictions if not p['timestamp'].startswith(today)]
    
    print(f"📊 Found {len(today_predictions)} predictions for today")
    
    # Group by timestamp to find duplicates
    timestamp_groups = {}
    for pred in today_predictions:
        ts = pred['timestamp']
        if ts not in timestamp_groups:
            timestamp_groups[ts] = []
        timestamp_groups[ts].append(pred)
    
    # Fix duplicates by adding small time offsets
    fixed_predictions = []
    
    for timestamp, preds in timestamp_groups.items():
        if len(preds) == 1:
            # No duplicates
            fixed_predictions.extend(preds)
        else:
            # Fix duplicates
            print(f"🔄 Fixing {len(preds)} duplicate predictions at {timestamp[:16]}")
            
            base_time = datetime.fromisoformat(timestamp)
            
            for i, pred in enumerate(preds):
                if i == 0:
                    # Keep first one as-is
                    fixed_predictions.append(pred)
                    print(f"   ✅ {pred['symbol']}: {timestamp[:16]} (unchanged)")
                else:
                    # Add small offset for others
                    offset_minutes = i * 2  # 2 minutes between each
                    new_time = base_time + timedelta(minutes=offset_minutes)
                    new_timestamp = new_time.isoformat()
                    
                    pred['timestamp'] = new_timestamp
                    fixed_predictions.append(pred)
                    print(f"   ✅ {pred['symbol']}: {new_timestamp[:16]} (+{offset_minutes}min)")
    
    # Combine fixed today predictions with other predictions
    all_predictions = other_predictions + fixed_predictions
    
    # Create backup before saving
    backup_file = pred_file.with_suffix(f'.json.backup_timestamp_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    import shutil
    shutil.copy2(pred_file, backup_file)
    print(f"📋 Backup created: {backup_file}")
    
    # Save updated predictions
    with open(pred_file, 'w') as f:
        json.dump(all_predictions, f, indent=2)
    
    print(f"✅ Updated {pred_file}")
    print(f"📊 Total predictions: {len(all_predictions)}")
    
    # Verify fix
    today_fixed = [p for p in all_predictions if p['timestamp'].startswith(today)]
    timestamps = [p['timestamp'] for p in today_fixed]
    unique_timestamps = set(timestamps)
    
    print(f"\n🔍 VERIFICATION:")
    print(f"   Today's predictions: {len(today_fixed)}")
    print(f"   Unique timestamps: {len(unique_timestamps)}")
    
    if len(timestamps) == len(unique_timestamps):
        print("   ✅ SUCCESS: All timestamps are now unique!")
    else:
        print("   ❌ ISSUE: Still have duplicate timestamps")
    
    # Show final timeline
    print(f"\n⏰ FINAL TIMELINE:")
    for pred in sorted(today_fixed, key=lambda x: x['timestamp']):
        time_str = pred['timestamp'][11:16]
        symbol = pred['symbol']
        signal = pred['prediction']['signal']
        confidence = pred['prediction']['confidence']
        print(f"   {time_str} | {symbol:8} | {signal:4} | {confidence:5.1%}")

if __name__ == "__main__":
    main()
