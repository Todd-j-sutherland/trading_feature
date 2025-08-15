#!/usr/bin/env python3
"""
Fix Missing Exit Prices using Yahoo Finance Historical Data

This script addresses the issue where 45.8% of trading outcomes are missing exit prices.
Instead of simulation, we use real Yahoo Finance historical data to backfill accurate exit prices.

Key benefits:
- Real market data vs simulated prices
- Accurate return calculations for ML training
- Proper performance metrics for backtesting
"""

import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YahooExitPriceFixer:
    """Fix missing exit prices using Yahoo Finance historical data"""
    
    def __init__(self, db_path: str = 'data/trading_unified.db'):
        self.db_path = db_path
        self.yahoo_cache = {}  # Cache historical data to avoid repeated API calls
        
    def get_historical_price(self, symbol: str, target_date: datetime) -> Optional[float]:
        """
        Get historical price for a symbol on a specific date from Yahoo Finance
        
        Args:
            symbol: ASX symbol (e.g., 'CBA.AX')
            target_date: Date to get price for
            
        Returns:
            Price or None if not found
        """
        try:
            # Convert target date to string for caching
            date_str = target_date.strftime('%Y-%m-%d')
            cache_key = f"{symbol}_{date_str}"
            
            if cache_key in self.yahoo_cache:
                return self.yahoo_cache[cache_key]
            
            # Get data from Yahoo Finance
            # We need a range to ensure we get the exact date or closest trading day
            start_date = target_date - timedelta(days=7)  # Look back 7 days
            end_date = target_date + timedelta(days=3)    # Look forward 3 days
            
            logger.info(f"Fetching {symbol} data for {date_str}")
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                logger.warning(f"No data found for {symbol} around {date_str}")
                return None
            
            # Try to get exact date first
            target_date_only = target_date.date()
            
            # Convert index to date for comparison
            hist.index = hist.index.date
            
            if target_date_only in hist.index:
                price = float(hist.loc[target_date_only]['Close'])
                logger.info(f"Found exact date price for {symbol} on {date_str}: ${price:.2f}")
            else:
                # Get closest available date
                available_dates = list(hist.index)
                closest_date = min(available_dates, key=lambda x: abs((x - target_date_only).days))
                price = float(hist.loc[closest_date]['Close'])
                logger.info(f"Using closest date {closest_date} for {symbol}: ${price:.2f} (target: {date_str})")
            
            # Cache the result
            self.yahoo_cache[cache_key] = price
            
            # Small delay to respect Yahoo Finance rate limits
            time.sleep(0.1)
            
            return price
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol} on {target_date}: {e}")
            return None
    
    def calculate_target_dates(self, prediction_timestamp: str) -> Dict[str, datetime]:
        """
        Calculate target dates for exit prices based on prediction timestamp
        
        Args:
            prediction_timestamp: ISO format timestamp string
            
        Returns:
            Dictionary with '1h', '4h', '1d' keys and corresponding datetime values
        """
        pred_dt = datetime.fromisoformat(prediction_timestamp.replace('Z', '+00:00').replace('+00:00', ''))
        
        return {
            '1h': pred_dt + timedelta(hours=1),
            '4h': pred_dt + timedelta(hours=4),
            '1d': pred_dt + timedelta(days=1)
        }
    
    def get_missing_exit_prices(self) -> List[Tuple]:
        """Get all outcomes with missing exit prices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, prediction_timestamp, entry_price, 
                   exit_price_1h, exit_price_4h, exit_price_1d
            FROM enhanced_outcomes 
            WHERE exit_price_1h IS NULL OR exit_price_4h IS NULL OR exit_price_1d IS NULL
            ORDER BY prediction_timestamp DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(results)} outcomes with missing exit prices")
        return results
    
    def fix_exit_price(self, outcome_id: int, symbol: str, prediction_timestamp: str, 
                      entry_price: float) -> Dict[str, Optional[float]]:
        """
        Fix exit prices for a single outcome using Yahoo Finance data
        
        Returns:
            Dictionary with updated exit prices and return percentages
        """
        target_dates = self.calculate_target_dates(prediction_timestamp)
        
        results = {
            'exit_price_1h': None,
            'exit_price_4h': None, 
            'exit_price_1d': None,
            'return_pct': None
        }
        
        # Get historical prices for each time horizon
        for horizon, target_date in target_dates.items():
            price = self.get_historical_price(symbol, target_date)
            if price:
                results[f'exit_price_{horizon}'] = price
        
        # Calculate return percentage using 1-day exit price if available
        if results['exit_price_1d'] and entry_price:
            return_pct = ((results['exit_price_1d'] - entry_price) / entry_price) * 100
            results['return_pct'] = return_pct
        
        return results
    
    def update_database(self, outcome_id: int, updates: Dict[str, Optional[float]]):
        """Update database with new exit prices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query dynamically for non-None values
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if value is not None:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if set_clauses:
            query = f"UPDATE enhanced_outcomes SET {', '.join(set_clauses)} WHERE id = ?"
            values.append(outcome_id)
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"Updated outcome {outcome_id} with {len(set_clauses)} new values")
        
        conn.close()
    
    def run_fix(self, limit: Optional[int] = None, dry_run: bool = False):
        """
        Run the exit price fixing process
        
        Args:
            limit: Maximum number of outcomes to process (for testing)
            dry_run: If True, don't update database, just show what would be done
        """
        logger.info("🔧 Starting Yahoo Finance Exit Price Fix")
        logger.info("=" * 50)
        
        missing_outcomes = self.get_missing_exit_prices()
        
        if limit:
            missing_outcomes = missing_outcomes[:limit]
            logger.info(f"Processing limited set: {len(missing_outcomes)} outcomes")
        
        successful_fixes = 0
        failed_fixes = 0
        
        for i, (outcome_id, symbol, pred_timestamp, entry_price, exit_1h, exit_4h, exit_1d) in enumerate(missing_outcomes):
            logger.info(f"\nProcessing {i+1}/{len(missing_outcomes)}: Outcome {outcome_id} ({symbol})")
            
            try:
                # Only process if we actually have missing data
                needs_update = exit_1h is None or exit_4h is None or exit_1d is None
                
                if not needs_update:
                    logger.info(f"Outcome {outcome_id} already has all exit prices")
                    continue
                
                updates = self.fix_exit_price(outcome_id, symbol, pred_timestamp, entry_price)
                
                if any(v is not None for v in updates.values()):
                    if not dry_run:
                        self.update_database(outcome_id, updates)
                    
                    successful_fixes += 1
                    
                    # Log what was updated
                    updated_items = [f"{k}: {v:.2f}" for k, v in updates.items() if v is not None]
                    logger.info(f"✅ Fixed: {', '.join(updated_items)}")
                else:
                    failed_fixes += 1
                    logger.warning(f"❌ Could not get prices for {symbol} at {pred_timestamp}")
                
            except Exception as e:
                failed_fixes += 1
                logger.error(f"❌ Error processing outcome {outcome_id}: {e}")
        
        # Summary
        logger.info(f"\n📊 SUMMARY")
        logger.info(f"=" * 30)
        logger.info(f"Successful fixes: {successful_fixes}")
        logger.info(f"Failed fixes: {failed_fixes}")
        logger.info(f"Total processed: {len(missing_outcomes)}")
        logger.info(f"Success rate: {successful_fixes/(successful_fixes+failed_fixes)*100:.1f}%")
        
        if dry_run:
            logger.info("🏃 DRY RUN - No database changes made")

def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix missing exit prices using Yahoo Finance data')
    parser.add_argument('--limit', type=int, help='Limit number of outcomes to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without updating database')
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    
    args = parser.parse_args()
    
    if args.install_deps:
        import subprocess
        print("📦 Installing required dependencies...")
        subprocess.run(['pip', 'install', 'yfinance', 'pandas'], check=True)
        print("✅ Dependencies installed successfully")
        return
    
    try:
        fixer = YahooExitPriceFixer()
        fixer.run_fix(limit=args.limit, dry_run=args.dry_run)
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Run with --install-deps to install required packages")
        print("Or manually install: pip install yfinance pandas")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()
