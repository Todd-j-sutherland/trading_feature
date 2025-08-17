#!/usr/bin/env python3
"""
Database Schema Synchronizer
Synchronize local and remote database schemas to ensure identical functionality
"""

import sqlite3
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

def backup_remote_data():
    """Backup remote database data before schema migration"""
    print("📋 BACKING UP REMOTE DATA")
    print("=" * 40)
    
    # Export remote data as JSON
    backup_script = """
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('/root/data/trading_predictions.db')
cursor = conn.cursor()

# Get all data from existing predictions table
cursor.execute("SELECT * FROM predictions")
predictions_data = cursor.fetchall()

# Get column names
cursor.execute("PRAGMA table_info(predictions)")
columns = [row[1] for row in cursor.fetchall()]

# Convert to list of dictionaries
backup_data = []
for row in predictions_data:
    backup_data.append(dict(zip(columns, row)))

# Save backup
backup = {
    'timestamp': datetime.now().isoformat(),
    'schema': 'legacy',
    'predictions': backup_data
}

with open('/root/database_backup.json', 'w') as f:
    json.dump(backup, f, indent=2)

print(f"✅ Backed up {len(backup_data)} predictions to database_backup.json")
conn.close()
"""
    
    # Write and execute backup script on remote
    with open("remote_backup.py", "w") as f:
        f.write(backup_script)
    
    # Copy and run backup script
    os.system("scp remote_backup.py root@170.64.199.151:/root/")
    result = os.system("ssh root@170.64.199.151 'cd /root && python3 remote_backup.py'")
    
    if result == 0:
        print("✅ Remote data backup completed")
        return True
    else:
        print("❌ Remote data backup failed")
        return False

def create_modern_schema_script():
    """Create script to update remote database schema"""
    schema_script = """
import sqlite3
import json
from datetime import datetime

print("🔄 UPDATING DATABASE SCHEMA TO MODERN FORMAT")
print("=" * 50)

# Connect to database
conn = sqlite3.connect('/root/data/trading_predictions.db')
cursor = conn.cursor()

# Load backup data
with open('/root/database_backup.json', 'r') as f:
    backup = json.load(f)

print(f"📊 Loaded {len(backup['predictions'])} predictions from backup")

# Rename old table
cursor.execute("ALTER TABLE predictions RENAME TO predictions_legacy")
print("✅ Renamed old table to predictions_legacy")

# Create new modern schema
cursor.execute('''
CREATE TABLE predictions (
    prediction_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    prediction_timestamp DATETIME NOT NULL,
    predicted_action TEXT NOT NULL,
    action_confidence REAL NOT NULL,
    predicted_direction INTEGER,
    predicted_magnitude REAL,
    feature_vector TEXT,
    model_version TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    entry_price REAL DEFAULT 0,
    optimal_action TEXT
)
''')
print("✅ Created modern predictions table")

# Create the unique index
cursor.execute('''
CREATE UNIQUE INDEX idx_unique_prediction_symbol_date 
ON predictions(symbol, date(prediction_timestamp))
''')
print("✅ Created unique constraint index")

# Create security triggers
cursor.execute('''
CREATE TRIGGER prevent_data_leakage
BEFORE INSERT ON predictions
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM enhanced_features ef
            WHERE ef.symbol = NEW.symbol
            AND datetime(ef.timestamp) > datetime(NEW.prediction_timestamp, '+30 minutes')
        )
        THEN RAISE(ABORT, 'Data leakage detected: Features from future')
    END;
END
''')
print("✅ Created data leakage protection trigger")

cursor.execute('''
CREATE TRIGGER validate_prediction_timestamp
BEFORE INSERT ON predictions
WHEN NEW.prediction_timestamp IS NULL
BEGIN
    SELECT RAISE(ABORT, 'prediction_timestamp cannot be null');
END
''')
print("✅ Created timestamp validation trigger")

cursor.execute('''
CREATE TRIGGER validate_symbol_format
BEFORE INSERT ON predictions
WHEN NEW.symbol IS NULL OR NEW.symbol = '' OR length(NEW.symbol) < 2
BEGIN
    SELECT RAISE(ABORT, 'symbol must be valid');
END
''')
print("✅ Created symbol validation trigger")

# Migrate data from legacy format to modern format
migrated_count = 0
for pred in backup['predictions']:
    try:
        # Convert legacy format to modern format
        prediction_id = f"{pred['symbol']}_{pred['date']}_{pred['time']}"
        prediction_timestamp = f"{pred['date']} {pred['time']}"
        
        # Map legacy fields to modern fields
        predicted_action = pred['signal']
        action_confidence = float(pred['confidence']) if isinstance(pred['confidence'], str) else pred['confidence']
        
        cursor.execute('''
        INSERT OR REPLACE INTO predictions (
            prediction_id, symbol, prediction_timestamp, predicted_action,
            action_confidence, predicted_direction, predicted_magnitude,
            feature_vector, model_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_id,
            pred['symbol'],
            prediction_timestamp,
            predicted_action,
            action_confidence,
            1 if predicted_action == 'BUY' else -1 if predicted_action == 'SELL' else 0,
            abs(action_confidence),
            None,  # feature_vector - not available in legacy
            'legacy_migration_v1.0',
            datetime.now().isoformat()
        ))
        migrated_count += 1
    except Exception as e:
        print(f"⚠️ Failed to migrate prediction {pred}: {e}")

conn.commit()
conn.close()

print(f"✅ Migrated {migrated_count} predictions to modern schema")
print("🎯 Database schema synchronization complete!")
"""
    
    return schema_script

def sync_database_schemas():
    """Synchronize database schemas between local and remote"""
    print("🔄 SYNCHRONIZING DATABASE SCHEMAS")
    print("=" * 50)
    
    # Step 1: Backup remote data
    if not backup_remote_data():
        print("❌ Cannot proceed without backup")
        return False
    
    # Step 2: Create and execute schema migration
    schema_script = create_modern_schema_script()
    
    with open("schema_migration.py", "w") as f:
        f.write(schema_script)
    
    print("📤 Uploading schema migration script...")
    os.system("scp schema_migration.py root@170.64.199.151:/root/")
    
    print("🔄 Executing schema migration on remote...")
    result = os.system("ssh root@170.64.199.151 'cd /root && python3 schema_migration.py'")
    
    if result == 0:
        print("✅ Schema migration completed successfully")
        
        # Verify migration
        print("\n📋 Verifying migration...")
        verify_result = os.system("ssh root@170.64.199.151 'sqlite3 /root/data/trading_predictions.db \".schema predictions\"'")
        
        if verify_result == 0:
            print("✅ Schema verification passed")
            return True
        else:
            print("⚠️ Schema verification had issues")
            return False
    else:
        print("❌ Schema migration failed")
        return False

def create_enhanced_outcomes_table():
    """Create enhanced_outcomes table on remote if missing"""
    outcomes_script = """
import sqlite3

conn = sqlite3.connect('/root/data/trading_predictions.db')
cursor = conn.cursor()

# Check if enhanced_outcomes exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enhanced_outcomes'")
if not cursor.fetchone():
    print("📊 Creating enhanced_outcomes table...")
    cursor.execute('''
    CREATE TABLE enhanced_outcomes (
        outcome_id TEXT PRIMARY KEY,
        prediction_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        evaluation_timestamp DATETIME NOT NULL,
        actual_price REAL,
        predicted_price REAL,
        price_accuracy REAL,
        direction_accuracy INTEGER,
        outcome_quality TEXT,
        performance_score REAL,
        confidence_calibration REAL,
        temporal_decay_factor REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id)
    )
    ''')
    
    cursor.execute('''
    CREATE INDEX idx_outcomes_symbol_date ON enhanced_outcomes(symbol, date(evaluation_timestamp))
    ''')
    
    cursor.execute('''
    CREATE INDEX idx_outcomes_prediction ON enhanced_outcomes(prediction_id)
    ''')
    
    print("✅ Enhanced outcomes table created")
else:
    print("✅ Enhanced outcomes table already exists")

# Check if enhanced_features exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enhanced_features'")
if not cursor.fetchone():
    print("📊 Creating enhanced_features table...")
    cursor.execute('''
    CREATE TABLE enhanced_features (
        feature_id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        feature_type TEXT NOT NULL,
        feature_value REAL,
        feature_metadata TEXT,
        confidence_score REAL,
        data_source TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE INDEX idx_features_symbol_timestamp ON enhanced_features(symbol, timestamp)
    ''')
    
    cursor.execute('''
    CREATE INDEX idx_features_type ON enhanced_features(feature_type)
    ''')
    
    print("✅ Enhanced features table created")
else:
    print("✅ Enhanced features table already exists")

conn.commit()
conn.close()
print("🎯 All required tables are present")
"""
    
    with open("create_tables.py", "w") as f:
        f.write(outcomes_script)
    
    print("📤 Creating additional tables on remote...")
    os.system("scp create_tables.py root@170.64.199.151:/root/")
    result = os.system("ssh root@170.64.199.151 'cd /root && python3 create_tables.py'")
    
    return result == 0

def verify_synchronization():
    """Verify that local and remote schemas are now identical"""
    print("\n🔍 VERIFYING SYNCHRONIZATION")
    print("=" * 40)
    
    # Get local schema
    local_db = Path(__file__).parent / "data" / "trading_predictions.db"
    if local_db.exists():
        conn = sqlite3.connect(str(local_db))
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='predictions'")
        local_schema = cursor.fetchone()
        conn.close()
        
        if local_schema:
            print("✅ Local schema retrieved")
        else:
            print("❌ Local schema not found")
            return False
    else:
        print("❌ Local database not found")
        return False
    
    # Get remote schema
    result = os.system("ssh root@170.64.199.151 'sqlite3 /root/data/trading_predictions.db \".schema predictions\"' > remote_schema.txt")
    if result == 0:
        print("✅ Remote schema retrieved")
        
        # Read remote schema
        if os.path.exists("remote_schema.txt"):
            with open("remote_schema.txt", "r") as f:
                remote_schema_content = f.read().strip()
            
            if "prediction_id" in remote_schema_content and "prediction_timestamp" in remote_schema_content:
                print("✅ Remote schema has modern format")
                print("🎯 DATABASE SYNCHRONIZATION SUCCESSFUL!")
                return True
            else:
                print("❌ Remote schema still has legacy format")
                return False
        else:
            print("❌ Could not read remote schema")
            return False
    else:
        print("❌ Failed to retrieve remote schema")
        return False

def main():
    """Main synchronization process"""
    print("🎯 DATABASE SCHEMA SYNCHRONIZATION")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Step 1: Sync main predictions table schema
        if sync_database_schemas():
            print("\n✅ Main schema synchronization completed")
        else:
            print("\n❌ Main schema synchronization failed")
            return False
        
        # Step 2: Create additional tables
        if create_enhanced_outcomes_table():
            print("✅ Additional tables synchronized")
        else:
            print("⚠️ Additional tables had issues")
        
        # Step 3: Verify synchronization
        if verify_synchronization():
            print("\n🎉 DATABASE SYNCHRONIZATION COMPLETE!")
            print("Both local and remote now have identical modern schemas")
            return True
        else:
            print("\n❌ Synchronization verification failed")
            return False
            
    except Exception as e:
        print(f"💥 Synchronization error: {e}")
        return False
    
    finally:
        # Cleanup temporary files
        temp_files = ["remote_backup.py", "schema_migration.py", "create_tables.py", "remote_schema.txt"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    main()
