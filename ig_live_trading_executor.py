#!/usr/bin/env python3
"""
Live IG Markets Demo Trading Executor with Real API Integration

This script connects predictions to actual IG Markets demo account trading.
Executes REAL trades using the IG Markets API.
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

# Import the real IG Markets API client
try:
    from ig_markets_trading_api import IGMarketsAPIClient, SYMBOL_TO_EPIC
    IG_API_AVAILABLE = True
except ImportError:
    IG_API_AVAILABLE = False
    logging.error("❌ IG Markets API client not available")

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ig_live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IGLiveTradingExecutor:
    def __init__(self):
        """Initialize the live trading executor with real IG Markets API"""
        self.db_path = "/root/test/data/trading_predictions.db"
        self.config_path = "/root/test/ig_markets_config_banks.json"
        self.last_execution_file = "/tmp/last_trading_execution.txt"
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize real IG Markets API client
        if IG_API_AVAILABLE:
            try:
                self.ig_client = IGMarketsAPIClient()
                logger.info("✅ IG Markets API client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize IG Markets API client: {e}")
                self.ig_client = None
        else:
            logger.error("❌ IG Markets API not available")
            self.ig_client = None
    
    def load_config(self) -> Dict:
        """Load IG Markets configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                logger.info("✅ Configuration loaded successfully")
                return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return {}
    
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
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found: {self.db_path}")
            return []
        
        last_execution = self.get_last_execution_time()
        if not last_execution:
            # First run - get signals from last hour only
            last_execution = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Set timeout for database operations
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            conn = sqlite3.connect(self.db_path, timeout=20)
            cursor = conn.cursor()
            
            # Get new BUY signals
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
                    'entry_price': row[4]
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
    
    def calculate_position_size(self, confidence: float, current_price: float) -> int:
        """Calculate position size based on confidence and risk management"""
        base_position_value = self.config.get('position_sizing', {}).get('max_position_value', 5000)
        
        # Scale position size by confidence (50% to 100% of base size)
        confidence_multiplier = 0.5 + (confidence * 0.5)
        position_value = base_position_value * confidence_multiplier
        
        # Calculate number of shares
        shares = max(1, int(position_value / current_price))
        
        # Respect min/max deal sizes
        min_deal_size = 1
        max_deal_size = 100  # Conservative limit for demo trading
        
        shares = max(min_deal_size, min(shares, max_deal_size))
        
        logger.info(f"Position size calculated: {shares} shares (confidence: {confidence:.3f})")
        return shares
    
    def execute_real_ig_trade(self, signal: Dict) -> bool:
        """Execute a REAL trade using IG Markets API"""
        if not self.ig_client:
            logger.error("❌ IG Markets API client not available")
            return False
        
        try:
            symbol = signal['symbol']
            confidence = signal['confidence']
            
            # Get IG epic for symbol
            ig_epic = SYMBOL_TO_EPIC.get(symbol)
            if not ig_epic:
                logger.error(f"❌ No IG epic mapping found for {symbol}")
                return False
            
            logger.info(f"🎯 Preparing REAL trade for {symbol} -> {ig_epic}")
            
            # Authenticate with IG Markets
            if not self.ig_client.authenticate():
                logger.error("❌ IG Markets authentication failed")
                return False
            
            # Get account info for debugging
            account_info = self.ig_client.get_account_info()
            if account_info:
                logger.info(f"📊 Account info retrieved successfully")
                # Log just the account count, not all data
                accounts = account_info.get('accounts', [])
                logger.info(f"📊 Found {len(accounts)} accounts available")
            
            # Get market info
            market_info = self.ig_client.get_market_info(ig_epic)
            if not market_info:
                logger.error(f"❌ Could not get market info for {ig_epic}")
                return False
            
            # Extract current price from market info
            snapshot = market_info.get('snapshot', {})
            bid_price = snapshot.get('bid')
            ask_price = snapshot.get('offer')
            current_price = ask_price if ask_price else bid_price
            
            if not current_price:
                logger.error(f"❌ Could not get current price for {ig_epic}")
                return False
            
            logger.info(f"💰 Current market price for {symbol}: Bid ${bid_price}, Ask ${ask_price}")
            
            # Calculate position size
            position_size = self.calculate_position_size(confidence, current_price)
            
            # Check market status
            market_status = snapshot.get('marketStatus')
            logger.info(f"🏛️ Market status for {ig_epic}: {market_status}")
            
            # Place the REAL order
            logger.info(f"🚀 Placing REAL BUY order: {position_size} shares of {symbol} ({ig_epic})")
            logger.info(f"💡 Trade value: ${position_size * current_price:.2f}, Confidence: {confidence:.1%}")
            
            order_result = self.ig_client.place_order(
                epic=ig_epic,
                direction="BUY",
                size=position_size,
                order_type="MARKET"
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"✅ REAL TRADE EXECUTED SUCCESSFULLY!")
                logger.info(f"📄 Deal Reference: {order_result.get('deal_reference')}")
                
                # Check final deal status
                if order_result.get('status'):
                    deal_status = order_result['status'].get('dealStatus')
                    logger.info(f"🎯 Final Deal Status: {deal_status}")
                
                return True
            else:
                logger.error(f"❌ REAL TRADE FAILED!")
                if order_result:
                    error_info = order_result.get('error', 'Unknown error')
                    logger.error(f"📄 Error Details: {error_info}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to execute REAL trade for {signal['symbol']}: {e}")
            return False
    
    def debug_ig_connection(self):
        """Debug IG Markets connection and account status"""
        if not self.ig_client:
            logger.error("❌ IG Markets client not initialized")
            return
        
        logger.info("🔍 Starting IG Markets connection debugging...")
        
        # Test authentication
        auth_success = self.ig_client.authenticate()
        logger.info(f"🔐 Authentication: {'✅ Success' if auth_success else '❌ Failed'}")
        
        if not auth_success:
            return
        
        # Test account access
        account_info = self.ig_client.get_account_info()
        if account_info:
            logger.info("✅ Account access successful")
            accounts = account_info.get('accounts', [])
            logger.info(f"📊 Found {len(accounts)} accounts")
        else:
            logger.error("❌ Account access failed")
        
        # Test getting positions
        positions = self.ig_client.get_positions()
        if positions is not None:
            logger.info(f"✅ Position access successful - {len(positions)} positions")
        else:
            logger.error("❌ Position access failed")
        
        # Test market data for each symbol
        for symbol, epic in SYMBOL_TO_EPIC.items():
            market_info = self.ig_client.get_market_info(epic)
            if market_info:
                snapshot = market_info.get('snapshot', {})
                bid = snapshot.get('bid')
                ask = snapshot.get('offer')
                status = snapshot.get('marketStatus')
                logger.info(f"✅ {symbol} ({epic}): Bid ${bid}, Ask ${ask}, Status: {status}")
            else:
                logger.error(f"❌ Failed to get market info for {symbol} ({epic})")
    
    def run_trading_execution(self):
        """Main execution loop with comprehensive debugging"""
        logger.info("🚀 Starting IG Markets REAL Demo Trading Execution")
        
        # Debug IG connection first
        self.debug_ig_connection()
        
        # Check if IG Markets API is available
        if not IG_API_AVAILABLE or not self.ig_client:
            logger.error("❌ IG Markets API not available - stopping execution")
            return
        
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
            
            # Only execute high-confidence trades (>65%)
            if signal['confidence'] >= 0.65:
                logger.info(f"🎯 Executing REAL trade for {signal['symbol']}...")
                if self.execute_real_ig_trade(signal):
                    successful_trades += 1
                    logger.info(f"✅ Trade #{successful_trades} executed successfully")
                    time.sleep(5)  # Rate limiting between trades
                else:
                    logger.error(f"❌ Trade execution failed for {signal['symbol']}")
            else:
                logger.info(f"⏭️ Skipping {signal['symbol']} - confidence too low ({signal['confidence']:.1%})")
        
        # Update last execution time
        if signals:
            latest_signal_time = max(signal['timestamp'] for signal in signals)
            self.update_last_execution_time(latest_signal_time)
        
        logger.info(f"🏁 Trading execution complete: {successful_trades}/{len(signals)} REAL trades executed")
        
        if successful_trades > 0:
            logger.info("🎉 Check your IG Markets demo account for executed trades!")
        
        # Final positions check
        if self.ig_client:
            positions = self.ig_client.get_positions()
            if positions:
                logger.info(f"📊 Current portfolio: {len(positions)} open positions")
            else:
                logger.info("📊 No open positions in account")

def main():
    """Main entry point"""
    executor = IGLiveTradingExecutor()
    executor.run_trading_execution()

if __name__ == "__main__":
    main()
