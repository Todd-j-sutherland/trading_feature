#!/usr/bin/env python3
"""
Restore predictions with proper schema mapping
"""
import sqlite3
import sys
import os
from datetime import datetime

def map_backup_to_current(backup_row, backup_columns):
    """Map backup row format to current schema"""
    
    # Create a dict from backup row
    backup_dict = dict(zip(backup_columns, backup_row))
    
    # Map old schema to new schema
    try:
        # Combine date and time for timestamp
        date_str = backup_dict.get('date', '')
        time_str = backup_dict.get('time', '')
        
        if date_str and time_str:
            timestamp = f"{date_str} {time_str}"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Map signal to action
        signal = backup_dict.get('signal', 'HOLD')
        if signal.upper() in ['BUY', 'SELL', 'HOLD']:
            predicted_action = signal.upper()
        else:
            predicted_action = 'HOLD'
        
        # Map signal to direction
        if predicted_action == 'BUY':
            predicted_direction = 1
        elif predicted_action == 'SELL':
            predicted_direction = -1
        else:
            predicted_direction = 0
        
        # Generate prediction ID
        symbol = backup_dict.get('symbol', 'UNKNOWN')
        prediction_id = f"restored_{symbol}_{date_str}_{time_str}".replace(' ', '_').replace(':', '')
        
        # Map other fields
        action_confidence = backup_dict.get('confidence', 0.5)
        if isinstance(action_confidence, str):
            try:
                action_confidence = float(action_confidence)
            except:
                action_confidence = 0.5
        
        return {
            'prediction_id': prediction_id,
            'symbol': symbol,
            'prediction_timestamp': timestamp,
            'predicted_action': predicted_action,
            'action_confidence': action_confidence,
            'predicted_direction': predicted_direction,
            'predicted_magnitude': 0.0,  # Default value
            'model_version': 'backup_restored',
            'entry_price': 0.0,  # Default value
            'optimal_action': predicted_action
        }
        
    except Exception as e:
        print(f"Error mapping row: {e}")
        return None

def restore_predictions_with_mapping():
    """Restore predictions with proper schema mapping"""
    
    backup_path = "backups/pre_unified_20250806_093310/predictions.db"
    current_path = "data/trading_predictions.db"
    
    print("🔄 Connecting to databases...")
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup database not found: {backup_path}")
        return False
    
    if not os.path.exists(current_path):
        print(f"❌ Current database not found: {current_path}")
        return False
    
    try:
        # Connect to both databases
        backup_db = sqlite3.connect(backup_path)
        current_db = sqlite3.connect(current_path)
        
        # Get all predictions from backup
        backup_cursor = backup_db.cursor()
        backup_cursor.execute("SELECT * FROM predictions ORDER BY date, time")
        predictions = backup_cursor.fetchall()
        
        print(f"📊 Found {len(predictions)} predictions in backup")
        
        if not predictions:
            print("ℹ️  No predictions to restore")
            return True
        
        # Get column names from backup
        backup_cursor.execute("PRAGMA table_info(predictions)")
        backup_columns = [col[1] for col in backup_cursor.fetchall()]
        
        print(f"📋 Backup columns: {backup_columns}")
        
        # Show some sample data
        print("📝 Sample backup data:")
        for i, row in enumerate(predictions[:3]):
            backup_dict = dict(zip(backup_columns, row))
            print(f"   Row {i+1}: {backup_dict}")
        
        current_cursor = current_db.cursor()
        
        # Required columns for current schema
        required_columns = [
            'prediction_id', 'symbol', 'prediction_timestamp', 
            'predicted_action', 'action_confidence', 'predicted_direction',
            'predicted_magnitude', 'model_version', 'entry_price', 'optimal_action'
        ]
        
        inserted_count = 0
        error_count = 0
        
        for i, row in enumerate(predictions):
            try:
                # Map the backup row to current schema
                mapped_data = map_backup_to_current(row, backup_columns)
                
                if mapped_data is None:
                    error_count += 1
                    continue
                
                # Create the insert query
                placeholders = ",".join(["?" for _ in required_columns])
                columns_str = ",".join(required_columns)
                values = [mapped_data[col] for col in required_columns]
                
                current_cursor.execute(f"INSERT OR IGNORE INTO predictions ({columns_str}) VALUES ({placeholders})", values)
                if current_cursor.rowcount > 0:
                    inserted_count += 1
                    if inserted_count <= 3:  # Show first few insertions
                        print(f"✅ Inserted: {mapped_data['symbol']} {mapped_data['predicted_action']} at {mapped_data['prediction_timestamp']}")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # Only show first few errors
                    print(f"⚠️  Error inserting row {i+1}: {e}")
        
        current_db.commit()
        print(f"✅ Successfully restored {inserted_count} predictions from backup")
        
        if error_count > 0:
            print(f"⚠️  {error_count} rows had errors during insertion")
        
        # Verify the restoration
        current_cursor.execute("SELECT COUNT(*) FROM predictions")
        final_count = current_cursor.fetchone()[0]
        print(f"📊 Final predictions count: {final_count}")
        
        # Show some restored predictions
        if final_count > 0:
            print("📝 Sample restored predictions:")
            current_cursor.execute("SELECT symbol, predicted_action, action_confidence, prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 5")
            for row in current_cursor.fetchall():
                print(f"   {row[0]}: {row[1]} (confidence: {row[2]}) at {row[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during restoration: {e}")
        return False
    finally:
        if 'backup_db' in locals():
            backup_db.close()
        if 'current_db' in locals():
            current_db.close()

if __name__ == "__main__":
    print("🔄 PREDICTION RESTORATION WITH SCHEMA MAPPING")
    print("=" * 50)
    
    success = restore_predictions_with_mapping()
    
    if success:
        print("🎉 Restoration completed successfully!")
    else:
        print("❌ Restoration failed!")
        sys.exit(1)
