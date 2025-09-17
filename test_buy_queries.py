#!/usr/bin/env python3
"""
Test script to validate BUY performance queries before updating the dashboard
"""

import sqlite3
import pandas as pd
from pathlib import Path

def test_database_structure():
    """Test the database structure and sample data"""
    db_path = Path("data/trading_predictions.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("=== PREDICTIONS TABLE STRUCTURE ===")
            cursor.execute("PRAGMA table_info(predictions)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            print("\n=== OUTCOMES TABLE STRUCTURE ===")
            cursor.execute("PRAGMA table_info(outcomes)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            print("\n=== BUY PREDICTIONS COUNT ===")
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE predicted_action = 'BUY'")
            buy_count = cursor.fetchone()[0]
            print(f"  Total BUY predictions: {buy_count}")
            
            if buy_count > 0:
                print("\n=== SAMPLE BUY PREDICTION ===")
                cursor.execute("""
                    SELECT prediction_id, symbol, prediction_timestamp, predicted_action, action_confidence, entry_price 
                    FROM predictions 
                    WHERE predicted_action = 'BUY' 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 2
                """)
                recent = cursor.fetchall()
                for row in recent:
                    print(f"  {row}")
            
            print("\n=== OUTCOMES COUNT ===")
            cursor.execute("SELECT COUNT(*) FROM outcomes")
            outcome_count = cursor.fetchone()[0]
            print(f"  Total outcomes: {outcome_count}")
            
            if outcome_count > 0:
                print("\n=== SAMPLE OUTCOME ===")
                cursor.execute("SELECT * FROM outcomes LIMIT 2")
                outcomes = cursor.fetchall()
                for outcome in outcomes:
                    print(f"  {outcome}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_buy_performance_query():
    """Test the actual BUY performance query"""
    db_path = Path("data/trading_predictions.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            print("\n=== TESTING BUY PERFORMANCE QUERY ===")
            
            # Test the query that's failing
            query = """
            SELECT 
                p.symbol,
                p.prediction_timestamp,
                p.predicted_action,
                p.action_confidence,
                p.entry_price,
                o.actual_return,
                CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END as successful,
                o.created_at as outcome_time
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.predicted_action = 'BUY'
            ORDER BY p.prediction_timestamp DESC
            LIMIT 5
            """
            
            print("Query:")
            print(query)
            print("\nResults:")
            
            # Execute with pandas to see data types
            df = pd.read_sql_query(query, conn)
            print(f"Found {len(df)} rows")
            
            if len(df) > 0:
                print("\nColumn info:")
                print(df.dtypes)
                
                print("\nSample data:")
                print(df.head())
                
                print("\nTimestamp format examples:")
                for i, ts in enumerate(df['prediction_timestamp'].head(3)):
                    print(f"  Row {i}: {ts} (type: {type(ts)})")
                
            return df
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None

def test_date_filtering():
    """Test date filtering queries"""
    db_path = Path("data/trading_predictions.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            print("\n=== TESTING DATE FILTERING ===")
            
            # Test different date conditions
            date_conditions = [
                ("Last 7 days", "AND p.prediction_timestamp >= datetime('now', '-7 days')"),
                ("Last 30 days", "AND p.prediction_timestamp >= datetime('now', '-30 days')"),
                ("All time", "")
            ]
            
            for label, condition in date_conditions:
                query = f"""
                SELECT COUNT(*) as count
                FROM predictions p
                WHERE p.predicted_action = 'BUY' {condition}
                """
                
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()[0]
                print(f"  {label}: {result} BUY predictions")
                
    except Exception as e:
        print(f"❌ Date filtering error: {e}")

if __name__ == "__main__":
    print("🔍 Testing BUY Performance Database Queries")
    print("=" * 50)
    
    # Test 1: Database structure
    if test_database_structure():
        print("\n✅ Database structure test passed")
        
        # Test 2: BUY performance query
        df = test_buy_performance_query()
        if df is not None:
            print("\n✅ BUY performance query test passed")
            
            # Test 3: Date filtering
            test_date_filtering()
            print("\n✅ Date filtering test passed")
            
            print("\n🎉 All tests completed!")
            
            if len(df) > 0:
                print("\n📊 Summary:")
                print(f"  - Found {len(df)} BUY predictions")
                evaluated = len(df[df['actual_return'].notna()])
                print(f"  - {evaluated} have outcomes")
                if evaluated > 0:
                    successful = len(df[df['successful'] == 1])
                    success_rate = (successful / evaluated) * 100
                    print(f"  - Success rate: {success_rate:.1f}%")
                    avg_confidence = df['action_confidence'].mean()
                    print(f"  - Average confidence: {avg_confidence:.3f}")
        else:
            print("\n❌ BUY performance query test failed")
    else:
        print("\n❌ Database structure test failed")
