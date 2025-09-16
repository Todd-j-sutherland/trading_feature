#!/usr/bin/env python3
"""
Fixed Dry Run Outcome Evaluator for Trading System
Shows what the outcomes would be without updating the database
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
        logging.FileHandler('/root/test/logs/dry_run_evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedDryRunOutcomeEvaluator:
    """Fixed dry run version of the outcome evaluator - doesn't update database"""
    
    def __init__(self, db_path: str = "/root/test/data/trading_predictions.db"):
        self.db_path = db_path
        self.results = []
        
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with WAL mode and timeouts"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')  # 30 second timeout
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
        
    def get_todays_predictions(self) -> List[Dict]:
        """Get today's predictions that need evaluation"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get today's predictions with outcomes check
            cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price,
                       p.model_version, o.outcome_id
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE date(substr(p.prediction_timestamp, 1, 10)) = date('now')
                ORDER BY p.prediction_timestamp DESC
            """)
            
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
                    'entry_price': row['entry_price'] or 0.0,
                    'model_version': row.get('model_version', 'unknown'),
                    'has_outcome': row['outcome_id'] is not None
                })
            
            logger.info(f"Found {len(predictions)} predictions from today")
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting today's predictions: {e}")
            return []
    
    def fetch_current_price(self, symbol: str, prediction_time: datetime) -> Optional[float]:
        """Fetch current price for evaluation using minute data"""
        try:
            # Try yfinance for current price
            ticker = yf.Ticker(symbol)
            
            # Get recent minute data for more current pricing
            hist = ticker.history(period='5d', interval='1m')
            
            if len(hist) > 0:
                # Get the most recent close price
                current_price = float(hist['Close'].iloc[-1])
                logger.debug(f"Fetched current price for {symbol}: ${current_price}")
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
                'prediction_id': prediction['prediction_id'],
                'symbol': symbol,
                'predicted_action': predicted_action,
                'prediction_timestamp': prediction['prediction_timestamp'],
                'action_confidence': prediction.get('action_confidence', 0.0),
                'model_version': prediction.get('model_version', 'unknown'),
                'actual_return': round(actual_return, 4),
                'actual_direction': actual_direction,
                'entry_price': round(entry_price, 4),
                'exit_price': round(current_price, 4),
                'evaluation_timestamp': datetime.now().isoformat(),
                'success': success,
                'price_change': round(current_price - entry_price, 4),
                'price_change_pct': round(actual_return, 2),
                'has_existing_outcome': prediction.get('has_outcome', False)
            }
            
            logger.debug(f"Calculated outcome for {symbol}: {actual_return:.2f}% return")
            return outcome
            
        except Exception as e:
            logger.error(f"Error calculating outcome for {prediction.get('prediction_id', 'unknown')}: {e}")
            return None
    
    def evaluate_todays_predictions(self) -> Dict:
        """Main evaluation function - dry run mode"""
        logger.info("🔍 Starting dry run outcome evaluation for today's predictions...")
        
        todays_predictions = self.get_todays_predictions()
        
        if not todays_predictions:
            logger.info("No predictions from today to evaluate")
            return {
                'total_predictions': 0,
                'evaluated_count': 0,
                'failed_count': 0,
                'results': [],
                'summary': {}
            }
        
        evaluated_count = 0
        failed_count = 0
        successful_predictions = 0
        total_return = 0.0
        
        for prediction in todays_predictions:
            try:
                outcome = self.calculate_outcome(prediction)
                
                if outcome is None:
                    logger.warning(f"Could not calculate outcome for {prediction['prediction_id']}")
                    failed_count += 1
                    continue
                
                self.results.append(outcome)
                evaluated_count += 1
                
                if outcome['success']:
                    successful_predictions += 1
                
                total_return += outcome['actual_return']
                
                status = "✅ SUCCESS" if outcome['success'] else "❌ FAILED"
                existing = " (Already has outcome)" if outcome['has_existing_outcome'] else " (New)"
                
                logger.info(f"{status} {outcome['symbol']}: {outcome['predicted_action']} -> {outcome['actual_return']:.2f}% return{existing}")
                
                # Small delay to prevent overwhelming APIs
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error evaluating prediction {prediction['prediction_id']}: {e}")
                failed_count += 1
        
        # Calculate summary statistics
        success_rate = (successful_predictions / evaluated_count * 100) if evaluated_count > 0 else 0
        avg_return = total_return / evaluated_count if evaluated_count > 0 else 0
        
        summary = {
            'total_predictions': len(todays_predictions),
            'evaluated_count': evaluated_count,
            'failed_count': failed_count,
            'successful_predictions': successful_predictions,
            'success_rate': round(success_rate, 2),
            'total_return': round(total_return, 2),
            'average_return': round(avg_return, 2),
            'evaluation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"📊 Dry Run Evaluation Summary:")
        logger.info(f"   Total Predictions: {summary['total_predictions']}")
        logger.info(f"   Successfully Evaluated: {summary['evaluated_count']}")
        logger.info(f"   Failed to Evaluate: {summary['failed_count']}")
        logger.info(f"   Successful Predictions: {summary['successful_predictions']}")
        logger.info(f"   Success Rate: {summary['success_rate']}%")
        logger.info(f"   Total Return: {summary['total_return']}%")
        logger.info(f"   Average Return: {summary['average_return']}%")
        
        return {
            'summary': summary,
            'results': self.results
        }
    
    def print_detailed_results(self):
        """Print detailed results table"""
        if not self.results:
            print("No results to display")
            return
            
        print("\n" + "="*120)
        print("DETAILED PREDICTION RESULTS")
        print("="*120)
        print(f"{'Symbol':<10} {'Action':<6} {'Conf':<5} {'Entry $':<8} {'Exit $':<8} {'Return %':<8} {'Status':<10} {'Time':<16}")
        print("-"*120)
        
        for result in self.results:
            status = "SUCCESS" if result['success'] else "FAILED"
            conf = f"{result['action_confidence']:.1f}" if result['action_confidence'] else "N/A"
            time_str = result['prediction_timestamp'][:16] if result['prediction_timestamp'] else "N/A"
            
            print(f"{result['symbol']:<10} {result['predicted_action']:<6} {conf:<5} "
                  f"{result['entry_price']:<8.2f} {result['exit_price']:<8.2f} "
                  f"{result['actual_return']:<8.2f} {status:<10} {time_str:<16}")
        
        print("-"*120)

def main():
    """Main execution function"""
    evaluator = FixedDryRunOutcomeEvaluator()
    
    try:
        results = evaluator.evaluate_todays_predictions()
        evaluator.print_detailed_results()
        
        # Save results to JSON file
        with open('/root/test/logs/dry_run_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Results saved to: /root/test/logs/dry_run_results.json")
        
    except Exception as e:
        logger.error(f"Fatal error in dry run evaluation: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
