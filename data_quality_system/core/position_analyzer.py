#!/usr/bin/env python3
"""
Position Detail Analyzer
Get comprehensive details for any specific trading position
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

def analyze_position_details(symbol=None, action=None, limit=10):
    """Analyze specific positions with full details"""
    
    print("🔍 Position Detail Analyzer")
    print("="*50)
    
    conn = sqlite3.connect("data/trading_unified.db")
    
    # Build query
    where_clause = "WHERE 1=1"
    if symbol:
        where_clause += f" AND o.symbol = '{symbol}'"
    if action:
        where_clause += f" AND o.optimal_action = '{action}'"
    
    query = f"""
    SELECT 
        o.symbol,
        datetime(o.prediction_timestamp) as prediction_time,
        o.optimal_action,
        o.confidence_score,
        o.entry_price,
        o.exit_price_1d,
        o.return_pct,
        
        -- Predictions vs Reality
        o.price_direction_1d as predicted_direction,
        CASE 
            WHEN o.return_pct > 0 THEN 1 
            WHEN o.return_pct < 0 THEN -1 
            ELSE 0 
        END as actual_direction,
        
        -- Technical Indicators
        f.rsi,
        f.macd_histogram,
        f.current_price,
        f.price_vs_sma20,
        f.price_vs_sma50,
        f.price_vs_sma200,
        f.bollinger_width,
        f.volume_ratio,
        
        -- Sentiment & News
        f.sentiment_score,
        f.news_count,
        f.reddit_sentiment,
        
        -- Market Context
        f.asx_market_hours,
        f.monday_effect,
        f.friday_effect,
        f.asx200_change,
        f.vix_level,
        
        -- Price Context
        f.price_change_1h,
        f.price_change_4h,
        f.price_change_1d,
        
        datetime(o.created_at) as outcome_time
        
    FROM enhanced_outcomes o 
    JOIN enhanced_features f ON o.feature_id = f.id 
    {where_clause}
    ORDER BY o.prediction_timestamp DESC
    LIMIT {limit}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ No positions found matching criteria")
        return
    
    print(f"\n📊 Found {len(df)} positions")
    
    for i, row in df.iterrows():
        print(f"\n" + "="*60)
        print(f" 🎯 POSITION {i+1}: {row['symbol']} - {row['optimal_action']}")
        print("="*60)
        
        print(f"\n📅 TIMING:")
        print(f"   Prediction: {row['prediction_time']}")
        print(f"   Market Hours: {'Yes' if row['asx_market_hours'] else 'No'}")
        print(f"   Monday Effect: {'Active' if row['monday_effect'] else 'No'}")
        print(f"   Friday Effect: {'Active' if row['friday_effect'] else 'No'}")
        
        print(f"\n💰 PERFORMANCE:")
        print(f"   Confidence: {row['confidence_score']:.3f}")
        print(f"   Entry Price: ${row['entry_price']:.2f}")
        print(f"   Exit Price: ${row['exit_price_1d']:.2f}")
        print(f"   Return: {row['return_pct']:.2f}%")
        
        # Prediction accuracy
        pred_dir = row['predicted_direction']
        actual_dir = row['actual_direction']
        direction_names = {1: "UP", 0: "FLAT", -1: "DOWN"}
        
        prediction_correct = pred_dir == actual_dir
        print(f"   Predicted Direction: {direction_names.get(pred_dir, 'Unknown')}")
        print(f"   Actual Direction: {direction_names.get(actual_dir, 'Unknown')}")
        print(f"   Prediction Accuracy: {'✅ Correct' if prediction_correct else '❌ Wrong'}")
        
        print(f"\n📈 TECHNICAL INDICATORS:")
        print(f"   RSI: {row['rsi']:.1f}")
        print(f"   MACD Histogram: {row['macd_histogram']:.4f}")
        print(f"   Price vs SMA20: {row['price_vs_sma20']:.2f}%")
        print(f"   Price vs SMA50: {row['price_vs_sma50']:.2f}%")
        print(f"   Price vs SMA200: {row['price_vs_sma200']:.2f}%")
        print(f"   Bollinger Width: {row['bollinger_width']:.2f}")
        print(f"   Volume Ratio: {row['volume_ratio']:.1f}x")
        
        print(f"\n📰 SENTIMENT & NEWS:")
        print(f"   Sentiment Score: {row['sentiment_score']:.4f}")
        print(f"   News Count: {row['news_count']}")
        print(f"   Reddit Sentiment: {row['reddit_sentiment']:.4f}")
        
        print(f"\n🌍 MARKET CONTEXT:")
        print(f"   ASX200 Change: {row['asx200_change']:.2f}%")
        print(f"   VIX Level: {row['vix_level']:.2f}")
        
        print(f"\n📊 RECENT PRICE ACTION:")
        print(f"   1h Change: {row['price_change_1h']:.2f}%")
        print(f"   4h Change: {row['price_change_4h']:.2f}%")
        print(f"   1d Change: {row['price_change_1d']:.2f}%")
        
        # Analysis summary
        print(f"\n🔍 ANALYSIS SUMMARY:")
        
        reasons = []
        
        # RSI analysis
        rsi = row['rsi']
        if rsi < 30:
            reasons.append("RSI oversold (<30) - potential bounce")
        elif rsi > 70:
            reasons.append("RSI overbought (>70) - potential reversal risk")
        elif 40 <= rsi <= 60:
            reasons.append("RSI neutral zone - balanced momentum")
        
        # Moving average position
        if row['price_vs_sma20'] > 2:
            reasons.append("Strong above SMA20 (+2%) - bullish trend")
        elif row['price_vs_sma20'] < -2:
            reasons.append("Weak below SMA20 (-2%) - bearish trend")
        
        # Volume
        if row['volume_ratio'] > 3:
            reasons.append(f"High volume ({row['volume_ratio']:.1f}x) - strong interest")
        elif row['volume_ratio'] < 1.5:
            reasons.append("Low volume - weak conviction")
        
        # Sentiment
        if abs(row['sentiment_score']) > 0.1:
            sentiment_direction = "Positive" if row['sentiment_score'] > 0 else "Negative"
            reasons.append(f"{sentiment_direction} sentiment ({row['sentiment_score']:.3f})")
        
        # News activity
        if row['news_count'] > 40:
            reasons.append(f"High news activity ({row['news_count']} articles)")
        
        for reason in reasons:
            print(f"   • {reason}")
        
        if not reasons:
            print("   • No significant technical or sentiment factors identified")

def main():
    """Main function with options"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1].upper() in ['BUY', 'SELL', 'HOLD']:
            action = sys.argv[1].upper()
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            analyze_position_details(symbol=symbol, action=action)
        else:
            symbol = sys.argv[1].upper()
            analyze_position_details(symbol=symbol)
    else:
        # Default: show all BUY positions
        print("🎯 Showing all BUY positions (use: python script.py BUY/SELL/HOLD or SYMBOL)")
        analyze_position_details(action='BUY')

if __name__ == "__main__":
    main()
