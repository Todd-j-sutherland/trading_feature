#!/usr/bin/env python3
"""
Fix missing exit prices and return percentages in enhanced_outcomes table.
The synthetic outcomes were created with 0 exit prices as placeholders.
This script calculates the actual exit prices based on entry_price and magnitude values.
"""

import sqlite3
import pandas as pd
from datetime import datetime

def fix_exit_prices_and_returns():
    """Fix missing exit prices and return percentages"""
    print("🔧 Starting Exit Price & Return Calculation Fix")
    print("=" * 60)
    
    db_path = 'data/trading_unified.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all records with missing exit prices (0 or NULL)
        print("📊 Checking for records with missing exit prices...")
        query = '''
            SELECT id, entry_price, price_magnitude_1h, price_magnitude_4h, price_magnitude_1d,
                   exit_price_1h, exit_price_4h, exit_price_1d, return_pct, symbol, optimal_action
            FROM enhanced_outcomes 
            WHERE (exit_price_1h = 0 OR exit_price_1h IS NULL 
                   OR exit_price_4h = 0 OR exit_price_4h IS NULL
                   OR exit_price_1d = 0 OR exit_price_1d IS NULL
                   OR return_pct = 0 OR return_pct IS NULL)
            AND entry_price > 0
            ORDER BY id
        '''
        
        df = pd.read_sql_query(query, conn)
        print(f"Found {len(df)} records with missing exit prices")
        
        if len(df) == 0:
            print("✅ No records need fixing!")
            return
        
        # Display sample of data before fixing
        print("\n📋 Sample records before fixing:")
        print(df[['id', 'symbol', 'entry_price', 'price_magnitude_1d', 'exit_price_1d', 'return_pct']].head(10).to_string(index=False))
        
        # Calculate missing exit prices
        fixed_count = 0
        
        for _, row in df.iterrows():
            record_id = row['id']
            entry_price = row['entry_price']
            
            # Calculate exit prices based on magnitude percentages
            # magnitude is percentage change: (exit_price - entry_price) / entry_price * 100
            # So: exit_price = entry_price * (1 + magnitude/100)
            
            exit_price_1h = entry_price * (1 + row['price_magnitude_1h'] / 100)
            exit_price_4h = entry_price * (1 + row['price_magnitude_4h'] / 100) 
            exit_price_1d = entry_price * (1 + row['price_magnitude_1d'] / 100)
            
            # Return percentage is the same as 1-day magnitude
            return_pct = row['price_magnitude_1d']
            
            # Update the record
            update_query = '''
                UPDATE enhanced_outcomes 
                SET exit_price_1h = ?, 
                    exit_price_4h = ?, 
                    exit_price_1d = ?, 
                    return_pct = ?
                WHERE id = ?
            '''
            
            cursor.execute(update_query, (
                round(exit_price_1h, 4),
                round(exit_price_4h, 4), 
                round(exit_price_1d, 4),
                round(return_pct, 4),
                record_id
            ))
            
            fixed_count += 1
            
            if fixed_count % 50 == 0:
                print(f"  ✓ Fixed {fixed_count}/{len(df)} records...")
        
        conn.commit()
        print(f"\n✅ Successfully fixed {fixed_count} records!")
        
        # Verify the fix
        print("\n🔍 Verifying fix - checking updated records:")
        verification_query = '''
            SELECT symbol, entry_price, exit_price_1d, return_pct, optimal_action
            FROM enhanced_outcomes 
            WHERE id IN (SELECT id FROM (
                SELECT id FROM enhanced_outcomes ORDER BY id LIMIT 10
            ))
            ORDER BY id
        '''
        
        verification_df = pd.read_sql_query(verification_query, conn)
        print(verification_df.to_string(index=False))
        
        # Check overall data quality now
        print("\n📈 Updated Data Quality Summary:")
        quality_query = '''
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN exit_price_1h IS NULL OR exit_price_1h = 0 THEN 1 ELSE 0 END) as null_exit_1h,
                SUM(CASE WHEN exit_price_1d IS NULL OR exit_price_1d = 0 THEN 1 ELSE 0 END) as null_exit_1d,
                SUM(CASE WHEN return_pct IS NULL OR return_pct = 0 THEN 1 ELSE 0 END) as null_returns,
                ROUND(AVG(return_pct), 4) as avg_return,
                ROUND(MIN(return_pct), 4) as min_return,
                ROUND(MAX(return_pct), 4) as max_return
            FROM enhanced_outcomes
        '''
        
        quality_df = pd.read_sql_query(quality_query, conn)
        print(quality_df.to_string(index=False))
        
        print("\n🎯 Action Distribution with Returns:")
        action_query = '''
            SELECT 
                optimal_action,
                COUNT(*) as count,
                ROUND(AVG(return_pct), 4) as avg_return,
                ROUND(AVG(CASE WHEN return_pct > 0 THEN 1.0 ELSE 0.0 END), 4) as win_rate
            FROM enhanced_outcomes
            GROUP BY optimal_action
            ORDER BY count DESC
        '''
        
        action_df = pd.read_sql_query(action_query, conn)
        print(action_df.to_string(index=False))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print("\n✅ Exit price and return calculation fix completed!")

if __name__ == "__main__":
    fix_exit_prices_and_returns()
