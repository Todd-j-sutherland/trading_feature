#!/usr/bin/env python3
"""
Analyze HOLD Prediction Issue
Investigate why ML predictions are all coming out as HOLD on remote server
"""

import json
import pandas as pd
from datetime import datetime

def analyze_hold_predictions():
    """Analyze the prediction data to understand HOLD bias"""
    
    print("🔍 Analyzing HOLD Prediction Issue")
    print("=" * 50)
    
    # Sample data from your remote predictions
    predictions = [
        {
            "symbol": "QBE.AX",
            "action": "HOLD",
            "confidence": 0.5964525146484376,
            "technical_features": 0.3781260986328125,
            "news_features": 0.2175640869140625,
            "volume_features": 0.0,
            "risk_features": 0.0,
            "market_trend_percentage": -0.26,
            "volume_trend_percentage": -30.6,
            "news_sentiment_score": 0.092,
            "composite_technical_score": 37,
            "breakdown": "Tech:0.372 + News:0.220 + Vol:0.000 + Risk:0.000 × Market:1.00 = 0.5"
        },
        {
            "symbol": "SUN.AX", 
            "action": "HOLD",
            "confidence": 0.47611047363281256,
            "technical_features": 0.3535006103515625,
            "news_features": 0.11922882080078125,
            "volume_features": 0.0,
            "risk_features": 0.0032015991210937508,
            "market_trend_percentage": -0.26,
            "volume_trend_percentage": -36.1,
            "news_sentiment_score": 0.008,
            "composite_technical_score": 35,
            "breakdown": "Tech:0.356 + News:0.120 + Vol:0.000 + Risk:0.000 × Market:1.00 = 0.476"
        },
        {
            "symbol": "NAB.AX",
            "action": "HOLD", 
            "confidence": 0.7618524780273438,
            "technical_features": 0.45219030761718754,
            "news_features": 0.2189324951171875,
            "volume_features": 0.0,
            "risk_features": 0.09471649169921875,
            "market_trend_percentage": -0.26,
            "volume_trend_percentage": -29.8,
            "news_sentiment_score": 0.084,
            "composite_technical_score": 45,
            "breakdown": "Tech:0.449 + News:0.220 + Vol:0.000 + Risk:0.100 × Market:1.00 = 0.769"
        },
        {
            "symbol": "CBA.AX",
            "action": "HOLD",
            "confidence": 0.5782915039062501,
            "technical_features": 0.3451405639648437,
            "news_features": 0.2222796630859375,
            "volume_features": 0.0,
            "risk_features": 0.0090118408203125,
            "market_trend_percentage": -0.26,
            "volume_trend_percentage": -36.0,
            "news_sentiment_score": 0.19,
            "composite_technical_score": 34,
            "breakdown": "Tech:0.352 + News:0.220 + Vol:0.000 + Risk:0.000 × Market:1.00 = 0.572"
        }
    ]
    
    df = pd.DataFrame(predictions)
    
    print("📊 PREDICTION ANALYSIS SUMMARY")
    print("-" * 30)
    print(f"Total Predictions: {len(df)}")
    print(f"All HOLD Actions: {all(df['action'] == 'HOLD')}")
    print(f"Average Confidence: {df['confidence'].mean():.1%}")
    print()
    
    print("🔍 KEY ISSUES IDENTIFIED:")
    print("-" * 25)
    
    # Issue 1: Volume Features are all zero
    volume_issues = df['volume_features'].sum() == 0
    print(f"1. ❌ Volume Features All Zero: {volume_issues}")
    if volume_issues:
        print("   • All volume_features = 0.0")
        print("   • Volume component not contributing to decisions")
        print("   • May indicate volume data pipeline issue")
    print()
    
    # Issue 2: Low technical scores
    low_tech = (df['composite_technical_score'] < 50).all()
    print(f"2. ⚠️  Low Technical Scores: {low_tech}")
    print(f"   • Technical scores range: {df['composite_technical_score'].min()}-{df['composite_technical_score'].max()}")
    print(f"   • All below neutral (50)")
    print("   • Suggests bearish technical conditions")
    print()
    
    # Issue 3: Negative market trend
    negative_trend = (df['market_trend_percentage'] < 0).all()
    print(f"3. 📉 Negative Market Trend: {negative_trend}")
    print(f"   • Market trend: {df['market_trend_percentage'].iloc[0]:.2f}%")
    print("   • Overall declining market sentiment")
    print()
    
    # Issue 4: Confidence range analysis
    conf_range = df['confidence'].max() - df['confidence'].min()
    print(f"4. 📊 Confidence Range Analysis:")
    print(f"   • Range: {df['confidence'].min():.1%} - {df['confidence'].max():.1%}")
    print(f"   • Spread: {conf_range:.1%}")
    print(f"   • Average: {df['confidence'].mean():.1%}")
    
    # Determine if this is reasonable HOLD behavior
    avg_confidence = df['confidence'].mean()
    if avg_confidence < 0.7:
        print("   • ⚠️ Low confidence suggests uncertain market conditions")
    print()
    
    print("🎯 DECISION LOGIC ANALYSIS:")
    print("-" * 27)
    
    # Analyze the decision thresholds
    print("Based on the ML model logic, HOLD decisions occur when:")
    print("• Confidence is in the middle range (not strongly BUY or SELL)")
    print("• Technical indicators are neutral/weak")
    print("• Market conditions are uncertain")
    print()
    
    print("📈 COMPONENT BREAKDOWN:")
    print("-" * 22)
    for i, row in df.iterrows():
        print(f"{row['symbol']}:")
        print(f"  Tech: {row['technical_features']:.3f} ({row['composite_technical_score']}/100)")
        print(f"  News: {row['news_features']:.3f} (sentiment: {row['news_sentiment_score']:+.3f})")
        print(f"  Volume: {row['volume_features']:.3f} (trend: {row['volume_trend_percentage']:.1f}%)")
        print(f"  Risk: {row['risk_features']:.3f}")
        print(f"  → Confidence: {row['confidence']:.1%} = {row['action']}")
        print()
    
    print("🔧 POTENTIAL FIXES:")
    print("-" * 17)
    print("1. 📊 Volume Data Pipeline:")
    print("   • Check if volume data is being fetched correctly")
    print("   • Verify volume trend calculation")
    print("   • Ensure volume features aren't being zeroed out")
    print()
    
    print("2. 📈 Technical Indicator Calibration:")
    print("   • Review RSI, MACD, Bollinger Band calculations")
    print("   • Check if technical scores are properly normalized")
    print("   • Verify technical data freshness")
    print()
    
    print("3. 🎯 Decision Threshold Tuning:")
    print("   • Current model may be too conservative")
    print("   • Consider adjusting BUY/SELL confidence thresholds")
    print("   • Review market condition filters")
    print()
    
    print("4. 📰 News Sentiment Impact:")
    print("   • News scores are low/neutral")
    print("   • Check news data quality and recency")
    print("   • Verify sentiment analysis accuracy")
    print()
    
    print("🚨 IMMEDIATE ACTIONS:")
    print("-" * 19)
    print("1. Check volume data source connectivity")
    print("2. Review technical indicator calculations")
    print("3. Verify market data freshness")
    print("4. Test with historical data that should produce BUY/SELL")
    print("5. Consider temporarily lowering decision thresholds")
    
    return df

def suggest_ml_fixes():
    """Suggest specific ML model fixes"""
    
    print("\n" + "="*60)
    print("🔧 SUGGESTED ML MODEL FIXES")
    print("="*60)
    
    print("""
🎯 CONFIDENCE THRESHOLD ADJUSTMENTS:

Current Logic (suspected):
- BUY: confidence > 0.75 AND positive technical + news
- SELL: confidence > 0.75 AND negative technical + news  
- HOLD: everything else

Suggested Adjustments:
- BUY: confidence > 0.65 OR (confidence > 0.55 AND technical > 0.4)
- SELL: confidence > 0.65 OR (confidence > 0.55 AND technical < -0.2)
- HOLD: confidence < 0.55

📊 COMPONENT WEIGHT REBALANCING:

Current weights appear to be:
- Technical: ~35-45% (primary driver)
- News: ~20-25% 
- Volume: 0% (BROKEN!)
- Risk: 0-10%

Suggested weights:
- Technical: 40%
- News: 30%
- Volume: 20% (FIX PIPELINE!)
- Risk: 10%

🔍 DEBUGGING COMMANDS:

Check volume data:
```python
# In your ML pipeline
print(f"Volume data: {volume_features}")
print(f"Volume trend: {volume_trend_percentage}")
print(f"Raw volume: {raw_volume_data}")
```

Check decision thresholds:
```python
# In decision logic
print(f"Confidence: {confidence}")
print(f"BUY threshold: {buy_threshold}")
print(f"SELL threshold: {sell_threshold}")
print(f"Final action: {action}")
```
""")

if __name__ == "__main__":
    df = analyze_hold_predictions()
    suggest_ml_fixes()
    
    print(f"\n📊 Analysis complete. {len(df)} predictions analyzed.")
    print("All predictions defaulting to HOLD due to:")
    print("• Volume pipeline failure (all 0.0)")
    print("• Low technical scores (all < 50)")
    print("• Conservative confidence thresholds")
    print("• Negative market trend bias")