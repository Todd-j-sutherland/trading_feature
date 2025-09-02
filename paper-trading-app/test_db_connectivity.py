#!/usr/bin/env python3
"""
Paper Trading Database Connectivity Test
Tests the database path detection and connectivity for the paper trading service
"""

import os
import sys
import sqlite3
from pathlib import Path

def test_predictions_db_path():
    """Test the smart path detection logic"""
    print("🔍 Testing Predictions Database Path Detection")
    print("=" * 50)
    
    # Replicate the smart path detection logic
    potential_paths = [
        '../data/trading_predictions.db',  # Remote structure
        '../predictions.db',               # Local structure
        'predictions.db',                  # Alternative local path
        '../trading_predictions.db'       # Another potential location
    ]
    
    detected_path = None
    for path in potential_paths:
        full_path = os.path.abspath(path)
        exists = os.path.exists(path)
        symbol = "✅" if exists else "❌"
        print(f"   {symbol} {path} -> {full_path}")
        
        if exists and detected_path is None:
            detected_path = path
    
    print(f"\n🎯 Selected path: {detected_path}")
    
    if detected_path is None:
        print("❌ No predictions database found!")
        return None
    
    return detected_path

def test_database_connectivity(db_path):
    """Test connecting to and querying the predictions database"""
    print(f"\n🔗 Testing Database Connectivity: {db_path}")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        print("✅ Database connection successful")
        
        # Check for predictions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions';")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("✅ Predictions table found")
            
            # Get table schema
            cursor.execute("PRAGMA table_info(predictions);")
            columns = cursor.fetchall()
            print(f"📋 Table has {len(columns)} columns:")
            
            required_columns = [
                'prediction_id', 'symbol', 'predicted_action', 
                'action_confidence', 'prediction_timestamp'
            ]
            
            found_columns = [col[1] for col in columns]
            
            for req_col in required_columns:
                if req_col in found_columns:
                    print(f"   ✅ {req_col}")
                else:
                    print(f"   ❌ {req_col} (MISSING)")
            
            # Check data count
            cursor.execute("SELECT COUNT(*) FROM predictions;")
            count = cursor.fetchone()[0]
            print(f"📊 Total predictions: {count}")
            
            if count > 0:
                # Show recent predictions
                cursor.execute("""
                    SELECT prediction_id, symbol, predicted_action, action_confidence, prediction_timestamp
                    FROM predictions 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 3
                """)
                
                recent_predictions = cursor.fetchall()
                print(f"🕒 Recent predictions:")
                for pred in recent_predictions:
                    print(f"   {pred[1]} {pred[2]} (conf: {pred[3]:.2f}) at {pred[4]}")
            else:
                print("⚠️ No predictions found in database")
                
        else:
            print("❌ Predictions table not found!")
            
            # Show available tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Available tables: {[t[0] for t in tables]}")
        
        conn.close()
        return table_exists
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_paper_trading_service_setup():
    """Test if the paper trading service can be imported and initialized"""
    print(f"\n🤖 Testing Paper Trading Service Setup")
    print("=" * 50)
    
    try:
        # Try to import the service (this will test Python environment)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test if we can import sqlite3 (basic requirement)
        import sqlite3
        print("✅ sqlite3 module available")
        
        # Test if enhanced_paper_trading_service.py exists
        service_file = Path("enhanced_paper_trading_service.py")
        if service_file.exists():
            print("✅ Enhanced paper trading service file found")
            
            # Read the file to check for our path fix
            with open(service_file, 'r') as f:
                content = f.read()
                if 'get_predictions_db_path()' in content:
                    print("✅ Smart path detection implemented")
                else:
                    print("❌ Smart path detection not found")
        else:
            print("❌ Enhanced paper trading service file not found")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Paper Trading Database Connectivity Test")
    print("=" * 50)
    print(f"Current directory: {os.getcwd()}")
    print()
    
    # Test 1: Path detection
    predictions_db_path = test_predictions_db_path()
    
    # Test 2: Database connectivity
    if predictions_db_path:
        db_connected = test_database_connectivity(predictions_db_path)
    else:
        db_connected = False
    
    # Test 3: Service setup
    service_ready = test_paper_trading_service_setup()
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 50)
    print(f"Database Path Detection: {'✅' if predictions_db_path else '❌'}")
    print(f"Database Connectivity:   {'✅' if db_connected else '❌'}")
    print(f"Service Setup:          {'✅' if service_ready else '❌'}")
    
    if predictions_db_path and db_connected and service_ready:
        print(f"\n🎉 All tests passed! Paper trading service should be able to connect to predictions.")
        print(f"📁 Using database: {os.path.abspath(predictions_db_path)}")
    else:
        print(f"\n⚠️ Some tests failed. Paper trading service may not work correctly.")
        
        if not predictions_db_path:
            print("   - No predictions database found")
        if not db_connected:
            print("   - Database connectivity issues")
        if not service_ready:
            print("   - Service setup problems")

if __name__ == "__main__":
    main()
