#!/usr/bin/env python3
"""
Enhanced Paper Trading Service - Backtesting Strategy Implementation
Features:
- One position per symbol maximum
- Continuous profit checking every 1 minute
- Configurable profit target (default $5)
- Real-time Yahoo Finance price data
- Exit when profit target reached or max hold time exceeded
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import pytz

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def is_asx_trading_hours(dt: datetime) -> bool:
    """
    Check if the given datetime is during ASX trading hours
    ASX trades Monday-Friday 10:00 AM - 4:00 PM AEST/AEDT
    """
    # Convert to Australian timezone
    au_tz = pytz.timezone('Australia/Sydney')
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    au_time = dt.astimezone(au_tz)
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if au_time.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if it's during trading hours (10:00 AM - 4:00 PM)
    trading_start = au_time.replace(hour=10, minute=0, second=0, microsecond=0)
    trading_end = au_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return trading_start <= au_time <= trading_end

def calculate_trading_time_minutes(entry_time: datetime, current_time: datetime) -> float:
    """
    Calculate the actual trading time in minutes between entry and current time,
    excluding weekends and after-hours periods
    """
    if entry_time >= current_time:
        return 0.0
    
    trading_minutes = 0.0
    check_time = entry_time
    
    # Step through time in 1-minute increments and count trading minutes
    while check_time < current_time:
        if is_asx_trading_hours(check_time):
            trading_minutes += 1.0
        
        check_time += timedelta(minutes=1)
        
        # Optimization: if we're outside trading hours, jump to next trading period
        if not is_asx_trading_hours(check_time):
            au_tz = pytz.timezone('Australia/Sydney')
            if check_time.tzinfo is None:
                check_time = pytz.utc.localize(check_time)
            
            au_time = check_time.astimezone(au_tz)
            
            # If it's weekend, jump to Monday 10 AM
            if au_time.weekday() >= 5:
                days_until_monday = 7 - au_time.weekday()
                next_trading = au_time.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
            # If it's after hours on weekday, jump to next day 10 AM
            elif au_time.hour >= 16:
                next_trading = (au_time + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            # If it's before hours on weekday, jump to 10 AM same day
            elif au_time.hour < 10:
                next_trading = au_time.replace(hour=10, minute=0, second=0, microsecond=0)
            else:
                # We're in trading hours, continue normal increment
                continue
            
            # Convert back to UTC and update check_time
            check_time = next_trading.astimezone(pytz.utc).replace(tzinfo=None)
    
    return trading_minutes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_paper_trading_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fixed paths for remote server
PREDICTIONS_DB_PATH = '/root/test/predictions.db'
PAPER_TRADING_DB_PATH = '/root/test/paper-trading-app/paper_trading.db'

class EnhancedPaperTradingService:
    """Enhanced paper trading service with backtesting strategy"""
    
    def __init__(self):
        """Initialize the service"""
        self.predictions_db_path = PREDICTIONS_DB_PATH
        self.paper_trading_db_path = PAPER_TRADING_DB_PATH
        self.last_processed_timestamp = None
        self.running = True
        
        # Trading configuration (matches backtesting strategy)
        self.config = {
            'profit_target': 20.0,  # Target profit per trade ($20)
            'max_hold_time_minutes': 1440,  # 24 hours max hold
            'position_size': 10000,  # $10k per position
            'commission_rate': 0.0,  # 0% commission (default - adjustable via dashboard)
            'min_commission': 0.0,  # Minimum commission (default $0)
            'max_commission': 100.0,  # Maximum commission cap
            'check_interval_seconds': 60,  # Check every 1 minute
            'prediction_check_interval_seconds': 300  # Check for new predictions every 5 minutes
        }
        
        # Active positions tracking
        self.active_positions = {}
        
        # Verify databases exist
        if not os.path.exists(self.predictions_db_path):
            raise FileNotFoundError(f"Predictions database not found: {self.predictions_db_path}")
        if not os.path.exists(self.paper_trading_db_path):
            raise FileNotFoundError(f"Paper trading database not found: {self.paper_trading_db_path}")
            
        self._initialize_database()
        self._load_active_positions()
        
        logger.info(f"✅ Enhanced Service initialized")
        logger.info(f"📊 Predictions DB: {self.predictions_db_path}")
        logger.info(f"💰 Paper Trading DB: {self.paper_trading_db_path}")
        logger.info(f"🎯 Strategy: One position per symbol, ${self.config['profit_target']} target")
        
        # Initialize last processed timestamp to 1 hour ago
        self.last_processed_timestamp = (datetime.now() - timedelta(hours=1)).isoformat()
        
    def _initialize_database(self):
        """Initialize enhanced database tables"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            # Enhanced positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE,
                    prediction_id TEXT,
                    entry_time DATETIME,
                    entry_price REAL,
                    shares INTEGER,
                    investment REAL,
                    commission_paid REAL,
                    target_profit REAL,
                    confidence REAL,
                    status TEXT DEFAULT 'OPEN',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Enhanced trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    prediction_id TEXT,
                    action TEXT,
                    entry_time DATETIME,
                    exit_time DATETIME,
                    entry_price REAL,
                    exit_price REAL,
                    shares INTEGER,
                    investment REAL,
                    proceeds REAL,
                    profit REAL,
                    commission_total REAL,
                    hold_time_minutes REAL,
                    exit_reason TEXT,
                    confidence REAL,
                    execution_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Configuration table for dashboard updates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_config (
                    key TEXT PRIMARY KEY,
                    value REAL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default config
            cursor.execute("""
                INSERT OR REPLACE INTO trading_config (key, value) VALUES 
                ('profit_target', ?),
                ('max_hold_time_minutes', ?),
                ('position_size', ?),
                ('check_interval_seconds', ?),
                ('commission_rate', ?),
                ('min_commission', ?),
                ('max_commission', ?)
            """, (
                self.config['profit_target'],
                self.config['max_hold_time_minutes'],
                self.config['position_size'],
                self.config['check_interval_seconds'],
                self.config['commission_rate'],
                self.config['min_commission'],
                self.config['max_commission']
            ))
            
            conn.commit()
            conn.close()
            logger.info("✅ Database tables initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
    
    def _load_config_from_database(self):
        """Load configuration from database (for dashboard updates)"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT key, value FROM trading_config")
            config_updates = dict(cursor.fetchall())
            
            for key, value in config_updates.items():
                if key in self.config:
                    old_value = self.config[key]
                    self.config[key] = float(value)
                    if abs(old_value - float(value)) > 0.01:  # Only log if changed
                        logger.info(f"📝 Config updated: {key} = {value} (was {old_value})")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
    
    def _load_active_positions(self):
        """Load active positions from database"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT symbol, prediction_id, entry_time, entry_price, shares, 
                       investment, commission_paid, target_profit, confidence
                FROM enhanced_positions 
                WHERE status = 'OPEN'
            """)
            
            for row in cursor.fetchall():
                symbol = row[0]
                self.active_positions[symbol] = {
                    'prediction_id': row[1],
                    'entry_time': datetime.fromisoformat(row[2]),
                    'entry_price': row[3],
                    'shares': row[4],
                    'investment': row[5],
                    'commission_paid': row[6],
                    'target_profit': row[7],
                    'confidence': row[8]
                }
            
            conn.close()
            
            if self.active_positions:
                logger.info(f"📈 Loaded {len(self.active_positions)} active positions:")
                for symbol, pos in self.active_positions.items():
                    logger.info(f"   {symbol}: {pos['shares']} shares @ ${pos['entry_price']:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error loading active positions: {e}")
    
    def check_for_new_predictions(self) -> List[Dict]:
        """Check for new BUY predictions in the database"""
        try:
            conn = sqlite3.connect(self.predictions_db_path)
            cursor = conn.cursor()
            
            # Get new BUY predictions only
            cursor.execute("""
                SELECT prediction_id, symbol, predicted_action, action_confidence, 
                       prediction_timestamp, entry_price, predicted_direction
                FROM predictions 
                WHERE prediction_timestamp > ? 
                AND predicted_action = 'BUY'
                ORDER BY prediction_timestamp ASC
            """, (self.last_processed_timestamp,))
            
            new_predictions = []
            for row in cursor.fetchall():
                prediction = {
                    'prediction_id': row[0],
                    'symbol': row[1],
                    'predicted_action': row[2],
                    'action_confidence': row[3],
                    'prediction_timestamp': row[4],
                    'entry_price': row[5],
                    'predicted_direction': row[6]
                }
                new_predictions.append(prediction)
                # Update last processed timestamp
                self.last_processed_timestamp = row[4]
            
            conn.close()
            return new_predictions
            
        except Exception as e:
            logger.error(f"❌ Error checking predictions: {e}")
            return []
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using real-time price fetcher"""
        try:
            from real_time_price_fetcher import RealTimePriceFetcher
            
            if not hasattr(self, '_price_fetcher'):
                self._price_fetcher = RealTimePriceFetcher()
            
            price_data = self._price_fetcher.get_current_price(symbol)
            
            if price_data:
                price, source_info, delay_minutes = price_data
                
                # Log with appropriate level based on delay
                if delay_minutes == 0:
                    logger.info(f"📊 {symbol}: ${price:.2f} from {source_info} (real-time)")
                elif delay_minutes <= 60:
                    logger.info(f"📊 {symbol}: ${price:.2f} from {source_info} ({delay_minutes}min delay)")
                else:
                    logger.warning(f"⚠️ {symbol}: ${price:.2f} from {source_info} ({delay_minutes}min delay - STALE)")
                
                return float(price)
            else:
                logger.error(f"❌ Could not get price for {symbol} from any data source")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting current price for {symbol}: {e}")
            return None
    
    def can_take_position(self, symbol: str) -> bool:
        """Check if we can take a position (one per symbol rule)"""
        return symbol not in self.active_positions
    
    def execute_buy_order(self, prediction: Dict) -> bool:
        """Execute a BUY order following backtesting strategy"""
        try:
            symbol = prediction['symbol']
            
            # Check one position per symbol rule
            if not self.can_take_position(symbol):
                logger.info(f"⚠️ Skipping {symbol} - already have position")
                return False
            
            # Get current price
            current_price = self.get_current_price(symbol)
            if current_price is None:
                logger.warning(f"⚠️ Could not get price for {symbol}")
                return False
            
            # Calculate position details
            position_size = self.config['position_size']
            shares = int(position_size / current_price)
            actual_investment = shares * current_price
            commission = max(
                self.config['min_commission'],
                min(self.config['max_commission'], actual_investment * self.config['commission_rate'])
            )
            total_cost = actual_investment + commission
            
            logger.info(f"🟢 EXECUTING BUY: {shares} {symbol} @ ${current_price:.2f}")
            logger.info(f"   Investment: ${actual_investment:.2f} + Commission: ${commission:.2f} = ${total_cost:.2f}")
            
            # Store position in memory and database
            position = {
                'prediction_id': prediction['prediction_id'],
                'entry_time': datetime.now(),
                'entry_price': current_price,
                'shares': shares,
                'investment': actual_investment,
                'commission_paid': commission,
                'target_profit': self.config['profit_target'],
                'confidence': prediction['action_confidence']
            }
            
            self.active_positions[symbol] = position
            
            # Save to database
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO enhanced_positions 
                (symbol, prediction_id, entry_time, entry_price, shares, investment, 
                 commission_paid, target_profit, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                position['prediction_id'],
                position['entry_time'].isoformat(),
                position['entry_price'],
                position['shares'],
                position['investment'],
                position['commission_paid'],
                position['target_profit'],
                position['confidence']
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Position opened for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error executing buy order: {e}")
            return False
    
    def check_position_exits(self):
        """Check all active positions for exit conditions"""
        current_time = datetime.now()
        
        # Only make exit decisions during trading hours
        if not is_asx_trading_hours(current_time):
            logger.info(f"⏸️ Market closed - skipping exit checks (positions will be evaluated when market reopens)")
            return
        
        positions_to_close = []
        
        for symbol, position in self.active_positions.items():
            # Get current price
            current_price = self.get_current_price(symbol)
            if current_price is None:
                continue
            
            # Calculate current profit
            current_value = position['shares'] * current_price
            exit_commission = max(
                self.config['min_commission'],
                min(self.config['max_commission'], current_value * self.config['commission_rate'])
            )
            net_proceeds = current_value - exit_commission
            current_profit = net_proceeds - position['investment']
            
            # Calculate trading time (only count time during ASX trading hours)
            hold_time_minutes = calculate_trading_time_minutes(position['entry_time'], current_time)
            
            # Check exit conditions
            should_exit = False
            exit_reason = ""
            
            # Profit target reached
            if current_profit >= position['target_profit']:
                should_exit = True
                exit_reason = f"Profit target reached (${current_profit:.2f} >= ${position['target_profit']:.2f})"
            
            # Max hold time exceeded (trading time)
            elif hold_time_minutes >= self.config['max_hold_time_minutes']:
                should_exit = True
                exit_reason = f"Max trading time exceeded ({hold_time_minutes:.0f} >= {self.config['max_hold_time_minutes']} trading min)"
            
            if should_exit:
                positions_to_close.append((symbol, current_price, current_profit, exit_commission, exit_reason, hold_time_minutes))
            else:
                # Log current status (show trading time)
                total_time_minutes = (current_time - position['entry_time']).total_seconds() / 60
                logger.info(f"📊 {symbol}: ${current_price:.2f} (P&L: ${current_profit:.2f}, Trading: {hold_time_minutes:.0f}min, Total: {total_time_minutes:.0f}min)")
        
        # Close positions that should exit
        for symbol, exit_price, profit, exit_commission, reason, hold_time in positions_to_close:
            self.close_position(symbol, exit_price, profit, exit_commission, reason, hold_time)
    
    def close_position(self, symbol: str, exit_price: float, profit: float, exit_commission: float, exit_reason: str, hold_time_minutes: float):
        """Close a position and record the trade"""
        try:
            if symbol not in self.active_positions:
                logger.warning(f"⚠️ Cannot close {symbol} - position not found")
                return
            
            position = self.active_positions[symbol]
            current_time = datetime.now()
            
            # Calculate final trade details
            proceeds = (position['shares'] * exit_price) - exit_commission
            total_commission = position['commission_paid'] + exit_commission
            
            logger.info(f"🔴 CLOSING POSITION: {symbol}")
            logger.info(f"   Entry: {position['shares']} @ ${position['entry_price']:.2f}")
            logger.info(f"   Exit: {position['shares']} @ ${exit_price:.2f}")
            logger.info(f"   P&L: ${profit:.2f} | Trading Time: {hold_time_minutes:.0f}min")
            logger.info(f"   Reason: {exit_reason}")
            
            # Record trade in database
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO enhanced_trades 
                (symbol, prediction_id, action, entry_time, exit_time, entry_price, exit_price,
                 shares, investment, proceeds, profit, commission_total, hold_time_minutes,
                 exit_reason, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                position['prediction_id'],
                'BUY_SELL',
                position['entry_time'].isoformat(),
                current_time.isoformat(),
                position['entry_price'],
                exit_price,
                position['shares'],
                position['investment'],
                proceeds,
                profit,
                total_commission,
                hold_time_minutes,
                exit_reason,
                position['confidence']
            ))
            
            # Update position status
            cursor.execute("""
                UPDATE enhanced_positions 
                SET status = 'CLOSED' 
                WHERE symbol = ? AND status = 'OPEN'
            """, (symbol,))
            
            conn.commit()
            conn.close()
            
            # Remove from active positions
            del self.active_positions[symbol]
            
            logger.info(f"✅ Trade completed for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error closing position for {symbol}: {e}")
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            # Get total trades and profit
            cursor.execute("""
                SELECT COUNT(*), SUM(profit), AVG(profit), AVG(hold_time_minutes)
                FROM enhanced_trades
            """)
            trade_stats = cursor.fetchone()
            
            # Get active positions value
            total_invested = sum(pos['investment'] + pos['commission_paid'] for pos in self.active_positions.values())
            
            conn.close()
            
            return {
                'active_positions': len(self.active_positions),
                'total_invested': total_invested,
                'total_trades': trade_stats[0] or 0,
                'total_profit': trade_stats[1] or 0,
                'avg_profit': trade_stats[2] or 0,
                'avg_hold_time': trade_stats[3] or 0,
                'symbols_held': list(self.active_positions.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting portfolio summary: {e}")
            return {}
    
    def run(self):
        """Main service loop with enhanced strategy"""
        logger.info("🚀 Enhanced Paper Trading Service started!")
        logger.info(f"🎯 Strategy: One position per symbol, ${self.config['profit_target']} profit target")
        logger.info(f"⏰ Position checks every {self.config['check_interval_seconds']}s")
        logger.info(f"📡 Prediction checks every {self.config['prediction_check_interval_seconds']}s")
        
        last_prediction_check = 0
        last_config_check = 0
        
        while self.running:
            try:
                current_time = time.time()
                current_datetime = datetime.now()
                is_market_open = is_asx_trading_hours(current_datetime)
                
                # Check for configuration updates every 5 minutes
                if current_time - last_config_check >= 300:
                    self._load_config_from_database()
                    last_config_check = current_time
                
                # Check active positions every minute (during trading hours only)
                if self.active_positions:
                    if is_market_open:
                        logger.info(f"🔍 Checking {len(self.active_positions)} active positions...")
                        self.check_position_exits()
                    else:
                        # Less frequent logging during market closed hours
                        if current_time % 600 == 0:  # Every 10 minutes
                            logger.info(f"💤 Market closed - {len(self.active_positions)} positions waiting for market open")
                
                # Check for new predictions every 5 minutes (during trading hours only)
                if is_market_open and current_time - last_prediction_check >= self.config['prediction_check_interval_seconds']:
                    new_predictions = self.check_for_new_predictions()
                    
                    if new_predictions:
                        logger.info(f"📈 Found {len(new_predictions)} new BUY predictions")
                        for prediction in new_predictions:
                            if self.can_take_position(prediction['symbol']):
                                self.execute_buy_order(prediction)
                            else:
                                logger.info(f"⚠️ Skipping {prediction['symbol']} - position already exists")
                    else:
                        logger.info("😴 No new BUY predictions")
                    
                    last_prediction_check = current_time
                
                # Portfolio summary (less frequent during closed hours)
                if is_market_open or current_time % 1800 == 0:  # Every 30 minutes when closed
                    summary = self.get_portfolio_summary()
                    if summary:
                        logger.info(f"💼 Portfolio: {summary['active_positions']} positions, {summary['total_trades']} trades, ${summary['total_profit']:.2f} profit")
                
                # Wait for next check
                time.sleep(self.config['check_interval_seconds'])
                
            except KeyboardInterrupt:
                logger.info("🛑 Service stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute on error

def main():
    """Main entry point"""
    try:
        service = EnhancedPaperTradingService()
        service.run()
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
