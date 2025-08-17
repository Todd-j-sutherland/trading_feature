#!/usr/bin/env python3
"""
Restore predictions from backup database to current database
"""
import sqlite3
import sys
import os

def restore_predictions():
    """Restore predictions from backup to current database"""
    
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
        backup_cursor.execute("SELECT * FROM predictions")
        predictions = backup_cursor.fetchall()
        
        print(f"📊 Found {len(predictions)} predictions in backup")
        
        if not predictions:
            print("ℹ️  No predictions to restore")
            return True
        
        # Get column names from backup
        backup_cursor.execute("PRAGMA table_info(predictions)")
        backup_columns = [col[1] for col in backup_cursor.fetchall()]
        
        # Get column names from current database
        current_cursor = current_db.cursor()
        current_cursor.execute("PRAGMA table_info(predictions)")
        current_columns = [col[1] for col in current_cursor.fetchall()]
        
        print(f"📋 Backup columns: {backup_columns}")
        print(f"📋 Current columns: {current_columns}")
        
        # Find common columns
        common_columns = [col for col in backup_columns if col in current_columns]
        print(f"🔗 Common columns: {common_columns}")
        
        if not common_columns:
            print("❌ No common columns found between backup and current database")
            return False
        
        # Map backup data to current schema
        backup_col_indices = [backup_columns.index(col) for col in common_columns]
        
        inserted_count = 0
        error_count = 0
        
        for i, row in enumerate(predictions):
            try:
                # Extract only the common columns from backup row
                mapped_row = tuple(row[j] for j in backup_col_indices)
                
                # Create placeholders for INSERT
                placeholders = ",".join(["?" for _ in common_columns])
                columns_str = ",".join(common_columns)
                
                current_cursor.execute(f"INSERT OR IGNORE INTO predictions ({columns_str}) VALUES ({placeholders})", mapped_row)
                if current_cursor.rowcount > 0:
                    inserted_count += 1
                    
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
    print("🔄 PREDICTION RESTORATION")
    print("=" * 40)
    
    success = restore_predictions()
    
    if success:
        print("🎉 Restoration completed successfully!")
    else:
        print("❌ Restoration failed!")
        sys.exit(1)
