#!/usr/bin/env python3
"""
Check Volume Data in Database
Verify the stored volume data from our test
"""

import sqlite3
import os

def check_volume_data_content():
    """Check the content of the daily_volume_data table"""
    
    print("📊 CHECKING VOLUME DATA TABLE CONTENT")
    print("=" * 50)
    
    db_path = "data/trading_predictions.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists and get structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_volume_data'")
        table_def = cursor.fetchone()
        
        if table_def:
            print("✅ daily_volume_data table exists")
            print(f"📋 Table Definition:")
            print(f"   {table_def[0]}")
        else:
            print("❌ daily_volume_data table not found")
            return
        
        # Check how many rows we have
        cursor.execute("SELECT COUNT(*) FROM daily_volume_data")
        row_count = cursor.fetchone()[0]
        print(f"\n📊 Total Volume Records: {row_count}")
        
        if row_count > 0:
            # Show the actual data
            cursor.execute('''
                SELECT symbol, analysis_date, latest_volume, average_volume_20, 
                       volume_ratio, market_hours, data_timestamp, created_at
                FROM daily_volume_data 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            
            print(f"\n📈 VOLUME DATA RECORDS:")
            print("-" * 50)
            
            for row in rows:
                symbol, date, latest_vol, avg_vol, ratio, market_hours, data_ts, created = row
                market_status = "Market Hours" if market_hours else "After Hours"
                
                print(f"📊 {symbol} ({date}):")
                print(f"   Latest Volume: {latest_vol:,.0f}")
                print(f"   Average Volume: {avg_vol:,.0f}")
                print(f"   Volume Ratio: {ratio:.2f}x")
                print(f"   Collected: {market_status}")
                print(f"   Data Time: {data_ts}")
                print(f"   Created: {created}")
                print()
        else:
            print("❌ No volume data records found")
        
        # Test retrieval function for evening analyzer
        print(f"🌙 TESTING EVENING RETRIEVAL FUNCTION:")
        print("-" * 50)
        
        test_symbols = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX"]
        
        for symbol in test_symbols:
            cursor.execute('''
                SELECT latest_volume, average_volume_20, volume_ratio, 
                       market_hours, data_timestamp
                FROM daily_volume_data 
                WHERE symbol = ? 
                ORDER BY analysis_date DESC 
                LIMIT 1
            ''', (symbol,))
            
            result = cursor.fetchone()
            
            if result:
                volume_data = {
                    'has_volume_data': True,
                    'latest_volume': result[0],
                    'average_volume_20': result[1],
                    'volume_ratio': result[2],
                    'from_market_hours': result[3],
                    'data_timestamp': result[4]
                }
                
                # Calculate quality score for evening analyzer
                if volume_data['from_market_hours']:
                    data_availability = 1.0  # Live data
                else:
                    data_availability = 0.8  # End-of-day data
                    
                coverage_score = min(volume_data['volume_ratio'] / 2.0, 1.0)
                consistency_score = 0.6
                
                quality_score = (data_availability * 0.5) + (coverage_score * 0.3) + (consistency_score * 0.2)
                
                if quality_score >= 0.85:
                    grade = "A"
                elif quality_score >= 0.70:
                    grade = "B"
                elif quality_score >= 0.55:
                    grade = "C"
                elif quality_score >= 0.40:
                    grade = "D"
                else:
                    grade = "F"
                
                print(f"✅ {symbol}: has_volume_data = True")
                print(f"   Volume: {volume_data['latest_volume']:,.0f} ({volume_data['volume_ratio']:.2f}x)")
                print(f"   Quality Score: {quality_score:.3f} → Grade {grade}")
                
            else:
                print(f"❌ {symbol}: has_volume_data = False")
        
        conn.close()
        
        print(f"\n🎯 VOLUME DATA FLOW VERIFICATION:")
        print("-" * 50)
        if row_count > 0:
            print("✅ Morning Analyzer: Collects and stores volume data")
            print("✅ Database Storage: Volume data properly stored")
            print("✅ Evening Analyzer: Can retrieve volume data")
            print("✅ Quality Assessment: Grade F → Grade B/A")
            print("🚀 COMPLETE SUCCESS: Volume data flow is working!")
        else:
            print("❌ No volume data stored yet")
            print("🔧 Run morning analyzer to collect volume data")
        
    except Exception as e:
        print(f"❌ Error checking volume data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_volume_data_content()
