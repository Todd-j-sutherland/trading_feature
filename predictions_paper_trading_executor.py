#!/usr/bin/env python3
"""
Enhanced Paper Trading Executor for Bank Predictions

This script connects our bank stock predictions to the enhanced paper trading system.
Uses real price data but simulated trades with position tracking and profit/loss.
"""

import os
import sys
import sqlite3
import logging
import json
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Add project paths
sys.path.append('/root/test')
sys.path.append('/root/test/app')

# Import price data collector
try:
    from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
    PRICE_DATA_AVAILABLE = True
except ImportError:
    PRICE_DATA_AVAILABLE = False
    logging.error("❌ Price data collector not available")

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/paper_trading_predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PredictionsPaperTradingExecutor:
    def __init__(self):
        """Initialize the predictions-based paper trading executor"""
        self.predictions_db_path = "/root/test/data/trading_predictions.db"
        self.paper_trading_db_path = "/root/test/paper-trading-app/paper_trading.db"
        self.last_execution_file = "/tmp/last_prediction_trading_execution.txt"
        
        # Initialize price data collector
        if PRICE_DATA_AVAILABLE:
            try:
                self.price_collector = EnhancedMarketDataCollector()
                logger.info("✅ Price data collector initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize price collector: {e}")
                self.price_collector = None
        else:
            self.price_collector = None
        
        # Trading configuration
        self.config = {
            'initial_balance': 100000.0,
            'position_sizing': {
                'max_position_value': 10000.0,
                'confidence_scaling': True,
                'min_confidence': 0.65
            },
            'risk_management': {
                'stop_loss_pct': 0.05,  # 5% stop loss
                'take_profit_pct': 0.10,  # 10% take profit
                'max_positions': 5
            }
        }
    
    def get_last_execution_time(self) -> Optional[str]:
        """Get the timestamp of last execution"""
        try:
            if os.path.exists(self.last_execution_file):
                with open(self.last_execution_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return None
    
    def update_last_execution_time(self, timestamp: str):
        """Update the last execution timestamp"""
        try:
            with open(self.last_execution_file, 'w') as f:
                f.write(timestamp)
        except Exception as e:
            logger.error(f"Failed to update execution time: {e}")
    
    def get_new_trading_signals(self) -> List[Dict]:
        """Get new BUY signals since last execution"""
        if not os.path.exists(self.predictions_db_path):
            logger.error(f"Predictions database not found: {self.predictions_db_path}")
            return []
        
        last_execution = self.get_last_execution_time()
        if not last_execution:
            # First run - get signals from last 2 hours
            last_execution = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Set timeout for database operations
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            conn = sqlite3.connect(self.predictions_db_path, timeout=20)
            cursor = conn.cursor()
            
            # Get new BUY signals from our bank predictions
            cursor.execute("""
                SELECT symbol, predicted_action, action_confidence, created_at, entry_price
                FROM predictions 
                WHERE predicted_action = 'BUY' 
                AND created_at > ?
                AND symbol IN ('CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX')
                ORDER BY created_at DESC
            """, (last_execution,))
            
            signals = []
            for row in cursor.fetchall():
                signals.append({
                    'symbol': row[0],
                    'action': row[1],
                    'confidence': row[2],
                    'timestamp': row[3],
                    'predicted_price': row[4] if row[4] else 0
                })
            
            conn.close()
            signal.alarm(0)
            
            logger.info(f"Found {len(signals)} new BUY signals")
            return signals
            
        except TimeoutException:
            logger.error("❌ Database query timed out")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch trading signals: {e}")
            return []
        finally:
            signal.alarm(0)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if not self.price_collector:
            logger.error("Price collector not available")
            return None
        
        try:
            # Set timeout for price collection
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)
            
            price_data = self.price_collector.get_current_price(symbol)
            signal.alarm(0)
            
            if price_data:
                if isinstance(price_data, dict):
                    current_price = price_data.get('price', price_data.get('bid', 0))
                else:
                    current_price = float(price_data)
                
                if current_price > 0:
                    logger.info(f"💰 Current price for {symbol}: ${current_price:.2f}")
                    return current_price
                
        except TimeoutException:
            logger.error(f"❌ Price fetch timed out for {symbol}")
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
        finally:
            signal.alarm(0)
        
        return None
    
    def calculate_position_size(self, confidence: float, current_price: float) -> int:
        """Calculate position size based on confidence"""
        max_value = self.config['position_sizing']['max_position_value']
        
        if self.config['position_sizing']['confidence_scaling']:
            # Scale by confidence: 50% to 100% of max
            confidence_multiplier = 0.5 + (confidence * 0.5)
            position_value = max_value * confidence_multiplier
        else:
            position_value = max_value
        
        shares = max(1, int(position_value / current_price))
        
        # Limit position size
        shares = min(shares, 200)  # Max 200 shares per position
        
        logger.info(f"📊 Position size: {shares} shares (value: ${shares * current_price:.2f}, confidence: {confidence:.1%})")
        return shares
    
    def get_paper_trading_connection(self):
        """Get connection to paper trading database"""
        try:
            if not os.path.exists(self.paper_trading_db_path):
                logger.error(f"Paper trading database not found: {self.paper_trading_db_path}")
                return None
                
            return sqlite3.connect(self.paper_trading_db_path, timeout=20)
        except Exception as e:
            logger.error(f"Failed to connect to paper trading database: {e}")
            return None
    
    def check_existing_position(self, symbol: str) -> Optional[Dict]:
        """Check if we already have a position in this symbol"""
        conn = self.get_paper_trading_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, quantity, entry_price, entry_time, entry_value
                FROM positions 
                WHERE symbol = ? AND status = 'open'
                ORDER BY entry_time DESC LIMIT 1
            """, (symbol,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'symbol': row[0],
                    'quantity': row[1],
                    'entry_price': row[2],
                    'entry_time': row[3],
                    'entry_value': row[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing position for {symbol}: {e}")
            return None
        finally:
            conn.close()
    
    def create_paper_position(self, signal: Dict, current_price: float, position_size: int) -> bool:
        """Create a new paper trading position"""
        conn = self.get_paper_trading_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            position_value = position_size * current_price
            
            # Insert new position
            cursor.execute("""
                INSERT INTO positions (
                    symbol, quantity, entry_price, entry_time, entry_value, 
                    strategy, confidence, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['symbol'],
                position_size,
                current_price,
                datetime.now().isoformat(),
                position_value,
                'predictions_ml',
                signal['confidence'],
                'open',
                f"ML prediction confidence: {signal['confidence']:.1%}"
            ))
            
            # Insert transaction record
            cursor.execute("""
                INSERT INTO transactions (
                    symbol, action, quantity, price, timestamp, value, fees, strategy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['symbol'],
                'BUY',
                position_size,
                current_price,
                datetime.now().isoformat(),
                position_value,
                0.0,  # No fees for paper trading
                'predictions_ml'
            ))
            
            conn.commit()
            
            logger.info(f"✅ Created paper position: {signal['symbol']} - {position_size} shares @ ${current_price:.2f}")
            logger.info(f"   Position value: ${position_value:.2f}, Confidence: {signal['confidence']:.1%}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create paper position: {e}")
            return False
        finally:
            conn.close()
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        conn = self.get_paper_trading_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Get open positions count
            cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
            open_positions = cursor.fetchone()[0]
            
            # Get total trades count
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE action = 'BUY'")
            total_trades = cursor.fetchone()[0]
            
            # Get total profit/loss
            cursor.execute("SELECT SUM(profit_loss) FROM positions WHERE status = 'closed'")
            total_profit = cursor.fetchone()[0] or 0.0
            
            # Get current positions
            cursor.execute("""
                SELECT symbol, quantity, entry_price, entry_time 
                FROM positions 
                WHERE status = 'open' 
                ORDER BY entry_time DESC
            """)
            current_positions = cursor.fetchall()
            
            return {
                'open_positions': open_positions,
                'total_trades': total_trades,
                'total_profit': total_profit,
                'positions': current_positions
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}
        finally:
            conn.close()
    
    def execute_paper_trade(self, signal: Dict) -> bool:
        """Execute a paper trade based on prediction signal"""
        try:
            symbol = signal['symbol']
            confidence = signal['confidence']
            
            # Check minimum confidence threshold
            min_confidence = self.config['position_sizing']['min_confidence']
            if confidence < min_confidence:
                logger.info(f"⏭️ Skipping {symbol} - confidence {confidence:.1%} below threshold {min_confidence:.1%}")
                return False
            
            # Check if we already have a position
            existing_position = self.check_existing_position(symbol)
            if existing_position:
                logger.info(f"📋 Already have position in {symbol} - skipping")
                return False
            
            # Check portfolio limits
            portfolio = self.get_portfolio_summary()
            max_positions = self.config['risk_management']['max_positions']
            if portfolio.get('open_positions', 0) >= max_positions:
                logger.info(f"📋 Portfolio limit reached ({max_positions} positions) - skipping {symbol}")
                return False
            
            # Get current price
            current_price = self.get_current_price(symbol)
            if not current_price:
                logger.error(f"❌ Could not get current price for {symbol}")
                return False
            
            # Calculate position size
            position_size = self.calculate_position_size(confidence, current_price)
            
            # Create the paper position
            if self.create_paper_position(signal, current_price, position_size):
                logger.info(f"🎯 PAPER TRADE EXECUTED: {symbol}")
                return True
            else:
                logger.error(f"❌ Failed to create paper position for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to execute paper trade for {signal['symbol']}: {e}")
            return False
    
    def run_trading_execution(self):
        """Main execution loop"""
        logger.info("🚀 Starting Predictions-Based Paper Trading Execution")
        
        # Check database connections
        if not os.path.exists(self.predictions_db_path):
            logger.error("❌ Predictions database not found")
            return
        
        if not os.path.exists(self.paper_trading_db_path):
            logger.error("❌ Paper trading database not found")
            return
        
        # Get current portfolio status
        portfolio = self.get_portfolio_summary()
        logger.info(f"📊 Current portfolio: {portfolio.get('open_positions', 0)} positions, {portfolio.get('total_trades', 0)} total trades, ${portfolio.get('total_profit', 0):.2f} profit")
        
        # Get new trading signals
        signals = self.get_new_trading_signals()
        
        if not signals:
            logger.info("ℹ️ No new trading signals found")
            return
        
        logger.info(f"📋 Processing {len(signals)} trading signals...")
        
        # Execute trades for each signal
        successful_trades = 0
        for signal in signals:
            logger.info(f"🔄 Processing signal: {signal['symbol']} (confidence: {signal['confidence']:.1%})")
            
            if self.execute_paper_trade(signal):
                successful_trades += 1
                logger.info(f"✅ Paper trade #{successful_trades} executed successfully")
                time.sleep(2)  # Small delay between trades
            else:
                logger.info(f"⏭️ Skipped trade for {signal['symbol']}")
        
        # Update last execution time
        if signals:
            latest_signal_time = max(signal['timestamp'] for signal in signals)
            self.update_last_execution_time(latest_signal_time)
        
        # Final portfolio status
        final_portfolio = self.get_portfolio_summary()
        logger.info(f"🏁 Execution complete: {successful_trades}/{len(signals)} trades executed")
        logger.info(f"📊 Final portfolio: {final_portfolio.get('open_positions', 0)} positions, ${final_portfolio.get('total_profit', 0):.2f} total profit")
        
        if successful_trades > 0:
            logger.info("🎉 New paper trades added to portfolio!")

def main():
    """Main entry point"""
    executor = PredictionsPaperTradingExecutor()
    executor.run_trading_execution()

if __name__ == "__main__":
    main()
