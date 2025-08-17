#!/usr/bin/env python3
"""
Cleanup Stale Trading Data - Remove old predictions and outcomes
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def cleanup_stale_data(db_path='data/trading_predictions.db', days_to_keep=7):
    """
    Remove predictions and outcomes older than specified days
    Default: Keep only last 7 days of data
    """
    print(f"🧹 Cleaning up stale trading data (keeping last {days_to_keep} days)...")
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cutoff_str = cutoff_date.isoformat()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get counts before cleanup
    pred_count_before = cursor.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    outcome_count_before = cursor.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
    enhanced_count_before = cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes").fetchone()[0]
    perf_count_before = cursor.execute("SELECT COUNT(*) FROM model_performance").fetchone()[0]
    
    print(f"📊 Data before cleanup:")
    print(f"   Predictions: {pred_count_before}")
    print(f"   Outcomes: {outcome_count_before}")
    print(f"   Enhanced Outcomes: {enhanced_count_before}")
    print(f"   Model Performance: {perf_count_before}")
    print(f"   Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show what will be deleted
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE prediction_timestamp < ?", (cutoff_str,))
    stale_predictions = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM outcomes o 
        INNER JOIN predictions p ON o.prediction_id = p.prediction_id 
        WHERE p.prediction_timestamp < ?
    """, (cutoff_str,))
    stale_outcomes = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM enhanced_outcomes eo 
        WHERE eo.prediction_timestamp < ?
    """, (cutoff_str,))
    stale_enhanced = cursor.fetchone()[0]
    
    print(f"\n🗑️  Will delete:")
    print(f"   {stale_predictions} stale predictions")
    print(f"   {stale_outcomes} stale outcomes")
    print(f"   {stale_enhanced} stale enhanced outcomes")
    
    if stale_predictions == 0:
        print("✅ No stale data found - all data is recent!")
        conn.close()
        return
    
    # Ask for confirmation
    response = input(f"\n⚠️  Delete {stale_predictions + stale_outcomes + stale_enhanced} stale records? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cleanup cancelled")
        conn.close()
        return
    
    # Delete stale enhanced outcomes first (has foreign key dependency)
    cursor.execute("DELETE FROM enhanced_outcomes WHERE prediction_timestamp < ?", (cutoff_str,))
    deleted_enhanced = cursor.rowcount
    
    # Delete stale outcomes (has foreign key dependency on predictions)
    cursor.execute("""
        DELETE FROM outcomes WHERE prediction_id IN (
            SELECT prediction_id FROM predictions WHERE prediction_timestamp < ?
        )
    """, (cutoff_str,))
    deleted_outcomes = cursor.rowcount
    
    # Delete stale predictions
    cursor.execute("DELETE FROM predictions WHERE prediction_timestamp < ?", (cutoff_str,))
    deleted_predictions = cursor.rowcount
    
    # Clean up model performance records older than 30 days
    old_perf_cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    cursor.execute("DELETE FROM model_performance WHERE evaluation_period_start < ?", (old_perf_cutoff,))
    deleted_performance = cursor.rowcount
    
    conn.commit()
    
    # Get counts after cleanup
    pred_count_after = cursor.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    outcome_count_after = cursor.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
    enhanced_count_after = cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes").fetchone()[0]
    perf_count_after = cursor.execute("SELECT COUNT(*) FROM model_performance").fetchone()[0]
    
    print(f"\n✅ Cleanup completed!")
    print(f"   Deleted {deleted_predictions} predictions")
    print(f"   Deleted {deleted_outcomes} outcomes")
    print(f"   Deleted {deleted_enhanced} enhanced outcomes")
    print(f"   Deleted {deleted_performance} old performance records")
    
    print(f"\n📊 Data after cleanup:")
    print(f"   Predictions: {pred_count_after} (was {pred_count_before})")
    print(f"   Outcomes: {outcome_count_after} (was {outcome_count_before})")
    print(f"   Enhanced Outcomes: {enhanced_count_after} (was {enhanced_count_before})")
    print(f"   Model Performance: {perf_count_after} (was {perf_count_before})")
    
    # Show remaining data timespan
    cursor.execute("SELECT MIN(prediction_timestamp), MAX(prediction_timestamp) FROM predictions")
    result = cursor.fetchone()
    if result[0]:
        print(f"\n📅 Remaining data spans: {result[0]} to {result[1]}")
    
    conn.close()
    
    print(f"\n🎉 Database cleanup successful! Keeping only recent {days_to_keep} days of data.")

def show_data_age_summary(db_path='data/trading_predictions.db'):
    """Show age distribution of current data"""
    print("📅 Current Data Age Summary:")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Age analysis
    cursor.execute("""
        SELECT 
            DATE(prediction_timestamp) as date,
            COUNT(*) as predictions
        FROM predictions 
        GROUP BY DATE(prediction_timestamp)
        ORDER BY date DESC
    """)
    
    results = cursor.fetchall()
    total_predictions = sum(r[1] for r in results)
    
    print(f"Total predictions: {total_predictions}")
    print("\nBy date:")
    for date, count in results:
        age = (datetime.now() - datetime.fromisoformat(date + 'T00:00:00')).days
        print(f"   {date}: {count} predictions ({age} days old)")
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup stale trading data')
    parser.add_argument('--days', type=int, default=7, help='Days of data to keep (default: 7)')
    parser.add_argument('--summary', action='store_true', help='Show data age summary only')
    parser.add_argument('--remote', action='store_true', help='Run on remote server')
    
    args = parser.parse_args()
    
    if args.summary:
        if args.remote:
            print("Use: ssh root@170.64.199.151 'cd /root/test && python3 cleanup_stale_data.py --summary'")
        else:
            show_data_age_summary()
    else:
        if args.remote:
            print("Transferring to remote server and running cleanup...")
            print("Use: ssh root@170.64.199.151 'cd /root/test && python3 cleanup_stale_data.py --days 7'")
        else:
            cleanup_stale_data(days_to_keep=args.days)
