#!/usr/bin/env python3
"""
Morning Data Analysis Report

Analyzes the morning routine data for critical issues and inconsistencies.
"""

import json
from datetime import datetime, timedelta
import pandas as pd

def analyze_morning_data():
    """Analyze the morning routine data for issues"""
    
    print("🔍 MORNING ROUTINE DATA ANALYSIS")
    print("=" * 50)
    
    # Sample data from your dashboard
    predictions_data = [
        {"symbol": "CBA.AX", "timestamp": "2025-08-14T09:55:47.840963", "action": "BUY", "confidence": 0.522, "optimal_action": 0},
        {"symbol": "ANZ.AX", "timestamp": "2025-08-14T09:54:56.089225", "action": "HOLD", "confidence": 0.455, "optimal_action": 0},
        {"symbol": "NAB.AX", "timestamp": "2025-08-14T09:51:05.579383", "action": "HOLD", "confidence": 0.478, "optimal_action": 0}
    ]
    
    enhanced_features_data = [
        {"symbol": "NAB.AX", "timestamp": "2025-08-14T17:52:38.627629", "sentiment": 0.032, "rsi": 44.59, "macd": 0.077, "volatility": 11.98, "price": 38.88},
        {"symbol": "WBC.AX", "timestamp": "2025-08-14T17:51:39.697819", "sentiment": 0.072, "rsi": 68.62, "macd": 0.522, "volatility": 22.07, "price": 36.04},
        {"symbol": "CBA.AX", "timestamp": "2025-08-14T17:50:42.462105", "sentiment": 0.045, "rsi": 13.71, "macd": -2.615, "volatility": 17.50, "price": 167.21}
    ]
    
    sentiment_data = [
        {"symbol": "NAB.AX", "timestamp": "2025-08-14T17:52:38.627629", "sentiment": 0.032, "confidence": 0.733, "news_count": 38, "reddit": 0.084},
        {"symbol": "WBC.AX", "timestamp": "2025-08-14T17:51:39.697819", "sentiment": 0.072, "confidence": 0.734, "news_count": 44, "reddit": 0.074},
        {"symbol": "CBA.AX", "timestamp": "2025-08-14T17:50:42.462105", "sentiment": 0.045, "confidence": 0.732, "news_count": 45, "reddit": 0.052}
    ]
    
    technical_data = [
        {"symbol": "NAB.AX", "timestamp": "2025-08-14T17:52:38.627629", "rsi": 44.59, "macd": 0.077, "bb_upper": 39.59, "bb_lower": 37.96, "volatility": 11.98, "volume": 579144.15},
        {"symbol": "WBC.AX", "timestamp": "2025-08-14T17:51:39.697819", "rsi": 68.62, "macd": 0.522, "bb_upper": 36.62, "bb_lower": 33.07, "volatility": 22.07, "volume": 896265.4},
        {"symbol": "CBA.AX", "timestamp": "2025-08-14T17:50:42.462105", "rsi": 13.71, "macd": -2.615, "bb_upper": 181.56, "bb_lower": 162.08, "volatility": 17.50, "volume": 442118.5}
    ]
    
    issues = []
    
    print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
    print("-" * 30)
    
    # Issue 1: Massive Timestamp Gap
    pred_times = [datetime.fromisoformat(p["timestamp"]) for p in predictions_data]
    feature_times = [datetime.fromisoformat(f["timestamp"]) for f in enhanced_features_data]
    
    time_gap = max(feature_times) - max(pred_times)
    print(f"⚠️  TIMESTAMP GAP: {time_gap.total_seconds() / 3600:.1f} hours between predictions and features")
    print(f"   • Predictions: Morning (9:51-9:55 AM)")
    print(f"   • Features: Evening (5:50-5:52 PM)")
    print("   • This suggests DATA LEAKAGE - using future data for past predictions!")
    issues.append("Severe timestamp mismatch indicating data leakage")
    
    # Issue 2: Abnormal Technical Indicators
    print(f"\n⚠️  TECHNICAL ANOMALIES:")
    for tech in technical_data:
        if tech["rsi"] < 20:
            print(f"   • {tech['symbol']}: RSI = {tech['rsi']:.1f} (Extremely oversold)")
            issues.append(f"{tech['symbol']} RSI extremely low: {tech['rsi']:.1f}")
        elif tech["rsi"] > 80:
            print(f"   • {tech['symbol']}: RSI = {tech['rsi']:.1f} (Extremely overbought)")
            issues.append(f"{tech['symbol']} RSI extremely high: {tech['rsi']:.1f}")
        
        if abs(tech["macd"]) > 2:
            print(f"   • {tech['symbol']}: MACD = {tech['macd']:.2f} (Abnormally large)")
            issues.append(f"{tech['symbol']} MACD abnormal: {tech['macd']:.2f}")
    
    # Issue 3: All Optimal Actions are 0
    print(f"\n⚠️  PREDICTION QUALITY:")
    zero_actions = sum(1 for p in predictions_data if p["optimal_action"] == 0)
    print(f"   • {zero_actions}/3 predictions have optimal_action = 0")
    print("   • This suggests ML model isn't providing meaningful recommendations")
    issues.append("All optimal_action values are 0 - model not functioning")
    
    # Issue 4: Price Analysis
    print(f"\n⚠️  PRICE ANALYSIS:")
    for i, tech in enumerate(technical_data):
        bb_width = tech["bb_upper"] - tech["bb_lower"]
        if tech["symbol"] == "CBA.AX" and tech["bb_upper"] > 180:
            print(f"   • {tech['symbol']}: Bollinger Bands ({tech['bb_upper']:.1f}, {tech['bb_lower']:.1f}) seem too wide")
            print(f"     Width: {bb_width:.1f} - May indicate calculation error")
            issues.append(f"{tech['symbol']} Bollinger Bands abnormally wide")
    
    # Issue 5: Sentiment vs Action Mismatch
    print(f"\n⚠️  SENTIMENT-ACTION ALIGNMENT:")
    for i, pred in enumerate(predictions_data):
        sentiment = sentiment_data[i]["sentiment"]
        action = pred["action"]
        
        if sentiment > 0.05 and action == "HOLD":
            print(f"   • {pred['symbol']}: Positive sentiment ({sentiment:.3f}) but action is HOLD")
        elif sentiment < -0.05 and action == "BUY":
            print(f"   • {pred['symbol']}: Negative sentiment ({sentiment:.3f}) but action is BUY")
    
    print(f"\n📊 SUMMARY:")
    print(f"   • Total Issues Found: {len(issues)}")
    print(f"   • Severity: CRITICAL (Data Leakage)")
    print(f"   • Recommended Action: Immediate investigation and fix")
    
    return issues

def generate_recommendations():
    """Generate specific recommendations to fix the issues"""
    
    print("\n\n💡 RECOMMENDED FIXES:")
    print("=" * 50)
    
    print("1. 🕐 FIX TIMESTAMP SYNCHRONIZATION:")
    print("   • Ensure all morning data uses the same time window")
    print("   • Predictions should be made BEFORE market data collection")
    print("   • Add timestamp validation in the pipeline")
    
    print("\n2. 🔧 TECHNICAL INDICATOR VALIDATION:")
    print("   • Add bounds checking for RSI (0-100)")
    print("   • Validate MACD calculations against known ranges")
    print("   • Implement Bollinger Bands sanity checks")
    
    print("\n3. 🤖 ML MODEL INVESTIGATION:")
    print("   • Debug why optimal_action is always 0")
    print("   • Check model training and prediction pipeline")
    print("   • Validate feature engineering process")
    
    print("\n4. 🔄 DATA FLOW AUDIT:")
    print("   • Implement idempotent morning routine (already created)")
    print("   • Add data freshness checks")
    print("   • Create timestamp consistency validation")
    
    print("\n5. 📈 IMMEDIATE ACTIONS:")
    print("   • Run morning routine again with proper timestamps")
    print("   • Validate all technical calculations")
    print("   • Check ML model loading and inference")

if __name__ == "__main__":
    issues = analyze_morning_data()
    generate_recommendations()
    
    print(f"\n🎯 NEXT STEPS:")
    print("   1. Fix timestamp synchronization immediately")
    print("   2. Validate technical indicator calculations") 
    print("   3. Debug ML model optimal_action generation")
    print("   4. Re-run morning routine with fixes")
    print("   5. Verify data consistency in dashboard")
