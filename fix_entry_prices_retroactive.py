#!/usr/bin/env python3
"""
Retroactive Entry Price Fixer
Fixes all predictions in the database that have entry_price = 0.0 by looking up historical prices
"""

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_entry_prices.log")
    ]
)
logger = logging.getLogger(__name__)

def get_historical_price(symbol, target_date):
    """
    Get historical price for a symbol on a specific date
    Try multiple methods to get the most accurate price
    """
    try:
        # Parse the target date
        if isinstance(target_date, str):
            # Handle timezone-aware datetime strings
            if '+' in target_date:
                target_date = target_date.split('+')[0]  # Remove timezone
            elif 'T' in target_date:
                target_date = target_date.replace('T', ' ')
            
            target_dt = datetime.fromisoformat(target_date.replace('Z', ''))
        else:
            target_dt = target_date
        
        logger.info(f"🔍 Looking up price for {symbol} on {target_dt.date()}")
        
        ticker = yf.Ticker(symbol)
        
        # Method 1: Try to get historical data around the target date
        start_date = target_dt.date() - timedelta(days=3)  # 3 days before
        end_date = target_dt.date() + timedelta(days=3)    # 3 days after
        
        hist = ticker.history(start=start_date, end=end_date, interval="1d")
        
        if not hist.empty:
            # Find the closest date to our target
            target_date_only = target_dt.date()
            hist_dates = [d.date() for d in hist.index]
            
            # Try exact date first
            for i, hist_date in enumerate(hist_dates):
                if hist_date == target_date_only:
                    price = float(hist['Close'].iloc[i])
                    logger.info(f"✅ {symbol}: Found exact date price = ${price:.2f}")
                    return price
            
            # If no exact date, find the closest date
            closest_idx = 0
            min_diff = abs((hist_dates[0] - target_date_only).days)
            
            for i, hist_date in enumerate(hist_dates):
                diff = abs((hist_date - target_date_only).days)
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = i
            
            price = float(hist['Close'].iloc[closest_idx])
            closest_date = hist_dates[closest_idx]
            logger.info(f"✅ {symbol}: Found closest date ({closest_date}, {min_diff} days diff) price = ${price:.2f}")
            return price
        
        # Method 2: Try current price as fallback
        logger.warning(f"⚠️ {symbol}: No historical data, trying current price")
        info = ticker.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        if current_price > 0:
            logger.info(f"💰 {symbol}: Using current price as fallback = ${current_price:.2f}")
            return float(current_price)
        
        # Method 3: Try recent history
        logger.warning(f"⚠️ {symbol}: Trying recent 1-week history")
        recent_hist = ticker.history(period="1wk")
        if not recent_hist.empty:
            price = float(recent_hist['Close'].iloc[-1])
            logger.info(f"💰 {symbol}: Using recent price = ${price:.2f}")
            return price
        
        logger.error(f"❌ {symbol}: All price lookup methods failed")
        return 0.0
        
    except Exception as e:
        logger.error(f"❌ {symbol}: Price lookup error: {e}")
        return 0.0

def fix_entry_prices(db_path):
    """Fix all entry prices that are 0.0 in the database"""
    
    logger.info("🔧 Starting retroactive entry price fix...")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find all predictions with entry_price = 0.0
        cursor.execute("""
            SELECT prediction_id, symbol, prediction_timestamp, entry_price 
            FROM predictions 
            WHERE entry_price = 0.0 OR entry_price IS NULL
            ORDER BY prediction_timestamp DESC
        """)
        
        zero_price_predictions = cursor.fetchall()
        
        if not zero_price_predictions:
            logger.info("✅ No predictions found with zero entry prices")
            return
        
        logger.info(f"🔍 Found {len(zero_price_predictions)} predictions with zero entry prices")
        
        fixed_count = 0
        failed_count = 0
        
        for prediction_id, symbol, timestamp, current_price in zero_price_predictions:
            logger.info(f"\n--- Fixing {symbol} ({prediction_id}) ---")
            
            # Get historical price for this prediction
            historical_price = get_historical_price(symbol, timestamp)
            
            if historical_price > 0:
                # Update the database
                cursor.execute("""
                    UPDATE predictions 
                    SET entry_price = ?
                    WHERE prediction_id = ?
                """, (historical_price, prediction_id))
                
                fixed_count += 1
                logger.info(f"✅ Fixed {symbol}: ${current_price} -> ${historical_price:.2f}")
            else:
                failed_count += 1
                logger.error(f"❌ Failed to get price for {symbol}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"\n🎉 RETROACTIVE FIX COMPLETE!")
        logger.info(f"   ✅ Fixed: {fixed_count} predictions")
        logger.info(f"   ❌ Failed: {failed_count} predictions")
        
        if fixed_count > 0:
            logger.info(f"   📊 Success rate: {fixed_count/(fixed_count+failed_count)*100:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False
    
    return True

def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default database path
        db_path = "data/trading_predictions.db"
    
    logger.info(f"🎯 Target database: {db_path}")
    
    # Check if database exists
    import os
    if not os.path.exists(db_path):
        logger.error(f"❌ Database not found: {db_path}")
        print(f"Usage: {sys.argv[0]} [database_path]")
        print(f"Default path: data/trading_predictions.db")
        return
    
    # Show preview of what will be fixed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE entry_price = 0.0 OR entry_price IS NULL")
    count = cursor.fetchone()[0]
    
    if count == 0:
        logger.info("✅ No predictions found with zero entry prices - nothing to fix!")
        return
    
    cursor.execute("""
        SELECT symbol, COUNT(*) as count
        FROM predictions 
        WHERE entry_price = 0.0 OR entry_price IS NULL
        GROUP BY symbol
        ORDER BY count DESC
    """)
    
    symbol_counts = cursor.fetchall()
    conn.close()
    
    print(f"\n📋 PREVIEW: Will fix {count} predictions with zero entry prices:")
    for symbol, symbol_count in symbol_counts:
        print(f"   {symbol}: {symbol_count} predictions")
    
    response = input(f"\n🤔 Continue with fixing {count} predictions? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        success = fix_entry_prices(db_path)
        if success:
            print("\n🎉 Entry price fix completed successfully!")
        else:
            print("\n❌ Entry price fix failed!")
    else:
        print("❌ Operation cancelled by user")

if __name__ == "__main__":
    main()
