#!/usr/bin/env python3
"""
Simple Database Examination Tool
Check what data we have in the trading predictions database
"""

import sqlite3
import sys

def examine_database():
    """Simple database examination"""
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        print("🔍 TRADING PREDICTIONS DATABASE ANALYSIS")
        print("=" * 50)
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   📈 Total rows: {count:,}")
            
            if count > 0:
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print(f"   📄 Columns ({len(columns)}):")
                for col in columns:
                    print(f"     - {col[1]} ({col[2]})")
                
                # Show date range if timestamp column exists
                timestamp_cols = ['prediction_timestamp', 'timestamp', 'created_at', 'date']
                for ts_col in timestamp_cols:
                    try:
                        cursor.execute(f"SELECT MIN({ts_col}), MAX({ts_col}) FROM {table_name} WHERE {ts_col} IS NOT NULL;")
                        date_range = cursor.fetchone()
                        if date_range[0]:
                            print(f"   📅 Date range ({ts_col}): {date_range[0]} to {date_range[1]}")
                            break
                    except:
                        continue
                
                # Show symbols if available
                try:
                    cursor.execute(f"SELECT DISTINCT symbol FROM {table_name} LIMIT 10;")
                    symbols = cursor.fetchall()
                    if symbols:
                        symbol_list = [s[0] for s in symbols]
                        print(f"   🏢 Symbols: {', '.join(symbol_list)}")
                except:
                    pass
                
                # Show sample data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
                samples = cursor.fetchall()
                print(f"   📄 Sample rows:")
                for i, row in enumerate(samples, 1):
                    row_str = str(row)
                    if len(row_str) > 80:
                        row_str = row_str[:80] + "..."
                    print(f"     {i}: {row_str}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    examine_database()
