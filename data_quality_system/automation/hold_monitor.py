#!/usr/bin/env python3
"""
HOLD Position Monitor
Quick check for HOLD pattern changes over time
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

def monitor_hold_patterns():
    """Monitor HOLD patterns with trend analysis"""
    
    print("🔒 HOLD Position Monitor")
    print("="*50)
    
    db_path = "data/trading_predictions.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Get recent data with dates
    query = """
    SELECT 
        created_at,
        symbol,
        optimal_action,
        return_pct,
        confidence_score,
        date(created_at) as trade_date
    FROM enhanced_outcomes 
    ORDER BY created_at DESC 
    LIMIT 200
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ No data found")
        return
    
    # Overall stats
    total = len(df)
    holds = len(df[df['optimal_action'] == 'HOLD'])
    buys = len(df[df['optimal_action'] == 'BUY'])
    sells = len(df[df['optimal_action'] == 'SELL'])
    
    print(f"\n📊 RECENT ACTIVITY ({total} positions):")
    print(f"   HOLD: {holds} ({holds/total*100:.1f}%)")
    print(f"   BUY:  {buys} ({buys/total*100:.1f}%)")
    print(f"   SELL: {sells} ({sells/total*100:.1f}%)")
    
    # Daily trend analysis
    daily_stats = df.groupby('trade_date').agg({
        'optimal_action': ['count', lambda x: (x == 'HOLD').sum()]
    }).round(2)
    
    # Flatten column names
    daily_stats.columns = ['total_trades', 'hold_trades']
    daily_stats['hold_rate'] = (daily_stats['hold_trades'] / daily_stats['total_trades'] * 100).round(1)
    
    print(f"\n📅 DAILY HOLD RATES (Recent 10 days):")
    for date, row in daily_stats.tail(10).iterrows():
        if row['total_trades'] >= 3:  # Only show days with sufficient data
            print(f"   {date}: {row['hold_rate']:.1f}% ({int(row['hold_trades'])}/{int(row['total_trades'])})")
    
    # Performance by action
    performance = df.groupby('optimal_action')['return_pct'].agg(['count', 'mean', 'std']).round(3)
    performance.columns = ['Count', 'Avg_Return', 'Std_Dev']
    
    print(f"\n💰 PERFORMANCE BY ACTION:")
    for action in ['HOLD', 'BUY', 'SELL']:
        if action in performance.index:
            row = performance.loc[action]
            print(f"   {action}: {row['Avg_Return']:.3f}% avg ({int(row['Count'])} positions)")
    
    # Symbol analysis
    symbol_holds = df.groupby('symbol').agg({
        'optimal_action': ['count', lambda x: (x == 'HOLD').sum()]
    })
    symbol_holds.columns = ['total', 'holds']
    symbol_holds['hold_rate'] = (symbol_holds['holds'] / symbol_holds['total'] * 100).round(1)
    symbol_holds = symbol_holds[symbol_holds['total'] >= 5]  # Filter for sufficient data
    
    print(f"\n📈 SYMBOL HOLD RATES:")
    for symbol, row in symbol_holds.sort_values('hold_rate', ascending=False).iterrows():
        print(f"   {symbol}: {row['hold_rate']:.1f}% ({int(row['holds'])}/{int(row['total'])})")
    
    # Check for recent changes
    recent_7d = df.head(min(50, len(df)))  # Last ~week
    older_data = df.tail(min(100, len(df)-50)) if len(df) > 50 else pd.DataFrame()
    
    if len(older_data) > 0:
        recent_hold_rate = (recent_7d['optimal_action'] == 'HOLD').sum() / len(recent_7d) * 100
        older_hold_rate = (older_data['optimal_action'] == 'HOLD').sum() / len(older_data) * 100
        
        print(f"\n📈 TREND ANALYSIS:")
        print(f"   Recent HOLD Rate: {recent_hold_rate:.1f}%")
        print(f"   Previous HOLD Rate: {older_hold_rate:.1f}%")
        
        if abs(recent_hold_rate - older_hold_rate) > 10:
            if recent_hold_rate > older_hold_rate:
                print(f"   🔺 HOLD rate increased by {recent_hold_rate - older_hold_rate:.1f}%")
            else:
                print(f"   🔻 HOLD rate decreased by {older_hold_rate - recent_hold_rate:.1f}%")
        else:
            print(f"   ➡️  HOLD rate stable (±{abs(recent_hold_rate - older_hold_rate):.1f}%)")
    
    # Confidence clustering check
    if 'confidence_score' in df.columns:
        hold_conf = df[df['optimal_action'] == 'HOLD']['confidence_score'].dropna()
        if len(hold_conf) > 0:
            import numpy as np
            conf_rounded = np.round(hold_conf, 2)
            conf_counts = conf_rounded.value_counts()
            
            if len(conf_counts) > 0:
                max_cluster = conf_counts.max()
                cluster_pct = (max_cluster / len(hold_conf)) * 100
                
                if cluster_pct > 20:
                    most_common = conf_counts.index[0]
                    print(f"\n🎯 CONFIDENCE CLUSTERING:")
                    print(f"   {cluster_pct:.1f}% of HOLD decisions have confidence {most_common}")
    
    print(f"\n" + "="*50)

if __name__ == "__main__":
    monitor_hold_patterns()
