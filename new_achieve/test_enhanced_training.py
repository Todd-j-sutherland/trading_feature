#!/usr/bin/env python3
"""
Test Enhanced Training Data Access

This script tests the exact same logic that the evening routine uses
to access enhanced training data.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

def test_enhanced_training_data():
    """Test the enhanced training data access"""
    print("🔍 Testing Enhanced Training Data Access")
    print("=" * 50)
    
    # Test both possible database paths
    data_dir = "data/ml_models"
    unified_db_path = os.path.join(data_dir, "trading_unified.db")
    old_db_path = os.path.join(data_dir, "enhanced_training_data.db")
    main_unified_path = "data/trading_unified.db"
    
    db_paths = [
        ("Main Unified DB", main_unified_path),
        ("ML Models Unified DB", unified_db_path), 
        ("Old Enhanced DB", old_db_path)
    ]
    
    for name, db_path in db_paths:
        print(f"\n📊 Testing: {name}")
        print(f"   Path: {db_path}")
        print(f"   Exists: {os.path.exists(db_path)}")
        
        if not os.path.exists(db_path):
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            
            # Test the exact query from enhanced_training_pipeline.py
            query = '''
                SELECT ef.*, eo.price_direction_1h, eo.price_direction_4h, eo.price_direction_1d,
                       eo.price_magnitude_1h, eo.price_magnitude_4h, eo.price_magnitude_1d,
                       eo.optimal_action, eo.confidence_score
                FROM enhanced_features ef
                INNER JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
                WHERE eo.price_direction_4h IS NOT NULL
                ORDER BY ef.timestamp
            '''
            
            df = pd.read_sql_query(query, conn)
            print(f"   Training Samples: {len(df)}")
            
            if len(df) > 0:
                print(f"   Columns: {len(df.columns)}")
                print(f"   Date Range: {df.iloc[0]['timestamp'] if 'timestamp' in df.columns else 'N/A'} to {df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else 'N/A'}")
                
                # Check for required features
                required_features = ['sentiment_score', 'rsi', 'macd_line', 'current_price']
                available_features = [f for f in required_features if f in df.columns]
                print(f"   Required Features Available: {len(available_features)}/{len(required_features)}")
                print(f"   Available: {available_features}")
                
                # Check outcomes
                outcome_cols = ['price_direction_1h', 'price_direction_4h', 'price_direction_1d']
                for col in outcome_cols:
                    if col in df.columns:
                        non_null = df[col].notna().sum()
                        print(f"   {col}: {non_null} non-null values")
            
            conn.close()
            
            if len(df) >= 50:
                print(f"   ✅ SUFFICIENT DATA ({len(df)} >= 50)")
            else:
                print(f"   ⚠️ INSUFFICIENT DATA ({len(df)} < 50)")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n🔧 Enhanced Training Pipeline Path Resolution:")
    print(f"   data_dir = 'data/ml_models'")
    print(f"   db_path = os.path.join(data_dir, 'trading_unified.db')")
    print(f"   Resolves to: {os.path.join('data/ml_models', 'trading_unified.db')}")
    print(f"   This path exists: {os.path.exists(os.path.join('data/ml_models', 'trading_unified.db'))}")

if __name__ == "__main__":
    test_enhanced_training_data()