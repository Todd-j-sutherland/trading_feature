#!/usr/bin/env python3
"""
Prediction Signal Handler - Integration between ML predictions and paper trading
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import create_database, get_session, init_default_account
from trading.engine import PaperTradingEngine, StrategyInterface, TradeResult
from config import TRADING_CONFIG

class PredictionSignalHandler:
    """Handles incoming prediction signals and converts them to paper trades"""
    
    def __init__(self, paper_trading_db_path="paper_trading.db", predictions_db_path="../predictions.db"):
        self.paper_trading_db = paper_trading_db_path
        self.predictions_db = predictions_db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize paper trading components
        self.engine = create_database(f"sqlite:///{self.paper_trading_db}")
        self.session = get_session(self.engine)
        self.account = init_default_account(self.session, TRADING_CONFIG['initial_balance'])
        
        # Initialize trading engine
        self.trading_engine = PaperTradingEngine(self.session, self.account.id)
        self.strategy_interface = StrategyInterface(self.trading_engine)
        
        # Position sizing configuration
        self.position_sizing = {
            'method': 'fixed_dollar',  # 'fixed_dollar', 'percent_portfolio', 'risk_based'
            'base_amount': 10000,      # $10k per position
            'max_portfolio_pct': 0.15, # Max 15% per position
            'confidence_multiplier': True  # Scale position by confidence
        }
        
        # Signal mapping configuration
        self.signal_mapping = {
            'BUY': {'action': 'BUY', 'confidence_threshold': 0.6},
            'SELL': {'action': 'SELL', 'confidence_threshold': 0.0},  # Always execute sells
            'HOLD': {'action': None, 'confidence_threshold': 0.0}     # No action for holds
        }
        
        self.logger.info("PredictionSignalHandler initialized")
    
    def calculate_position_size(self, symbol: str, signal_strength: float, confidence: float) -> int:
        """Calculate position size based on signal and portfolio"""
        try:
            # Get current portfolio value
            portfolio_summary = self.trading_engine.get_portfolio_summary()
            portfolio_value = portfolio_summary.get('account', {}).get('portfolio_value', 0)
            
            # Get current price
            current_price = self.trading_engine.get_current_price(symbol)
            if not current_price or current_price <= 0:
                self.logger.warning(f"Could not get price for {symbol}")
                return 0
            
            # Calculate base position value
            if self.position_sizing['method'] == 'fixed_dollar':
                base_value = self.position_sizing['base_amount']
            elif self.position_sizing['method'] == 'percent_portfolio':
                base_value = portfolio_value * self.position_sizing['max_portfolio_pct']
            else:  # risk_based
                base_value = min(
                    self.position_sizing['base_amount'],
                    portfolio_value * self.position_sizing['max_portfolio_pct']
                )
            
            # Apply confidence multiplier
            if self.position_sizing['confidence_multiplier']:
                # Scale between 0.5x and 1.5x based on confidence
                confidence_factor = 0.5 + (confidence * 1.0)
                base_value *= confidence_factor
            
            # Calculate shares (round down to whole shares)
            shares = int(base_value / current_price)
            
            # Ensure minimum viable position
            if shares < 10:
                shares = 10 if base_value >= (current_price * 10) else 0
            
            return shares
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0
    
    def process_prediction_signal(self, prediction_data: Dict) -> TradeResult:
        """Process a prediction signal and execute trade if appropriate"""
        try:
            # Extract prediction data
            symbol = prediction_data.get('symbol', '').upper()
            prediction = prediction_data.get('prediction', '').upper()
            confidence = prediction_data.get('confidence', 0.0)
            reasoning = prediction_data.get('reasoning', '')
            timestamp = prediction_data.get('timestamp', datetime.now())
            signal_strength = prediction_data.get('signal_strength', 0.5)
            
            self.logger.info(f"Processing signal: {symbol} {prediction} (confidence: {confidence:.2f})")
            
            # Validate signal
            if not symbol or prediction not in self.signal_mapping:
                return TradeResult(success=False, message=f"Invalid signal: {symbol} {prediction}")
            
            signal_config = self.signal_mapping[prediction]
            
            # Check confidence threshold
            if confidence < signal_config['confidence_threshold']:
                return TradeResult(
                    success=False, 
                    message=f"Confidence {confidence:.2f} below threshold {signal_config['confidence_threshold']}"
                )
            
            # No action for HOLD signals
            if signal_config['action'] is None:
                return TradeResult(success=True, message=f"HOLD signal processed - no action taken")
            
            action = signal_config['action']
            
            # Handle BUY signals
            if action == 'BUY':
                quantity = self.calculate_position_size(symbol, signal_strength, confidence)
                if quantity <= 0:
                    return TradeResult(success=False, message="Could not calculate valid position size")
                
                result = self.trading_engine.execute_market_buy(
                    symbol=symbol,
                    quantity=quantity,
                    strategy_source="ML_Prediction_System",
                    confidence=confidence,
                    notes=f"ML Prediction: {reasoning}"
                )
                
            # Handle SELL signals
            elif action == 'SELL':
                # Check if we have a position to sell
                portfolio_summary = self.trading_engine.get_portfolio_summary()
                positions = portfolio_summary.get('positions', [])
                
                current_position = None
                for pos in positions:
                    if pos['symbol'] == symbol:
                        current_position = pos
                        break
                
                if not current_position or current_position['quantity'] <= 0:
                    return TradeResult(
                        success=False, 
                        message=f"No position to sell for {symbol}"
                    )
                
                # Sell entire position (could be modified to partial sells)
                quantity = current_position['quantity']
                
                result = self.trading_engine.execute_market_sell(
                    symbol=symbol,
                    quantity=quantity,
                    strategy_source="ML_Prediction_System",
                    confidence=confidence,
                    notes=f"ML Prediction: {reasoning}"
                )
            
            # Log the result
            if result.success:
                self.logger.info(f"Trade executed successfully: {result.message}")
            else:
                self.logger.warning(f"Trade failed: {result.message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing prediction signal: {e}")
            return TradeResult(success=False, message=f"Processing error: {str(e)}")
    
    def monitor_predictions_database(self, check_interval_minutes: int = 5):
        """Monitor the predictions database for new predictions"""
        self.logger.info(f"Starting prediction monitoring (checking every {check_interval_minutes} minutes)")
        
        last_check = datetime.now() - timedelta(days=1)  # Start from yesterday
        
        while True:
            try:
                # Connect to predictions database
                conn = sqlite3.connect(self.predictions_db)
                cursor = conn.cursor()
                
                # Query for new predictions since last check
                cursor.execute('''
                    SELECT 
                        p.prediction_id,
                        p.symbol,
                        p.prediction,
                        p.confidence,
                        p.timestamp,
                        p.signal_strength,
                        p.reasoning
                    FROM predictions p
                    WHERE p.timestamp > ?
                    ORDER BY p.timestamp DESC
                ''', (last_check,))
                
                new_predictions = cursor.fetchall()
                
                if new_predictions:
                    self.logger.info(f"Found {len(new_predictions)} new predictions")
                    
                    for pred in new_predictions:
                        prediction_data = {
                            'prediction_id': pred[0],
                            'symbol': pred[1],
                            'prediction': pred[2],
                            'confidence': pred[3],
                            'timestamp': pred[4],
                            'signal_strength': pred[5] if pred[5] else 0.5,
                            'reasoning': pred[6] if pred[6] else 'ML Model Prediction'
                        }
                        
                        # Process the signal
                        result = self.process_prediction_signal(prediction_data)
                        
                        # Log result to console/file
                        if result.success:
                            print(f"✅ {prediction_data['symbol']}: {result.message}")
                        else:
                            print(f"❌ {prediction_data['symbol']}: {result.message}")
                
                # Update last check time
                last_check = datetime.now()
                conn.close()
                
                # Wait before next check
                import time
                time.sleep(check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                import time
                time.sleep(60)  # Wait 1 minute before retrying
    
    def process_historical_predictions(self, days_back: int = 7):
        """Process historical predictions for backtesting"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            conn = sqlite3.connect(self.predictions_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    p.prediction_id,
                    p.symbol,
                    p.prediction,
                    p.confidence,
                    p.timestamp,
                    p.signal_strength,
                    p.reasoning
                FROM predictions p
                WHERE p.timestamp >= ?
                ORDER BY p.timestamp ASC
            ''', (cutoff_date,))
            
            predictions = cursor.fetchall()
            conn.close()
            
            results = []
            
            print(f"Processing {len(predictions)} historical predictions...")
            
            for pred in predictions:
                prediction_data = {
                    'prediction_id': pred[0],
                    'symbol': pred[1],
                    'prediction': pred[2],
                    'confidence': pred[3],
                    'timestamp': pred[4],
                    'signal_strength': pred[5] if pred[5] else 0.5,
                    'reasoning': pred[6] if pred[6] else f'Historical ML Prediction {pred[0]}'
                }
                
                result = self.process_prediction_signal(prediction_data)
                results.append({
                    'prediction': prediction_data,
                    'result': result
                })
                
                if result.success:
                    print(f"✅ {prediction_data['timestamp']}: {prediction_data['symbol']} {prediction_data['prediction']} - {result.message}")
                else:
                    print(f"❌ {prediction_data['timestamp']}: {prediction_data['symbol']} {prediction_data['prediction']} - {result.message}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing historical predictions: {e}")
            return []
    
    def get_trading_performance_summary(self) -> Dict:
        """Get summary of trading performance from prediction signals"""
        try:
            portfolio_summary = self.trading_engine.get_portfolio_summary()
            
            # Get ML strategy specific trades
            ml_trades = self.session.query(Trade).filter_by(
                account_id=self.trading_engine.account_id,
                strategy_source="ML_Prediction_System"
            ).all()
            
            if not ml_trades:
                return {'message': 'No ML prediction trades found'}
            
            total_trades = len(ml_trades)
            winning_trades = len([t for t in ml_trades if t.pnl and t.pnl > 0])
            total_pnl = sum(t.pnl for t in ml_trades if t.pnl)
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_pnl_per_trade': avg_pnl,
                'portfolio_value': portfolio_summary.get('account', {}).get('portfolio_value', 0),
                'total_return_pct': portfolio_summary.get('account', {}).get('total_pnl_pct', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}

# Standalone functions for integration
def send_prediction_signal(symbol: str, prediction: str, confidence: float, reasoning: str = "") -> TradeResult:
    """Simple function to send a prediction signal to paper trader"""
    handler = PredictionSignalHandler()
    
    signal_data = {
        'symbol': symbol,
        'prediction': prediction,
        'confidence': confidence,
        'reasoning': reasoning,
        'timestamp': datetime.now(),
        'signal_strength': confidence  # Use confidence as signal strength
    }
    
    return handler.process_prediction_signal(signal_data)

def start_live_monitoring():
    """Start live monitoring of predictions database"""
    handler = PredictionSignalHandler()
    handler.monitor_predictions_database(check_interval_minutes=1)  # Check every minute

if __name__ == "__main__":
    # Example usage
    handler = PredictionSignalHandler()
    
    # Test with a sample signal
    test_signal = {
        'symbol': 'CBA.AX',
        'prediction': 'BUY',
        'confidence': 0.85,
        'reasoning': 'Strong technical indicators and positive sentiment',
        'timestamp': datetime.now(),
        'signal_strength': 0.8
    }
    
    result = handler.process_prediction_signal(test_signal)
    print(f"Test result: {result.message}")
    
    # Show performance summary
    performance = handler.get_trading_performance_summary()
    print(f"Performance summary: {performance}")
