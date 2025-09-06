#!/usr/bin/env python3
"""
Paper Trader - Main trading engine with position and fund management
Processes predictions and executes paper trades with IG Markets integration
"""

import logging
import json
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

# Add the src directory to path for imports
sys.path.append(os.path.dirname(__file__))

from position_manager import PositionManager, Position
from enhanced_ig_client import EnhancedIGMarketsClient

logger = logging.getLogger(__name__)

class PaperTrader:
    """
    Main paper trading engine with position limits and fund management
    """
    
    def __init__(self, 
                 config_dir: str = "config",
                 data_dir: str = "data",
                 main_predictions_db: str = "../data/trading_predictions.db"):
        
        self.config_dir = config_dir
        self.data_dir = data_dir
        self.main_predictions_db = main_predictions_db
        
        # Initialize components
        self.position_manager = PositionManager(
            db_path=os.path.join(data_dir, "paper_trading.db"),
            config_path=os.path.join(config_dir, "trading_parameters.json")
        )
        
        self.ig_client = EnhancedIGMarketsClient(
            config_path=os.path.join(config_dir, "ig_markets_config_banks.json")
        )
        
        # Load trading parameters
        self.trading_params = self._load_trading_params()
        
        # Initialize exit strategy if available
        self.exit_strategy = self._init_exit_strategy()
        
        logger.info("✅ Paper Trader initialized")
    
    def _load_trading_params(self) -> Dict:
        """Load trading parameters"""
        try:
            config_path = os.path.join(self.config_dir, "trading_parameters.json")
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Trading parameters not found, using defaults")
            return {}
    
    def _init_exit_strategy(self):
        """Initialize enhanced exit strategy engine"""
        try:
            # Try to import the new enhanced exit strategy engine
            from exit_strategy_engine import ExitStrategyEngine
            
            engine = ExitStrategyEngine(config_path="config/ig_markets_config_banks.json")
            logger.info("✅ Enhanced exit strategy engine loaded for 7-bank system")
            return engine
        except ImportError:
            try:
                # Fallback to Phase 4 exit strategy
                sys.path.append('../phase4_development/exit_strategy')
                from ig_markets_exit_strategy_engine import ExitStrategyEngine
                
                engine = ExitStrategyEngine()
                logger.info("✅ Phase 4 exit strategy engine loaded")
                return engine
            except ImportError:
                logger.warning("Exit strategy engine not available, using simple rules")
                return None
    
    def get_new_predictions(self) -> List[Dict]:
        """Get new predictions that haven't been paper traded yet"""
        try:
            # Get existing prediction IDs from paper trades
            existing_ids = set()
            try:
                for position in self.position_manager.get_open_positions():
                    # Extract prediction ID if stored (would need to be added to Position class)
                    pass
                
                # Also check closed positions to avoid re-trading
                conn = sqlite3.connect(self.position_manager.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT position_id FROM positions")
                for row in cursor.fetchall():
                    existing_ids.add(row[0])
                conn.close()
                
            except Exception as e:
                logger.warning(f"Could not get existing trade IDs: {e}")
            
            # Get recent predictions from main database
            main_db_path = os.path.join(os.path.dirname(__file__), '..', self.main_predictions_db)
            
            if not os.path.exists(main_db_path):
                logger.warning(f"Main predictions database not found: {main_db_path}")
                return []
            
            conn = sqlite3.connect(main_db_path)
            cursor = conn.cursor()
            
            # Get predictions from last 4 hours that are BUY/SELL only
            cursor.execute("""
                SELECT * FROM predictions 
                WHERE prediction_timestamp > datetime('now', '-4 hours')
                AND predicted_action IN ('BUY', 'SELL')
                AND action_confidence >= ?
                ORDER BY prediction_timestamp DESC
            """, (self.trading_params.get("trading_rules", {}).get("min_confidence_threshold", 0.6),))
            
            columns = [desc[0] for desc in cursor.description]
            predictions = []
            
            for row in cursor.fetchall():
                prediction = dict(zip(columns, row))
                
                # Skip if we already have a position for this symbol
                if not self.position_manager.has_open_position(prediction['symbol']):
                    predictions.append(prediction)
            
            conn.close()
            
            logger.info(f"Found {len(predictions)} new predictions to evaluate")
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting new predictions: {e}")
            return []
    
    def execute_paper_trade(self, prediction: Dict) -> Optional[Position]:
        """Execute a paper trade based on prediction"""
        try:
            symbol = prediction['symbol']
            action = prediction['predicted_action']
            confidence = prediction['action_confidence']
            
            logger.info(f"🎯 Evaluating trade: {action} {symbol} (confidence: {confidence:.2f})")
            
            # Skip HOLD actions
            if action == 'HOLD':
                logger.info(f"Skipping HOLD action for {symbol}")
                return None
            
            # Check confidence threshold
            min_confidence = self.trading_params.get("trading_rules", {}).get("min_confidence_threshold", 0.6)
            if confidence < min_confidence:
                logger.info(f"Confidence {confidence:.2f} below threshold {min_confidence} for {symbol}")
                return None
            
            # Map to IG Markets EPIC or get symbol config
            epic_config = self.ig_client.map_symbol_to_epic(symbol)
            
            # Get current market price with enhanced error handling
            market_data = self.ig_client.get_market_data(epic_config)
            if not market_data:
                logger.warning(f"Could not get market price for {symbol}")
                return None
            
            # Check if market is open
            if market_data.get('market_status') != 'TRADEABLE':
                logger.info(f"Market not tradeable for {symbol}: {market_data.get('market_status')}")
                return None
            
            # Get current account balance
            balance = self.position_manager.get_account_balance()
            
            # Determine entry price (use offer for buy, bid for sell)
            entry_price = market_data['offer'] if action == 'BUY' else market_data['bid']
            
            # Calculate position size
            quantity = self.position_manager.calculate_position_size(
                confidence, entry_price, balance.available_funds
            )
            
            if quantity <= 0:
                logger.warning(f"Calculated position size is 0 for {symbol}")
                return None
            
            # Calculate required funds
            required_funds = quantity * entry_price
            
            # Check if we can open this position
            can_open, reason = self.position_manager.can_open_position(symbol, required_funds)
            if not can_open:
                logger.warning(f"Cannot open position for {symbol}: {reason}")
                return None
            
            # Create position object
            epic_str = epic_config if isinstance(epic_config, str) else epic_config.get('ig_epic', symbol)
            position = Position(
                position_id=str(uuid.uuid4()),
                symbol=symbol,
                epic=epic_str,
                action=action,
                quantity=quantity,
                entry_price=entry_price,
                entry_time=datetime.now(),
                confidence=confidence
            )
            
            # Open the position
            if self.position_manager.open_position(position):
                logger.info(f"✅ Paper trade executed: {action} {quantity} {symbol} @ ${entry_price}")
                return position
            else:
                logger.error(f"Failed to open position for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing paper trade for {prediction.get('symbol', 'unknown')}: {e}")
            return None
    
    def evaluate_exit_conditions(self, position: Position, current_price: float) -> Dict:
        """Evaluate exit conditions for a position"""
        try:
            if self.exit_strategy:
                # Use enhanced exit strategy for bank positions
                position_data = {
                    'symbol': position.symbol,
                    'entry_price': position.entry_price,
                    'entry_time': position.entry_time.isoformat(),
                    'confidence': position.confidence,
                    'action': position.action,
                    'quantity': position.quantity
                }
                
                exit_result = self.exit_strategy.evaluate_exit(position_data)
                
                return {
                    'should_exit': exit_result.get('should_exit', False),
                    'reason': exit_result.get('exit_reason', 'NO_EXIT'),
                    'confidence': exit_result.get('exit_confidence', 0.0),
                    'urgency': exit_result.get('urgency', 0),
                    'current_price': exit_result.get('current_price', current_price),
                    'return_pct': exit_result.get('return_percentage', 0.0)
                }
            else:
                # Use simple profit/loss rules
                profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                if position.action == 'SELL':
                    profit_pct = -profit_pct
                
                # Get exit thresholds from config
                profit_target = self.trading_params.get("risk_management", {}).get("profit_target_percentage", 3.0)
                stop_loss = self.trading_params.get("risk_management", {}).get("stop_loss_percentage", 2.0)
                max_hold_days = self.trading_params.get("risk_management", {}).get("max_position_hold_days", 5)
                
                # Check time limit
                days_held = (datetime.now() - position.entry_time).days
                if days_held >= max_hold_days:
                    return {'should_exit': True, 'reason': 'TIME_LIMIT', 'confidence': 0.7, 'urgency': 3}
                
                # Check profit target
                if profit_pct >= profit_target:
                    return {'should_exit': True, 'reason': 'PROFIT_TARGET', 'confidence': 0.8, 'urgency': 4}
                
                # Check stop loss
                if profit_pct <= -stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS', 'confidence': 0.9, 'urgency': 5}
                
                return {'should_exit': False, 'reason': 'NO_EXIT', 'confidence': 0.0, 'urgency': 0}
                
        except Exception as e:
            logger.error(f"Error evaluating exit conditions: {e}")
            # Default to simple stop loss
            profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            if profit_pct <= -5.0:  # Emergency stop loss
                return {'should_exit': True, 'reason': 'EMERGENCY_STOP', 'confidence': 1.0, 'urgency': 5}
            
            return {'should_exit': False, 'reason': 'ERROR_NO_EXIT', 'confidence': 0.0, 'urgency': 0}
    
    def evaluate_open_positions(self) -> List[Position]:
        """Evaluate all open positions for exit conditions"""
        open_positions = self.position_manager.get_open_positions()
        closed_positions = []
        
        logger.info(f"🔍 Evaluating {len(open_positions)} open positions")
        
        for position in open_positions:
            try:
                # Get current market price
                market_data = self.ig_client.get_market_data(position.epic)
                if not market_data:
                    logger.warning(f"Could not get current price for {position.symbol}")
                    continue
                
                # Use bid for BUY positions, offer for SELL positions when exiting
                current_price = market_data['bid'] if position.action == 'BUY' else market_data['offer']
                
                # Evaluate exit conditions
                exit_decision = self.evaluate_exit_conditions(position, current_price)
                
                logger.debug(f"Exit evaluation for {position.symbol}: {exit_decision}")
                
                if exit_decision['should_exit']:
                    # Close the position
                    if self.position_manager.close_position(
                        position.position_id, 
                        current_price, 
                        exit_decision['reason']
                    ):
                        position.exit_price = current_price
                        position.exit_reason = exit_decision['reason']
                        closed_positions.append(position)
                        logger.info(f"✅ Closed position: {position.symbol} - {exit_decision['reason']}")
                    else:
                        logger.error(f"Failed to close position: {position.symbol}")
                
            except Exception as e:
                logger.error(f"Error evaluating position {position.symbol}: {e}")
        
        return closed_positions
    
    def run_trading_cycle(self) -> Dict:
        """Run a complete trading cycle"""
        logger.info("🎯 Starting paper trading cycle")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'new_trades': 0,
            'closed_trades': 0,
            'open_positions': 0,
            'account_balance': 0.0,
            'available_funds': 0.0,
            'errors': []
        }
        
        try:
            # Process new predictions
            logger.info("📊 Processing new predictions...")
            predictions = self.get_new_predictions()
            
            executed_trades = []
            for prediction in predictions:
                try:
                    trade = self.execute_paper_trade(prediction)
                    if trade:
                        executed_trades.append(trade)
                except Exception as e:
                    error_msg = f"Error processing prediction for {prediction.get('symbol', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            results['new_trades'] = len(executed_trades)
            logger.info(f"✅ Executed {len(executed_trades)} new paper trades")
            
            # Evaluate open positions
            logger.info("🔍 Evaluating open positions...")
            closed_trades = self.evaluate_open_positions()
            results['closed_trades'] = len(closed_trades)
            logger.info(f"✅ Closed {len(closed_trades)} positions")
            
            # Get account status
            balance = self.position_manager.get_account_balance()
            results['account_balance'] = balance.total_balance
            results['available_funds'] = balance.available_funds
            results['open_positions'] = self.position_manager.get_open_positions_count()
            
            # Log performance summary
            performance = self.position_manager.get_performance_summary()
            logger.info(f"📈 Performance Summary:")
            logger.info(f"   Total Trades: {performance['total_trades']}")
            logger.info(f"   Win Rate: {performance['win_rate']:.1f}%")
            logger.info(f"   Total P&L: ${performance['total_profit_loss']:.2f}")
            logger.info(f"   Account Balance: ${balance.total_balance:.2f}")
            logger.info(f"   Available Funds: ${balance.available_funds:.2f}")
            
        except Exception as e:
            error_msg = f"Error in trading cycle: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        logger.info("✅ Paper trading cycle completed")
        return results
    
    def get_account_info(self) -> Dict:
        """Get account information for compatibility with test systems"""
        try:
            balance = self.position_manager.get_account_balance()
            performance = self.position_manager.get_performance_summary()
            open_positions = self.position_manager.get_open_positions()
            
            return {
                'account_id': self.ig_client.account_id or 'Paper_Trading_Account',
                'account_type': 'paper_trading',
                'currency': 'AUD',
                'balance': {
                    'total': balance.total_balance,
                    'available': balance.available_funds,
                    'used': balance.used_funds
                },
                'positions': {
                    'open_count': len(open_positions),
                    'symbols': [p.symbol for p in open_positions]
                },
                'performance': {
                    'total_trades': performance.get('total_trades', 0),
                    'win_rate': performance.get('win_rate', 0.0),
                    'profit_loss': performance.get('total_profit_loss', 0.0)
                },
                'status': 'operational'
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {
                'account_id': 'error',
                'status': 'error',
                'error': str(e)
            }
    
    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        try:
            balance = self.position_manager.get_account_balance()
            performance = self.position_manager.get_performance_summary()
            open_positions = self.position_manager.get_open_positions()
            rate_limit = self.ig_client.get_rate_limit_status()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'account': {
                    'total_balance': balance.total_balance,
                    'available_funds': balance.available_funds,
                    'used_funds': balance.used_funds,
                    'unrealized_pnl': balance.unrealized_pnl,
                    'realized_pnl': balance.realized_pnl
                },
                'positions': {
                    'open_count': len(open_positions),
                    'open_symbols': [p.symbol for p in open_positions]
                },
                'performance': performance,
                'api_status': {
                    'authenticated': self.ig_client.access_token is not None,
                    'account_id': self.ig_client.account_id,
                    'token_expires': self.ig_client.token_expires_at.isoformat() if self.ig_client.token_expires_at else None,
                    'rate_limit': rate_limit
                },
                'exit_strategy': {
                    'available': self.exit_strategy is not None,
                    'type': 'Phase4' if self.exit_strategy else 'Simple'
                }
            }
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
