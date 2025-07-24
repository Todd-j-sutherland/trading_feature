#!/usr/bin/env python3
"""
Clean up duplicate predictions and test deduplication logic
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Clean up duplicates and test the system"""
    print("🧹 Cleaning up duplicate predictions...")
    
    try:
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        
        tracker = MLProgressionTracker()
        
        # First, do a dry run to see what duplicates exist
        print("\n🔍 Scanning for duplicates...")
        duplicate_count = tracker.cleanup_duplicate_predictions(dry_run=True)
        
        if duplicate_count > 0:
            print(f"\n📊 Found {duplicate_count} duplicate predictions")
            
            # Ask for confirmation to remove them
            response = input("\n❓ Remove duplicates? (y/N): ").strip().lower()
            
            if response in ['y', 'yes']:
                print("\n🗑️ Removing duplicates...")
                removed_count = tracker.cleanup_duplicate_predictions(dry_run=False)
                print(f"✅ Successfully removed {removed_count} duplicate predictions")
            else:
                print("❌ Cleanup cancelled")
        else:
            print("✅ No duplicates found")
        
        # Show current prediction stats
        print(f"\n📈 Current prediction history: {len(tracker.prediction_history)} total predictions")
        
        # Show recent predictions by symbol
        from collections import defaultdict
        recent_by_symbol = defaultdict(list)
        
        for pred in tracker.prediction_history[-20:]:  # Last 20 predictions
            recent_by_symbol[pred['symbol']].append(pred)
        
        print("\n📋 Recent predictions by symbol:")
        for symbol, preds in recent_by_symbol.items():
            print(f"  {symbol}: {len(preds)} predictions")
            for pred in preds[-3:]:  # Show last 3
                timestamp = pred['timestamp'][:16]  # Just date and time
                signal = pred['prediction'].get('signal', 'N/A')
                confidence = pred['prediction'].get('confidence', 0)
                print(f"    {timestamp} - {signal} @ {confidence:.1%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
