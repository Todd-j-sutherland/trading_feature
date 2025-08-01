#!/usr/bin/env python3
"""
Backfill outcomes for existing enhanced features that are >4 hours old
"""
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import time

class OutcomeBackfiller:
    def __init__(self):
        self.db_path = 'data/ml_models/enhanced_training_data.db'
    
    def get_price_data(self, symbol, start_time, end_time):
        """Get price data for outcome calculation"""
        try:
            # ASX symbols already have .AX suffix - use as is
            ticker = yf.Ticker(symbol)
            
            # Get hourly data for more precise outcome calculation
            hist = ticker.history(
                start=start_time - timedelta(hours=1),  # Get a bit before for entry price
                end=end_time + timedelta(hours=1),      # Get a bit after for exit price
                interval='1h'
            )
            
            if hist.empty:
                print(f"⚠️  No price data found for {symbol}")
                return None, None
            
            # Find closest entry and exit prices
            entry_price = hist['Close'].iloc[0] if len(hist) > 0 else None
            exit_price = hist['Close'].iloc[-1] if len(hist) > 1 else None
            
            return entry_price, exit_price
            
        except Exception as e:
            print(f"❌ Error fetching price data for {symbol}: {e}")
            return None, None

    def backfill_outcomes(self):
        """Backfill outcomes for existing enhanced features"""
        print("🔄 BACKFILLING OUTCOMES FOR EXISTING PREDICTIONS")
        print("=" * 60)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get features older than 4 hours that don't have outcomes
        cutoff_time = datetime.now() - timedelta(hours=4)
        
        cursor.execute('''
            SELECT ef.id, ef.symbol, ef.timestamp, ef.sentiment_score, ef.confidence, ef.current_price
            FROM enhanced_features ef
            LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
            WHERE datetime(ef.timestamp) < ? 
            AND eo.feature_id IS NULL
            ORDER BY ef.timestamp DESC
        ''', (cutoff_time.isoformat(),))
        
        features_to_backfill = cursor.fetchall()
        
        if not features_to_backfill:
            print("✅ No features need outcome backfilling")
            conn.close()
            return
        
        print(f"📊 Found {len(features_to_backfill)} features needing outcome backfilling")
        
        outcomes_recorded = 0
        
        for feature_id, symbol, timestamp, sentiment, confidence, entry_price in features_to_backfill:
            try:
                pred_time = datetime.fromisoformat(timestamp)
                outcome_time = pred_time + timedelta(hours=4)
                
                print(f"📋 Processing {symbol} (ID: {feature_id}) from {timestamp}")
                
                # Get price data
                entry_price_actual, exit_price = self.get_price_data(symbol, pred_time, outcome_time)
                
                if entry_price_actual is None or exit_price is None:
                    print(f"❌ Skipping {symbol} - insufficient price data")
                    continue
                
                # Calculate return percentage
                return_pct = ((exit_price - entry_price_actual) / entry_price_actual) * 100
                
                # Determine optimal action based on actual outcome
                if return_pct > 1.0:
                    optimal_action = "BUY"
                elif return_pct < -1.0:
                    optimal_action = "SELL"
                else:
                    optimal_action = "HOLD"
                
                # Insert outcome record
                cursor.execute('''
                    INSERT INTO enhanced_outcomes (
                        feature_id, symbol, prediction_timestamp, 
                        price_direction_4h, price_magnitude_4h,
                        entry_price, exit_price_4h, exit_timestamp,
                        return_pct, optimal_action, confidence_score,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feature_id, symbol, timestamp,
                    1 if return_pct > 0 else -1,  # price_direction_4h
                    abs(return_pct),               # price_magnitude_4h
                    entry_price_actual, exit_price, outcome_time.isoformat(),
                    return_pct, optimal_action, confidence,
                    datetime.now().isoformat()
                ))
                
                outcomes_recorded += 1
                print(f"✅ {symbol}: {return_pct:+.2f}% return, action: {optimal_action}")
                
                # Rate limiting to avoid overwhelming yfinance
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing {symbol} (ID: {feature_id}): {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n🎯 BACKFILL COMPLETE")
        print(f"   Outcomes recorded: {outcomes_recorded}")
        print(f"   Success rate: {(outcomes_recorded/len(features_to_backfill)*100):.1f}%")

def main():
    backfiller = OutcomeBackfiller()
    backfiller.backfill_outcomes()

if __name__ == "__main__":
    main()
