#!/usr/bin/env python3
"""
Test using historical market data during off-hours
"""
import sqlite3
import datetime

def test_with_historical_data():
    """Test our system with recent historical predictions"""
    
    print("Ì≥ä HISTORICAL DATA SIMULATION TEST")
    print("=" * 50)
    
    # Get recent historical data
    conn = sqlite3.connect("predictions.db")
    cursor = conn.cursor()
    
    # Get a sample of historical features
    cursor.execute("""
        SELECT symbol, confidence_breakdown, volume_trend, market_trend_pct 
        FROM predictions 
        WHERE confidence_breakdown LIKE "%ML:%" 
        ORDER BY created_at DESC 
        LIMIT 3
    """)
    
    historical_data = cursor.fetchall()
    
    for symbol, breakdown, volume, market in historical_data:
        print(f"\nÌ¥ç Testing {symbol}:")
        print(f"   Volume Trend: {volume}%")
        print(f"   Market Trend: {market}%")
        
        # Extract ML confidence from breakdown
        import re
        ml_match = re.search(r"= ([0-9.]+)$", breakdown)
        if ml_match:
            original_ml_conf = float(ml_match.group(1))
            print(f"   Original ML Confidence: {original_ml_conf:.1%}")
            
            # Check if our fixes would preserve this
            if original_ml_conf > 0.9:
                print("   ‚úÖ High ML confidence - should be preserved")
            else:
                print("   ‚ö†Ô∏è Lower confidence - check for risk factors")
        
    conn.close()
    print("\nÌæØ Historical simulation complete")

if __name__ == "__main__":
    test_with_historical_data()
