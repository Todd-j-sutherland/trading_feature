#!/usr/bin/env python3
"""
Fixed Outcome Evaluator - Corrects Bad Entry Prices
Addresses the issue where old predictions have incorrect entry prices
"""

import sys
import os
import logging
import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import uuid
import time
from typing import Dict, List, Optional

# Add the current directory to Python path
sys.path.insert(0, '/root/test')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/test/logs/fixed_outcome_evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CorrectedOutcomeEvaluator:
    """Outcome evaluator that corrects bad entry prices"""
    
    def __init__(self, db_path="/root/test/data/trading_predictions.db"):
        self.db_path = db_path
        self.max_retries = 3
        self.retry_delay = 2
        
        # Known good price ranges for validation
        self.price_ranges = {
            'CSL.AX': (180, 250),    # CSL trades ~$200-220
            'CBA.AX': (150, 180),    # CBA trades ~$160-170  
            'WBC.AX': (35, 45),      # WBC trades ~$37-40
            'ANZ.AX': (30, 40),      # ANZ trades ~$32-35
            'NAB.AX': (40, 50),      # NAB trades ~$42-45
            'MQG.AX': (200, 250),    # MQG trades ~$220-230
            'QBE.AX': (15, 25),      # QBE trades ~$18-20
            'SUN.AX': (12, 18),      # SUN trades ~$14-16
            'TLS.AX': (3, 6),        # TLS trades ~$4-5
            'BHP.AX': (35, 50),      # BHP trades ~$40-45
            'RIO.AX': (110, 130),    # RIO trades ~$115-125
        }
        
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        conn.row_factory = sqlite3.Row
        return conn
    
    def is_entry_price_valid(self, symbol: str, entry_price: float) -> bool:
        """Check if entry price is within reasonable range for the symbol"""
        if symbol not in self.price_ranges:
            return True  # Unknown symbol, assume valid
            
        min_price, max_price = self.price_ranges[symbol]
        return min_price <= entry_price <= max_price
    
    def get_correct_entry_price(self, symbol: str, prediction_time: datetime) -> Optional[float]:
        """Get correct entry price from market data at prediction time"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get data for the prediction day
            start_date = prediction_time.date()
            end_date = start_date + timedelta(days=1)
            
            hist = ticker.history(start=start_date, end=end_date, interval='1h')
            
            if len(hist) == 0:
                # Try a wider range if no data for that specific day
                start_date = prediction_time.date() - timedelta(days=2)
                end_date = prediction_time.date() + timedelta(days=1)
                hist = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(hist) > 0:
                # Use the closest available price
                price = float(hist['Close'].iloc[0])
                
                # Validate the price
                if self.is_entry_price_valid(symbol, price):
                    return price
                else:
                    logger.warning(f"Invalid historical price for {symbol}: ${price}")
                    return None
            else:
                logger.warning(f"No historical data for {symbol} at {prediction_time}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical price for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='2d', interval='1h')
            
            if len(hist) > 0:
                price = float(hist['Close'].iloc[-1])
                
                # Validate the price
                if self.is_entry_price_valid(symbol, price):
                    return price
                else:
                    logger.warning(f"Invalid current price for {symbol}: ${price}")
                    return None
            else:
                logger.warning(f"No current data for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_pending_predictions(self) -> List[Dict]:
        """Get predictions that need corrected evaluation"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get predictions that either:
            # 1. Haven't been evaluated yet, OR
            # 2. Have unrealistic returns (indicating bad entry prices)
            cursor.execute("""
                SELECT DISTINCT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price,
                       o.actual_return
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE (
                    -- Never evaluated
                    o.prediction_id IS NULL 
                    OR 
                    -- Has unrealistic return (bad entry price)
                    (o.actual_return > 50 OR o.actual_return < -50)
                )
                AND p.prediction_timestamp > datetime('now', '-7 days')
                AND p.prediction_timestamp < datetime('now', '-4 hours')
                ORDER BY p.prediction_timestamp DESC
                LIMIT 100
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            predictions = []
            for row in results:
                predictions.append({
                    'prediction_id': row['prediction_id'],
                    'symbol': row['symbol'],
                    'prediction_timestamp': row['prediction_timestamp'],
                    'predicted_action': row['predicted_action'],
                    'action_confidence': row['action_confidence'],
                    'stored_entry_price': row['entry_price'],
                    'existing_return': row['actual_return']
                })
            
            logger.info(f"Found {len(predictions)} predictions needing corrected evaluation")
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting pending predictions: {e}")
            return []
    
    def calculate_corrected_outcome(self, prediction: Dict) -> Optional[Dict]:
        """Calculate outcome with corrected entry price"""
        try:
            symbol = prediction['symbol']
            prediction_time = datetime.fromisoformat(prediction['prediction_timestamp'])
            stored_entry_price = prediction['stored_entry_price']
            
            # Check if stored entry price is valid
            entry_price = stored_entry_price
            price_corrected = False
            
            if not self.is_entry_price_valid(symbol, stored_entry_price):
                logger.info(f"Correcting invalid entry price for {symbol}: ${stored_entry_price}")
                corrected_price = self.get_correct_entry_price(symbol, prediction_time)
                
                if corrected_price is not None:
                    entry_price = corrected_price
                    price_corrected = True
                    logger.info(f"Corrected {symbol} entry price: ${stored_entry_price} → ${entry_price}")
                else:
                    logger.warning(f"Could not correct entry price for {symbol}, skipping")
                    return None
            
            # Get current price for evaluation
            current_price = self.get_current_price(symbol)
            if current_price is None:
                return None
            
            # Calculate return with corrected entry price
            actual_return = ((current_price - entry_price) / entry_price) * 100
            actual_direction = 1 if current_price > entry_price else 0
            
            # Determine if prediction was successful
            predicted_action = prediction['predicted_action'].upper()
            success = False
            
            if predicted_action == 'BUY' and actual_direction == 1:
                success = True
            elif predicted_action == 'SELL' and actual_direction == 0:
                success = True  
            elif predicted_action == 'HOLD' and abs(actual_return) < 2.0:
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
                    'price_corrected': price_corrected,
                    'original_entry_price': stored_entry_price,
                    'corrected_entry_price': entry_price,
                    'price_change': round(current_price - entry_price, 4),
                    'price_change_pct': round(actual_return, 2)
                }),
                'performance_metrics': json.dumps({
                    'confidence': prediction.get('action_confidence', 0.0),
                    'success': success,
                    'return': actual_return,
                    'evaluation_method': 'corrected_entry_price'
                })
            }
            
            # Validate the outcome
            if abs(actual_return) > 20:  # Still unrealistic
                logger.warning(f"Still unrealistic return for {symbol}: {actual_return:.2f}%")
                return None
            
            return outcome
            
        except Exception as e:
            logger.error(f"Error calculating corrected outcome: {e}")
            return None
    
    def store_corrected_outcome(self, outcome: Dict) -> bool:
        """Store or update the corrected outcome"""
        for attempt in range(self.max_retries):
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Delete existing outcome if it exists
                cursor.execute("DELETE FROM outcomes WHERE prediction_id = ?", 
                             (outcome['prediction_id'],))
                
                # Insert corrected outcome
                cursor.execute("""
                    INSERT INTO outcomes (
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
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"Database error: {e}")
                    return False
            except Exception as e:
                logger.error(f"Error storing outcome: {e}")
                return False
        
        return False
    
    def run_corrected_evaluation(self):
        """Main evaluation function with entry price correction"""
        logger.info("🔧 Starting Corrected Outcome Evaluation...")
        
        predictions = self.get_pending_predictions()
        
        if not predictions:
            logger.info("No predictions need corrected evaluation")
            return 0
        
        corrected_count = 0
        failed_count = 0
        price_corrections = 0
        
        for prediction in predictions:
            try:
                # Show existing problematic return if any
                if prediction.get('existing_return'):
                    logger.info(f"Correcting {prediction['symbol']} with return {prediction['existing_return']:.1f}%")
                
                outcome = self.calculate_corrected_outcome(prediction)
                
                if outcome is None:
                    failed_count += 1
                    continue
                
                # Check if price was corrected
                outcome_details = json.loads(outcome.get('outcome_details', '{}'))
                if outcome_details.get('price_corrected', False):
                    price_corrections += 1
                
                if self.store_corrected_outcome(outcome):
                    corrected_count += 1
                    logger.info(f"✅ Corrected {prediction['symbol']}: {outcome['actual_return']:.2f}% return")
                else:
                    failed_count += 1
                
                # Prevent overwhelming
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing {prediction['prediction_id']}: {e}")
                failed_count += 1
        
        logger.info(f"📊 Corrected Evaluation Summary:")
        logger.info(f"   Predictions Processed: {len(predictions)}")
        logger.info(f"   Successfully Corrected: {corrected_count}")
        logger.info(f"   Failed: {failed_count}")
        logger.info(f"   Entry Prices Corrected: {price_corrections}")
        
        return corrected_count

def main():
    """Main execution"""
    evaluator = CorrectedOutcomeEvaluator()
    
    try:
        corrected_count = evaluator.run_corrected_evaluation()
        print(f"✅ Corrected {corrected_count} prediction outcomes")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
