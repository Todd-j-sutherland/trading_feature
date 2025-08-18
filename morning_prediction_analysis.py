#!/usr/bin/env python3
"""
Morning Predictions Analysis - Validate Aug 18, 07:33 predictions
"""

import sys
import sqlite3
from datetime import datetime
import yfinance as yf

def analyze_predictions():
    """Analyze the problematic predictions from this morning"""
    print("🔍 ANALYZING AUGUST 18 MORNING PREDICTIONS")
    print("=" * 60)
    
    conn = sqlite3.connect('/root/test/data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get the specific predictions
    cursor.execute('''
    SELECT symbol, prediction_timestamp, predicted_action, action_confidence, 
           predicted_direction, predicted_magnitude, model_version
    FROM predictions 
    WHERE prediction_timestamp LIKE '2025-08-18T07:33%'
    ORDER BY symbol
    ''')
    
    predictions = cursor.fetchall()
    
    print(f"📊 Found {len(predictions)} predictions at 07:33")
    print(f"🕐 Timestamp: 2025-08-18T07:33:39 (7:33 AM AEST)")
    print(f"⏰ Market Status: BEFORE OPEN (market opens at 10:00 AM)")
    print()
    
    # Analyze each prediction
    issues = []
    symbols = []
    
    print("📋 PREDICTION DETAILS:")
    print("Symbol\tAction\tConf\tDirection\tMagnitude\tModel")
    print("-" * 60)
    
    for pred in predictions:
        symbol, timestamp, action, confidence, direction, magnitude, model = pred
        symbols.append(symbol)
        print(f"{symbol}\t{action}\t{confidence}\t{direction}\t\t{magnitude}\t{model}")
    
    # Issue analysis
    print(f"\n🚨 ISSUES DETECTED:")
    
    # Check if all actions are the same
    unique_actions = set(pred[2] for pred in predictions)
    if len(unique_actions) == 1:
        issues.append(f"❌ All predictions have identical action: {list(unique_actions)[0]}")
    
    # Check if all confidences are 0.5 (default)
    unique_confidences = set(pred[3] for pred in predictions)
    if len(unique_confidences) == 1 and 0.5 in unique_confidences:
        issues.append(f"❌ All predictions have default confidence: 0.5")
    
    # Check if all timestamps are identical
    unique_timestamps = set(pred[1] for pred in predictions)
    if len(unique_timestamps) == 1:
        issues.append(f"❌ All predictions have identical timestamp (generated simultaneously)")
    
    # Check model version
    model_versions = set(pred[6] for pred in predictions if pred[6])
    if not model_versions or None in model_versions:
        issues.append(f"❌ Missing model version information")
    
    for issue in issues:
        print(f"  {issue}")
    
    # Get current market data for comparison
    print(f"\n📈 CURRENT MARKET DATA (for validation):")
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = info.get('regularMarketPrice', hist['Close'].iloc[-1])
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                change_pct = ((current_price - prev_close) / prev_close) * 100
                
                # Simple sentiment based on price movement
                if change_pct > 2:
                    market_sentiment = "Strong Positive"
                elif change_pct > 0:
                    market_sentiment = "Positive" 
                elif change_pct < -2:
                    market_sentiment = "Strong Negative"
                elif change_pct < 0:
                    market_sentiment = "Negative"
                else:
                    market_sentiment = "Neutral"
                
                print(f"  {symbol}: ${current_price:.2f} ({change_pct:+.2f}%) - {market_sentiment}")
                
                # Compare with prediction
                prediction_action = next(pred[2] for pred in predictions if pred[0] == symbol)
                if prediction_action == "SELL" and change_pct > 0:
                    print(f"    ⚠️ MISMATCH: Predicted SELL but stock is UP")
                elif prediction_action == "BUY" and change_pct < 0:
                    print(f"    ⚠️ MISMATCH: Predicted BUY but stock is DOWN")
                
        except Exception as e:
            print(f"  {symbol}: Error getting data - {e}")
    
    conn.close()
    
    # Final assessment
    print(f"\n🎯 ASSESSMENT:")
    if len(issues) > 2:
        print("❌ INVALID PREDICTIONS - System appears to be in fallback/error mode")
        print("   These predictions should NOT be used for trading")
        return False
    else:
        print("✅ Predictions appear valid")
        return True

def check_what_went_wrong():
    """Investigate what caused the invalid predictions"""
    print(f"\n🔍 ROOT CAUSE ANALYSIS")
    print("=" * 40)
    
    print("Possible causes for identical 0.5 confidence predictions:")
    print("1. ❌ ML model failed to load properly")
    print("2. ❌ Data sources were unavailable")
    print("3. ❌ Sentiment analysis failed")
    print("4. ❌ System fell back to default values")
    print("5. ❌ Import errors in prediction logic")
    
    print(f"\nFrom earlier validation:")
    print("✅ yfinance is working")
    print("✅ transformers is working") 
    print("❌ NewsTradingAnalyzer import failed")
    print("❌ No morning cron log generated")
    
    print(f"\n🔧 RECOMMENDATIONS:")
    print("1. Fix the NewsTradingAnalyzer import error")
    print("2. Run morning routine manually to test")
    print("3. Check all ML model dependencies")
    print("4. Verify data collection is working")

def main():
    """Main analysis"""
    print("🚨 MORNING PREDICTION VALIDATION REPORT")
    print("=" * 70)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    valid = analyze_predictions()
    check_what_went_wrong()
    
    print(f"\n🎯 FINAL VERDICT:")
    if valid:
        print("✅ Predictions are valid and can be used")
    else:
        print("❌ Predictions are INVALID - DO NOT USE for trading")
        print("⚠️ System needs debugging before next trading session")
    
    return valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
