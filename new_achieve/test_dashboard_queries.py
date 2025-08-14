#!/usr/bin/env python3
"""
Test script for ML dashboard queries
"""

import sqlite3
import pandas as pd
from datetime import datetime

def test_queries():
    """Test all dashboard queries"""
    
    print("🔍 Testing ML Dashboard Queries")
    print("=" * 50)
    
    conn = sqlite3.connect('data/trading_unified.db')
    
    # Test 1: Latest combined data
    print("\n1. Testing Latest Combined Data Query...")
    query1 = """
    WITH latest_data AS (
        SELECT 
            ef.symbol,
            ef.timestamp,
            ef.sentiment_score,
            ef.confidence as sentiment_confidence,
            ef.news_count,
            ef.reddit_sentiment,
            ef.rsi,
            ef.macd_line,
            ef.current_price,
            ef.price_change_1d,
            ef.volatility_20d,
            eo.optimal_action,
            eo.confidence_score as ml_confidence,
            eo.return_pct,
            eo.price_direction_1d,
            ROW_NUMBER() OVER (PARTITION BY ef.symbol ORDER BY ef.timestamp DESC) as rn
        FROM enhanced_features ef
        JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
    )
    SELECT * FROM latest_data WHERE rn = 1 ORDER BY symbol
    """
    
    df1 = pd.read_sql_query(query1, conn)
    print(f"✅ Latest data: {len(df1)} symbols")
    print(df1[['symbol', 'optimal_action', 'sentiment_score', 'ml_confidence']].head())
    
    # Test 2: ML Performance data
    print("\n2. Testing ML Performance Query...")
    query2 = """
    SELECT 
        symbol,
        COUNT(*) as total_predictions,
        SUM(CASE WHEN optimal_action = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
        SUM(CASE WHEN optimal_action = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
        SUM(CASE WHEN optimal_action = 'HOLD' THEN 1 ELSE 0 END) as hold_signals,
        ROUND(AVG(confidence_score), 3) as avg_ml_confidence,
        ROUND(AVG(return_pct), 3) as avg_return,
        ROUND(SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate_pct
    FROM enhanced_outcomes 
    GROUP BY symbol 
    ORDER BY avg_return DESC
    """
    
    df2 = pd.read_sql_query(query2, conn)
    print(f"✅ Performance data: {len(df2)} symbols")
    print(df2[['symbol', 'total_predictions', 'avg_return', 'win_rate_pct']].head())
    
    # Test 3: Training overview
    print("\n3. Testing Training Overview Query...")
    query3 = """
    SELECT 
        COUNT(*) as total_samples,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(date(timestamp)) as earliest_date,
        MAX(date(timestamp)) as latest_date,
        ROUND(AVG(sentiment_score), 3) as avg_sentiment,
        ROUND(AVG(confidence), 3) as avg_confidence,
        ROUND(AVG(rsi), 1) as avg_rsi
    FROM enhanced_features
    """
    
    df3 = pd.read_sql_query(query3, conn)
    print(f"✅ Training overview:")
    print(df3.iloc[0].to_dict())
    
    # Test 4: Action distribution
    print("\n4. Testing Action Distribution Query...")
    query4 = """
    SELECT 
        optimal_action,
        COUNT(*) as count,
        ROUND(AVG(confidence_score), 3) as avg_confidence,
        ROUND(AVG(return_pct), 3) as avg_return_pct
    FROM enhanced_outcomes 
    GROUP BY optimal_action 
    ORDER BY count DESC
    """
    
    df4 = pd.read_sql_query(query4, conn)
    print(f"✅ Action distribution:")
    print(df4)
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 All queries executed successfully!")
    print("\nSummary:")
    print(f"  • {len(df1)} symbols with latest data")
    print(f"  • {df3.iloc[0]['total_samples']} total ML training samples")
    print(f"  • {len(df4)} different action types")
    print(f"  • Date range: {df3.iloc[0]['earliest_date']} to {df3.iloc[0]['latest_date']}")
    
    return True

if __name__ == "__main__":
    try:
        test_queries()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
