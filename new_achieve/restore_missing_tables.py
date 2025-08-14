#!/usr/bin/env python3
"""
Restore Missing Tables to Unified Database

The dashboard.py requires specific tables that were in enhanced_training_data.db
but weren't migrated to the unified database. This script will restore them.
"""

import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def restore_missing_tables():
    """Restore missing tables from archived database to unified database"""
    
    # Paths
    archived_db = Path("archive/cleanup_20250805_195133/databases/enhanced_training_data.db")
    unified_db = Path("data/trading_unified.db")
    
    if not archived_db.exists():
        logger.error(f"Archived database not found: {archived_db}")
        return False
    
    if not unified_db.exists():
        logger.error(f"Unified database not found: {unified_db}")
        return False
    
    try:
        # Connect to both databases
        source_conn = sqlite3.connect(archived_db)
        target_conn = sqlite3.connect(unified_db)
        
        # Tables to restore
        tables_to_restore = [
            "enhanced_features",
            "enhanced_outcomes", 
            "model_performance_enhanced"
        ]
        
        for table_name in tables_to_restore:
            logger.info(f"🔄 Restoring table: {table_name}")
            
            # Get table schema from source
            cursor = source_conn.cursor()
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            schema_row = cursor.fetchone()
            
            if not schema_row:
                logger.warning(f"⚠️ Table {table_name} not found in source database")
                continue
            
            create_sql = schema_row[0]
            
            # Create table in target database (IF NOT EXISTS to avoid conflicts)
            create_sql_safe = create_sql.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
            target_conn.execute(create_sql_safe)
            
            # Copy data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if rows:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                placeholders = ",".join(["?" for _ in columns])
                
                # Insert data
                target_conn.executemany(
                    f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})",
                    rows
                )
                
                logger.info(f"✅ Restored {len(rows)} records to {table_name}")
            else:
                logger.info(f"📋 No data to restore for {table_name}")
        
        # Commit changes
        target_conn.commit()
        
        # Close connections
        source_conn.close()
        target_conn.close()
        
        logger.info("🎉 Successfully restored missing tables to unified database")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error restoring tables: {e}")
        return False

def verify_tables():
    """Verify that all required tables now exist in unified database"""
    unified_db = Path("data/trading_unified.db")
    
    required_tables = [
        "bank_sentiment",
        "ml_predictions", 
        "positions",
        "trading_signals",
        "enhanced_features",
        "enhanced_outcomes",
        "model_performance_enhanced"
    ]
    
    try:
        conn = sqlite3.connect(unified_db)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        logger.info("📊 Table verification:")
        all_present = True
        
        for table in required_tables:
            if table in existing_tables:
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"  ✅ {table}: {count} records")
            else:
                logger.error(f"  ❌ {table}: MISSING")
                all_present = False
        
        conn.close()
        
        if all_present:
            logger.info("🎉 All required tables are present in unified database")
        else:
            logger.error("❌ Some required tables are still missing")
        
        return all_present
        
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting restoration of missing tables...")
    
    if restore_missing_tables():
        if verify_tables():
            logger.info("✅ Restoration completed successfully!")
        else:
            logger.error("❌ Verification failed - some tables may be missing")
    else:
        logger.error("❌ Restoration failed")