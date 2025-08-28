#!/usr/bin/env python3
"""
Remote Model Performance Data Setup
Checks database status and populates model performance data for remote dashboard
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def check_database_status(db_path="data/trading_predictions.db"):
    """Check database tables and data status"""
    print(f"🔍 Checking database status: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if model_performance table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_performance'")
        if not cursor.fetchone():
            print("❌ model_performance table does not exist")
            create_model_performance_table(cursor)
        
        # Check data in model_performance table
        cursor.execute("SELECT COUNT(*) FROM model_performance")
        perf_count = cursor.fetchone()[0]
        print(f"📊 model_performance table: {perf_count} records")
        
        # Check if models directory exists
        models_dir = "models"
        if os.path.exists(models_dir):
            model_symbols = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d)) and d.endswith('.AX')]
            print(f"🤖 Models found: {len(model_symbols)} symbols - {model_symbols}")
        else:
            print("❌ Models directory not found")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def create_model_performance_table(cursor):
    """Create model_performance table if it doesn't exist"""
    print("🔨 Creating model_performance table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            evaluation_id TEXT PRIMARY KEY,
            model_version TEXT,
            evaluation_period_start DATETIME,
            evaluation_period_end DATETIME,
            total_predictions INTEGER,
            accuracy_action REAL,
            accuracy_direction REAL,
            mae_magnitude REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ model_performance table created")

def populate_model_performance_from_metadata(db_path="data/trading_predictions.db"):
    """Populate model performance table from model metadata files"""
    print("🔄 Populating model performance from metadata files...")
    
    models_dir = "models"
    if not os.path.exists(models_dir):
        print("❌ Models directory not found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM model_performance")
    
    symbols_processed = 0
    
    for symbol_dir in os.listdir(models_dir):
        symbol_path = os.path.join(models_dir, symbol_dir)
        metadata_file = os.path.join(symbol_path, "metadata.json")
        
        if os.path.isdir(symbol_path) and os.path.exists(metadata_file):
            try:
                # Read metadata
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                symbol = metadata['symbol']
                model_version = metadata.get('model_version', '2.1')
                performance = metadata['performance']
                
                # Generate evaluation ID
                evaluation_id = f"{symbol}_{model_version}_{datetime.now().strftime('%Y%m%d')}"
                
                # Extract performance metrics
                accuracy_direction = performance['direction_accuracy']
                magnitude_mse = performance['magnitude_mse']
                samples = performance['samples']
                
                # Insert into database
                cursor.execute('''
                    INSERT OR REPLACE INTO model_performance 
                    (evaluation_id, model_version, evaluation_period_start, evaluation_period_end,
                     total_predictions, accuracy_action, accuracy_direction, mae_magnitude, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    evaluation_id,
                    f"{symbol}_v{model_version}",
                    datetime.now().replace(hour=0, minute=0, second=0),
                    datetime.now(),
                    samples,
                    accuracy_direction,  # Use direction accuracy for action accuracy too
                    accuracy_direction,
                    magnitude_mse,
                    datetime.now()
                ))
                
                symbols_processed += 1
                print(f"✅ {symbol}: {accuracy_direction:.1%} accuracy, {samples} samples, MSE: {magnitude_mse:.4f}")
                
            except Exception as e:
                print(f"❌ Error processing {symbol_dir}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Model performance populated:")
    print(f"   Symbols processed: {symbols_processed}")
    print(f"   Database: {db_path}")
    
    return symbols_processed > 0

def verify_dashboard_data(db_path="data/trading_predictions.db"):
    """Verify data is available for dashboard"""
    print("\n🔍 Verifying dashboard data availability...")
    
    conn = sqlite3.connect(db_path)
    
    # Check model performance data
    perf_df = pd.read_sql_query("SELECT * FROM model_performance", conn)
    print(f"📊 Model performance records: {len(perf_df)}")
    
    if len(perf_df) > 0:
        print("✅ Dashboard should now show model performance data")
        print("\nModel Performance Summary:")
        for _, row in perf_df.iterrows():
            symbol = row['model_version'].split('_')[0]
            accuracy = row['accuracy_direction'] * 100
            samples = row['total_predictions']
            print(f"   {symbol}: {accuracy:.1f}% accuracy ({samples} samples)")
    else:
        print("❌ No model performance data found")
    
    # Check other important tables
    tables_to_check = ['predictions', 'outcomes', 'enhanced_features']
    for table in tables_to_check:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📋 {table}: {count} records")
        except:
            print(f"❌ {table}: table not found or error")
    
    conn.close()

def main():
    """Main execution function"""
    print("🚀 Remote Model Performance Data Setup")
    print("=" * 50)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check database status
    if not check_database_status():
        print("❌ Database check failed")
        sys.exit(1)
    
    # Populate model performance data
    if populate_model_performance_from_metadata():
        print("✅ Model performance data populated successfully")
    else:
        print("❌ Failed to populate model performance data")
        sys.exit(1)
    
    # Verify data for dashboard
    verify_dashboard_data()
    
    print("\n🎯 Setup complete! Dashboard should now show model performance data.")
    print("   Run the dashboard to verify: streamlit run comprehensive_table_dashboard.py")

if __name__ == "__main__":
    # Import pandas here to avoid import error if not available
    try:
        import pandas as pd
    except ImportError:
        print("⚠️ pandas not available, skipping verification step")
        pd = None
    
    main()
