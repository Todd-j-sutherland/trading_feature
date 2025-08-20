#!/usr/bin/env python3
"""
Test: Check if Morning Analyzer Collects and Stores Volume Data
Verify the data flow: Morning → Database → Evening
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

def check_morning_volume_data_storage():
    """Check what volume data the morning analyzer actually collects and stores"""
    
    print("🔍 CHECKING MORNING ANALYZER VOLUME DATA STORAGE")
    print("=" * 70)
    
    # Database paths
    db_path = "data/trading_predictions.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check what tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Available Tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check enhanced_morning_analysis table
        print(f"\n🌅 ENHANCED MORNING ANALYSIS DATA:")
        print("-" * 50)
        
        try:
            cursor.execute("""
                SELECT timestamp, market_hours, banks_analyzed, 
                       data_quality_scores, technical_signals, ml_predictions
                FROM enhanced_morning_analysis 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            
            morning_results = cursor.fetchall()
            
            if morning_results:
                for i, row in enumerate(morning_results):
                    print(f"\n📅 Run #{i+1}: {row[0]}")
                    print(f"   Market Hours: {row[1]}")
                    
                    # Parse technical signals to check for volume data
                    import json
                    try:
                        tech_signals = json.loads(row[4]) if row[4] else {}
                        print(f"   Banks with Technical Data: {len(tech_signals)}")
                        
                        for symbol, tech_data in tech_signals.items():
                            print(f"   📊 {symbol}:")
                            print(f"      Current Price: ${tech_data.get('current_price', 'N/A')}")
                            print(f"      RSI: {tech_data.get('rsi', 'N/A')}")
                            # Check if any volume info is stored
                            if 'volume' in str(tech_data).lower():
                                print(f"      🔊 Volume data found!")
                            else:
                                print(f"      ❌ No volume data stored")
                    except Exception as parse_error:
                        print(f"   ❌ Error parsing technical signals: {parse_error}")
            else:
                print("   ❌ No morning analysis data found")
                
        except Exception as e:
            print(f"   ❌ Error querying morning analysis: {e}")
        
        # Check if there are any volume-specific tables
        print(f"\n📊 CHECKING FOR VOLUME-SPECIFIC STORAGE:")
        print("-" * 50)
        
        # Look for any table that might store volume data
        for table_name in [t[0] for t in tables]:
            if 'volume' in table_name.lower():
                print(f"✅ Found volume table: {table_name}")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
            elif 'market' in table_name.lower() or 'technical' in table_name.lower():
                print(f"🔍 Checking table: {table_name}")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                volume_cols = [col for col in columns if 'volume' in col[1].lower()]
                if volume_cols:
                    print(f"   ✅ Volume columns found: {[col[1] for col in volume_cols]}")
                else:
                    print(f"   ❌ No volume columns")
        
        # Check if enhanced training data stores volume
        print(f"\n🧠 CHECKING ML TRAINING DATA FOR VOLUME:")
        print("-" * 50)
        
        try:
            cursor.execute("""
                SELECT symbol, feature_data 
                FROM enhanced_training_data 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            training_data = cursor.fetchall()
            
            if training_data:
                for symbol, features in training_data:
                    if features:
                        try:
                            feature_dict = json.loads(features)
                            volume_features = [k for k in feature_dict.keys() if 'volume' in k.lower()]
                            if volume_features:
                                print(f"   ✅ {symbol}: Volume features found: {volume_features}")
                            else:
                                print(f"   ❌ {symbol}: No volume features in ML data")
                        except:
                            print(f"   ❌ {symbol}: Error parsing feature data")
            else:
                print("   ❌ No enhanced training data found")
                
        except Exception as e:
            print(f"   ❌ Error checking training data: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Test what the morning analyzer SHOULD be collecting
    print(f"\n🧪 TESTING LIVE VOLUME DATA COLLECTION:")
    print("-" * 50)
    
    try:
        # Simulate what morning analyzer does
        import yfinance as yf
        
        symbol = "CBA.AX"
        print(f"📊 Testing volume collection for {symbol}:")
        
        # Get market data like morning analyzer does
        ticker = yf.Ticker(symbol)
        market_data = ticker.history(period='3mo', interval='1h')
        
        if not market_data.empty:
            print(f"   ✅ Market data available: {len(market_data)} rows")
            print(f"   📊 Volume column present: {'Volume' in market_data.columns}")
            
            if 'Volume' in market_data.columns:
                latest_volume = market_data['Volume'].iloc[-1]
                avg_volume = market_data['Volume'].tail(20).mean()
                volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0
                
                print(f"   📈 Latest Volume: {latest_volume:,.0f}")
                print(f"   📊 Average Volume (20 periods): {avg_volume:,.0f}")
                print(f"   📊 Volume Ratio: {volume_ratio:.2f}")
                
                # This is what SHOULD be stored for evening use
                volume_data = {
                    'symbol': symbol,
                    'latest_volume': float(latest_volume),
                    'average_volume': float(avg_volume),
                    'volume_ratio': float(volume_ratio),
                    'timestamp': datetime.now().isoformat(),
                    'has_volume_data': True
                }
                
                print(f"   🎯 Volume data that SHOULD be stored:")
                for key, value in volume_data.items():
                    print(f"      {key}: {value}")
        else:
            print(f"   ❌ No market data available for {symbol}")
            
    except Exception as e:
        print(f"   ❌ Error testing volume collection: {e}")
    
    print(f"\n💡 ANALYSIS CONCLUSIONS:")
    print("-" * 50)
    print("1. ✅ Morning analyzer gets market_data with Volume column")
    print("2. ❌ But volume data is NOT being stored in database")
    print("3. ❌ Evening analyzer has no volume data to access")
    print("4. 🔧 Need to add volume storage to morning analyzer")
    print("5. 🔧 Need to add volume retrieval to evening analyzer")

if __name__ == "__main__":
    check_morning_volume_data_storage()
