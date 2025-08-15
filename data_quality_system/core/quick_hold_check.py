#!/usr/bin/env python3
"""
Quick HOLD Analysis - Just the findings
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def quick_hold_analysis():
    """Quick analysis without file saving"""
    
    # Load data
    conn = sqlite3.connect("data/trading_predictions.db")
    all_data = pd.read_sql_query("SELECT * FROM enhanced_outcomes ORDER BY created_at DESC LIMIT 1000", conn)
    hold_data = all_data[all_data['optimal_action'] == 'HOLD'].copy()
    conn.close()
    
    print("🔒 HOLD POSITION ANALYSIS - QUICK FINDINGS")
    print("="*60)
    
    total = len(all_data)
    holds = len(hold_data)
    hold_pct = (holds / total) * 100
    
    print(f"\n📊 BASIC STATS:")
    print(f"   Total Positions: {total}")
    print(f"   HOLD Positions: {holds}")
    print(f"   HOLD Percentage: {hold_pct:.1f}%")
    
    # Returns analysis
    hold_returns = hold_data['return_pct'].dropna()
    all_returns = all_data['return_pct'].dropna()
    
    if len(hold_returns) > 0:
        hold_avg = float(hold_returns.mean())
        all_avg = float(all_returns.mean())
        win_rate = float((hold_returns > 0).sum() / len(hold_returns))
        zero_returns = int((hold_returns == 0).sum())
        
        print(f"\n💰 HOLD PERFORMANCE:")
        print(f"   Average Return: {hold_avg:.3f}%")
        print(f"   Overall Average: {all_avg:.3f}%")
        print(f"   Win Rate: {win_rate:.1%}")
        print(f"   Zero Returns: {zero_returns}")
        
        # Check for suspicious patterns
        return_counts = hold_returns.value_counts()
        if len(return_counts) > 0:
            max_identical = int(return_counts.max())
            most_common = float(return_counts.index[0])
            identical_pct = (max_identical / len(hold_returns)) * 100
            
            if identical_pct > 15:
                print(f"   ⚠️  {max_identical} positions ({identical_pct:.1f}%) have identical return: {most_common:.3f}%")
    
    # Symbol analysis
    hold_by_symbol = hold_data['symbol'].value_counts()
    total_by_symbol = all_data['symbol'].value_counts()
    
    high_hold_symbols = []
    for symbol in total_by_symbol.index:
        if total_by_symbol[symbol] >= 3:  # Sufficient data
            hold_count = hold_by_symbol.get(symbol, 0)
            hold_rate = (hold_count / total_by_symbol[symbol]) * 100
            if hold_rate > 90:
                high_hold_symbols.append((symbol, hold_rate, hold_count, total_by_symbol[symbol]))
    
    print(f"\n📈 SYMBOL PATTERNS:")
    print(f"   Symbols Analyzed: {len([s for s in total_by_symbol.index if total_by_symbol[s] >= 3])}")
    print(f"   High HOLD Rate (>90%): {len(high_hold_symbols)}")
    
    if high_hold_symbols:
        print(f"   Top Biased Symbols:")
        for symbol, rate, hold_cnt, total_cnt in sorted(high_hold_symbols, key=lambda x: x[1], reverse=True)[:5]:
            print(f"     {symbol}: {rate:.1f}% ({hold_cnt}/{total_cnt})")
    
    # Confidence analysis
    if 'confidence_score' in hold_data.columns:
        hold_conf = hold_data['confidence_score'].dropna()
        all_conf = all_data['confidence_score'].dropna()
        
        if len(hold_conf) > 0:
            hold_conf_avg = float(hold_conf.mean())
            all_conf_avg = float(all_conf.mean())
            
            print(f"\n🎯 CONFIDENCE PATTERNS:")
            print(f"   HOLD Avg Confidence: {hold_conf_avg:.3f}")
            print(f"   Overall Avg Confidence: {all_conf_avg:.3f}")
            
            # Check for clustering
            conf_rounded = np.round(hold_conf, 2)
            conf_counts = conf_rounded.value_counts()
            
            if len(conf_counts) > 0:
                max_cluster = int(conf_counts.max())
                most_common_conf = float(conf_counts.index[0])
                cluster_pct = (max_cluster / len(hold_conf)) * 100
                
                if cluster_pct > 20:
                    print(f"   ⚠️  {cluster_pct:.1f}% of HOLD decisions have confidence {most_common_conf}")
    
    print(f"\n" + "="*60)

if __name__ == "__main__":
    quick_hold_analysis()
