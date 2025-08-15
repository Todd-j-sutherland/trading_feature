#!/usr/bin/env python3
"""
Simple Data Quality Fix
=======================

A simpler, more reliable approach to fix the data quality issues.
"""

import subprocess
from datetime import datetime

def run_remote_query(query, description=""):
    """Execute SQL query on remote database"""
    cmd = f"ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db \"{query}\"'"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            if description:
                print(f"✅ {description}")
            return result.stdout.strip()
        else:
            if description:
                print(f"❌ {description}: {result.stderr}")
            return None
    except Exception as e:
        if description:
            print(f"❌ {description}: {e}")
        return None

def fix_data_quality():
    print("🔧 SIMPLE DATA QUALITY FIX")
    print("=" * 50)
    
    # 1. Remove duplicates by keeping only the latest record per symbol per day
    print("\n1. Removing duplicate enhanced_features...")
    
    # First, let's see what we have
    count = run_remote_query(
        "SELECT COUNT(*) FROM enhanced_features;",
        "Counting current records"
    )
    
    if count:
        print(f"   Current records: {count}")
    
    # Remove duplicates using a simpler approach
    dedup_query = """
    DELETE FROM enhanced_features 
    WHERE id NOT IN (
        SELECT MAX(id) 
        FROM enhanced_features 
        GROUP BY symbol, DATE(timestamp)
    );
    """
    
    run_remote_query(dedup_query, "Removing duplicate records (keeping latest per symbol per day)")
    
    # Check final count
    final_count = run_remote_query(
        "SELECT COUNT(*) FROM enhanced_features;",
        "Counting deduplicated records"
    )
    
    if final_count:
        print(f"   Final records: {final_count}")
    
    # 2. Fix null analysis_timestamps
    print("\n2. Fixing null analysis_timestamps...")
    
    null_count = run_remote_query(
        "SELECT COUNT(*) FROM enhanced_features WHERE analysis_timestamp IS NULL;",
        "Counting null analysis_timestamps"
    )
    
    if null_count and int(null_count) > 0:
        print(f"   Found {null_count} null timestamps")
        
        run_remote_query(
            "UPDATE enhanced_features SET analysis_timestamp = timestamp WHERE analysis_timestamp IS NULL;",
            "Updating null analysis_timestamps"
        )
        
        # Verify
        remaining = run_remote_query(
            "SELECT COUNT(*) FROM enhanced_features WHERE analysis_timestamp IS NULL;",
            "Verifying fix"
        )
        print(f"   Remaining null timestamps: {remaining}")
    else:
        print("   No null analysis_timestamps found")
    
    # 3. Add unique constraint
    print("\n3. Adding unique constraint...")
    
    run_remote_query(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_enhanced_features_unique ON enhanced_features(symbol, DATE(timestamp));",
        "Creating unique constraint"
    )
    
    # 4. Verify final state
    print("\n4. Final verification...")
    
    # Check for any remaining duplicates
    duplicates = run_remote_query(
        "SELECT symbol, DATE(timestamp), COUNT(*) FROM enhanced_features GROUP BY symbol, DATE(timestamp) HAVING COUNT(*) > 1;",
        "Checking for remaining duplicates"
    )
    
    if not duplicates:
        print("   ✅ No duplicates found")
    else:
        print(f"   ❌ Still have duplicates: {duplicates}")
    
    # Show final summary
    summary = run_remote_query("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT DATE(timestamp)) as unique_dates,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM enhanced_features;
    """, "Getting final summary")
    
    if summary:
        parts = summary.split('|')
        if len(parts) >= 5:
            total, symbols, dates, earliest, latest = parts
            print(f"\n📊 FINAL SUMMARY:")
            print(f"   Total Records: {total}")
            print(f"   Unique Symbols: {symbols}")
            print(f"   Unique Dates: {dates}")
            print(f"   Date Range: {earliest} to {latest}")

if __name__ == "__main__":
    fix_data_quality()
