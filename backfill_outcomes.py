#!/usr/bin/env python3
"""
Backfill Outcomes - Record outcomes for existing enhanced features
"""
import sqlite3
import requests
import time
from datetime import datetime, timedelta
import yfinance as yf

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
            return None, Nonedef backfill_outcomes():
    """Backfill outcomes for existing enhanced features"""
    conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
    cursor = conn.cursor()
    
    # Get features older than 4 hours without outcomes
    cutoff_time = datetime.now() - timedelta(hours=4)
    
    cursor.execute('''
        SELECT ef.id, ef.symbol, ef.timestamp, ef.current_price, ef.rsi, ef.sentiment_score
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE eo.feature_id IS NULL
        AND datetime(ef.timestamp) < ?
        ORDER BY ef.timestamp DESC
    ''', (cutoff_time.isoformat(),))
    
    features = cursor.fetchall()
    
    print(f"🔍 Found {len(features)} features without outcomes to backfill")
    
    success_count = 0
    error_count = 0
    
    for feature_id, symbol, timestamp, entry_price, rsi, sentiment in features:
        try:
            # Parse timestamp
            feature_time = datetime.fromisoformat(timestamp)
            hours_old = (datetime.now() - feature_time).total_seconds() / 3600
            
            print(f"\n📊 Processing {symbol} (ID: {feature_id}) - {hours_old:.1f}h old")
            
            # Get price data
            start_price, end_price = get_price_data(symbol, feature_time, 4)
            
            if start_price is None or end_price is None:
                print(f"❌ Skipping {symbol} - no price data")
                error_count += 1
                continue
            
            # Calculate return
            return_pct = ((end_price - start_price) / start_price) * 100
            
            # Determine optimal action based on RSI
            if rsi < 30:
                optimal_action = 'BUY'
            elif rsi > 70:
                optimal_action = 'SELL'
            else:
                optimal_action = 'HOLD'
            
            # Insert outcome record
            cursor.execute('''
                INSERT INTO enhanced_outcomes (
                    feature_id, symbol, prediction_timestamp, 
                    entry_price, exit_price_4h, return_pct, 
                    optimal_action, confidence_score, exit_timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature_id,
                symbol, 
                timestamp,
                start_price,
                end_price,
                return_pct,
                optimal_action,
                0.8 if abs(return_pct) > 0.5 else 0.6,  # Confidence based on magnitude
                (feature_time + timedelta(hours=4)).isoformat(),
                datetime.now().isoformat()
            ))
            
            success_count += 1
            print(f"✅ {symbol}: {start_price:.2f} → {end_price:.2f} ({return_pct:+.2f}%) - {optimal_action}")
            
            # Rate limiting to avoid overwhelming APIs
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            error_count += 1
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ BACKFILL COMPLETE:")
    print(f"   Successfully processed: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total features processed: {len(features)}")

if __name__ == "__main__":
    print("🔄 ENHANCED FEATURES OUTCOME BACKFILL")
    print("=" * 50)
    backfill_outcomes()
