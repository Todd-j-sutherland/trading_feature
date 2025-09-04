#!/usr/bin/env python3
"""
Database Structure Cleanup Script
Removes deprecated tables and optimizes the trading database
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

def backup_database(db_path: str) -> str:
    """Create a backup of the database before cleanup"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path

def analyze_table_usage(db_path: str):
    """Analyze which tables are actually being used"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n📊 TABLE USAGE ANALYSIS")
    print("=" * 50)
    
    table_stats = {}
    
    for table in tables:
        try:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            # Get recent activity (if has timestamp column)
            recent_count = 0
            timestamp_cols = ['timestamp', 'created_at', 'prediction_timestamp', 'evaluation_timestamp']
            
            for col in timestamp_cols:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} >= datetime('now', '-7 days')")
                    recent_count = cursor.fetchone()[0]
                    break
                except:
                    continue
            
            # Determine usage level
            usage_level = "🔴 UNUSED"
            if row_count == 0:
                usage_level = "⚫ EMPTY"
            elif recent_count > 0:
                usage_level = "🟢 ACTIVE"
            elif row_count > 100:
                usage_level = "🟡 LEGACY"
            
            table_stats[table] = {
                'total_rows': row_count,
                'recent_rows': recent_count,
                'usage_level': usage_level
            }
            
            print(f"{usage_level} {table}: {row_count:,} total, {recent_count} recent")
            
        except Exception as e:
            print(f"❌ Error analyzing {table}: {e}")
    
    conn.close()
    return table_stats

def identify_deprecated_tables(table_stats: dict) -> list:
    """Identify tables that can be safely removed"""
    
    # Known deprecated tables based on analysis
    deprecated_patterns = [
        'model_performance',  # Not used by dashboard
        'biased_predictions_backup_',
        'enhanced_features_backup_',
        'invalid_predictions_backup',
        'ml_backup_',
        'predictions_backup_',
        '_backup_',
        '_9999'  # Backup tables with this pattern
    ]
    
    deprecated_tables = []
    
    for table, stats in table_stats.items():
        # Empty tables that aren't core
        if stats['total_rows'] == 0 and table not in ['predictions', 'outcomes', 'enhanced_features']:
            deprecated_tables.append(table)
        
        # Tables matching deprecated patterns
        for pattern in deprecated_patterns:
            if pattern in table:
                deprecated_tables.append(table)
                break
        
        # Specific deprecated tables we identified
        if table in ['model_performance']:  # Not used in production dashboard
            deprecated_tables.append(table)
    
    return list(set(deprecated_tables))  # Remove duplicates

def cleanup_database(db_path: str, dry_run: bool = True):
    """Clean up deprecated tables and optimize database"""
    
    print(f"\n🧹 DATABASE CLEANUP {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print("=" * 50)
    
    # Backup first if not dry run
    if not dry_run:
        backup_path = backup_database(db_path)
    
    # Analyze current usage
    table_stats = analyze_table_usage(db_path)
    
    # Identify deprecated tables
    deprecated_tables = identify_deprecated_tables(table_stats)
    
    print(f"\n🗑️  TABLES TO REMOVE ({len(deprecated_tables)}):")
    for table in deprecated_tables:
        stats = table_stats.get(table, {})
        print(f"   - {table} ({stats.get('total_rows', 0)} rows)")
    
    if not dry_run and deprecated_tables:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        removed_count = 0
        for table in deprecated_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Removed: {table}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {table}: {e}")
        
        # Optimize database
        print("\n🔧 Optimizing database...")
        cursor.execute("VACUUM")
        cursor.execute("REINDEX")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleanup completed: {removed_count} tables removed")
    
    # Show recommended indexes
    print(f"\n📊 RECOMMENDED INDEXES:")
    recommended_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(prediction_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_prediction_id ON outcomes(prediction_id);",
        "CREATE INDEX IF NOT EXISTS idx_outcomes_eval_time ON outcomes(evaluation_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_enhanced_features_symbol ON enhanced_features(symbol);"
    ]
    
    for index in recommended_indexes:
        print(f"   {index}")
    
    if not dry_run:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for index in recommended_indexes:
            try:
                cursor.execute(index)
                print(f"✅ Created index")
            except Exception as e:
                print(f"⚠️  Index already exists or failed: {e}")
        conn.commit()
        conn.close()

def main():
    """Main cleanup function"""
    db_path = "data/trading_predictions.db"
    
    print("🔍 COMPREHENSIVE DATABASE STRUCTURE CLEANUP")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Database: {db_path}")
    
    # First run in dry-run mode
    print("\n👀 DRY RUN - No changes will be made")
    cleanup_database(db_path, dry_run=True)
    
    # Ask user for confirmation
    response = input("\n❓ Do you want to proceed with the cleanup? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        print("\n🚀 EXECUTING CLEANUP...")
        cleanup_database(db_path, dry_run=False)
        print("\n✅ DATABASE CLEANUP COMPLETED!")
    else:
        print("\n❌ Cleanup cancelled")

if __name__ == "__main__":
    main()
