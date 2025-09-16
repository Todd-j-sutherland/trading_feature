#!/usr/bin/env python3
"""
Simple Dry Run Outcome Evaluator for Trading System
Shows what the outcomes would be without updating the database
"""

import sqlite3
import json
from datetime import datetime, timedelta
import yfinance as yf
import time

class SimpleDryRunEvaluator:
    """Simple dry run version of the outcome evaluator"""
    
    def __init__(self, db_path: str = "/root/test/data/trading_predictions.db"):
        self.db_path = db_path
        self.results = []
        
    def get_todays_predictions(self):
        """Get today's predictions"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()
            
            # Get today's predictions
            cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price,
                       CASE WHEN o.outcome_id IS NULL THEN 0 ELSE 1 END as has_outcome
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE date(substr(p.prediction_timestamp, 1, 10)) = date('now')
                ORDER BY p.prediction_timestamp DESC
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            print(f"Found {len(results)} predictions from today")
            return results
            
        except Exception as e:
            print(f"Error getting predictions: {e}")
            return []
    
    def fetch_current_price(self, symbol):
        """Fetch current price"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d', interval='1m')
            
            if len(hist) > 0:
                return float(hist['Close'].iloc[-1])
            return None
                
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def evaluate_predictions(self):
        """Main evaluation function"""
        print("🔍 Starting dry run outcome evaluation for today's predictions...")
        
        predictions = self.get_todays_predictions()
        
        if not predictions:
            print("No predictions from today to evaluate")
            return
        
        evaluated_count = 0
        failed_count = 0
        successful_predictions = 0
        total_return = 0.0
        
        print(f"\n{'Symbol':<10} {'Action':<6} {'Conf':<5} {'Entry $':<8} {'Exit $':<8} {'Return %':<8} {'Status':<10}")
        print("-" * 80)
        
        for row in predictions:
            prediction_id, symbol, timestamp, predicted_action, confidence, entry_price, has_outcome = row
            
            try:
                # Get entry price if not available
                if entry_price is None or entry_price == 0.0:
                    pred_time = datetime.fromisoformat(timestamp)
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=pred_time.date(), 
                                        end=(pred_time + timedelta(days=1)).date(), 
                                        interval='1h')
                    if len(hist) > 0:
                        entry_price = float(hist['Close'].iloc[0])
                    else:
                        failed_count += 1
                        continue
                
                # Get current price
                current_price = self.fetch_current_price(symbol)
                if current_price is None:
                    failed_count += 1
                    continue
                
                # Calculate return
                actual_return = ((current_price - entry_price) / entry_price) * 100
                actual_direction = 1 if current_price > entry_price else 0
                
                # Determine success
                predicted_action_upper = predicted_action.upper()
                success = False
                if predicted_action_upper == 'BUY' and actual_direction == 1:
                    success = True
                elif predicted_action_upper == 'SELL' and actual_direction == 0:
                    success = True
                elif predicted_action_upper == 'HOLD' and abs(actual_return) < 1.0:
                    success = True
                
                # Store result
                result = {
                    'prediction_id': prediction_id,
                    'symbol': symbol,
                    'predicted_action': predicted_action_upper,
                    'actual_return': round(actual_return, 4),
                    'entry_price': round(entry_price, 4),
                    'exit_price': round(current_price, 4),
                    'success': success,
                    'has_existing_outcome': bool(has_outcome)
                }
                self.results.append(result)
                
                evaluated_count += 1
                if success:
                    successful_predictions += 1
                total_return += actual_return
                
                status = "✅ SUCCESS" if success else "❌ FAILED"
                conf_str = f"{confidence:.1f}" if confidence else "N/A"
                
                print(f"{symbol:<10} {predicted_action_upper:<6} {conf_str:<5} "
                      f"{entry_price:<8.2f} {current_price:<8.2f} "
                      f"{actual_return:<8.2f} {status:<10}")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"Error evaluating {symbol}: {e}")
                failed_count += 1
        
        # Calculate summary
        success_rate = (successful_predictions / evaluated_count * 100) if evaluated_count > 0 else 0
        avg_return = total_return / evaluated_count if evaluated_count > 0 else 0
        
        summary = {
            'total_predictions': len(predictions),
            'evaluated_count': evaluated_count,
            'failed_count': failed_count,
            'successful_predictions': successful_predictions,
            'success_rate': round(success_rate, 2),
            'total_return': round(total_return, 2),
            'average_return': round(avg_return, 2),
            'evaluation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print("\n" + "="*80)
        print("📊 DRY RUN EVALUATION SUMMARY")
        print("="*80)
        print(f"Total Predictions: {summary['total_predictions']}")
        print(f"Successfully Evaluated: {summary['evaluated_count']}")
        print(f"Failed to Evaluate: {summary['failed_count']}")
        print(f"Successful Predictions: {summary['successful_predictions']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Total Return: {summary['total_return']}%")
        print(f"Average Return: {summary['average_return']}%")
        print("="*80)
        
        # Save results
        results_data = {
            'summary': summary,
            'results': self.results
        }
        
        with open('/root/test/logs/dry_run_results.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📁 Results saved to: /root/test/logs/dry_run_results.json")

def main():
    evaluator = SimpleDryRunEvaluator()
    evaluator.evaluate_predictions()

if __name__ == "__main__":
    main()
