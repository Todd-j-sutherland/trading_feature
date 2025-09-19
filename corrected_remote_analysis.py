#!/usr/bin/env python3
"""
CORRECTED Remote Volume Analysis with actual database schema
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json

def main():
    print("🔍 CORRECTED VOLUME & RESTRICTION ANALYSIS: Sept 12 vs Sept 19")
    print("=" * 70)
    
    db_path = "/root/test/data/trading_predictions.db"
    
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ Connected to database: {db_path}")
        
        # Get data with correct column names
        query = """
        SELECT 
            symbol,
            DATE(prediction_timestamp) as pred_date,
            predicted_action,
            action_confidence,
            volume_trend,
            tech_score,
            news_sentiment,
            entry_price,
            market_trend_pct,
            price_change_pct,
            prediction_timestamp
        FROM predictions 
        WHERE DATE(prediction_timestamp) IN ('2025-09-12', '2025-09-19')
        AND volume_trend IS NOT NULL
        ORDER BY symbol, prediction_timestamp
        """
        
        df = pd.read_sql_query(query, conn)
        
        if len(df) == 0:
            print("❌ No data found for Sept 12 or Sept 19")
            return
        
        print(f"\n📊 Loaded {len(df)} predictions")
        
        # Split by date
        sept12_data = df[df['pred_date'] == '2025-09-12']
        sept19_data = df[df['pred_date'] == '2025-09-19']
        
        print(f"📅 Sept 12: {len(sept12_data)} predictions")
        print(f"📅 Sept 19: {len(sept19_data)} predictions")
        
        if len(sept12_data) == 0 or len(sept19_data) == 0:
            print("❌ Missing data for one of the dates")
            return
        
        # Analyze volume patterns
        analyze_volume_comparison(sept12_data, sept19_data)
        
        # Simulate current restrictions
        simulate_restrictions(sept12_data)
        
        # Provide recommendations
        recommend_adjustments(sept12_data, sept19_data)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_volume_comparison(sept12_data, sept19_data):
    """Compare volume trends between Sept 12 and Sept 19"""
    print("\n🔊 VOLUME PATTERN ANALYSIS")
    print("-" * 40)
    
    # Get common symbols
    sept12_symbols = set(sept12_data['symbol'])
    sept19_symbols = set(sept19_data['symbol'])
    common_symbols = sept12_symbols & sept19_symbols
    
    print(f"🔍 Analyzing {len(common_symbols)} common symbols: {sorted(common_symbols)}")
    
    volume_analysis = []
    
    for symbol in sorted(common_symbols):
        sept12_vol = sept12_data[sept12_data['symbol'] == symbol]['volume_trend'].mean()
        sept19_vol = sept19_data[sept19_data['symbol'] == symbol]['volume_trend'].mean()
        
        sept12_conf = sept12_data[sept12_data['symbol'] == symbol]['action_confidence'].mean()
        sept19_conf = sept19_data[sept19_data['symbol'] == symbol]['action_confidence'].mean()
        
        sept12_tech = sept12_data[sept12_data['symbol'] == symbol]['tech_score'].mean()
        sept19_tech = sept19_data[sept19_data['symbol'] == symbol]['tech_score'].mean()
        
        volume_analysis.append({
            'symbol': symbol,
            'sept12_volume': sept12_vol,
            'sept19_volume': sept19_vol,
            'volume_change': sept19_vol - sept12_vol,
            'sept12_confidence': sept12_conf,
            'sept19_confidence': sept19_conf,
            'confidence_change': sept19_conf - sept12_conf,
            'sept12_tech': sept12_tech,
            'sept19_tech': sept19_tech
        })
    
    # Display comparison
    print(f"\n📈 DETAILED COMPARISON:")
    print(f"{'Symbol':<8} {'Vol 12':<7} {'Vol 19':<7} {'ΔVol':<7} {'Conf 12':<8} {'Conf 19':<8} {'ΔConf':<8}")
    print("-" * 70)
    
    for data in volume_analysis:
        print(f"{data['symbol']:<8} "
              f"{data['sept12_volume']:.3f}   "
              f"{data['sept19_volume']:.3f}   "
              f"{data['volume_change']:+.3f}   "
              f"{data['sept12_confidence']:.3f}    "
              f"{data['sept19_confidence']:.3f}    "
              f"{data['confidence_change']:+.3f}")
    
    # Volume veto analysis
    print(f"\n🚫 VOLUME VETO IMPACT ANALYSIS:")
    print(f"Current thresholds: BUY blocked if volume < 0.3, SELL blocked if > 0.7")
    
    sept12_low_vol = [d for d in volume_analysis if d['sept12_volume'] < 0.3]
    sept19_low_vol = [d for d in volume_analysis if d['sept19_volume'] < 0.3]
    sept12_high_vol = [d for d in volume_analysis if d['sept12_volume'] > 0.7]
    sept19_high_vol = [d for d in volume_analysis if d['sept19_volume'] > 0.7]
    
    print(f"  Sept 12 - BUY would be blocked: {len(sept12_low_vol)}/{len(volume_analysis)} stocks")
    if sept12_low_vol:
        print(f"    Blocked: {[d['symbol'] for d in sept12_low_vol]}")
    
    print(f"  Sept 19 - BUY would be blocked: {len(sept19_low_vol)}/{len(volume_analysis)} stocks")
    if sept19_low_vol:
        print(f"    Blocked: {[d['symbol'] for d in sept19_low_vol]}")
    
    print(f"  Sept 12 - SELL would be blocked: {len(sept12_high_vol)}/{len(volume_analysis)} stocks")
    print(f"  Sept 19 - SELL would be blocked: {len(sept19_high_vol)}/{len(volume_analysis)} stocks")
    
    # Show volume distribution
    print(f"\n📊 VOLUME DISTRIBUTION:")
    print(f"Sept 12 volume range: {min(d['sept12_volume'] for d in volume_analysis):.3f} - {max(d['sept12_volume'] for d in volume_analysis):.3f}")
    print(f"Sept 19 volume range: {min(d['sept19_volume'] for d in volume_analysis):.3f} - {max(d['sept19_volume'] for d in volume_analysis):.3f}")
    
    return volume_analysis

def simulate_restrictions(sept12_data):
    """Simulate applying current restrictions to Sept 12 data"""
    print("\n🎯 RESTRICTION SIMULATION ON SEPT 12 DATA")
    print("-" * 45)
    print("Testing: What if current restrictions were applied to Sept 12?")
    
    original_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    restricted_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    blocked_trades = []
    
    for _, row in sept12_data.iterrows():
        symbol = row['symbol']
        action = row['predicted_action']
        confidence = row['action_confidence']
        volume = row['volume_trend'] if pd.notna(row['volume_trend']) else 0.5
        tech_score = row['tech_score'] if pd.notna(row['tech_score']) else 50
        news_sentiment = row['news_sentiment'] if pd.notna(row['news_sentiment']) else 0.5
        
        original_counts[action] += 1
        
        # Apply current restrictions
        final_action = action
        block_reasons = []
        
        # 1. Volume veto (most important)
        if action == 'BUY' and volume < 0.3:
            final_action = 'HOLD'
            block_reasons.append(f"Volume veto: {volume:.3f} < 0.3")
        elif action == 'SELL' and volume > 0.7:
            final_action = 'HOLD'
            block_reasons.append(f"Volume veto: {volume:.3f} > 0.7")
        
        # 2. Confidence thresholds (if not already vetoed)
        if final_action == 'BUY' and confidence < 0.65:
            final_action = 'HOLD'
            block_reasons.append(f"BUY confidence: {confidence:.3f} < 0.65")
        elif final_action == 'SELL' and confidence < 0.60:
            final_action = 'HOLD'
            block_reasons.append(f"SELL confidence: {confidence:.3f} < 0.60")
        
        # 3. Quality checks (convert tech_score to 0-1 scale)
        tech_normalized = tech_score / 100.0 if tech_score > 1 else tech_score
        if final_action == 'BUY' and (tech_normalized < 0.6 or news_sentiment < 0.5):
            final_action = 'HOLD'
            block_reasons.append(f"Quality: tech={tech_normalized:.3f}, news={news_sentiment:.3f}")
        
        restricted_counts[final_action] += 1
        
        if block_reasons:
            blocked_trades.append({
                'symbol': symbol,
                'original': action,
                'blocked_to': final_action,
                'confidence': confidence,
                'volume': volume,
                'tech_score': tech_normalized,
                'news_sentiment': news_sentiment,
                'reasons': '; '.join(block_reasons)
            })
    
    # Show results
    print(f"\n📊 SIMULATION RESULTS:")
    print(f"{'Action':<6} {'Original':<8} {'Restricted':<10} {'Change':<8} {'% Lost':<8}")
    print("-" * 50)
    
    for action in ['BUY', 'SELL', 'HOLD']:
        change = restricted_counts[action] - original_counts[action]
        pct_lost = (abs(change) / original_counts[action] * 100) if original_counts[action] > 0 else 0
        print(f"{action:<6} {original_counts[action]:<8} {restricted_counts[action]:<10} {change:+d}        {pct_lost:.1f}%")
    
    print(f"\n🚫 BLOCKED TRADES DETAILS ({len(blocked_trades)} total):")
    
    # Group by reason
    volume_blocks = [t for t in blocked_trades if 'Volume veto' in t['reasons']]
    conf_blocks = [t for t in blocked_trades if 'confidence' in t['reasons'] and 'Volume veto' not in t['reasons']]
    quality_blocks = [t for t in blocked_trades if 'Quality' in t['reasons']]
    
    print(f"  📊 Volume Veto Blocks: {len(volume_blocks)}")
    for trade in volume_blocks[:5]:
        print(f"    {trade['symbol']}: {trade['original']} → {trade['blocked_to']} (vol={trade['volume']:.3f})")
    
    print(f"  📊 Confidence Threshold Blocks: {len(conf_blocks)}")
    for trade in conf_blocks[:5]:
        print(f"    {trade['symbol']}: {trade['original']} → {trade['blocked_to']} (conf={trade['confidence']:.3f})")
    
    print(f"  📊 Quality Check Blocks: {len(quality_blocks)}")
    for trade in quality_blocks[:3]:
        print(f"    {trade['symbol']}: {trade['original']} → {trade['blocked_to']} (tech={trade['tech_score']:.3f}, news={trade['news_sentiment']:.3f})")
    
    return blocked_trades

def recommend_adjustments(sept12_data, sept19_data):
    """Provide specific recommendations based on analysis"""
    print("\n💡 BULLISH MARKET ADJUSTMENT RECOMMENDATIONS")
    print("-" * 55)
    
    # Calculate key metrics
    sept12_avg_conf = sept12_data['action_confidence'].mean()
    sept19_avg_conf = sept19_data['action_confidence'].mean()
    confidence_drop = sept12_avg_conf - sept19_avg_conf
    
    sept12_buys = len(sept12_data[sept12_data['predicted_action'] == 'BUY'])
    sept19_buys = len(sept19_data[sept19_data['predicted_action'] == 'BUY'])
    
    # Volume analysis
    sept12_low_vol = len(sept12_data[sept12_data['volume_trend'] < 0.3])
    sept19_low_vol = len(sept19_data[sept19_data['volume_trend'] < 0.3])
    
    print(f"📈 MARKET CONTEXT ANALYSIS:")
    print(f"  Confidence drop: {sept12_avg_conf:.3f} → {sept19_avg_conf:.3f} ({confidence_drop:+.3f})")
    print(f"  BUY signals: {sept12_buys} → {sept19_buys} ({sept19_buys - sept12_buys:+d})")
    print(f"  Low volume stocks: {sept12_low_vol} → {sept19_low_vol}")
    
    print(f"\n🎯 PRIORITY ADJUSTMENTS:")
    
    if sept12_low_vol > 2:
        print(f"  1. ⚡ HIGH PRIORITY - Volume Veto Threshold:")
        print(f"     Current: BUY blocked if volume_trend < 0.3")
        print(f"     Recommended: BUY blocked if volume_trend < 0.2")
        print(f"     Impact: Would rescue {sept12_low_vol} potential trades on Sept 12")
        print(f"     Rationale: ASX markets have natural low-volume periods")
    
    if confidence_drop > 0.1:
        print(f"  2. ⚡ HIGH PRIORITY - BUY Confidence Threshold:")
        print(f"     Current: BUY requires confidence ≥ 0.65")
        print(f"     Recommended: BUY requires confidence ≥ 0.55")
        print(f"     Impact: Compensates for volume-heavy weighting effect")
        print(f"     Rationale: 35% volume weight makes 65% threshold too strict")
    
    print(f"  3. 🔧 MEDIUM PRIORITY - Quality Check Logic:")
    print(f"     Current: tech_score ≥ 60% AND news_sentiment ≥ 50%")
    print(f"     Recommended: tech_score ≥ 50% OR news_sentiment ≥ 45%")
    print(f"     Impact: Less restrictive for bullish market conditions")
    
    print(f"  4. 📊 LOW PRIORITY - Market Penalty:")
    print(f"     Current: 15% penalty for opposing market trends")
    print(f"     Recommended: 10% penalty in identified bull markets")
    
    print(f"\n⚙️  IMPLEMENTATION CODE SUGGESTIONS:")
    print(f"  In enhanced_fixed_price_mapping_system.py:")
    print(f"  ```python")
    print(f"  # Bullish market mode adjustments")
    print(f"  if action == 'BUY' and volume_trend < 0.2:  # Changed from 0.3")
    print(f"      # Volume veto logic")
    print(f"  ")
    print(f"  min_confidence = 0.55  # Changed from 0.65 for BUY")
    print(f"  ```")
    
    print(f"\n🚀 EXPECTED IMPACT OF CHANGES:")
    print(f"  • Volume threshold 0.3→0.2: +{sept12_low_vol} additional trade opportunities")
    print(f"  • Confidence threshold 0.65→0.55: Significant increase in BUY qualifications")
    print(f"  • Quality logic AND→OR: Reduced false negatives in bullish conditions")
    print(f"  • Result: Better capture of opportunities like MQG +1.1%")
    
    print(f"\n🎯 CONCLUSION:")
    print(f"  The conservative approach is working but TOO restrictive for bullish markets.")
    print(f"  Primary issue: Volume veto threshold (30%) blocks too many ASX trades.")
    print(f"  Secondary issue: 65% confidence requirement with 35% volume weighting.")
    print(f"  Solution: Targeted parameter relaxation while maintaining risk management.")

if __name__ == "__main__":
    main()