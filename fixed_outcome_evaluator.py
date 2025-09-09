#!/usr/bin/env python3
"""
Fixed Outcome Evaluator for Trading System
Addresses database locking and NULL constraint issues
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
        logging.FileHandler('/root/test/logs/evaluation_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedOutcomeEvaluator:
    """Fixed version of the outcome evaluator with proper error handling"""
    
    def __init__(self, db_path: str = "/root/test/data/trading_predictions.db"):
        self.db_path = db_path
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with WAL mode and timeouts"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')  # 30 second timeout
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
        
    def get_pending_predictions(self, hours_ago: int = 4) -> List[Dict]:
        """Get predictions that need evaluation"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Find predictions older than specified hours that haven't been evaluated
            cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE o.prediction_id IS NULL
                AND p.prediction_timestamp < datetime('now', '-{} hours')
                AND p.prediction_timestamp > datetime('now', '-72 hours')
                ORDER BY p.prediction_timestamp DESC
                LIMIT 50
            """.format(hours_ago))
            
            results = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            predictions = []
            for row in results:
                predictions.append({
                    'prediction_id': row['prediction_id'],
                    'symbol': row['symbol'],
                    'prediction_timestamp': row['prediction_timestamp'],
                    'predicted_action': row['predicted_action'],
                    'action_confidence': row['action_confidence'],
                    'entry_price': row['entry_price'] or 0.0
                })
            
            logger.info(f"Found {len(predictions)} predictions needing evaluation")
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting pending predictions: {e}")
            return []
    
    def fetch_current_price(self, symbol: str, prediction_time: datetime) -> Optional[float]:
        """Fetch current price for evaluation"""
        try:
            # Try yfinance for current price
            ticker = yf.Ticker(symbol)
            
            # Get recent data
            end_time = datetime.now()
            start_time = prediction_time.date()
            
            hist = ticker.history(start=start_time, end=end_time, interval='1h')
            
            if len(hist) > 0:
                # Get the most recent close price
                current_price = float(hist['Close'].iloc[-1])
                logger.debug(f"Fetched price for {symbol}: ${current_price}")
                return current_price
            else:
                logger.warning(f"No price data available for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def calculate_outcome(self, prediction: Dict) -> Optional[Dict]:
        """Calculate outcome for a prediction"""
        try:
            symbol = prediction['symbol']
            prediction_time = datetime.fromisoformat(prediction['prediction_timestamp'])
            entry_price = prediction.get('entry_price', 0.0)
            
            # If no entry price recorded, try to get it from historical data
            if entry_price == 0.0:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=prediction_time.date(), 
                                    end=(prediction_time + timedelta(days=1)).date(), 
                                    interval='1h')
                if len(hist) > 0:
                    entry_price = float(hist['Close'].iloc[0])
                else:
                    logger.warning(f"No entry price available for {symbol}")
                    return None
            
            # Get current price
            current_price = self.fetch_current_price(symbol, prediction_time)
            if current_price is None:
                return None
            
            # Calculate return
            if entry_price > 0:
                actual_return = ((current_price - entry_price) / entry_price) * 100
            else:
                actual_return = 0.0
            
            # Determine direction (1 = up, 0 = down)
            actual_direction = 1 if current_price > entry_price else 0
            
            # Determine if prediction was successful
            predicted_action = prediction['predicted_action'].upper()
            
            success = False
            if predicted_action == 'BUY' and actual_direction == 1:
                success = True
            elif predicted_action == 'SELL' and actual_direction == 0:
                success = True
            elif predicted_action == 'HOLD' and abs(actual_return) < 1.0:
                success = True
            
            outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': round(actual_return, 4),
                'actual_direction': actual_direction,
                'entry_price': round(entry_price, 4),
                'exit_price': round(current_price, 4),
                'evaluation_timestamp': datetime.now().isoformat(),
                'outcome_details': json.dumps({
                    'predicted_action': predicted_action,
                    'success': success,
                    'price_change': round(current_price - entry_price, 4),
                    'price_change_pct': round(actual_return, 2)
                }),
                'performance_metrics': json.dumps({
                    'confidence': prediction.get('action_confidence', 0.0),
                    'success': success,
                    'return': actual_return
                })
            }
            
            logger.debug(f"Calculated outcome for {symbol}: {actual_return:.2f}% return")
            return outcome
            
        except Exception as e:
            logger.error(f"Error calculating outcome for {prediction.get('prediction_id', 'unknown')}: {e}")
            return None
    
    def store_outcome(self, outcome: Dict) -> bool:
        """Store outcome with retry logic"""
        for attempt in range(self.max_retries):
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Verify all required fields are present
                required_fields = ['outcome_id', 'prediction_id', 'actual_return', 
                                 'actual_direction', 'entry_price', 'exit_price', 
                                 'evaluation_timestamp']
                
                for field in required_fields:
                    if field not in outcome or outcome[field] is None:
                        logger.error(f"Missing required field: {field}")
                        return False
                
                # Insert the outcome
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
                
                logger.debug(f"Successfully stored outcome for prediction {outcome['prediction_id']}")
                return True
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    logger.warning(f"Database locked, retry {attempt + 1}/{self.max_retries}")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"Database error storing outcome: {e}")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error storing outcome: {e}")
                return False
        
        return False
    
    def evaluate_pending_predictions(self) -> int:
        """Main evaluation function"""
        logger.info("🔍 Starting outcome evaluation...")
        
        pending_predictions = self.get_pending_predictions()
        
        if not pending_predictions:
            logger.info("No pending predictions to evaluate")
            return 0
        
        evaluated_count = 0
        failed_count = 0
        
        for prediction in pending_predictions:
            try:
                outcome = self.calculate_outcome(prediction)
                
                if outcome is None:
                    logger.warning(f"Could not calculate outcome for {prediction['prediction_id']}")
                    failed_count += 1
                    continue
                
                if self.store_outcome(outcome):
                    evaluated_count += 1
                    logger.info(f"✅ Evaluated {prediction['symbol']}: {outcome['actual_return']:.2f}% return")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to store outcome for {prediction['prediction_id']}")
                
                # Small delay to prevent overwhelming the database
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error evaluating prediction {prediction['prediction_id']}: {e}")
                failed_count += 1
        
        logger.info(f"📊 Evaluation complete: {evaluated_count} successful, {failed_count} failed")
        return evaluated_count

def main():
    """Main execution function"""
    evaluator = FixedOutcomeEvaluator()
    
    try:
        evaluated_count = evaluator.evaluate_pending_predictions()
        print(f"Evaluated {evaluated_count} predictions")
        
    except Exception as e:
        logger.error(f"Fatal error in evaluation: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
