#!/usr/bin/env python3
"""
Database Investigation Script - Local Environment
Investigate the predictions database structure and paper-trading-app configuration
"""

import sqlite3
import os
import sys
from pathlib import Path

def investigate_database(db_path, db_name):
    """Investigate a database and show its structure"""
    print(f"\n🔍 Investigating {db_name}: {db_path}")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get file size
        file_size = os.path.getsize(db_path) / 1024  # KB
        print(f"📁 File size: {file_size:.1f} KB")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables found: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            print(f"\n  📊 Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"     Columns: {len(columns)}")
            for col in columns:
                print(f"       - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"     Rows: {count}")
            
            # Show sample data for key tables
            if table_name.lower() in ['predictions', 'enhanced_positions', 'enhanced_trades'] and count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                print(f"     Sample data:")
                for i, row in enumerate(rows):
                    print(f"       Row {i+1}: {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error investigating database: {e}")
        return False

def check_paper_trading_config():
    """Check paper trading app configuration"""
    print(f"\n🔧 Paper Trading App Configuration")
    print("=" * 60)
    
    config_file = Path("paper-trading-app/config.py")
    service_file = Path("paper-trading-app/enhanced_paper_trading_service.py")
    
    if config_file.exists():
        print(f"✅ Config file found: {config_file}")
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if 'PREDICTIONS_DB_PATH' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if 'PREDICTIONS_DB_PATH' in line:
                            print(f"   {line.strip()}")
        except Exception as e:
            print(f"   Error reading config: {e}")
    else:
        print(f"❌ Config file not found: {config_file}")
    
    if service_file.exists():
        print(f"✅ Service file found: {service_file}")
        try:
            with open(service_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                for line in lines:
                    if 'PREDICTIONS_DB_PATH' in line and not line.strip().startswith('#'):
                        print(f"   {line.strip()}")
        except Exception as e:
            print(f"   Error reading service: {e}")
    else:
        print(f"❌ Service file not found: {service_file}")

def analyze_path_discrepancy():
    """Analyze the path discrepancy between local and remote"""
    print(f"\n📂 Path Analysis")
    print("=" * 60)
    
    # Current working directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Expected remote structure
    remote_structure = "/root/test/"
    local_structure = current_dir
    
    print(f"Local structure:  {local_structure}")
    print(f"Remote structure: {remote_structure}")
    
    # Check for different potential database locations
    potential_db_paths = [
        "predictions.db",
        "data/trading_predictions.db", 
        "trading_predictions.db",
        "paper-trading-app/../data/trading_predictions.db",
        "paper-trading-app/../predictions.db",
        "../data/trading_predictions.db",
        "../predictions.db"
    ]
    
    print(f"\n🔍 Checking potential database paths:")
    for path in potential_db_paths:
        full_path = os.path.join(current_dir, path)
        exists = os.path.exists(full_path)
        symbol = "✅" if exists else "❌"
        print(f"   {symbol} {path} -> {full_path}")

def suggest_fixes():
    """Suggest potential fixes for the integration issue"""
    print(f"\n💡 Suggested Fixes")
    print("=" * 60)
    
    print("1. **Database Path Configuration:**")
    print("   - Update PREDICTIONS_DB_PATH in enhanced_paper_trading_service.py")
    print("   - Current: '../data/trading_predictions.db'")
    print("   - Local should be: '../predictions.db' or 'predictions.db'")
    
    print("\n2. **Environment Setup:**")
    print("   - Local environment doesn't have Python installed")
    print("   - This prevents running the paper trading service locally")
    print("   - Consider installing Python or using WSL")
    
    print("\n3. **Directory Structure:**") 
    print("   - Remote: /root/test/")
    print("   - Local: C:/Users/todd.sutherland/trading_feature/")
    print("   - Paper trading app needs different relative paths")
    
    print("\n4. **Testing Recommendations:**")
    print("   - Test paper trading service on remote environment")
    print("   - Use database copying for local development")
    print("   - Set up proper Python environment locally")

def main():
    """Main investigation function"""
    print("🔍 Trading Feature Database Investigation")
    print("=========================================")
    
    # Find all databases
    databases_to_check = [
        ("predictions.db", "Main Predictions Database"),
        ("trading_data.db", "Trading Data Database"),
        ("enhanced_trading_data.db", "Enhanced Trading Data"),
        ("paper-trading-app/paper_trading.db", "Paper Trading Database"),
        ("paper-trading-app/trading.db", "Legacy Trading Database"),
        ("paper-trading-app/enhanced_positions.db", "Enhanced Positions Database")
    ]
    
    for db_path, description in databases_to_check:
        investigate_database(db_path, description)
    
    check_paper_trading_config()
    analyze_path_discrepancy()
    suggest_fixes()
    
    print(f"\n📋 Investigation Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
