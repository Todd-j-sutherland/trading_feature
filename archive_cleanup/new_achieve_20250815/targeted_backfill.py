#!/usr/bin/env python3
"""
Targeted backfill for specific features that are eligible for outcome generation.
Focuses on features 324-330 which are old enough (>4 hours) to have outcomes.
"""

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

class TargetedBackfill:
    def __init__(self):
        self.db_path = 'data/trading_unified.db'
        
    def get_eligible_features(self):
        """Get features that are old enough (>4 hours) but missing outcomes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get features 324-330 that don't have outcomes
        cursor.execute('''
        SELECT ef.id, ef.symbol, ef.timestamp 
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.id BETWEEN 324 AND 330
        AND eo.feature_id IS NULL
        ORDER BY ef.id
        ''')
        
        features = cursor.fetchall()
        conn.close()
        
        # Filter to only features old enough
        cutoff_time = datetime.now() - timedelta(hours=4)
        eligible = []
        
        for feature_id, symbol, timestamp in features:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if 'T' in timestamp else datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            hours_ago = (datetime.now() - dt.replace(tzinfo=None)).total_seconds() / 3600
            
            if hours_ago >= 4:
                eligible.append((feature_id, symbol, dt.replace(tzinfo=None)))
        
        return eligible
    
    def get_price_data(self, symbol, start_time):
        """Get price data for outcome calculation."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get data from start_time to now with 1-hour intervals
            end_time = start_time + timedelta(hours=6)  # Get extra data for safety
            
            print(f"  Fetching data from {start_time} to {end_time}")
            
            # Get hourly data
            data = ticker.history(start=start_time.strftime('%Y-%m-%d'), 
                                end=end_time.strftime('%Y-%m-%d'), 
                                interval='1h')
            
            if len(data) == 0:
                print(f"  No hourly data, trying daily data")
                # Fallback to daily data
                data = ticker.history(start=(start_time - timedelta(days=1)).strftime('%Y-%m-%d'), 
                                    end=(end_time + timedelta(days=1)).strftime('%Y-%m-%d'))
            
            return data
            
        except Exception as e:
            print(f"  Error fetching data: {e}")
            return None
    
    def calculate_outcomes(self, price_data, start_time):
        """Calculate price direction and optimal action based on price data."""
        if price_data is None or len(price_data) == 0:
            return None, None, None, None
        
        # Convert timezone-aware index to timezone-naive for comparison
        price_data_naive = price_data.copy()
        if hasattr(price_data.index, 'tz') and price_data.index.tz is not None:
            price_data_naive.index = price_data.index.tz_convert(None)
        
        # Find the closest price to start_time
        start_price = None
        for idx, row in price_data_naive.iterrows():
            if idx >= start_time:
                start_price = row['Close']
                break
        
        if start_price is None:
            # Use the last available price before start_time
            before_start = price_data_naive[price_data_naive.index <= start_time]
            if len(before_start) > 0:
                start_price = before_start['Close'].iloc[-1]
            else:
                return None, None, None, None
        
        # Find price 4 hours later
        target_time = start_time + timedelta(hours=4)
        end_price = None
        
        # Look for price at target time or after
        for idx, row in price_data_naive.iterrows():
            if idx >= target_time:
                end_price = row['Close']
                break
        
        if end_price is None:
            # If no exact match, use the next trading day's opening or closest available
            after_target = price_data_naive[price_data_naive.index > start_time]
            if len(after_target) > 0:
                end_price = after_target['Close'].iloc[-1]  # Use last available price
            else:
                end_price = start_price  # Fallback to same price (no change)
        
        print(f"    Start time: {start_time}, Target time: {target_time}")
        print(f"    Start price: ${start_price:.2f}, End price: ${end_price:.2f}")
        print(f"    Available data points: {len(price_data_naive)}")
        
        # Calculate direction (1 for up, 0 for down)
        price_direction = 1 if end_price > start_price else 0
        
        # Simple optimal action based on direction
        optimal_action = 'BUY' if price_direction == 1 else 'SELL'
        
        return price_direction, optimal_action, start_price, end_price
    
    def save_outcome(self, feature_id, symbol, price_direction, optimal_action, entry_price, exit_price):
        """Save outcome to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate return percentage
            return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            price_magnitude = abs(return_pct)
            
            cursor.execute('''
            INSERT INTO enhanced_outcomes (
                feature_id, symbol, prediction_timestamp, 
                price_direction_4h, price_magnitude_4h, optimal_action, 
                entry_price, exit_price_4h, return_pct, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature_id, symbol, datetime.now().isoformat(),
                price_direction, price_magnitude, optimal_action,
                entry_price, exit_price, return_pct, datetime.now().isoformat()
            ))
            
            conn.commit()
            print(f"    ✓ Saved outcome: direction={price_direction}, action={optimal_action}, return={return_pct:.2%}")
            return True
            
        except Exception as e:
            print(f"    ✗ Error saving outcome: {e}")
            return False
        finally:
            conn.close()
    
    def run(self):
        """Run the targeted backfill."""
        print("🎯 TARGETED BACKFILL FOR ELIGIBLE FEATURES")
        print("=" * 50)
        
        eligible_features = self.get_eligible_features()
        print(f"Found {len(eligible_features)} eligible features")
        
        if not eligible_features:
            print("No eligible features found!")
            return
        
        success_count = 0
        
        for feature_id, symbol, timestamp in eligible_features:
            print(f"\n📋 Processing {symbol} (ID: {feature_id}) from {timestamp}")
            
            # Get price data
            price_data = self.get_price_data(symbol, timestamp)
            
            if price_data is not None and len(price_data) > 0:
                # Calculate outcomes
                price_direction, optimal_action, start_price, end_price = self.calculate_outcomes(price_data, timestamp)
                
                if price_direction is not None:
                    # Save to database
                    if self.save_outcome(feature_id, symbol, price_direction, optimal_action, start_price, end_price):
                        success_count += 1
                else:
                    print("    ⚠️ Could not calculate outcomes from price data")
            else:
                print("    ❌ No price data available")
        
        print(f"\n🎯 BACKFILL COMPLETE")
        print(f"   Outcomes recorded: {success_count}/{len(eligible_features)}")
        print(f"   Success rate: {(success_count/len(eligible_features)*100):.1f}%")

if __name__ == "__main__":
    backfill = TargetedBackfill()
    backfill.run()
