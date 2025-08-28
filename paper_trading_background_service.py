#!/usr/bin/env python3
"""
Paper Trading Background Service
Monitors predictions database and automatically executes paper trades
Runs independently from the main ML system
"""

import sqlite3
import time
import sys
import os
import signal
import logging
from datetime import datetime, timedelta
from typing import Set, Dict, List, Optional
import json

# Add paper trading app to path
paper_trading_path = os.path.join(os.path.dirname(__file__), 'paper-trading-app')
sys.path.append(paper_trading_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading_service.log'),
        logging.StreamHandler()
    ]
)

class PaperTradingService:
    """Background service for automated paper trading based on ML predictions"""
    
    def __init__(self, predictions_db_path="predictions.db", check_interval=300):
        self.predictions_db = predictions_db_path
        self.check_interval = check_interval  # 5 minutes = 300 seconds
        self.processed_predictions: Set[str] = set()
        self.running = True
        self.logger = logging.getLogger(__name__)
        
        # Load processed predictions from state file
        self._load_state()
        
        # Initialize paper trading components
        try:
            from database.models import create_database, get_session, init_default_account
            from trading.engine import PaperTradingEngine, StrategyInterface
            from config import TRADING_CONFIG
            
            # Setup paper trading database
            paper_db_path = os.path.join(paper_trading_path, "paper_trading.db")
            engine = create_database(f"sqlite:///{paper_db_path}")
            session = get_session(engine)
            account = init_default_account(session, TRADING_CONFIG['initial_balance'])
            
            # Initialize trading components
            self.trading_engine = PaperTradingEngine(session, account.id)
            self.strategy_interface = StrategyInterface(self.trading_engine)
            
            self.logger.info(f"✅ Paper trading service initialized")
            self.logger.info(f"💰 Account balance: ${account.cash_balance:,.2f}")
            
        except ImportError as e:
            self.logger.error(f"❌ Failed to initialize paper trading: {e}")
            raise
        
        # Trading configuration
        self.config = {
            'confidence_thresholds': {
                'BUY': 0.6,   # 60% confidence required for buys
                'SELL': 0.0,  # Always execute sells
                'HOLD': 0.0   # No action for holds
            },
            'position_sizing': {
                'base_amount': 10000,     # $10k base position
                'max_portfolio_pct': 0.15, # 15% max per position
                'confidence_scaling': True
            },
            'price_validation': {
                'max_age_minutes': 10,  # Use prices up to 10 minutes old
                'required_volume': 1000 # Minimum daily volume
            }
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"🛑 Received shutdown signal ({signum})")
        self.running = False
    
    def _load_state(self):
        """Load previously processed predictions from state file"""
        state_file = "paper_trading_service_state.json"
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_predictions = set(state.get('processed_predictions', []))
                    self.logger.info(f"📁 Loaded {len(self.processed_predictions)} processed predictions from state")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load state file: {e}")
            self.processed_predictions = set()
    
    def _save_state(self):
        """Save processed predictions to state file"""
        state_file = "paper_trading_service_state.json"
        try:
            state = {
                'processed_predictions': list(self.processed_predictions),
                'last_updated': datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save state file: {e}")
    
    def get_current_price_yahoo(self, symbol: str) -> Optional[float]:
        """Get current price from Yahoo Finance with error handling"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            
            # Try current price first
            info = ticker.info
            if 'currentPrice' in info and info['currentPrice'] > 0:
                price = float(info['currentPrice'])
                self.logger.debug(f"💰 {symbol}: Current price ${price:.2f}")
                return price
            
            # Fallback to recent history
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                
                # Validate volume if required
                if volume < self.config['price_validation']['required_volume']:
                    self.logger.warning(f"⚠️ {symbol}: Low volume {volume:,} shares")
                
                self.logger.debug(f"💰 {symbol}: Recent price ${price:.2f} (volume: {volume:,})")
                return price
            
            self.logger.warning(f"⚠️ {symbol}: No price data available")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ {symbol}: Error fetching price - {e}")
            return None
    
    def check_for_new_predictions(self) -> List[Dict]:
        """Check for new predictions that haven't been processed"""
        try:
            conn = sqlite3.connect(self.predictions_db)
            cursor = conn.cursor()
            
            # Get predictions we haven't processed yet
            if self.processed_predictions:
                placeholders = ','.join('?' * len(self.processed_predictions))
                query = f"""
                    SELECT prediction_id, symbol, predicted_action, action_confidence, 
                           prediction_timestamp, predicted_magnitude, reasoning
                    FROM predictions 
                    WHERE prediction_id NOT IN ({placeholders})
                    ORDER BY prediction_timestamp DESC
                    LIMIT 20
                """
                cursor.execute(query, list(self.processed_predictions))
            else:
                cursor.execute("""
                    SELECT prediction_id, symbol, predicted_action, action_confidence, 
                           prediction_timestamp, predicted_magnitude, reasoning
                    FROM predictions 
                    ORDER BY prediction_timestamp DESC
                    LIMIT 20
                """)
            
            predictions = cursor.fetchall()
            conn.close()
            
            # Convert to dict format
            new_predictions = []
            for pred in predictions:
                pred_data = {
                    'prediction_id': pred[0],
                    'symbol': pred[1],
                    'predicted_action': pred[2],
                    'confidence': pred[3] if pred[3] is not None else 0.0,
                    'timestamp': pred[4],
                    'magnitude': pred[5] if pred[5] is not None else 0.0,
                    'reasoning': pred[6] if pred[6] else 'ML Prediction'
                }
                new_predictions.append(pred_data)
                
                # Mark as processed
                self.processed_predictions.add(pred[0])
            
            if new_predictions:
                self.logger.info(f"🔍 Found {len(new_predictions)} new predictions to process")
            
            return new_predictions
            
        except Exception as e:
            self.logger.error(f"❌ Error checking for new predictions: {e}")
            return []
    
    def calculate_position_size(self, symbol: str, confidence: float, current_price: float) -> int:
        """Calculate position size based on confidence and portfolio constraints"""
        try:
            # Get current portfolio summary
            portfolio = self.trading_engine.get_portfolio_summary()
            portfolio_value = portfolio.get('account', {}).get('portfolio_value', 0)
            
            if portfolio_value <= 0:
                self.logger.warning(f"⚠️ Invalid portfolio value: ${portfolio_value}")
                return 0
            
            # Base position size
            base_amount = self.config['position_sizing']['base_amount']
            max_portfolio_pct = self.config['position_sizing']['max_portfolio_pct']
            
            # Apply portfolio limit
            max_position_value = portfolio_value * max_portfolio_pct
            position_value = min(base_amount, max_position_value)
            
            # Scale by confidence if enabled
            if self.config['position_sizing']['confidence_scaling']:
                # Scale between 0.5x and 1.5x based on confidence
                confidence_factor = 0.5 + (confidence * 1.0)
                position_value *= confidence_factor
            
            # Calculate shares
            shares = int(position_value / current_price)
            
            # Minimum viable position
            if shares < 10:
                if position_value >= (current_price * 10):
                    shares = 10
                else:
                    shares = 0
            
            self.logger.debug(f"📊 {symbol}: Position size {shares} shares (${position_value:,.0f} @ ${current_price:.2f})")
            return shares
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating position size for {symbol}: {e}")
            return 0
    
    def process_prediction(self, pred_data: Dict) -> bool:
        """Process a single prediction and execute trade if appropriate"""
        try:
            symbol = pred_data['symbol']
            action = pred_data['predicted_action'].upper()
            confidence = pred_data['confidence']
            timestamp = pred_data['timestamp']
            reasoning = pred_data['reasoning']
            
            self.logger.info(f"🔄 Processing: {symbol} {action} (confidence: {confidence:.2f})")
            
            # Check confidence threshold
            threshold = self.config['confidence_thresholds'].get(action, 0.0)
            if confidence < threshold:
                self.logger.info(f"   ⏭️ Skipped - confidence {confidence:.2f} below threshold {threshold}")
                return True  # Successfully processed (just skipped)
            
            # Skip HOLD actions
            if action == 'HOLD':
                self.logger.info(f"   ⏭️ Skipped - HOLD action")
                return True
            
            # Get current price from Yahoo Finance
            current_price = self.get_current_price_yahoo(symbol)
            if current_price is None:
                self.logger.warning(f"   ❌ Failed - could not get current price")
                return False
            
            # Execute trade based on action
            if action == 'BUY':
                # Calculate position size
                quantity = self.calculate_position_size(symbol, confidence, current_price)
                if quantity <= 0:
                    self.logger.warning(f"   ❌ Failed - invalid position size")
                    return False
                
                # Execute buy order
                result = self.trading_engine.execute_market_buy(
                    symbol=symbol,
                    quantity=quantity,
                    strategy_source="ML_Background_Service",
                    confidence=confidence,
                    notes=f"Auto-trade from ML prediction: {reasoning}"
                )
                
            elif action == 'SELL':
                # Check if we have a position to sell
                portfolio = self.trading_engine.get_portfolio_summary()
                positions = portfolio.get('positions', [])
                
                current_position = None
                for pos in positions:
                    if pos['symbol'] == symbol:
                        current_position = pos
                        break
                
                if not current_position or current_position['quantity'] <= 0:
                    self.logger.info(f"   ⏭️ Skipped - no position to sell")
                    return True
                
                # Execute sell order
                result = self.trading_engine.execute_market_sell(
                    symbol=symbol,
                    quantity=current_position['quantity'],
                    strategy_source="ML_Background_Service",
                    confidence=confidence,
                    notes=f"Auto-trade from ML prediction: {reasoning}"
                )
            
            else:
                self.logger.warning(f"   ❌ Unknown action: {action}")
                return False
            
            # Log result
            if result.success:
                self.logger.info(f"   ✅ SUCCESS: {result.message}")
                if result.executed_price and result.executed_quantity:
                    total_value = result.executed_price * result.executed_quantity
                    self.logger.info(f"   💰 Executed: {result.executed_quantity} shares @ ${result.executed_price:.2f} = ${total_value:,.2f}")
                    if result.commission:
                        self.logger.info(f"   💸 Commission: ${result.commission:.2f}")
                return True
            else:
                self.logger.warning(f"   ❌ FAILED: {result.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error processing prediction {pred_data.get('prediction_id', 'unknown')}: {e}")
            return False
    
    def show_portfolio_summary(self):
        """Display current portfolio summary"""
        try:
            portfolio = self.trading_engine.get_portfolio_summary()
            account = portfolio.get('account', {})
            
            self.logger.info("📊 PORTFOLIO SUMMARY")
            self.logger.info(f"   💰 Portfolio Value: ${account.get('portfolio_value', 0):,.2f}")
            self.logger.info(f"   💵 Cash Balance: ${account.get('cash_balance', 0):,.2f}")
            self.logger.info(f"   📈 Total P&L: ${account.get('total_pnl', 0):+,.2f} ({account.get('total_pnl_pct', 0):+.2f}%)")
            
            positions = portfolio.get('positions', [])
            if positions:
                self.logger.info(f"   📊 Active Positions: {len(positions)}")
                for pos in positions[:3]:  # Show top 3
                    self.logger.info(f"      • {pos['symbol']}: {pos['quantity']} shares, P&L: ${pos['unrealized_pnl']:+,.0f}")
            else:
                self.logger.info("   📊 No active positions")
                
        except Exception as e:
            self.logger.error(f"❌ Error showing portfolio summary: {e}")
    
    def run(self):
        """Main service loop"""
        self.logger.info("🚀 Paper Trading Background Service Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Monitoring: {self.predictions_db}")
        self.logger.info(f"⏱️  Check interval: {self.check_interval} seconds")
        self.logger.info(f"🎯 BUY threshold: {self.config['confidence_thresholds']['BUY']:.0%}")
        self.logger.info(f"💰 Base position: ${self.config['position_sizing']['base_amount']:,}")
        self.logger.info("🔄 Service running... Press Ctrl+C to stop")
        self.logger.info("=" * 60)
        
        last_summary_time = datetime.now()
        processed_this_session = 0
        
        while self.running:
            try:
                # Check for new predictions
                new_predictions = self.check_for_new_predictions()
                
                if new_predictions:
                    self.logger.info(f"🔔 Processing {len(new_predictions)} new predictions")
                    
                    successful = 0
                    failed = 0
                    
                    for pred in new_predictions:
                        if self.process_prediction(pred):
                            successful += 1
                        else:
                            failed += 1
                    
                    processed_this_session += len(new_predictions)
                    
                    # Summary
                    self.logger.info(f"📋 Batch complete: {successful} successful, {failed} failed")
                    
                    # Save state after processing
                    self._save_state()
                
                # Show periodic summary (every 30 minutes)
                if (datetime.now() - last_summary_time).seconds > 1800:
                    self.show_portfolio_summary()
                    self.logger.info(f"📈 Session stats: {processed_this_session} predictions processed")
                    last_summary_time = datetime.now()
                
                # Wait before next check
                self.logger.debug(f"😴 Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Service stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        # Cleanup
        self._save_state()
        self.show_portfolio_summary()
        self.logger.info(f"👋 Paper Trading Service stopped. Processed {processed_this_session} predictions this session.")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Paper Trading Background Service')
    parser.add_argument('--db', default='predictions.db', 
                       help='Path to predictions database (default: predictions.db)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds (default: 300 = 5 minutes)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (single check, then exit)')
    
    args = parser.parse_args()
    
    try:
        service = PaperTradingService(
            predictions_db_path=args.db,
            check_interval=args.interval
        )
        
        if args.test:
            print("🧪 Running in test mode...")
            predictions = service.check_for_new_predictions()
            print(f"Found {len(predictions)} new predictions")
            if predictions:
                print("Recent predictions:")
                for pred in predictions[:3]:
                    print(f"  • {pred['symbol']} {pred['predicted_action']} (confidence: {pred['confidence']:.2f})")
            service.show_portfolio_summary()
        else:
            service.run()
            
    except KeyboardInterrupt:
        print("\n👋 Service interrupted")
    except Exception as e:
        print(f"❌ Service error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
