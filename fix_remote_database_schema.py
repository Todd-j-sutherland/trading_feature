#!/usr/bin/env python3
"""
Remote Database Schema Fixer
Fix the missing market_context column in the predictions table
"""

import sqlite3
import sys
from pathlib import Path

def fix_database_schema(db_path="predictions.db"):
    """Add missing market_context column to predictions table"""
    
    print(f"🔧 Fixing database schema: {db_path}")
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(predictions);")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Current columns: {columns}")
        
        # Check if market_context column exists
        if 'market_context' in columns:
            print("✅ market_context column already exists!")
            conn.close()
            return True
        
        # Add the missing column
        print("➕ Adding market_context column...")
        cursor.execute("""
            ALTER TABLE predictions 
            ADD COLUMN market_context TEXT DEFAULT 'NEUTRAL'
        """)
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(predictions);")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Updated columns: {new_columns}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if 'market_context' in new_columns:
            print("✅ Successfully added market_context column!")
            return True
        else:
            print("❌ Failed to add market_context column")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

def check_outcomes_table(db_path="predictions.db"):
    """Check if outcomes table needs any updates"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check outcomes table schema
        cursor.execute("PRAGMA table_info(outcomes);")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Outcomes table columns: {columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking outcomes table: {e}")
        return False

def main():
    """Main execution function"""
    
    print("🔧 Remote Database Schema Fixer")
    print("=" * 50)
    
    # Fix predictions table
    success = fix_database_schema()
    
    # Check outcomes table
    check_outcomes_table()
    
    if success:
        print("\n✅ Database schema fix completed successfully!")
        print("🚀 The market-aware prediction system should now work properly.")
    else:
        print("\n❌ Database schema fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
