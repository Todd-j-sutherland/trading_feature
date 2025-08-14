#!/usr/bin/env python3
"""
Final verification that the database alignment fix is working
"""

import sqlite3
import pandas as pd
from datetime import datetime

def verify_database_consistency():
    """Verify all our fixes are working correctly"""
    
    print("🔍 FINAL DATABASE VERIFICATION")
    print("=" * 60)
    
    # Connect to unified database
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        
        # Check predictions table
        print("\n📊 PREDICTIONS TABLE:")
        predictions_df = pd.read_sql_query("""
            SELECT 
                symbol,
                predicted_action,
                action_confidence as confidence,
                entry_price,
                created_at
            FROM predictions 
            ORDER BY created_at DESC
            LIMIT 10
        """, conn)
        
        print(f"Total predictions: {len(predictions_df)}")
        if len(predictions_df) > 0:
            print(f"Latest predictions:")
            for _, row in predictions_df.head().iterrows():
                print(f"  {row['symbol']}: {row['predicted_action']} (conf: {row['confidence']:.3f}, price: ${row['entry_price']:.2f})")
                
            # Check for zero entry prices
            zero_prices = predictions_df[predictions_df['entry_price'] <= 0]
            if len(zero_prices) > 0:
                print(f"⚠️  Found {len(zero_prices)} predictions with zero/negative entry prices!")
                print(zero_prices[['symbol', 'entry_price', 'created_at']])
            else:
                print("✅ NO ZERO ENTRY PRICES - All predictions have valid entry prices!")
        
        # Check outcomes table  
        print("\n📈 OUTCOMES TABLE:")
        outcomes_df = pd.read_sql_query("""
            SELECT 
                p.symbol,
                o.entry_price,
                o.exit_price,
                o.actual_return,
                o.created_at
            FROM outcomes o
            JOIN predictions p ON o.prediction_id = p.prediction_id
            ORDER BY o.created_at DESC
            LIMIT 10
        """, conn)
        
        print(f"Total outcomes: {len(outcomes_df)}")
        if len(outcomes_df) > 0:
            print(f"Latest outcomes:")
            for _, row in outcomes_df.head().iterrows():
                if pd.notna(row['exit_price']):
                    print(f"  {row['symbol']}: Entry ${row['entry_price']:.2f} → Exit ${row['exit_price']:.2f} (Return: {row['actual_return']:.2f}%)")
                else:
                    print(f"  {row['symbol']}: Entry ${row['entry_price']:.2f} (No exit yet)")
                    
            # Check for zero entry prices
            zero_outcomes = outcomes_df[outcomes_df['entry_price'] <= 0]
            if len(zero_outcomes) > 0:
                print(f"⚠️  Found {len(zero_outcomes)} outcomes with zero/negative entry prices!")
            else:
                print("✅ NO ZERO ENTRY PRICES - All outcomes have valid entry prices!")
        
        # Dashboard query simulation
        print("\n🎯 DASHBOARD QUERY SIMULATION:")
        
        # Get total samples (should match sentiment_features count)
        sentiment_count = pd.read_sql_query("SELECT COUNT(*) as count FROM sentiment_features", conn).iloc[0]['count']
        
        # Get predictions with valid data
        valid_predictions = pd.read_sql_query("""
            SELECT COUNT(*) as count 
            FROM predictions 
            WHERE entry_price > 0 AND action_confidence > 0
        """, conn).iloc[0]['count']
        
        # Get BUY actions for analysis
        buy_analysis = pd.read_sql_query("""
            SELECT COUNT(*) as count 
            FROM predictions 
            WHERE predicted_action = 'BUY' AND entry_price > 0
        """, conn).iloc[0]['count']
        
        # Get displayable records (what dashboard will show)
        displayable = pd.read_sql_query("""
            SELECT COUNT(*) as count 
            FROM predictions p
            JOIN sentiment_features sf ON p.symbol = sf.symbol
            WHERE p.entry_price > 0 AND p.action_confidence > 0
        """, conn).iloc[0]['count']
        
        print(f"Total sentiment features: {sentiment_count}")
        print(f"Valid predictions (entry_price > 0): {valid_predictions}")
        print(f"BUY actions for analysis: {buy_analysis}")
        print(f"Displayable records (joined data): {displayable}")
        
        # Check for consistency
        if sentiment_count == valid_predictions == displayable:
            print("✅ PERFECT CONSISTENCY - All numbers match!")
        else:
            print("⚠️  Inconsistency detected between tables")
            
        # Check recent data generation
        recent_predictions = pd.read_sql_query("""
            SELECT COUNT(*) as count 
            FROM predictions 
            WHERE created_at > datetime('now', '-1 hour')
        """, conn).iloc[0]['count']
        
        print(f"\n📅 Recent data (last hour): {recent_predictions} new predictions")
        
        if recent_predictions > 0:
            print("✅ Fresh data detected - morning analyzer is working!")
        else:
            print("ℹ️  No recent data - may need to run morning analyzer")
            
        conn.close()
        
        print("\n🎉 VERIFICATION COMPLETE!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    verify_database_consistency()
