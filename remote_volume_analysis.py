#!/usr/bin/env python3
"""
REMOTE Volume and Restriction Analysis: Sept 12 vs Sept 19
To be run on the remote server: root@170.64.199.151
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json

def main():
    print("🔍 REMOTE VOLUME & RESTRICTION ANALYSIS: Sept 12 vs Sept 19")
    print("=" * 65)
    
    # Database path on remote server
    db_path = "/root/test/data/trading_predictions.db"
    
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ Connected to database: {db_path}")
        
        # Check available dates
        date_query = """
        SELECT DISTINCT DATE(prediction_timestamp) as pred_date, COUNT(*) as count
        FROM predictions 
        WHERE DATE(prediction_timestamp) BETWEEN '2025-09-10' AND '2025-09-20'
        GROUP BY DATE(prediction_timestamp)
        ORDER BY pred_date
        """
        
        date_df = pd.read_sql_query(date_query, conn)
        print(f"\n📅 Available prediction dates:")
        for _, row in date_df.iterrows():
            print(f"  {row['pred_date']}: {row['count']} predictions")
        
        # Get Sept 12 and Sept 19 data
        main_query = """
        SELECT 
            symbol,
            DATE(prediction_timestamp) as pred_date,
            predicted_action,
            action_confidence,
            volume_trend,
            technical_score,
            news_sentiment,
            risk_assessment,
            entry_price,
            prediction_timestamp
        FROM predictions 
        WHERE DATE(prediction_timestamp) IN ('2025-09-12', '2025-09-19')
        ORDER BY symbol, prediction_timestamp
        """
        
        df = pd.read_sql_query(main_query, conn)
        
        if len(df) == 0:
            print("❌ No data found for Sept 12 or Sept 19")
            return
        
        print(f"\n📊 Loaded {len(df)} predictions")
        
        # Split by date
        sept12_data = df[df['pred_date'] == '2025-09-12']
        sept19_data = df[df['pred_date'] == '2025-09-19']
        
        print(f"📅 Sept 12: {len(sept12_data)} predictions")
        print(f"📅 Sept 19: {len(sept19_data)} predictions")
        
        # Analyze volume patterns
        analyze_volume_comparison(sept12_data, sept19_data)
        
        # Simulate current restrictions on Sept 12 data
        simulate_restrictions(sept12_data)
        
        # Provide adjustment recommendations
        recommend_adjustments(sept12_data, sept19_data)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_volume_comparison(sept12_data, sept19_data):
    """Compare volume trends between Sept 12 and Sept 19"""
    print("\n🔊 VOLUME PATTERN COMPARISON")
    print("-" * 45)
    
    # Get symbols present in both dates
    sept12_symbols = set(sept12_data['symbol'])
    sept19_symbols = set(sept19_data['symbol'])
    common_symbols = sept12_symbols & sept19_symbols
    
    print(f"🔍 Analyzing {len(common_symbols)} common symbols")
    
    if len(common_symbols) == 0:
        print("❌ No common symbols found between dates")
        return
    
    volume_analysis = []
    
    for symbol in sorted(common_symbols):
        sept12_vol = sept12_data[sept12_data['symbol'] == symbol]['volume_trend'].mean()
        sept19_vol = sept19_data[sept19_data['symbol'] == symbol]['volume_trend'].mean()
        
        sept12_conf = sept12_data[sept12_data['symbol'] == symbol]['action_confidence'].mean()
        sept19_conf = sept19_data[sept19_data['symbol'] == symbol]['action_confidence'].mean()
        
        volume_analysis.append({
            'symbol': symbol,
            'sept12_volume': sept12_vol,
            'sept19_volume': sept19_vol,
            'volume_change': sept19_vol - sept12_vol,
            'sept12_confidence': sept12_conf,
            'sept19_confidence': sept19_conf,
            'confidence_change': sept19_conf - sept12_conf
        })
    
    # Display volume comparison
    print(f"\n📈 VOLUME TRENDS:")
    print(f"{'Symbol':<8} {'Sept12':<7} {'Sept19':<7} {'Δ Vol':<7} {'Sept12 Conf':<12} {'Sept19 Conf':<12} {'Δ Conf':<8}")
    print("-" * 75)
    
    for data in volume_analysis:
        print(f"{data['symbol']:<8} "
              f"{data['sept12_volume']:.3f}   "
              f"{data['sept19_volume']:.3f}   "
              f"{data['volume_change']:+.3f}   "
              f"{data['sept12_confidence']:.3f}        "
              f"{data['sept19_confidence']:.3f}        "
              f"{data['confidence_change']:+.3f}")
    
    # Volume veto analysis
    print(f"\n🚫 VOLUME VETO IMPACT (Current threshold: BUY < 0.3, SELL > 0.7):")
    
    sept12_low_vol = sum(1 for d in volume_analysis if d['sept12_volume'] < 0.3)
    sept19_low_vol = sum(1 for d in volume_analysis if d['sept19_volume'] < 0.3)
    sept12_high_vol = sum(1 for d in volume_analysis if d['sept12_volume'] > 0.7)
    sept19_high_vol = sum(1 for d in volume_analysis if d['sept19_volume'] > 0.7)
    
    print(f"  Sept 12 - BUY would be blocked: {sept12_low_vol}/{len(volume_analysis)} stocks")
    print(f"  Sept 19 - BUY would be blocked: {sept19_low_vol}/{len(volume_analysis)} stocks")
    print(f"  Sept 12 - SELL would be blocked: {sept12_high_vol}/{len(volume_analysis)} stocks")
    print(f"  Sept 19 - SELL would be blocked: {sept19_high_vol}/{len(volume_analysis)} stocks")
    
    return volume_analysis

def simulate_restrictions(sept12_data):
    """Simulate applying current restrictions to Sept 12 data"""
    print("\n🎯 RESTRICTION SIMULATION ON SEPT 12")
    print("-" * 42)
    
    original_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    restricted_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    blocked_trades = []
    
    for _, row in sept12_data.iterrows():
        symbol = row['symbol']
        action = row['predicted_action']
        confidence = row['action_confidence']
        volume = row['volume_trend']
        technical = row['technical_score']
        news = row['news_sentiment']
        
        original_counts[action] += 1
        
        # Apply current restrictions
        final_action = action
        block_reasons = []
        
        # 1. Volume veto
        if action == 'BUY' and volume < 0.3:
            final_action = 'HOLD'
            block_reasons.append(f"Vol veto ({volume:.3f} < 0.3)")
        elif action == 'SELL' and volume > 0.7:
            final_action = 'HOLD'
            block_reasons.append(f"Vol veto ({volume:.3f} > 0.7)")
        
        # 2. Confidence thresholds
        if final_action == 'BUY' and confidence < 0.65:
            final_action = 'HOLD'
            block_reasons.append(f"Conf threshold ({confidence:.3f} < 0.65)")
        elif final_action == 'SELL' and confidence < 0.60:
            final_action = 'HOLD'
            block_reasons.append(f"Conf threshold ({confidence:.3f} < 0.60)")
        
        # 3. Quality checks (for BUY only)
        if final_action == 'BUY' and (technical < 0.6 or news < 0.5):
            final_action = 'HOLD'
            block_reasons.append(f"Quality fail (tech:{technical:.3f}, news:{news:.3f})")
        
        restricted_counts[final_action] += 1
        
        if block_reasons:
            blocked_trades.append({
                'symbol': symbol,
                'original': action,
                'blocked_to': final_action,
                'confidence': confidence,
                'volume': volume,
                'reasons': '; '.join(block_reasons)
            })
    
    # Show results
    print(f"📊 SIMULATION RESULTS:")
    print(f"{'Action':<6} {'Original':<8} {'After Restrictions':<18} {'Change':<8}")
    print("-" * 45)
    
    for action in ['BUY', 'SELL', 'HOLD']:
        change = restricted_counts[action] - original_counts[action]
        print(f"{action:<6} {original_counts[action]:<8} {restricted_counts[action]:<18} {change:+d}")
    
    print(f"\n🚫 BLOCKED TRADES ({len(blocked_trades)} total):")
    for trade in blocked_trades[:8]:  # Show first 8
        print(f"  {trade['symbol']}: {trade['original']} → {trade['blocked_to']} "
              f"(conf:{trade['confidence']:.3f}, vol:{trade['volume']:.3f}) - {trade['reasons']}")
    
    if len(blocked_trades) > 8:
        print(f"  ... and {len(blocked_trades) - 8} more blocked trades")
    
    return blocked_trades

def recommend_adjustments(sept12_data, sept19_data):
    """Provide specific adjustment recommendations"""
    print("\n💡 RECOMMENDED ADJUSTMENTS FOR BULLISH MARKETS")
    print("-" * 55)
    
    # Calculate metrics
    sept12_avg_conf = sept12_data['action_confidence'].mean()
    sept19_avg_conf = sept19_data['action_confidence'].mean()
    
    buy_signals_12 = len(sept12_data[sept12_data['predicted_action'] == 'BUY'])
    buy_signals_19 = len(sept19_data[sept19_data['predicted_action'] == 'BUY'])
    
    low_volume_12 = len(sept12_data[sept12_data['volume_trend'] < 0.3])
    low_volume_19 = len(sept19_data[sept19_data['volume_trend'] < 0.3])
    
    print(f"📈 MARKET CONTEXT:")
    print(f"  Sept 12 avg confidence: {sept12_avg_conf:.3f}")
    print(f"  Sept 19 avg confidence: {sept19_avg_conf:.3f}")
    print(f"  Confidence change: {sept19_avg_conf - sept12_avg_conf:+.3f}")
    print(f"  Sept 12 BUY signals: {buy_signals_12}")
    print(f"  Sept 19 BUY signals: {buy_signals_19}")
    
    print(f"\n🎯 SPECIFIC RECOMMENDATIONS:")
    
    if low_volume_12 > 2:
        print(f"  1. VOLUME VETO ADJUSTMENT:")
        print(f"     Current: BUY blocked if volume < 0.3")
        print(f"     Suggested: BUY blocked if volume < 0.2")
        print(f"     Impact: Would allow {low_volume_12} more trades on Sept 12")
    
    high_conf_blocked = len(sept12_data[
        (sept12_data['predicted_action'] == 'BUY') & 
        (sept12_data['action_confidence'] >= 0.55) & 
        (sept12_data['action_confidence'] < 0.65)
    ])
    
    if high_conf_blocked > 0:
        print(f"  2. CONFIDENCE THRESHOLD ADJUSTMENT:")
        print(f"     Current: BUY requires ≥ 65% confidence")
        print(f"     Suggested: BUY requires ≥ 55% confidence")
        print(f"     Impact: Would allow {high_conf_blocked} more trades on Sept 12")
    
    print(f"\n⚙️  IMPLEMENTATION PRIORITY:")
    print(f"  HIGH: Volume veto 0.3 → 0.2 (immediate opportunity capture)")
    print(f"  HIGH: BUY confidence 65% → 55% (volume-weighted system adjustment)")
    print(f"  MED:  Quality checks from AND to OR logic")
    print(f"  LOW:  Dynamic thresholds based on market regime")
    
    print(f"\n🔧 BULLISH MARKET MODE PARAMETERS:")
    print(f"  volume_veto_buy_threshold: 0.2   (from 0.3)")
    print(f"  volume_veto_sell_threshold: 0.8  (from 0.7)")
    print(f"  buy_confidence_threshold: 0.55   (from 0.65)")
    print(f"  sell_confidence_threshold: 0.55  (from 0.60)")
    print(f"  quality_check_logic: 'OR'        (from 'AND')")
    print(f"  market_penalty_rate: 0.10        (from 0.15)")

if __name__ == "__main__":
    main()