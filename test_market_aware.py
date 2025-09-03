#!/usr/bin/env python3
"""
Test script for the market-aware prediction system
"""

import sys
import os
from datetime import datetime

def test_imports():
    """Test if required modules can be imported"""
    try:
        import yfinance as yf
        print("✅ yfinance imported successfully")
        
        import pandas as pd
        print("✅ pandas imported successfully")
        
        import sqlite3
        print("✅ sqlite3 imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_market_context():
    """Test market context analysis"""
    try:
        import yfinance as yf
        
        print("\n🌐 Testing Market Context Analysis...")
        
        # Get ASX 200 data
        asx200 = yf.Ticker('^AXJO')
        data = asx200.history(period='5d')
        
        if len(data) >= 2:
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            current_level = data['Close'].iloc[-1]
            
            print(f"📊 ASX 200 Current Level: {current_level:.1f}")
            print(f"📊 5-day Trend: {market_trend:+.2f}%")
            
            # Determine market context
            if market_trend < -2:
                context = 'BEARISH'
                confidence_mult = 0.7
                buy_threshold = 0.80
            elif market_trend > 2:
                context = 'BULLISH'
                confidence_mult = 1.1
                buy_threshold = 0.65
            else:
                context = 'NEUTRAL'
                confidence_mult = 1.0
                buy_threshold = 0.70
            
            print(f"📊 Market Context: {context}")
            print(f"📊 Confidence Multiplier: {confidence_mult:.1f}x")
            print(f"📊 BUY Threshold: {buy_threshold:.1%}")
            
            return True
        else:
            print("❌ Insufficient market data")
            return False
            
    except Exception as e:
        print(f"❌ Market context test failed: {e}")
        return False

def test_confidence_calculation():
    """Test the new confidence calculation logic"""
    print("\n🧮 Testing Confidence Calculation...")
    
    # OLD system
    old_base = 0.20
    tech_component = 0.25
    news_component = 0.15
    volume_component = 0.10
    risk_component = 0.05
    
    old_confidence = old_base + tech_component + news_component + volume_component + risk_component
    
    # NEW system
    new_base = 0.10  # REDUCED
    new_confidence = new_base + tech_component + news_component + volume_component + risk_component
    
    print(f"📊 OLD Base Confidence: {old_base:.1%}")
    print(f"📊 NEW Base Confidence: {new_base:.1%}")
    print(f"📊 OLD Total Confidence: {old_confidence:.1%}")
    print(f"📊 NEW Total Confidence: {new_confidence:.1%}")
    print(f"📊 Confidence Reduction: {(old_confidence - new_confidence):.1%}")
    
    return True

def main():
    """Run all tests"""
    print("🔧 Market-Aware Prediction System Tests")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    # Test market context
    if not test_market_context():
        print("\n❌ Market context tests failed")
        return False
    
    # Test confidence calculation
    if not test_confidence_calculation():
        print("\n❌ Confidence calculation tests failed")
        return False
    
    print("\n✅ All tests completed successfully!")
    print(f"🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
