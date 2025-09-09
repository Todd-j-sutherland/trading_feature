#!/usr/bin/env python3
"""
Analyze BUY predictions performance and identify issues
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

def analyze_database(db_path):
    """Analyze the predictions database"""
    try:
        conn = sqlite3.connect(db_path)
        
        # Get table schemas
        print("🔍 DATABASE ANALYSIS")
        print("=" * 50)
        
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print(f"📊 Tables found: {', '.join(tables['name'].tolist())}")
        print()
        
        # Analyze predictions table
        if 'predictions' in tables['name'].values:
            print("📈 PREDICTIONS TABLE ANALYSIS")
            print("-" * 30)
            
            # Get column info
            columns = pd.read_sql_query("PRAGMA table_info(predictions)", conn)
            print(f"Columns: {', '.join(columns['name'].tolist())}")
            print()
            
            # Basic stats
            total_preds = pd.read_sql_query("SELECT COUNT(*) as count FROM predictions", conn)
            print(f"Total predictions: {total_preds['count'].iloc[0]}")
            
            # Recent predictions
            recent = pd.read_sql_query("""
                SELECT predicted_action, COUNT(*) as count 
                FROM predictions 
                WHERE datetime(created_at) >= datetime('now', '-7 days')
                GROUP BY predicted_action
                ORDER BY count DESC
            """, conn)
            print(f"\n📅 Recent predictions (last 7 days):")
            for _, row in recent.iterrows():
                print(f"  {row['predicted_action']}: {row['count']}")
            
            # Get sample BUY predictions with details
            buy_samples = pd.read_sql_query("""
                SELECT 
                    symbol, predicted_action, action_confidence, 
                    market_context, tech_score, news_sentiment,
                    volume_trend, confidence_breakdown,
                    created_at
                FROM predictions 
                WHERE predicted_action = 'BUY' 
                ORDER BY created_at DESC 
                LIMIT 10
            """, conn)
            
            print(f"\n🎯 RECENT BUY PREDICTIONS SAMPLE:")
            print("-" * 40)
            for _, row in buy_samples.iterrows():
                print(f"Symbol: {row['symbol']}")
                print(f"  Action: {row['predicted_action']} (Confidence: {row['action_confidence']:.3f})")
                print(f"  Market Context: {row['market_context']}")
                print(f"  Tech Score: {row['tech_score']}")
                print(f"  News Sentiment: {row['news_sentiment']}")
                print(f"  Volume Trend: {row['volume_trend']}")
                print(f"  Time: {row['created_at']}")
                if row['confidence_breakdown']:
                    print(f"  Breakdown: {row['confidence_breakdown']}")
                print()
        
        # Analyze outcomes table if it exists
        if 'outcomes' in tables['name'].values:
            print("📊 OUTCOMES TABLE ANALYSIS")
            print("-" * 30)
            
            outcomes_count = pd.read_sql_query("SELECT COUNT(*) as count FROM outcomes", conn)
            print(f"Total outcomes: {outcomes_count['count'].iloc[0]}")
            
            # Recent outcomes
            recent_outcomes = pd.read_sql_query("""
                SELECT 
                    prediction_id, return_pct, success,
                    entry_price, exit_price, evaluation_timestamp
                FROM outcomes 
                ORDER BY evaluation_timestamp DESC 
                LIMIT 10
            """, conn)
            
            print(f"\n🎯 RECENT OUTCOMES SAMPLE:")
            print("-" * 40)
            for _, row in recent_outcomes.iterrows():
                print(f"ID: {row['prediction_id']}")
                print(f"  Return: {row['return_pct']:.4f}%")
                print(f"  Success: {row['success']}")
                print(f"  Entry: ${row['entry_price']:.2f} → Exit: ${row['exit_price']:.2f}")
                print(f"  Time: {row['evaluation_timestamp']}")
                print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        return False

def analyze_buy_performance(db_path):
    """Analyze BUY prediction performance specifically"""
    try:
        conn = sqlite3.connect(db_path)
        
        print("\n🚨 BUY PREDICTION PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        # Join predictions with outcomes to analyze BUY performance
        query = """
        SELECT 
            p.symbol, p.predicted_action, p.action_confidence,
            p.market_context, p.tech_score, p.news_sentiment,
            p.volume_trend, p.created_at,
            o.return_pct, o.success, o.entry_price, o.exit_price
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.predicted_action = 'BUY'
        AND o.return_pct IS NOT NULL
        ORDER BY p.created_at DESC
        LIMIT 20
        """
        
        buy_performance = pd.read_sql_query(query, conn)
        
        if len(buy_performance) > 0:
            print(f"📊 Analyzed {len(buy_performance)} BUY predictions with outcomes")
            
            success_rate = (buy_performance['success'] == 1).mean()
            avg_return = buy_performance['return_pct'].mean()
            
            print(f"✅ Success Rate: {success_rate:.2%}")
            print(f"📈 Average Return: {avg_return:.4f}%")
            print()
            
            # Analyze by market context
            context_analysis = buy_performance.groupby('market_context').agg({
                'success': lambda x: (x == 1).mean(),
                'return_pct': 'mean',
                'action_confidence': 'mean'
            }).round(4)
            
            print("📊 BUY PERFORMANCE BY MARKET CONTEXT:")
            print(context_analysis)
            print()
            
            # Analyze failed BUY predictions
            failed_buys = buy_performance[buy_performance['success'] == 0]
            print(f"❌ FAILED BUY PREDICTIONS ({len(failed_buys)} total):")
            print("-" * 40)
            
            for _, row in failed_buys.head(10).iterrows():
                print(f"Symbol: {row['symbol']} | Return: {row['return_pct']:.3f}%")
                print(f"  Confidence: {row['action_confidence']:.3f} | Market: {row['market_context']}")
                print(f"  Tech Score: {row['tech_score']} | News: {row['news_sentiment']:.3f}")
                print(f"  Volume Trend: {row['volume_trend']:.3f}")
                print(f"  Price: ${row['entry_price']:.2f} → ${row['exit_price']:.2f}")
                print()
        else:
            print("❌ No BUY predictions with outcomes found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing BUY performance: {e}")

if __name__ == "__main__":
    db_path = "data/trading_predictions.db"
    print(f"🔍 Analyzing database: {db_path}")
    print()
    
    if analyze_database(db_path):
        analyze_buy_performance(db_path)
    
    print("\n✅ Analysis complete!")