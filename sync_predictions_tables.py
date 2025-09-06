#!/usr/bin/env python3
"""
Sync Script: Market-Aware Predictions → Main Predictions Table

This script bridges the gap between the new market_aware_predictions table
and the legacy predictions table that the dashboard still uses.
"""

import sqlite3
import os
from datetime import datetime
import sys

def sync_predictions_tables():
    """Sync market_aware_predictions to main predictions table"""
    
    # Database path
    db_path = "data/trading_predictions.db"
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting predictions table sync...")
        
        # Get latest timestamp from main predictions table
        cursor.execute("SELECT MAX(created_at) FROM predictions")
        latest_main = cursor.fetchone()[0]
        print(f"Latest prediction in main table: {latest_main}")
        
        # Get count of market-aware predictions newer than latest main
        cursor.execute("""
            SELECT COUNT(*) FROM market_aware_predictions 
            WHERE timestamp > COALESCE(?, '1970-01-01')
        """, (latest_main,))
        pending_count = cursor.fetchone()[0]
        print(f"Market-aware predictions to sync: {pending_count}")
        
        if pending_count == 0:
            print("No new predictions to sync.")
            return True
        
        # Sync new predictions from market_aware_predictions to predictions
        # Map schema: market_aware_predictions -> predictions table
        cursor.execute("""
            INSERT INTO predictions (
                symbol, 
                prediction_timestamp,
                predicted_action, 
                action_confidence, 
                predicted_direction, 
                predicted_magnitude,
                feature_vector,
                model_version,
                created_at,
                entry_price
            )
            SELECT 
                symbol,
                timestamp as prediction_timestamp,
                COALESCE(recommended_action, 'HOLD') as predicted_action,
                COALESCE(confidence, 0.5) as action_confidence,
                CASE 
                    WHEN predicted_price > current_price THEN 1  -- UP
                    WHEN predicted_price < current_price THEN -1 -- DOWN
                    ELSE 0 -- NEUTRAL
                END as predicted_direction,
                COALESCE(ABS(price_change_pct), 0.0) as predicted_magnitude,
                COALESCE(prediction_details, '{}') as feature_vector,
                COALESCE(model_used, 'market_aware_v1') as model_version,
                timestamp as created_at,
                COALESCE(current_price, 0.0) as entry_price
            FROM market_aware_predictions
            WHERE timestamp > COALESCE(?, '1970-01-01')
            ORDER BY timestamp ASC
        """, (latest_main,))
        
        synced_count = cursor.rowcount
        conn.commit()
        
        print(f"Successfully synced {synced_count} predictions")
        
        # Verify sync
        cursor.execute("SELECT COUNT(*), MAX(created_at) FROM predictions")
        total_count, new_latest = cursor.fetchone()
        print(f"Main predictions table now has: {total_count} total predictions")
        print(f"Latest prediction: {new_latest}")
        
        # Show latest few predictions by symbol
        cursor.execute("""
            SELECT symbol, predicted_action, action_confidence, created_at
            FROM predictions 
            WHERE created_at > COALESCE(?, '1970-01-01')
            ORDER BY created_at DESC 
            LIMIT 10
        """, (latest_main,))
        
        recent_predictions = cursor.fetchall()
        if recent_predictions:
            print("\nRecent synced predictions:")
            for pred in recent_predictions:
                print(f"  {pred[0]}: {pred[1]} (conf: {pred[2]:.3f}) at {pred[3]}")
        
        return True
        
    except Exception as e:
        print(f"Error during sync: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main execution"""
    print(f"Predictions Table Sync - {datetime.now()}")
    print("=" * 50)
    
    success = sync_predictions_tables()
    
    if success:
        print("\n✅ Sync completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Sync failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
