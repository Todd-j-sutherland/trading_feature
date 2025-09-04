#!/usr/bin/env python3
"""
Test script to verify WBC.AX data retrieval
"""

import sqlite3
import json
from datetime import datetime, timedelta

def test_wbc_data(hours=168):
    """Test WBC.AX data retrieval with the same logic as the dashboard"""
    
    print(f"🔍 Testing WBC.AX data retrieval for last {hours} hours")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('trading_predictions.db')
    
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        print(f"Time range: {start_time.isoformat()} to {end_time.isoformat()}")
        
        # Get enhanced features data
        features_query = """
        SELECT 
            timestamp,
            current_price,
            sentiment_score,
            confidence,
            rsi,
            macd_line,
            price_change_1h,
            price_change_4h
        FROM enhanced_features 
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        
        cursor = conn.execute(features_query, ("WBC.AX", start_time.isoformat()))
        features_data = cursor.fetchall()
        
        print(f"\n📊 Found {len(features_data)} enhanced_features records")
        
        # Get prediction data
        predictions_query = """
        SELECT 
            prediction_timestamp,
            predicted_action,
            action_confidence,
            entry_price
        FROM predictions 
        WHERE symbol = ? AND prediction_timestamp >= ?
        ORDER BY prediction_timestamp ASC
        """
        
        cursor = conn.execute(predictions_query, ("WBC.AX", start_time.isoformat()))
        predictions_data = cursor.fetchall()
        
        print(f"📈 Found {len(predictions_data)} prediction records")
        
        # Process the data like the dashboard does
        timestamps = []
        prices = []
        sentiment_scores = []
        rsi_values = []
        
        for row in features_data:
            timestamp, price, sentiment, confidence, rsi, macd_line, price_1h, price_4h = row
            
            timestamps.append(timestamp)
            prices.append(price if price is not None else 0)
            sentiment_scores.append(sentiment if sentiment is not None else 0)
            rsi_values.append(rsi if rsi is not None else 50)
        
        print(f"\n✅ Processed data:")
        print(f"   📅 Timestamps: {len(timestamps)}")
        print(f"   💰 Prices: {len(prices)}")
        print(f"   📊 Sentiment scores: {len(sentiment_scores)}")
        print(f"   📈 RSI values: {len(rsi_values)}")
        
        if timestamps:
            print(f"\n📋 Sample data:")
            print(f"   Latest timestamp: {timestamps[-1]}")
            print(f"   Latest price: ${prices[-1]:.2f}")
            print(f"   Latest sentiment: {sentiment_scores[-1]:.3f}")
            print(f"   Latest RSI: {rsi_values[-1]:.1f}")
        
        # Create API-like response
        response = {
            "symbol": "WBC.AX",
            "timerange_hours": hours,
            "data_points": len(timestamps),
            "price_data": {
                "timestamps": timestamps,
                "prices": prices
            },
            "sentiment_data": {
                "timestamps": timestamps,
                "sentiment_scores": sentiment_scores
            },
            "technical_data": {
                "timestamps": timestamps,
                "rsi_values": rsi_values
            }
        }
        
        print(f"\n🎯 API Response Preview:")
        print(f"   Symbol: {response['symbol']}")
        print(f"   Time range: {response['timerange_hours']} hours")
        print(f"   Data points: {response['data_points']}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        conn.close()

def test_all_symbols():
    """Test all symbols for data availability"""
    
    symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX', 'BHP.AX']
    
    print("🔍 Testing all symbols for data availability")
    print("=" * 60)
    
    conn = sqlite3.connect('trading_predictions.db')
    
    try:
        for symbol in symbols:
            cursor = conn.execute("SELECT COUNT(*) FROM enhanced_features WHERE symbol = ?", (symbol,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor = conn.execute("SELECT MAX(timestamp) FROM enhanced_features WHERE symbol = ?", (symbol,))
                latest = cursor.fetchone()[0]
                print(f"✅ {symbol}: {count:2d} records, latest: {latest}")
            else:
                print(f"❌ {symbol}: No data")
    
    finally:
        conn.close()

if __name__ == "__main__":
    # Test WBC.AX specifically
    result = test_wbc_data(168)
    
    print("\n" + "="*60)
    
    # Test all symbols
    test_all_symbols()
    
    if result and result['data_points'] > 0:
        print(f"\n🎉 SUCCESS: WBC.AX has {result['data_points']} data points!")
        print("The API should now return proper data for WBC.AX")
    else:
        print("\n⚠️  No data found - check if the database has WBC.AX records")
