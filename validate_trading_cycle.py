#!/usr/bin/env python3
"""
Trading Cycle Validation Script
Run this after morning + evening analysis to verify the system is working correctly
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def validate_trading_cycle():
    """Validate that morning and evening analysis is working correctly"""
    
    print("🔍 TRADING CYCLE VALIDATION")
    print("=" * 40)
    
    conn = sqlite3.connect('data/trading_unified.db')
    
    # Check recent activity (last 24 hours)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n📊 RECENT ACTIVITY (since {yesterday})")
    print("-" * 35)
    
    # Recent features
    recent_features_query = f"""
    SELECT 
        COUNT(*) as new_features,
        COUNT(DISTINCT symbol) as symbols_analyzed,
        MAX(timestamp) as latest_feature,
        AVG(sentiment_score) as avg_sentiment,
        AVG(rsi) as avg_rsi
    FROM enhanced_features 
    WHERE timestamp >= '{yesterday}'
    """
    
    features_result = pd.read_sql_query(recent_features_query, conn).iloc[0]
    
    print(f"New Features: {features_result['new_features']}")
    print(f"Symbols Analyzed: {features_result['symbols_analyzed']}")
    print(f"Latest Feature: {features_result['latest_feature']}")
    print(f"Avg Sentiment: {features_result['avg_sentiment']:.4f}")
    print(f"Avg RSI: {features_result['avg_rsi']:.1f}")
    
    # Recent outcomes
    recent_outcomes_query = f"""
    SELECT 
        COUNT(*) as new_outcomes,
        COUNT(DISTINCT symbol) as symbols_with_outcomes,
        COUNT(CASE WHEN return_pct IS NOT NULL THEN 1 END) as outcomes_with_returns,
        COUNT(CASE WHEN exit_price_1d IS NOT NULL THEN 1 END) as outcomes_with_exit_prices,
        MAX(prediction_timestamp) as latest_outcome
    FROM enhanced_outcomes 
    WHERE prediction_timestamp >= '{yesterday}'
    """
    
    outcomes_result = pd.read_sql_query(recent_outcomes_query, conn).iloc[0]
    
    print(f"\nNew Outcomes: {outcomes_result['new_outcomes']}")
    print(f"Symbols with Outcomes: {outcomes_result['symbols_with_outcomes']}")
    print(f"Outcomes with Returns: {outcomes_result['outcomes_with_returns']}")
    print(f"Outcomes with Exit Prices: {outcomes_result['outcomes_with_exit_prices']}")
    print(f"Latest Outcome: {outcomes_result['latest_outcome']}")
    
    # Data quality check
    print(f"\n✅ QUALITY CHECKS")
    print("-" * 20)
    
    if outcomes_result['new_outcomes'] > 0:
        exit_price_completion = (outcomes_result['outcomes_with_exit_prices'] / outcomes_result['new_outcomes']) * 100
        return_completion = (outcomes_result['outcomes_with_returns'] / outcomes_result['new_outcomes']) * 100
        
        print(f"Exit Price Completion: {exit_price_completion:.1f}%")
        print(f"Return Calculation: {return_completion:.1f}%")
        
        if exit_price_completion >= 80:
            print("✅ Exit price tracking: WORKING")
        else:
            print("❌ Exit price tracking: NEEDS ATTENTION")
            
        if return_completion >= 95:
            print("✅ Return calculations: WORKING")
        else:
            print("❌ Return calculations: NEEDS ATTENTION")
    else:
        print("ℹ️ No new outcomes to validate (may need evening run)")
    
    # Recent trading actions
    if outcomes_result['new_outcomes'] > 0:
        actions_query = f"""
        SELECT 
            optimal_action,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence,
            AVG(return_pct) as avg_return
        FROM enhanced_outcomes 
        WHERE prediction_timestamp >= '{yesterday}'
        GROUP BY optimal_action
        ORDER BY count DESC
        """
        
        actions_df = pd.read_sql_query(actions_query, conn)
        
        print(f"\n📈 RECENT TRADING ACTIONS")
        print("-" * 30)
        
        for _, row in actions_df.iterrows():
            action = row['optimal_action']
            count = row['count']
            confidence = row['avg_confidence'] if pd.notna(row['avg_confidence']) else 'N/A'
            avg_return = row['avg_return'] if pd.notna(row['avg_return']) else 0
            
            print(f"{action}: {count} predictions, Confidence: {confidence}, Avg Return: {avg_return:.4f}%")
    
    # Overall system health
    print(f"\n🏥 SYSTEM HEALTH")
    print("-" * 20)
    
    total_features = pd.read_sql_query("SELECT COUNT(*) as count FROM enhanced_features", conn).iloc[0]['count']
    total_outcomes = pd.read_sql_query("SELECT COUNT(*) as count FROM enhanced_outcomes", conn).iloc[0]['count']
    
    print(f"Total Features: {total_features}")
    print(f"Total Outcomes: {total_outcomes}")
    print(f"Feature-to-Outcome Ratio: {(total_outcomes/total_features)*100:.1f}%")
    
    if features_result['new_features'] > 0 and outcomes_result['new_outcomes'] > 0:
        print("\n🎉 SYSTEM STATUS: HEALTHY")
        print("✅ Morning analysis: Collecting features")
        print("✅ Evening analysis: Recording outcomes")
    elif features_result['new_features'] > 0:
        print("\n⚠️ SYSTEM STATUS: PARTIAL")
        print("✅ Morning analysis: Working")
        print("❌ Evening analysis: May need to run")
    else:
        print("\n❌ SYSTEM STATUS: INACTIVE")
        print("❌ No recent activity detected")
    
    conn.close()

if __name__ == "__main__":
    validate_trading_cycle()
