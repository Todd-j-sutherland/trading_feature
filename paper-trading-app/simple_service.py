#!/usr/bin/env python3
"""
Fixed Paper Trading Background Service
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

class SimplePaperTradingService:
    """Simplified paper trading service with fixed paths"""
    
    def __init__(self):
        """Initialize the service"""
        self.predictions_db_path = PREDICTIONS_DB_PATH
        self.paper_trading_db_path = PAPER_TRADING_DB_PATH
        self.last_processed_id = 0
        self.running = True
        
        # Verify databases exist
        if not os.path.exists(self.predictions_db_path):
            raise FileNotFoundError(f"Predictions database not found: {self.predictions_db_path}")
        if not os.path.exists(self.paper_trading_db_path):
            raise FileNotFoundError(f"Paper trading database not found: {self.paper_trading_db_path}")
            
        logger.info(f"✅ Service initialized")
        logger.info(f"📊 Predictions DB: {self.predictions_db_path}")
        logger.info(f"💰 Paper Trading DB: {self.paper_trading_db_path}")
    
    def check_for_new_predictions(self) -> List[Dict]:
        """Check for new predictions in the database"""
        try:
            conn = sqlite3.connect(self.predictions_db_path)
            cursor = conn.cursor()
            
            # Get predictions newer than our last processed ID
            cursor.execute("""
                SELECT id, symbol, prediction, confidence, timestamp, close_price
                FROM predictions 
                WHERE id > ? 
                ORDER BY id ASC
            """, (self.last_processed_id,))
            
            new_predictions = []
            for row in cursor.fetchall():
                prediction = {
                    'id': row[0],
                    'symbol': row[1],
                    'prediction': row[2],
                    'confidence': row[3],
                    'timestamp': row[4],
                    'close_price': row[5]
                }
                new_predictions.append(prediction)
                self.last_processed_id = max(self.last_processed_id, row[0])
            
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
    
    def process_signal(self, prediction: Dict) -> bool:
        """Process a trading signal"""
        try:
            symbol = prediction['symbol']
            signal = prediction['prediction']
            confidence = prediction['confidence']
            
            logger.info(f"🔄 Processing signal: {symbol} = {signal} (confidence: {confidence:.2f})")
            
            # Get current price
            current_price = self.get_current_price(symbol)
            if current_price is None:
                logger.warning(f"⚠️ Could not get price for {symbol}")
                return False
            
            logger.info(f"💲 Current price for {symbol}: ${current_price:.2f}")
            
            # For demo, just log the action we would take
            if signal == 1:  # Buy signal
                action = "BUY"
                logger.info(f"🟢 Would BUY {symbol} at ${current_price:.2f}")
            elif signal == -1:  # Sell signal
                action = "SELL"
                logger.info(f"🔴 Would SELL {symbol} at ${current_price:.2f}")
            else:
                action = "HOLD"
                logger.info(f"⚪ Would HOLD {symbol} at ${current_price:.2f}")
            
            # Record this in our database (simplified)
            self.record_trade_signal(prediction, current_price, action)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            return False
    
    def record_trade_signal(self, prediction: Dict, current_price: float, action: str):
        """Record the trade signal in our database"""
        try:
            conn = sqlite3.connect(self.paper_trading_db_path)
            cursor = conn.cursor()
            
            # Create a simple trades table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    symbol TEXT,
                    action TEXT,
                    signal_price REAL,
                    current_price REAL,
                    confidence REAL,
                    timestamp TEXT,
                    processed_at TEXT
                )
            """)
            
            # Insert the signal
            cursor.execute("""
                INSERT INTO trade_signals 
                (prediction_id, symbol, action, signal_price, current_price, confidence, timestamp, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction['id'],
                prediction['symbol'],
                action,
                prediction.get('close_price', 0),
                current_price,
                prediction['confidence'],
                prediction['timestamp'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"📝 Recorded {action} signal for {prediction['symbol']}")
            
        except Exception as e:
            logger.error(f"❌ Error recording trade signal: {e}")
    
    def run(self):
        """Main service loop"""
        logger.info("🚀 Paper Trading Service started!")
        logger.info("🔍 Monitoring for new predictions every 5 minutes...")
        
        while self.running:
            try:
                # Check for new predictions
                new_predictions = self.check_for_new_predictions()
                
                if new_predictions:
                    logger.info(f"📈 Found {len(new_predictions)} new predictions")
                    for prediction in new_predictions:
                        self.process_signal(prediction)
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
        service = SimplePaperTradingService()
        service.run()
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
