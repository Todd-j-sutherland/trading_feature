#!/usr/bin/env python3
"""
Database Consolidation Script
Migrates all trading data to trading_predictions.db as single source of truth
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_databases():
    """Create backups before consolidation"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"data/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    databases = [
        "data/trading_unified.db",
        "data/trading_unified.db", 
        "data/trading_unified.db"
    ]
    
    for db in databases:
        if os.path.exists(db):
            shutil.copy2(db, backup_dir)
            print(f"Backed up {db} to {backup_dir}")
    
    return backup_dir

def get_table_data(db_path, table_name):
    """Get all data from a table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get all data
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        conn.close()
        return columns, data
    except Exception as e:
        print(f"Error reading {table_name} from {db_path}: {e}")
        return None, None

def insert_data_safely(target_conn, table_name, columns, data):
    """Insert data into target table, handling conflicts"""
    if not data:
        print(f"No data to insert into {table_name}")
        return 0
    
    cursor = target_conn.cursor()
    
    # Create placeholders for INSERT
    placeholders = ','.join(['?' for _ in columns])
    
    inserted_count = 0
    skipped_count = 0
    
    for row in data:
        try:
            cursor.execute(f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})", row)
            inserted_count += 1
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                skipped_count += 1
                print(f"Skipped duplicate row in {table_name}: {e}")
            else:
                print(f"Error inserting row in {table_name}: {e}")
        except Exception as e:
            print(f"Unexpected error inserting row in {table_name}: {e}")
    
    print(f"Table {table_name}: {inserted_count} inserted, {skipped_count} skipped")
    return inserted_count

def consolidate_databases():
    """Main consolidation function"""
    print("=== TRADING DATABASE CONSOLIDATION ===")
    print("Target: trading_predictions.db as single source of truth")
    print()
    
    # 1. Backup existing databases
    backup_dir = backup_databases()
    print(f"Backups created in: {backup_dir}")
    print()
    
    # 2. Connect to target database
    target_db = "data/trading_unified.db"
    target_conn = sqlite3.connect(target_db)
    
    print("=== MIGRATION FROM trading_unified.db ===")
    
    # 3. Migrate data from trading_unified.db
    source_db = "data/trading_unified.db"
    if os.path.exists(source_db):
        # Tables to migrate
        tables_to_migrate = [
            "predictions",
            "enhanced_outcomes", 
            "enhanced_features",
            "sentiment_features",
            "enhanced_morning_analysis",
            "enhanced_evening_analysis",
            "model_performance"
        ]
        
        for table in tables_to_migrate:
            print(f"Migrating {table}...")
            columns, data = get_table_data(source_db, table)
            if columns and data:
                inserted = insert_data_safely(target_conn, table, columns, data)
                print(f"  -> {inserted} records migrated")
            else:
                print(f"  -> No data found or error reading {table}")
        
        target_conn.commit()
    else:
        print(f"Source database {source_db} not found")
    
    print()
    print("=== MIGRATION FROM trading_data.db ===")
    
    # 4. Migrate relevant data from trading_data.db
    source_db = "data/trading_unified.db"
    if os.path.exists(source_db):
        # Check what tables exist
        conn = sqlite3.connect(source_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"Available tables in trading_data.db: {tables}")
        
        for table in tables:
            if table in ["enhanced_morning_analysis", "sentiment_features"]:
                print(f"Migrating {table}...")
                columns, data = get_table_data(source_db, table)
                if columns and data:
                    inserted = insert_data_safely(target_conn, table, columns, data)
                    print(f"  -> {inserted} records migrated")
    
    target_conn.commit()
    target_conn.close()
    
    print()
    print("=== VERIFICATION ===")
    
    # 5. Verify the consolidated database
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    # Check data counts
    verification_tables = ["predictions", "enhanced_outcomes", "enhanced_features"]
    for table in verification_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} records")
        except Exception as e:
            print(f"Error checking {table}: {e}")
    
    conn.close()
    
    print()
    print("=== CONSOLIDATION COMPLETE ===")
    print(f"All data consolidated into: {target_db}")
    print(f"Backups available in: {backup_dir}")
    print()
    print("Next steps:")
    print("1. Update all dashboard files to use trading_predictions.db")
    print("2. Test the consolidated database")
    print("3. Remove old database files (trading_unified.db, trading_data.db)")

if __name__ == "__main__":
    consolidate_databases()
