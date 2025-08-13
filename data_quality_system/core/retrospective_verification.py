#!/usr/bin/env python3
"""
Retrospective Labeling Verification
Proves that the system is doing post-hoc classification, not prediction
"""

import sqlite3
import pandas as pd
from datetime import datetime

def verify_retrospective_labeling():
    """Verify that actions are assigned retrospectively"""
    
    print("🔍 RETROSPECTIVE LABELING VERIFICATION")
    print("="*60)
    
    conn = sqlite3.connect("data/trading_unified.db")
    
    # Get all positions with timing data
    query = """
    SELECT 
        symbol,
        datetime(prediction_timestamp) as pred_time,
        datetime(created_at) as label_time,
        optimal_action,
        return_pct,
        price_direction_1d,
        confidence_score,
        ROUND((julianday(created_at) - julianday(prediction_timestamp)) * 24, 1) as hours_delay
    FROM enhanced_outcomes 
    WHERE optimal_action IN ('BUY', 'SELL')
    ORDER BY prediction_timestamp
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("❌ No BUY/SELL positions found")
        return
    
    print(f"\n📊 FOUND {len(df)} BUY/SELL POSITIONS")
    
    # Analyze timing patterns
    immediate_labels = df[df['hours_delay'] < 1]
    delayed_labels = df[df['hours_delay'] >= 1]
    
    print(f"\n⏱️  TIMING ANALYSIS:")
    print(f"   Immediate labels (<1h): {len(immediate_labels)}")
    print(f"   Delayed labels (≥1h): {len(delayed_labels)}")
    print(f"   Average delay: {df['hours_delay'].mean():.1f} hours")
    print(f"   Maximum delay: {df['hours_delay'].max():.1f} hours")
    
    # Check for retrospective pattern
    print(f"\n🔍 RETROSPECTIVE EVIDENCE:")
    
    # Evidence 1: Variable delays
    if df['hours_delay'].std() > 10:
        print(f"   ✅ Variable labeling delays (std: {df['hours_delay'].std():.1f}h)")
        print(f"      → Suggests waiting for outcomes before labeling")
    
    # Evidence 2: BUY labels with negative returns
    buy_positions = df[df['optimal_action'] == 'BUY']
    negative_buys = buy_positions[buy_positions['return_pct'] < 0]
    
    if len(negative_buys) > 0:
        print(f"   ✅ {len(negative_buys)} BUY positions with negative returns")
        print(f"      → Proves system didn't predict correctly")
    
    # Evidence 3: Inconsistent direction vs action
    inconsistent = df[
        ((df['optimal_action'] == 'BUY') & (df['price_direction_1d'] == -1)) |
        ((df['optimal_action'] == 'SELL') & (df['price_direction_1d'] == 1))
    ]
    
    if len(inconsistent) > 0:
        print(f"   ✅ {len(inconsistent)} positions with contradictory direction/action")
        print(f"      → Direction predictions disagree with action labels")
    
    # Show specific examples
    print(f"\n📋 DETAILED EXAMPLES:")
    print("-" * 60)
    
    for i, row in df.head(8).iterrows():
        status = "✅" if row['return_pct'] > 0 else "❌"
        direction = "UP" if row['price_direction_1d'] == 1 else "DOWN" if row['price_direction_1d'] == -1 else "NULL"
        
        print(f"{status} {row['symbol']} - {row['optimal_action']}")
        print(f"   Pred: {row['pred_time']}")
        print(f"   Label: {row['label_time']} (+{row['hours_delay']}h)")
        print(f"   Direction: {direction} | Return: {row['return_pct']:.2f}%")
        
        # Check for contradictions
        if row['optimal_action'] == 'BUY' and row['return_pct'] < 0:
            print(f"   ⚠️  CONTRADICTION: BUY signal but negative return!")
        if row['optimal_action'] == 'BUY' and row['price_direction_1d'] == -1:
            print(f"   ⚠️  CONTRADICTION: BUY signal but predicted DOWN!")
            
        print()
    
    # Simulate what real predictions should look like
    print(f"🎯 WHAT REAL PREDICTIONS SHOULD BE:")
    print(f"   1. Make prediction at prediction_timestamp")
    print(f"   2. Store immediately (delay = 0)")
    print(f"   3. Wait for actual outcomes")
    print(f"   4. Evaluate accuracy separately")
    print(f"   5. NEVER change the original prediction")
    
    # Show the labeling logic
    print(f"\n🔧 CURRENT LABELING LOGIC (WRONG):")
    print(f"   if actual_return > 0.5%: label = 'BUY'")
    print(f"   elif actual_return < -0.5%: label = 'SELL'") 
    print(f"   else: label = 'HOLD'")
    print(f"   → This is curve-fitting, not prediction!")

def main():
    verify_retrospective_labeling()

if __name__ == "__main__":
    main()
