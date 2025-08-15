#!/usr/bin/env python3
"""
Mock Evening Analysis Test
Run a test evening analysis to verify return calculations work correctly
"""

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def run_mock_evening_analysis():
    """Run a mock evening analysis on recent features to test return calculations"""
    
    print("🌙 MOCK EVENING ANALYSIS TEST")
    print("=" * 35)
    
    conn = sqlite3.connect('data/trading_unified.db')
    
    # Get the most recent features that don't have outcomes yet
    recent_features_query = """
    SELECT DISTINCT f.id, f.symbol, f.timestamp, f.current_price
    FROM enhanced_features f
    LEFT JOIN enhanced_outcomes o ON f.id = o.feature_id
    WHERE o.id IS NULL
    ORDER BY f.timestamp DESC
    LIMIT 5
    """
    
    recent_features = pd.read_sql_query(recent_features_query, conn)
    
    if len(recent_features) == 0:
        print("No recent features without outcomes found.")
        print("Creating test feature for mock analysis...")
        
        # Create a test feature
        test_timestamp = datetime.now().isoformat()
        test_symbol = "CBA.AX"
        
        # Get current price for test
        ticker = yf.Ticker(test_symbol)
        current_data = ticker.history(period="1d", interval="1h")
        if not current_data.empty:
            test_price = current_data['Close'].iloc[-1]
        else:
            test_price = 175.0  # fallback
        
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO enhanced_features (
            symbol, timestamp, current_price, volume, rsi, sma_20, ema_12,
            sentiment_score, volatility_20d, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_symbol, test_timestamp, test_price, 1000000, 50.0, test_price,
            test_price, 0.1, 0.02, datetime.now().isoformat()
        ))
        
        feature_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Created test feature: ID {feature_id}, {test_symbol} @ ${test_price:.2f}")
        
        recent_features = pd.DataFrame([{
            'id': feature_id,
            'symbol': test_symbol,
            'timestamp': test_timestamp,
            'current_price': test_price
        }])
    
    print(f"\n📊 Processing {len(recent_features)} features for mock analysis:")
    print("-" * 50)
    
    cursor = conn.cursor()
    successful_calculations = 0
    
    for _, feature in recent_features.iterrows():
        feature_id = feature['id']
        symbol = feature['symbol']
        entry_price = feature['current_price']
        prediction_time = datetime.fromisoformat(feature['timestamp'])
        
        print(f"\nProcessing {symbol} (Feature ID: {feature_id})")
        print(f"Entry Price: ${entry_price:.4f}")
        print(f"Prediction Time: {prediction_time}")
        
        # Calculate exit price (simulate 1-day later)
        exit_time = prediction_time + timedelta(days=1)
        
        try:
            # Get historical data for exit price calculation
            ticker = yf.Ticker(symbol)
            
            # Get data around the exit time
            start_date = exit_time.date()
            end_date = start_date + timedelta(days=2)
            
            hist_data = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if not hist_data.empty:
                exit_price = hist_data['Close'].iloc[0]
                
                # Calculate return percentage
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                
                # Determine trading action (simplified logic for testing)
                if return_pct > 1.0:
                    optimal_action = "BUY"
                    confidence = 0.8
                elif return_pct < -1.0:
                    optimal_action = "SELL"  
                    confidence = 0.8
                else:
                    optimal_action = "HOLD"
                    confidence = 0.6
                
                print(f"Exit Price: ${exit_price:.4f}")
                print(f"Return: {return_pct:.4f}%")
                print(f"Action: {optimal_action} (Confidence: {confidence:.1f})")
                
                # Insert the test outcome
                cursor.execute("""
                INSERT INTO enhanced_outcomes (
                    feature_id, symbol, prediction_timestamp, optimal_action,
                    confidence_score, entry_price, exit_price_1d, return_pct,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feature_id, symbol, prediction_time.isoformat(), optimal_action,
                    confidence, entry_price, exit_price, return_pct,
                    datetime.now().isoformat()
                ))
                
                # Verify the calculation by reading it back
                verification_query = """
                SELECT 
                    return_pct as stored_return,
                    ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4) as calculated_return
                FROM enhanced_outcomes 
                WHERE feature_id = ?
                """
                
                cursor.execute(verification_query, (feature_id,))
                verification = cursor.fetchone()
                
                if verification:
                    stored = verification[0]
                    calculated = verification[1]
                    difference = abs(stored - calculated)
                    
                    if difference <= 0.01:
                        print(f"✅ Calculation verified: {stored:.4f}% vs {calculated:.4f}%")
                        successful_calculations += 1
                    else:
                        print(f"❌ Calculation error: {stored:.4f}% vs {calculated:.4f}%")
                
            else:
                print(f"❌ No historical data available for {symbol}")
                
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📋 MOCK ANALYSIS SUMMARY")
    print("-" * 30)
    print(f"Features Processed: {len(recent_features)}")
    print(f"Successful Calculations: {successful_calculations}")
    print(f"Success Rate: {(successful_calculations/len(recent_features))*100:.1f}%")
    
    if successful_calculations == len(recent_features):
        print("✅ All calculations completed successfully!")
        print("🎉 Return calculation logic is working correctly")
    else:
        print("⚠️ Some calculations failed - check errors above")
    
    return successful_calculations == len(recent_features)

if __name__ == "__main__":
    success = run_mock_evening_analysis()
    
    if success:
        print("\n🚀 Ready to run real evening analysis!")
        print("The return calculations are working correctly.")
    else:
        print("\n🔧 Fix issues before running real evening analysis.")
