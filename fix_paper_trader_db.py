#!/usr/bin/env python3
"""
IG Markets Paper Trader - Fixed Database Connection
Quick fix for the database connection issue
"""

import sqlite3
import sys

def fix_paper_trader():
    """Fix the database connection issue in the paper trader"""
    
    # Read the current file
    with open('/root/test/ig_markets_paper_trader.py', 'r') as f:
        content = f.read()
    
    # Find and replace the problematic query
    old_query = '''        # Find predictions from last 4 hours that aren't already traded
        cursor.execute("""
            SELECT p.* FROM predictions p
            LEFT JOIN paper_trades pt ON p.prediction_id = pt.prediction_id
            WHERE pt.prediction_id IS NULL
            AND p.prediction_timestamp > datetime('now', '-4 hours')
            AND p.predicted_action IN ('BUY', 'SELL')
            ORDER BY p.prediction_timestamp DESC
        """)'''
    
    new_query = '''        # Get already traded prediction IDs from paper trading database
        paper_conn = sqlite3.connect(self.db_path)
        paper_cursor = paper_conn.cursor()
        paper_cursor.execute("SELECT DISTINCT prediction_id FROM paper_trades")
        traded_ids = [row[0] for row in paper_cursor.fetchall()]
        paper_conn.close()
        
        # Find predictions from last 4 hours that aren't already traded
        if traded_ids:
            placeholders = ','.join(['?' for _ in traded_ids])
            cursor.execute(f"""
                SELECT * FROM predictions 
                WHERE prediction_id NOT IN ({placeholders})
                AND prediction_timestamp > datetime('now', '-4 hours')
                AND predicted_action IN ('BUY', 'SELL')
                ORDER BY prediction_timestamp DESC
            """, traded_ids)
        else:
            cursor.execute("""
                SELECT * FROM predictions 
                WHERE prediction_timestamp > datetime('now', '-4 hours')
                AND predicted_action IN ('BUY', 'SELL')
                ORDER BY prediction_timestamp DESC
            """)'''
    
    # Replace the problematic section
    if old_query in content:
        content = content.replace(old_query, new_query)
        
        # Write the fixed version
        with open('/root/test/ig_markets_paper_trader.py', 'w') as f:
            f.write(content)
        
        print("✅ Fixed database connection issue")
        return True
    else:
        print("❌ Could not find the problematic query to fix")
        return False

if __name__ == "__main__":
    fix_paper_trader()
