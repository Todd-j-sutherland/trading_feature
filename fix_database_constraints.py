#!/usr/bin/env python3
"""
Database Constraint Fixer
Fix the critical database constraint conflicts identified in the deep analysis.
"""

import sqlite3
import os
from pathlib import Path

def fix_database_constraints():
    """Fix conflicting UNIQUE indexes on predictions table"""
    print("🔧 FIXING DATABASE CONSTRAINT CONFLICTS")
    print("=" * 50)
    
    # Find database files
    project_root = Path(__file__).parent
    db_files = [
        project_root / "trading_data.db",
        project_root / "data" / "trading_predictions.db",
        project_root / "trading_predictions.db"
    ]
    
    fixed_databases = []
    
    for db_path in db_files:
        if not db_path.exists():
            continue
            
        print(f"\n🔍 Processing: {db_path}")
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if predictions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
            if not cursor.fetchone():
                print(f"  ⚠️  No predictions table found")
                conn.close()
                continue
            
            # Get current indexes on predictions table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='predictions'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            print(f"  📋 Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"    • {idx}")
            
            # Identify duplicate UNIQUE indexes on symbol+date
            duplicate_indexes = [
                'idx_predictions_symbol_date',
                'idx_predictions_unique_symbol_date'
            ]
            
            removed_count = 0
            for dup_idx in duplicate_indexes:
                if dup_idx in indexes:
                    try:
                        cursor.execute(f"DROP INDEX IF EXISTS {dup_idx}")
                        print(f"  ✅ Removed duplicate index: {dup_idx}")
                        removed_count += 1
                    except Exception as e:
                        print(f"  ❌ Failed to remove {dup_idx}: {e}")
            
            # Verify remaining indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='predictions'")
            remaining_indexes = [row[0] for row in cursor.fetchall()]
            
            print(f"  📊 Remaining indexes: {len(remaining_indexes)}")
            for idx in remaining_indexes:
                print(f"    • {idx}")
            
            # Test insertion to verify fix
            try:
                test_sql = """
                INSERT OR REPLACE INTO predictions 
                (symbol, prediction_date, predicted_price, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
                """
                
                from datetime import datetime
                test_data = (
                    'TEST.AX',
                    datetime.now().strftime('%Y-%m-%d'),
                    100.50,
                    0.85,
                    datetime.now().isoformat()
                )
                
                cursor.execute(test_sql, test_data)
                
                # Clean up test data
                cursor.execute("DELETE FROM predictions WHERE symbol = 'TEST.AX'")
                
                print(f"  ✅ Database insertion test: PASSED")
                
            except Exception as e:
                print(f"  ❌ Database insertion test: FAILED - {e}")
            
            conn.commit()
            conn.close()
            
            if removed_count > 0:
                fixed_databases.append(str(db_path))
                print(f"  🎯 Database fixed: {removed_count} duplicate indexes removed")
            else:
                print(f"  ℹ️  No duplicate indexes to remove")
                
        except Exception as e:
            print(f"  💥 Error processing database: {e}")
    
    print(f"\n🎉 CONSTRAINT FIXING COMPLETE")
    print(f"  📊 Databases processed: {len([db for db in db_files if db.exists()])}")
    print(f"  ✅ Databases fixed: {len(fixed_databases)}")
    
    if fixed_databases:
        print(f"  🎯 Fixed databases:")
        for db in fixed_databases:
            print(f"    • {db}")
        print(f"\n💡 The database should now accept new predictions without constraint conflicts!")
    else:
        print(f"  ℹ️  No constraint issues found or all already resolved")

if __name__ == "__main__":
    fix_database_constraints()
