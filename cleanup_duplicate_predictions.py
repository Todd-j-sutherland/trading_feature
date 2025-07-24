#!/usr/bin/env python3
"""
Clean up duplicate ML predictions that were created during debugging/testing
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def cleanup_duplicate_predictions():
    """Remove duplicate predictions keeping only the latest one for each symbol per hour"""
    
    prediction_file = "data/ml_performance/prediction_history.json"
    
    if not os.path.exists(prediction_file):
        print("No prediction history file found")
        return
    
    # Load current predictions
    with open(prediction_file, 'r') as f:
        predictions = json.load(f)
    
    print(f"Total predictions before cleanup: {len(predictions)}")
    
    # Group predictions by symbol and hour to identify duplicates
    grouped = defaultdict(list)
    
    for pred in predictions:
        try:
            timestamp = pred['timestamp']
            symbol = pred['symbol']
            
            # Group by symbol and hour (to allow different predictions in different hours)
            hour_key = timestamp[:13]  # YYYY-MM-DDTHH
            key = f"{symbol}_{hour_key}"
            
            grouped[key].append(pred)
            
        except Exception as e:
            print(f"Error processing prediction {pred.get('id', 'unknown')}: {e}")
            continue
    
    # Keep only the latest prediction for each symbol+hour group
    cleaned_predictions = []
    duplicates_removed = 0
    
    for key, group in grouped.items():
        if len(group) == 1:
            # No duplicates, keep the single prediction
            cleaned_predictions.append(group[0])
        else:
            # Multiple predictions in same hour for same symbol - keep the latest
            # Sort by timestamp (latest first)
            sorted_group = sorted(group, key=lambda x: x['timestamp'], reverse=True)
            latest = sorted_group[0]
            
            print(f"Found {len(group)} duplicates for {key}")
            print(f"  Keeping: {latest['id']} at {latest['timestamp']}")
            for dup in sorted_group[1:]:
                print(f"  Removing: {dup['id']} at {dup['timestamp']}")
            
            cleaned_predictions.append(latest)
            duplicates_removed += len(group) - 1
    
    # Sort by timestamp
    cleaned_predictions.sort(key=lambda x: x['timestamp'])
    
    print(f"\nRemoved {duplicates_removed} duplicate predictions")
    print(f"Final predictions count: {len(cleaned_predictions)}")
    
    # Backup original file
    backup_file = f"{prediction_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w') as f:
        json.dump(predictions, f, indent=2)
    print(f"Original file backed up to: {backup_file}")
    
    # Save cleaned predictions
    with open(prediction_file, 'w') as f:
        json.dump(cleaned_predictions, f, indent=2)
    
    print(f"✅ Cleanup complete! Removed {duplicates_removed} duplicates.")

def show_recent_predictions():
    """Show recent predictions to verify cleanup"""
    
    prediction_file = "data/ml_performance/prediction_history.json"
    
    if not os.path.exists(prediction_file):
        print("No prediction history file found")
        return
    
    with open(prediction_file, 'r') as f:
        predictions = json.load(f)
    
    print("\n📊 Recent predictions (last 20):")
    print("Time\t\tSymbol\tSignal\tConfidence")
    print("-" * 50)
    
    for pred in predictions[-20:]:
        timestamp = pred['timestamp'][:16]  # YYYY-MM-DDTHH:MM
        symbol = pred['symbol']
        signal = pred['prediction'].get('signal', 'N/A')
        confidence = pred['prediction'].get('confidence', 0) * 100
        
        print(f"{timestamp}\t{symbol}\t{signal}\t{confidence:.1f}%")

if __name__ == "__main__":
    print("🧹 Starting duplicate prediction cleanup...")
    cleanup_duplicate_predictions()
    show_recent_predictions()
