#!/bin/bash
# Restore predictions from backup to current database

REMOTE_HOST="170.64.199.151"
REMOTE_USER="root"
REMOTE_PATH="/root/test"

echo "🔄 Restoring predictions from backup..."
echo "=" * 50

# Function to run commands with venv activated
run_with_venv() {
    local cmd="$1"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && source dashboard_venv/bin/activate && ${cmd}"
}

echo "1. 📋 Creating backup of current database..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && cp data/trading_predictions.db data/trading_predictions.db.backup_$(date +%Y%m%d_%H%M%S)"

echo "2. 🔍 Checking backup predictions count..."
backup_count=$(ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && sqlite3 backups/pre_unified_20250806_093310/predictions.db 'SELECT COUNT(*) FROM predictions;'")
echo "   Found ${backup_count} predictions in backup"

echo "3. 📊 Checking current predictions count..."
current_count=$(ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && sqlite3 data/trading_predictions.db 'SELECT COUNT(*) FROM predictions;'")
echo "   Current database has ${current_count} predictions"

if [ "$backup_count" -gt "$current_count" ]; then
    echo "4. 🔄 Restoring predictions from backup..."
    
    # Create the restore script
    restore_script='
import sqlite3
import sys

# Connect to both databases
backup_db = sqlite3.connect("backups/pre_unified_20250806_093310/predictions.db")
current_db = sqlite3.connect("data/trading_predictions.db")

try:
    # Get all predictions from backup
    backup_cursor = backup_db.cursor()
    backup_cursor.execute("SELECT * FROM predictions")
    predictions = backup_cursor.fetchall()
    
    # Get column names from backup
    backup_cursor.execute("PRAGMA table_info(predictions)")
    backup_columns = [col[1] for col in backup_cursor.fetchall()]
    
    # Get column names from current database
    current_cursor = current_db.cursor()
    current_cursor.execute("PRAGMA table_info(predictions)")
    current_columns = [col[1] for col in current_cursor.fetchall()]
    
    print(f"Backup columns: {backup_columns}")
    print(f"Current columns: {current_columns}")
    
    # Find common columns
    common_columns = [col for col in backup_columns if col in current_columns]
    print(f"Common columns: {common_columns}")
    
    if not common_columns:
        print("ERROR: No common columns found between backup and current database")
        sys.exit(1)
    
    # Map backup data to current schema
    backup_col_indices = [backup_columns.index(col) for col in common_columns]
    
    inserted_count = 0
    for row in predictions:
        # Extract only the common columns from backup row
        mapped_row = tuple(row[i] for i in backup_col_indices)
        
        # Create placeholders for INSERT
        placeholders = ",".join(["?" for _ in common_columns])
        columns_str = ",".join(common_columns)
        
        try:
            current_cursor.execute(f"INSERT OR IGNORE INTO predictions ({columns_str}) VALUES ({placeholders})", mapped_row)
            if current_cursor.rowcount > 0:
                inserted_count += 1
        except Exception as e:
            print(f"Error inserting row: {e}")
            continue
    
    current_db.commit()
    print(f"Successfully restored {inserted_count} predictions from backup")
    
    # Verify the restoration
    current_cursor.execute("SELECT COUNT(*) FROM predictions")
    final_count = current_cursor.fetchone()[0]
    print(f"Final predictions count: {final_count}")
    
except Exception as e:
    print(f"Error during restoration: {e}")
    current_db.rollback()
finally:
    backup_db.close()
    current_db.close()
'

    # Execute the restore script
    run_with_venv "python3 -c \"$restore_script\""
    
    echo "5. ✅ Verification..."
    final_count=$(ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && sqlite3 data/trading_predictions.db 'SELECT COUNT(*) FROM predictions;'")
    echo "   Final predictions count: ${final_count}"
    
    if [ "$final_count" -gt "$current_count" ]; then
        echo "🎉 SUCCESS: Predictions restored from backup!"
        echo "   Restored: $((final_count - current_count)) additional predictions"
    else
        echo "⚠️  No new predictions were added - they may already exist or have different schemas"
    fi
else
    echo "4. ℹ️  Current database already has same or more predictions than backup"
fi

echo ""
echo "📊 Final database status:"
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && sqlite3 data/trading_predictions.db 'SELECT COUNT(*) as predictions FROM predictions; SELECT COUNT(*) as outcomes FROM outcomes; SELECT COUNT(*) as features FROM enhanced_features;'"

echo ""
echo "✅ Prediction restoration completed!"
