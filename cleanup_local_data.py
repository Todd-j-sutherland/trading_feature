#!/usr/bin/env python3
"""
Local Data Directory Cleanup
Removes unnecessary databases and files from data/* while preserving essential data
"""

import os
import shutil
import sqlite3
from pathlib import Path
import subprocess

def get_directory_size(path):
    """Get directory size in MB"""
    result = subprocess.run(['du', '-sm', path], capture_output=True, text=True)
    if result.returncode == 0:
        return int(result.stdout.split()[0])
    return 0

def check_database_content(db_path):
    """Check if database has meaningful content"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        # Count total records across all tables
        total_records = 0
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                total_records += cursor.fetchone()[0]
            except:
                pass
        
        conn.close()
        return table_count, total_records
    except:
        return 0, 0

def main():
    data_dir = Path("data")
    
    print("🧹 LOCAL DATA DIRECTORY CLEANUP")
    print("=" * 50)
    
    # Check current directory size
    total_size_before = get_directory_size("data")
    print(f"\n📊 Current data directory size: {total_size_before} MB")
    
    # Files and directories to remove
    items_to_remove = [
        # Empty or unnecessary databases
        "enhanced_outcomes.db",  # Empty (0 tables)
        "outcomes.db",          # Empty (0 tables)
        
        # Backup and duplicate databases  
        "trading_unified.db.backup_20250810_091517",  # 2.1MB backup
        "trading_unified.db",       # 1.7MB - not used by current system
        "trading_data.db",          # 128KB, only 3 tables
        
        # Large directories that can be regenerated
        "migration_backup/",    # 91MB - old migration data
        "ml_models/",          # 45MB - can be retrained
        "quality_models/",     # 2.9MB - can be regenerated
        
        # Cache and temporary files
        "marketaux_cache.json", # 896KB cache file
        "sentiment_history.json", # 60KB old sentiment data
        "multi_bank_collector.log", # 24KB log file
        "marketaux_usage.json", # 4KB usage tracking
        
        # Empty directories
        "cache/",
        "locks/",
        "json_backups/",
        "historical/",
        "sentiment_cache/",
        "sentiment_history/",
        "position_tracking/",
        "ml_trading_sessions/",
        "ml_performance/",
        "ml_monitoring/",
        "ml_performance_history/",
        
        # Report directories (can be regenerated)
        "fix_reports/",
        "quality_reports/",
        "impact_analysis/",
        "hold_analysis/",
    ]
    
    # Keep these essential files
    keep_files = [
        "trading_predictions.db",  # Main database - actively used by current system
    ]
    
    print(f"\n🔍 Analysis of databases:")
    for db_file in ["trading_predictions.db", "trading_unified.db", "trading_data.db", "enhanced_outcomes.db", "outcomes.db"]:
        if (data_dir / db_file).exists():
            tables, records = check_database_content(data_dir / db_file)
            size_mb = (data_dir / db_file).stat().st_size / (1024*1024)
            status = "✅ KEEP" if db_file in keep_files else "❌ REMOVE"
            print(f"   {db_file}: {tables} tables, {records} records, {size_mb:.1f}MB - {status}")
    
    print(f"\n🗑️  Items to remove:")
    total_removed_size = 0
    
    for item in items_to_remove:
        item_path = data_dir / item
        if item_path.exists():
            if item_path.is_dir():
                size = get_directory_size(str(item_path))
                print(f"   📁 {item} ({size}MB)")
                total_removed_size += size
            else:
                size_mb = item_path.stat().st_size / (1024*1024)
                print(f"   📄 {item} ({size_mb:.1f}MB)")
                total_removed_size += size_mb
    
    print(f"\n💾 Items to keep:")
    for item in keep_files:
        item_path = data_dir / item
        if item_path.exists():
            size_mb = item_path.stat().st_size / (1024*1024)
            print(f"   ✅ {item} ({size_mb:.1f}MB)")
    
    print(f"\n📈 Space savings: ~{total_removed_size:.1f}MB will be freed")
    
    # Confirm before deletion
    response = input(f"\n❓ Proceed with cleanup? This will remove {len(items_to_remove)} items (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return
    
    print(f"\n🧹 Starting cleanup...")
    removed_count = 0
    
    for item in items_to_remove:
        item_path = data_dir / item
        if item_path.exists():
            try:
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                    print(f"   ✅ Removed directory: {item}")
                else:
                    item_path.unlink()
                    print(f"   ✅ Removed file: {item}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {item}: {e}")
    
    # Check final size
    total_size_after = get_directory_size("data")
    actual_savings = total_size_before - total_size_after
    
    print(f"\n🎉 CLEANUP COMPLETE!")
    print(f"   📊 Before: {total_size_before}MB")
    print(f"   📊 After: {total_size_after}MB") 
    print(f"   💾 Saved: {actual_savings}MB")
    print(f"   🗑️  Removed: {removed_count} items")
    
    print(f"\n✅ Essential databases preserved:")
    print(f"   • trading_predictions.db (main production database - actively used)")
    
    print(f"\n🔄 Next steps:")
    print(f"   • Run 'python trigger_enhanced_analytics.py' to regenerate ML models if needed")
    print(f"   • Cache files will be regenerated automatically during normal operation")

if __name__ == "__main__":
    main()
