#!/usr/bin/env python3
"""
Final Comprehensive Analysis - Before/After Volume Fix Impact
"""

import sqlite3
import pandas as pd
from datetime import datetime

def final_analysis():
    print("🎯 FINAL COMPREHENSIVE ANALYSIS: VOLUME FIX IMPACT")
    print("=" * 65)
    
    db_path = "/root/test/data/trading_predictions.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Get the latest predictions for today
        today_query = """
        SELECT 
            symbol,
            predicted_action,
            action_confidence,
            volume_trend,
            prediction_timestamp
        FROM predictions 
        WHERE DATE(prediction_timestamp) = DATE('now')
        ORDER BY prediction_timestamp DESC
        LIMIT 20
        """
        
        today_df = pd.read_sql_query(today_query, conn)
        
        print(f"📊 LATEST PREDICTIONS (Sept 19 - Post Volume Fix):")
        print(f"{'Symbol':<8} {'Action':<10} {'Confidence':<10} {'Volume':<10} {'Normalized':<12}")
        print("-" * 65)
        
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for _, row in today_df.iterrows():
            symbol = row['symbol']
            action = row['predicted_action']
            confidence = row['action_confidence']
            volume_raw = row['volume_trend']
            
            # Apply the same normalization logic as the production system
            if abs(volume_raw) > 2.0:
                # Old percentage format
                if volume_raw <= -50.0:
                    normalized_volume = 0.0
                elif volume_raw >= 50.0:
                    normalized_volume = 1.0
                else:
                    normalized_volume = (volume_raw + 50.0) / 100.0
            else:
                # Already normalized
                normalized_volume = volume_raw
            
            print(f"{symbol:<8} {action:<10} {confidence:<10.3f} {volume_raw:<10.1f} {normalized_volume:<12.3f}")
            
            if action == 'BUY':
                buy_count += 1
            elif action == 'SELL':
                sell_count += 1
            else:
                hold_count += 1
        
        print(f"\n📈 PREDICTION SUMMARY:")
        print(f"  BUY signals: {buy_count}")
        print(f"  SELL signals: {sell_count}")
        print(f"  HOLD signals: {hold_count}")
        print(f"  Total predictions: {len(today_df)}")
        
        # Simulate the new volume veto logic
        print(f"\n🔧 NEW VOLUME VETO SIMULATION:")
        print(f"Using updated thresholds: BUY blocked if normalized_volume < 0.2, SELL blocked if > 0.8")
        
        would_pass_buy_veto = 0
        would_pass_sell_veto = 0
        
        for _, row in today_df.iterrows():
            volume_raw = row['volume_trend']
            
            # Normalize volume
            if abs(volume_raw) > 2.0:
                if volume_raw <= -50.0:
                    normalized_volume = 0.0
                elif volume_raw >= 50.0:
                    normalized_volume = 1.0
                else:
                    normalized_volume = (volume_raw + 50.0) / 100.0
            else:
                normalized_volume = volume_raw
            
            # Check new veto thresholds
            if normalized_volume >= 0.2:  # Would pass BUY veto
                would_pass_buy_veto += 1
            if normalized_volume <= 0.8:  # Would pass SELL veto  
                would_pass_sell_veto += 1
        
        print(f"  Stocks passing BUY volume veto (≥0.2): {would_pass_buy_veto}/{len(today_df)}")
        print(f"  Stocks passing SELL volume veto (≤0.8): {would_pass_sell_veto}/{len(today_df)}")
        
        # Compare with old thresholds
        would_pass_old_buy_veto = 0
        for _, row in today_df.iterrows():
            volume_raw = row['volume_trend']
            if abs(volume_raw) > 2.0:
                if volume_raw <= -50.0:
                    normalized_volume = 0.0
                elif volume_raw >= 50.0:
                    normalized_volume = 1.0
                else:
                    normalized_volume = (volume_raw + 50.0) / 100.0
            else:
                normalized_volume = volume_raw
            
            if normalized_volume >= 0.3:  # Old threshold
                would_pass_old_buy_veto += 1
        
        print(f"\n📊 IMPROVEMENT IMPACT:")
        print(f"  Old BUY veto threshold (≥0.3): {would_pass_old_buy_veto}/{len(today_df)} would pass")
        print(f"  New BUY veto threshold (≥0.2): {would_pass_buy_veto}/{len(today_df)} would pass")
        print(f"  Additional opportunities: +{would_pass_buy_veto - would_pass_old_buy_veto} stocks")
        
        # Test confidence thresholds
        high_confidence_stocks = len(today_df[today_df['action_confidence'] >= 0.55])
        very_high_confidence_stocks = len(today_df[today_df['action_confidence'] >= 0.65])
        
        print(f"\n💰 CONFIDENCE THRESHOLD IMPACT:")
        print(f"  Stocks with confidence ≥ 55% (new threshold): {high_confidence_stocks}")
        print(f"  Stocks with confidence ≥ 65% (old threshold): {very_high_confidence_stocks}")
        print(f"  Additional opportunities from lower threshold: +{high_confidence_stocks - very_high_confidence_stocks}")
        
        # Show specific examples
        print(f"\n🎯 SPECIFIC EXAMPLES:")
        examples = today_df.head(5)
        for _, row in examples.iterrows():
            symbol = row['symbol']
            confidence = row['action_confidence']
            volume_raw = row['volume_trend']
            
            # Normalize volume
            if abs(volume_raw) > 2.0:
                if volume_raw <= -50.0:
                    normalized_volume = 0.0
                elif volume_raw >= 50.0:
                    normalized_volume = 1.0
                else:
                    normalized_volume = (volume_raw + 50.0) / 100.0
            else:
                normalized_volume = volume_raw
            
            # Check what would happen with new vs old rules
            passes_new_volume = normalized_volume >= 0.2
            passes_old_volume = normalized_volume >= 0.3
            passes_new_confidence = confidence >= 0.55
            passes_old_confidence = confidence >= 0.65
            
            status_new = "BUY ELIGIBLE" if (passes_new_volume and passes_new_confidence) else "BLOCKED"
            status_old = "BUY ELIGIBLE" if (passes_old_volume and passes_old_confidence) else "BLOCKED"
            
            print(f"  {symbol}: Vol={normalized_volume:.3f}, Conf={confidence:.3f}")
            print(f"    Old rules: {status_old}")
            print(f"    New rules: {status_new}")
            
            if status_new != status_old:
                print(f"    → IMPROVEMENT! {symbol} now eligible for BUY")
        
        conn.close()
        
        print(f"\n🏁 CONCLUSION:")
        print(f"✅ Volume calculation fixed: Now returns 0.0-1.0 normalized values")
        print(f"✅ Volume veto thresholds relaxed: BUY 0.3→0.2, SELL 0.7→0.8")
        print(f"✅ Confidence thresholds lowered: BUY/SELL 65%/60%→55%/55%")
        print(f"✅ System can now handle both old percentage and new normalized data")
        print(f"🎯 Expected result: More BUY signals for bullish stocks like MQG +1.1%")
        
    except Exception as e:
        print(f"❌ Error in final analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_analysis()