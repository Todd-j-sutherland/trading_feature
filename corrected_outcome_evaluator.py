#!/usr/bin/env python3
"""
Corrected Outcome Evaluator - Fixed Pricing Logic
Addresses the pricing duplication bug by using proper timestamp-based pricing.
"""

import sqlite3
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/corrected_outcome_evaluator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CorrectedOutcomeEvaluator:
    """Fixed evaluation system with proper timestamp-based pricing"""
    
    def __init__(self, db_path: str = 'predictions.db'):
        self.db_path = db_path
        
    def get_db_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        conn.row_factory = sqlite3.Row
        return conn
        
    def get_precise_entry_price(self, symbol: str, prediction_time: datetime) -> float:
        """
        Get precise entry price at prediction timestamp using 1-minute intervals
        
        Args:
            symbol: Stock symbol (e.g., 'MQG.AX')
            prediction_time: Exact timestamp when prediction was made
            
        Returns:
            Precise entry price at prediction time
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get 1-minute data for the prediction day
            start_date = prediction_time.date()
            end_date = (prediction_time + timedelta(days=1)).date()
            
            # Try 1-minute interval first for precision
            hist_1m = ticker.history(start=start_date, end=end_date, interval='1m')
            
            if not hist_1m.empty:
                # Find the closest minute to prediction time
                prediction_hour_minute = prediction_time.strftime('%H:%M')
                
                # Convert prediction time to market timezone and find closest price
                target_time = prediction_time.replace(second=0, microsecond=0)
                
                # Find closest available price point
                closest_price = None
                min_diff = float('inf')
                
                for idx, row in hist_1m.iterrows():
                    time_diff = abs((idx.to_pydatetime() - target_time).total_seconds())
                    if time_diff < min_diff:
                        min_diff = time_diff
                        closest_price = float(row['Close'])
                
                if closest_price is not None:
                    logger.info(f"Found precise entry price for {symbol} at {prediction_time}: ${closest_price} (±{min_diff/60:.1f}min)")
                    return closest_price
            
            # Fallback to hourly data if 1-minute not available
            hist_1h = ticker.history(start=start_date, end=end_date, interval='1h')
            if not hist_1h.empty:
                # Use opening price of the closest hour
                entry_price = float(hist_1h['Open'].iloc[0])
                logger.info(f"Using hourly fallback entry price for {symbol}: ${entry_price}")
                return entry_price
                
            # Final fallback to daily opening price
            hist_daily = ticker.history(start=start_date, end=end_date)
            if not hist_daily.empty:
                entry_price = float(hist_daily['Open'].iloc[0])
                logger.info(f"Using daily opening price fallback for {symbol}: ${entry_price}")
                return entry_price
                
        except Exception as e:
            logger.error(f"Error getting precise entry price for {symbol}: {e}")
            
        return 0.0
    
    def get_exit_price_at_evaluation(self, symbol: str, evaluation_time: datetime) -> float:
        """
        Get exit price at evaluation time (4+ hours after prediction)
        
        Args:
            symbol: Stock symbol
            evaluation_time: When the evaluation is being performed
            
        Returns:
            Exit price at evaluation time
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get price data for evaluation day
            eval_date = evaluation_time.date()
            
            # Try to get hourly data first for precision
            hist_1h = ticker.history(start=eval_date, end=eval_date + timedelta(days=1), interval='1h')
            
            if not hist_1h.empty:
                # Find the closest hour to evaluation time
                target_time = evaluation_time.replace(minute=0, second=0, microsecond=0)
                
                closest_price = None
                min_diff = float('inf')
                
                for idx, row in hist_1h.iterrows():
                    time_diff = abs((idx.to_pydatetime() - target_time).total_seconds())
                    if time_diff < min_diff:
                        min_diff = time_diff
                        closest_price = float(row['Close'])
                
                if closest_price is not None:
                    logger.info(f"Found precise exit price for {symbol} at {evaluation_time}: ${closest_price} (±{min_diff/60:.1f}min)")
                    return closest_price
            
            # Fallback to daily close price
            hist_daily = ticker.history(start=eval_date, end=eval_date + timedelta(days=1))
            if not hist_daily.empty:
                exit_price = float(hist_daily['Close'].iloc[0])
                logger.info(f"Using daily close price for {symbol}: ${exit_price}")
                return exit_price
                
        except Exception as e:
            logger.error(f"Error getting exit price for {symbol}: {e}")
            
        return 0.0
    
    def get_pending_predictions(self, hours_ago: int = 4) -> List[Dict]:
        """Get predictions that need evaluation (4+ hours old)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE o.prediction_id IS NULL
                AND datetime(substr(p.prediction_timestamp, 1, 19)) < datetime('now', '-{} hours')
                AND datetime(substr(p.prediction_timestamp, 1, 19)) > datetime('now', '-72 hours')
                ORDER BY p.prediction_timestamp DESC
                LIMIT 50
            """.format(hours_ago))
            
            results = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting pending predictions: {e}")
            return []
    
    def evaluate_prediction_with_correct_pricing(self, prediction: Dict) -> Optional[Dict]:
        """
        Evaluate a prediction with corrected timestamp-based pricing logic
        
        Args:
            prediction: Prediction data from database
            
        Returns:
            Outcome data with accurate entry/exit prices
        """
        try:
            symbol = prediction['symbol']
            prediction_timestamp = prediction['prediction_timestamp']
            predicted_action = prediction['predicted_action']
            
            # Parse prediction timestamp
            if isinstance(prediction_timestamp, str):
                prediction_time = datetime.fromisoformat(prediction_timestamp.replace('Z', '+00:00'))
                if prediction_time.tzinfo:
                    prediction_time = prediction_time.replace(tzinfo=None)
            else:
                prediction_time = prediction_timestamp
            
            logger.info(f"Evaluating {symbol} prediction from {prediction_time}")
            
            # Get PRECISE entry price at prediction timestamp (1-minute interval)
            stored_entry_price = prediction.get('entry_price', 0.0) or 0.0
            
            if stored_entry_price > 0:
                # Use the stored entry price if available
                entry_price = stored_entry_price
                logger.info(f"Using stored entry price for {symbol}: ${entry_price}")
            else:
                # Get precise entry price at prediction time
                entry_price = self.get_precise_entry_price(symbol, prediction_time)
                if entry_price == 0.0:
                    logger.warning(f"Could not determine entry price for {symbol}")
                    return None
            
            # Get exit price at evaluation time (NOW - 4+ hours after prediction)
            evaluation_time = datetime.now()
            exit_price = self.get_exit_price_at_evaluation(symbol, evaluation_time)
            
            if exit_price == 0.0:
                logger.warning(f"Could not determine exit price for {symbol}")
                return None
            
            # Calculate accurate returns
            if entry_price > 0:
                actual_return = ((exit_price - entry_price) / entry_price) * 100
            else:
                actual_return = 0.0
            
            actual_direction = 1 if exit_price > entry_price else 0
            
            # Determine success based on predicted action
            if predicted_action == 'BUY':
                success = actual_return > 0
            elif predicted_action == 'SELL':
                success = actual_return < 0
            else:  # HOLD
                success = abs(actual_return) < 2.0  # Consider HOLD successful if <2% movement
            
            # Create outcome record
            outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': round(actual_return, 4),
                'actual_direction': actual_direction,
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'evaluation_timestamp': evaluation_time.isoformat(),
                'outcome_details': json.dumps({
                    'predicted_action': predicted_action,
                    'success': success,
                    'price_change': round(exit_price - entry_price, 4),
                    'price_change_pct': round(actual_return, 2),
                    'evaluation_method': 'corrected_timestamp_pricing',
                    'entry_method': 'stored_price' if stored_entry_price > 0 else 'precise_timestamp',
                    'exit_method': 'evaluation_time_price'
                }),
                'performance_metrics': json.dumps({
                    'confidence_accuracy': round(float(prediction.get('action_confidence', 0)), 4),
                    'prediction_success': success,
                    'return_magnitude': round(abs(exit_price - entry_price), 4),
                    'market_context': prediction.get('market_context', 'UNKNOWN'),
                    'evaluation_accuracy_score': round(1.0 if success else 0.0, 2)
                })
            }
            
            logger.info(f"✅ {symbol}: Entry ${entry_price} → Exit ${exit_price} = {actual_return:+.2f}% ({'🟢 Win' if success else '🔴 Loss'})")
            
            return outcome
            
        except Exception as e:
            logger.error(f"Error evaluating prediction: {e}")
            return None
    
    def save_outcome(self, outcome: Dict) -> bool:
        """Save corrected outcome to database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO outcomes (
                    outcome_id, prediction_id, actual_return, actual_direction,
                    entry_price, exit_price, evaluation_timestamp,
                    outcome_details, performance_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome['outcome_id'],
                outcome['prediction_id'],
                outcome['actual_return'],
                outcome['actual_direction'],
                outcome['entry_price'],
                outcome['exit_price'],
                outcome['evaluation_timestamp'],
                outcome.get('outcome_details', '{}'),
                outcome.get('performance_metrics', '{}')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving outcome: {e}")
            return False
    
    def run_corrected_evaluation(self):
        """Run evaluation with corrected pricing logic"""
        logger.info("🔧 Starting CORRECTED outcome evaluation...")
        
        pending = self.get_pending_predictions(hours_ago=4)
        logger.info(f"Found {len(pending)} predictions to evaluate")
        
        evaluated_count = 0
        for prediction in pending:
            outcome = self.evaluate_prediction_with_correct_pricing(prediction)
            if outcome and self.save_outcome(outcome):
                evaluated_count += 1
            time.sleep(0.1)  # Rate limiting
        
        logger.info(f"✅ Completed corrected evaluation: {evaluated_count}/{len(pending)} predictions processed")
        return evaluated_count

if __name__ == "__main__":
    evaluator = CorrectedOutcomeEvaluator()
    evaluator.run_corrected_evaluation()
