#!/usr/bin/env python3
"""
Database Consolidation Fix
Merge data from multiple database files into the main database
"""

import sqlite3
import os
import shutil
from datetime import datetime

def consolidate_remote_databases():
    """
    Consolidate multiple database files into the main enhanced database
    """
    print("🔧 DATABASE CONSOLIDATION FIX")
    print("=" * 50)
    
    main_db = "data/ml_models/enhanced_training_data.db"
    
    # Find all database files
    possible_dbs = [
        "morning_analysis.db",
        "enhanced_training_data.db", 
        "./enhanced_training_data.db",
        "data/enhanced_training_data.db"
    ]
    
    print("📁 Database file inventory:")
    found_dbs = []
    
    for db_path in possible_dbs:
        if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
            stat = os.stat(db_path)
            print(f"   ✅ {db_path} ({stat.st_size:,} bytes)")
            found_dbs.append(db_path)
        else:
            print(f"   ❌ {db_path} (not found or empty)")
    
    if not found_dbs:
        print("   💡 No additional databases found to consolidate")
        return True
    
    # Backup main database
    backup_path = f"{main_db}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(main_db):
        shutil.copy2(main_db, backup_path)
        print(f"📦 Backup created: {backup_path}")
    
    try:
        # Connect to main database
        main_conn = sqlite3.connect(main_db)
        main_cursor = main_conn.cursor()
        
        print(f"\n🔍 Analyzing main database:")
        main_cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        main_features_before = main_cursor.fetchone()[0]
        
        main_cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        main_outcomes_before = main_cursor.fetchone()[0]
        
        print(f"   Features before: {main_features_before}")
        print(f"   Outcomes before: {main_outcomes_before}")
        
        # Consolidate data from other databases
        for source_db in found_dbs:
            print(f"\n📥 Consolidating from: {source_db}")
            
            try:
                # Attach source database
                main_cursor.execute(f"ATTACH DATABASE '{source_db}' AS source_db")
                
                # Check if source has compatible tables
                main_cursor.execute("""
                    SELECT name FROM source_db.sqlite_master 
                    WHERE type='table' AND name IN ('enhanced_features', 'enhanced_outcomes')
                """)
                source_tables = [row[0] for row in main_cursor.fetchall()]
                
                if 'enhanced_features' in source_tables:
                    # Get count from source
                    main_cursor.execute("SELECT COUNT(*) FROM source_db.enhanced_features")
                    source_features = main_cursor.fetchone()[0]
                    print(f"   Source features: {source_features}")
                    
                    if source_features > 0:
                        # Copy features that don't exist in main (avoid duplicates)
                        main_cursor.execute("""
                            INSERT OR IGNORE INTO enhanced_features 
                            SELECT * FROM source_db.enhanced_features
                        """)
                        copied_features = main_cursor.rowcount
                        print(f"   ✅ Copied {copied_features} new features")
                
                if 'enhanced_outcomes' in source_tables:
                    # Get count from source
                    main_cursor.execute("SELECT COUNT(*) FROM source_db.enhanced_outcomes")
                    source_outcomes = main_cursor.fetchone()[0]
                    print(f"   Source outcomes: {source_outcomes}")
                    
                    if source_outcomes > 0:
                        # Copy outcomes that don't exist in main
                        main_cursor.execute("""
                            INSERT OR IGNORE INTO enhanced_outcomes 
                            SELECT * FROM source_db.enhanced_outcomes
                        """)
                        copied_outcomes = main_cursor.rowcount
                        print(f"   ✅ Copied {copied_outcomes} new outcomes")
                
                # Detach source database
                main_cursor.execute("DETACH DATABASE source_db")
                
            except Exception as e:
                print(f"   ❌ Error consolidating {source_db}: {e}")
                continue
        
        # Final count
        main_cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        main_features_after = main_cursor.fetchone()[0]
        
        main_cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL")
        main_outcomes_after = main_cursor.fetchone()[0]
        
        main_conn.commit()
        main_conn.close()
        
        print(f"\n📊 Consolidation results:")
        print(f"   Features: {main_features_before} → {main_features_after} (+{main_features_after - main_features_before})")
        print(f"   Outcomes: {main_outcomes_before} → {main_outcomes_after}")
        
        training_ready = main_features_after >= 50 and main_outcomes_after >= 50
        print(f"   Training readiness: {'✅ READY' if training_ready else '❌ INSUFFICIENT'}")
        
        if training_ready:
            print(f"\n🎉 SUCCESS! Database consolidated and ready for ML training")
            print(f"   No synthetic data needed - using real market data!")
        
        return training_ready
        
    except Exception as e:
        print(f"❌ Consolidation error: {e}")
        return False

def verify_database_consistency():
    """
    Verify that the database now matches morning routine expectations
    """
    print(f"\n🔍 Verifying database consistency...")
    
    db_path = "data/ml_models/enhanced_training_data.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check features by symbol (should match 7 banks)
        cursor.execute("""
            SELECT symbol, COUNT(*) as count 
            FROM enhanced_features 
            GROUP BY symbol 
            ORDER BY symbol
        """)
        symbol_counts = cursor.fetchall()
        
        print(f"   📊 Banks in database:")
        for symbol, count in symbol_counts:
            print(f"     {symbol}: {count} features")
        
        total_banks = len(symbol_counts)
        total_features = sum(count for _, count in symbol_counts)
        
        print(f"   📈 Summary:")
        print(f"     Banks: {total_banks}")
        print(f"     Total features: {total_features}")
        
        # Check if this now matches morning routine output
        if total_banks == 7 and total_features >= 300:
            print(f"   ✅ Database now consistent with morning routine expectations!")
        else:
            print(f"   ⚠️ Still some inconsistency - may need morning routine re-run")
        
        conn.close()
        return total_banks == 7
        
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database consolidation fix...\n")
    
    success = consolidate_remote_databases()
    
    if success:
        verify_database_consistency()
        print(f"\n✅ Database consolidation complete!")
        print(f"💡 Try running: python -m app.main morning")
        print(f"   Should now show consistent data between routine and database")
    else:
        print(f"\n❌ Consolidation failed. Manual review needed.")
    
    print(f"\n" + "=" * 50)
