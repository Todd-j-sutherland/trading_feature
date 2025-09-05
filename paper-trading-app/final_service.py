#!/usr/bin/env python3
"""
Paper Trading Background Service - Fixed Version
"""
import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Fixed paths for remote server
PREDICTIONS_DB_PATH = '/root/test/predictions.db'
PAPER_TRADING_DB_PATH = '/root/test/paper-trading-app/paper_trading.db'

class PaperTradingService:
    """Paper trading service that monitors predictions and executes trades"""
    
    def __init__(self):
        """Initialize the service"""
        self.predictions_db_path = PREDICTIONS_DB_PATH
        self.paper_trading_db_path = PAPER_TRADING_DB_PATH
        self.last_processed_timestamp = None
        self.running = True
        
        # Verify databases exist
        if not os.path.exists(self.predictions_db_path):
            raise FileNotFoundError(f"Predictions database not found: {self.predictions_db_path}")
        if not os.path.exists(self.paper_trading_db_path):
            raise FileNotFoundError(f"Paper trading database not found: {self.paper_trading_db_path}")
            
        logger.info(f"✅ Service initialized")
        logger.info(f"📊 Predictions DB: {self.predictions_db_path}")
        logger.info(f"💰 Paper Trading DB: {self.paper_trading_db_path}")
        
        # Initialize last processed timestamp to 1 hour ago
        self.last_processed_timestamp = (datetime.now() - timedelta(hours=1)).isoformat()
    
    def check_for_new_predictions(self) -> List[Dict]:
        """Check for new predictions in the database"""
        try:
            conn = sqlite3.connect(self.predictions_db_path)
            cursor = conn.cursor()
            
            # Get predictions newer than our last processed timestamp
            cursor.execute("""
                SELECT prediction_id, symbol, predicted_action, action_confidence, 
                       prediction_timestamp, entry_price, predicted_direction
                FROM predictions 
                WHERE prediction_timestamp > ? 
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
        """Get current price using yfinance"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, price: float, confidence: float) -> int:
        """Calculate position size based on confidence and available capital"""
        # Simple position sizing: higher confidence = larger position
        base_amount = 10000  # Base $10,000 per trade
        confidence_multiplier = min(confidence, 1.0)  # Cap at 1.0
        position_value = base_amount * confidence_multiplier
        
        # Calculate shares (minimum 1 share)
        shares = max(1, int(position_value / price))
        return shares
    
    def process_signal(self, prediction: Dict) -> bool:
        """Process a trading signal and execute paper trade"""
        try:
            symbol = prediction['symbol']
            action = prediction['predicted_action']
            confidence = prediction['action_confidence']
            predicted_price = prediction.get('entry_price', 0)
            
            logger.info(f"🔄 Processing signal: {symbol} = {action} (confidence: {confidence:.3f})")
            
            # Get current price
            current_price = self.get_current_price(symbol)
            if current_price is None:
                logger.warning(f"⚠️ Could not get price for {symbol}")
                return False
            
            logger.info(f"💲 Current price for {symbol}: ${current_price:.2f}")
            logger.info(f"📊 Predicted price was: ${predicted_price:.2f}")
            
            # Calculate position size
            shares = self.calculate_position_size(current_price, confidence)
            trade_value = shares * current_price
            
            # Execute the trade based on action
            if action.upper() == 'BUY':
                logger.info(f"🟢 EXECUTING BUY: {shares} shares of {symbol} at ${current_price:.2f} (${trade_value:.2f})")
                self.execute_buy_order(symbol, shares, current_price, prediction)
            elif action.upper() == 'SELL':
                logger.info(f"🔴 EXECUTING SELL: {shares} shares of {symbol} at ${current_price:.2f} (${trade_value:.2f})")
                self.execute_sell_order(symbol, shares, current_price, prediction)
            else:  # HOLD
                logger.info(f"⚪ HOLDING {symbol} - no action taken")
                self.record_hold_signal(symbol, current_price, prediction)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            return False
    
    def execute_buy_order(self, symbol: str, shares: int, price: float, prediction: Dict):
        """Execute a buy order"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            # Create trades table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT,
                    symbol TEXT,
                    action TEXT,
                    shares INTEGER,
                    price REAL,
                    trade_value REAL,
                    commission REAL,
                    confidence REAL,
                    predicted_price REAL,
                    prediction_timestamp TEXT,
                    execution_timestamp TEXT,
                    status TEXT DEFAULT 'EXECUTED'
                )
            """)
            
            # Calculate commission (0.25% with min $5, max $25)
            commission = max(5.0, min(25.0, shares * price * 0.0025))
            total_cost = (shares * price) + commission
            
            # Insert the trade
            cursor.execute("""
                INSERT INTO paper_trades 
                (prediction_id, symbol, action, shares, price, trade_value, commission, 
                 confidence, predicted_price, prediction_timestamp, execution_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction['prediction_id'],
                symbol,
                'BUY',
                shares,
                price,
                total_cost,
                commission,
                prediction['action_confidence'],
                prediction.get('entry_price', 0),
                prediction['prediction_timestamp'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ BUY order recorded: {shares} {symbol} @ ${price:.2f} (Commission: ${commission:.2f})")
            
        except Exception as e:
            logger.error(f"❌ Error executing buy order: {e}")
    
    def execute_sell_order(self, symbol: str, shares: int, price: float, prediction: Dict):
        """Execute a sell order"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            # Calculate commission
            commission = max(5.0, min(25.0, shares * price * 0.0025))
            total_proceeds = (shares * price) - commission
            
            # Insert the trade
            cursor.execute("""
                INSERT INTO paper_trades 
                (prediction_id, symbol, action, shares, price, trade_value, commission, 
                 confidence, predicted_price, prediction_timestamp, execution_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction['prediction_id'],
                symbol,
                'SELL',
                shares,
                price,
                total_proceeds,
                commission,
                prediction['action_confidence'],
                prediction.get('entry_price', 0),
                prediction['prediction_timestamp'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ SELL order recorded: {shares} {symbol} @ ${price:.2f} (Commission: ${commission:.2f})")
            
        except Exception as e:
            logger.error(f"❌ Error executing sell order: {e}")
    
    def record_hold_signal(self, symbol: str, price: float, prediction: Dict):
        """Record a hold signal"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            # Create signals table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hold_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT,
                    symbol TEXT,
                    price REAL,
                    confidence REAL,
                    predicted_price REAL,
                    prediction_timestamp TEXT,
                    recorded_timestamp TEXT
                )
            """)
            
            # Insert the hold signal
            cursor.execute("""
                INSERT INTO hold_signals 
                (prediction_id, symbol, price, confidence, predicted_price, 
                 prediction_timestamp, recorded_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction['prediction_id'],
                symbol,
                price,
                prediction['action_confidence'],
                prediction.get('entry_price', 0),
                prediction['prediction_timestamp'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"📝 HOLD signal recorded for {symbol} @ ${price:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error recording hold signal: {e}")
    
    def run(self):
        """Main service loop"""
        logger.info("🚀 Paper Trading Service started!")
        logger.info("🔍 Monitoring for new predictions every 5 minutes...")
        logger.info(f"⏰ Starting from timestamp: {self.last_processed_timestamp}")
        
        while self.running:
            try:
                # Check for new predictions
                new_predictions = self.check_for_new_predictions()
                
                if new_predictions:
                    logger.info(f"📈 Found {len(new_predictions)} new predictions")
                    for prediction in new_predictions:
                        self.process_signal(prediction)
                        time.sleep(2)  # Small delay between trades
                else:
                    logger.info("😴 No new predictions found")
                
                # Wait 5 minutes
                logger.info("⏰ Waiting 5 minutes for next check...")
                time.sleep(300)  # 5 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Service stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute on error

def main():
    """Main entry point"""
    try:
        service = PaperTradingService()
        service.run()
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
