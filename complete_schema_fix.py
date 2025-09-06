#!/usr/bin/env python3
"""
Complete Remote Database Schema Fixer
Add all missing market-aware columns to the predictions table
"""

import sqlite3
import sys
from pathlib import Path

def add_missing_columns(db_path="predictions.db"):
    """Add all missing market-aware columns to predictions table"""
    
    print(f"🔧 Adding missing market-aware columns to: {db_path}")
    
    # List of required columns for market-aware predictions
    required_columns = [
        ("market_context", "TEXT", "NEUTRAL"),
        ("market_trend_pct", "REAL", "0.0"),
        ("market_volatility", "REAL", "0.0"),
        ("market_momentum", "REAL", "0.0"),
        ("sector_performance", "REAL", "0.0"),
        ("volume_profile", "TEXT", "NORMAL"),
        ("risk_level", "TEXT", "MEDIUM"),
        ("confidence_components", "TEXT", "{}"),
        ("technical_indicators", "TEXT", "{}"),
        ("news_impact_score", "REAL", "0.0"),
        ("volume_trend_score", "REAL", "0.0"),
        ("price_momentum", "REAL", "0.0")
    ]
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(predictions);")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Current columns: {len(existing_columns)} columns")
        
        # Add missing columns one by one
        columns_added = 0
        for col_name, col_type, default_value in required_columns:
            if col_name not in existing_columns:
                try:
                    print(f"➕ Adding column: {col_name} ({col_type})")
                    cursor.execute(f"""
                        ALTER TABLE predictions 
                        ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'
                    """)
                    columns_added += 1
                except Exception as e:
                    print(f"⚠️  Failed to add {col_name}: {e}")
            else:
                print(f"✅ Column {col_name} already exists")
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(predictions);")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Final schema: {len(final_columns)} columns")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"✅ Added {columns_added} new columns to predictions table!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False

def verify_schema(db_path="predictions.db"):
    """Verify the database schema is complete"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get full schema info
        cursor.execute("PRAGMA table_info(predictions);")
        columns_info = cursor.fetchall()
        
        print("\n📊 FINAL PREDICTIONS TABLE SCHEMA:")
        print("-" * 60)
        for col_info in columns_info:
            col_id, name, type_, notnull, default, pk = col_info
            print(f"  {name:<25} {type_:<10} {f'DEFAULT {default}' if default else ''}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying schema: {e}")
        return False

def test_market_aware_insert(db_path="predictions.db"):
    """Test if we can insert a market-aware prediction"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test insert with market-aware data
        test_data = {
            'prediction_id': 'test_market_aware_001',
            'symbol': 'TEST.AX',
            'predicted_action': 'HOLD',
            'action_confidence': 0.65,
            'predicted_direction': 'UP',
            'predicted_magnitude': 0.02,
            'feature_vector': '1,2,3,4,5',
            'model_version': 'market_aware_ensemble',
            'market_context': 'BULLISH',
            'market_trend_pct': 1.25,
            'market_volatility': 0.15,
            'confidence_components': '{"tech": 0.4, "news": 0.2, "volume": 0.05}'
        }
        
        # Build insert query
        columns = ', '.join(test_data.keys())
        placeholders = ', '.join(['?' for _ in test_data])
        
        cursor.execute(f"""
            INSERT OR REPLACE INTO predictions ({columns})
            VALUES ({placeholders})
        """, list(test_data.values()))
        
        # Verify insert
        cursor.execute("SELECT * FROM predictions WHERE prediction_id = ?", 
                      (test_data['prediction_id'],))
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if result:
            print("✅ Market-aware prediction insert test: SUCCESS!")
            return True
        else:
            print("❌ Market-aware prediction insert test: FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Insert test failed: {e}")
        return False

def main():
    """Main execution function"""
    
    print("🔧 Complete Remote Database Schema Fixer")
    print("=" * 60)
    
    # Add missing columns
    success = add_missing_columns()
    
    if success:
        # Verify schema
        verify_schema()
        
        # Test market-aware insert
        test_market_aware_insert()
        
        print("\n🚀 Database is now ready for market-aware predictions!")
    else:
        print("\n❌ Schema update failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
