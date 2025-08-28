#!/usr/bin/env python3
"""
Live Prediction Monitor - Continuously monitors predictions.db for new signals
"""

import sys
import os
import signal
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration.prediction_signal_handler import PredictionSignalHandler

class LivePredictionMonitor:
    """Live monitoring service for prediction signals"""
    
    def __init__(self):
        self.handler = PredictionSignalHandler()
        self.running = True
        self.processed_predictions = set()  # Track processed prediction IDs
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received shutdown signal ({signum})")
        self.running = False
    
    def start_monitoring(self, check_interval_seconds: int = 30):
        """Start live monitoring with specified interval"""
        print("🚀 Starting Live Prediction Monitor")
        print("=" * 50)
        print(f"⏱️  Check interval: {check_interval_seconds} seconds")
        print(f"📊 Paper trading account ID: {self.handler.account.id}")
        print(f"💰 Starting balance: ${self.handler.account.cash_balance:,.2f}")
        print("🔄 Monitoring for new predictions...")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        last_summary_time = datetime.now()
        
        while self.running:
            try:
                # Check for new predictions
                new_signals = self.check_for_new_predictions()
                
                if new_signals:
                    print(f"\n🔔 Found {len(new_signals)} new prediction(s)")
                    
                    for signal_data in new_signals:
                        self.process_signal(signal_data)
                
                # Show periodic summary (every 5 minutes)
                if (datetime.now() - last_summary_time).seconds > 300:
                    self.show_periodic_summary()
                    last_summary_time = datetime.now()
                
                # Wait before next check
                time.sleep(check_interval_seconds)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        print("👋 Live monitoring stopped")
    
    def check_for_new_predictions(self):
        """Check for new predictions since last check"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.handler.predictions_db)
            cursor = conn.cursor()
            
            # Get all prediction IDs we haven't processed yet
            if self.processed_predictions:
                placeholders = ','.join('?' * len(self.processed_predictions))
                cursor.execute(f'''
                    SELECT 
                        p.prediction_id,
                        p.symbol,
                        p.prediction,
                        p.confidence,
                        p.timestamp,
                        p.signal_strength,
                        p.reasoning
                    FROM predictions p
                    WHERE p.prediction_id NOT IN ({placeholders})
                    ORDER BY p.timestamp DESC
                    LIMIT 10
                ''', list(self.processed_predictions))
            else:
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
                    ORDER BY p.timestamp DESC
                    LIMIT 10
                ''')
            
            predictions = cursor.fetchall()
            conn.close()
            
            # Convert to signal format
            new_signals = []
            for pred in predictions:
                signal_data = {
                    'prediction_id': pred[0],
                    'symbol': pred[1],
                    'prediction': pred[2],
                    'confidence': pred[3],
                    'timestamp': pred[4],
                    'signal_strength': pred[5] if pred[5] else 0.5,
                    'reasoning': pred[6] if pred[6] else 'ML Model Prediction'
                }
                new_signals.append(signal_data)
                
                # Mark as processed
                self.processed_predictions.add(pred[0])
            
            return new_signals
            
        except Exception as e:
            print(f"❌ Error checking for new predictions: {e}")
            return []
    
    def process_signal(self, signal_data):
        """Process a single prediction signal"""
        try:
            timestamp = signal_data['timestamp']
            symbol = signal_data['symbol']
            prediction = signal_data['prediction']
            confidence = signal_data['confidence']
            
            print(f"📡 {timestamp}: {symbol} {prediction} (confidence: {confidence:.2f})")
            
            result = self.handler.process_prediction_signal(signal_data)
            
            if result.success:
                print(f"   ✅ {result.message}")
                if result.executed_price and result.executed_quantity:
                    total_value = result.executed_price * result.executed_quantity
                    print(f"   💰 Executed: {result.executed_quantity} shares @ ${result.executed_price:.2f} = ${total_value:,.2f}")
            else:
                print(f"   ❌ {result.message}")
            
        except Exception as e:
            print(f"❌ Error processing signal: {e}")
    
    def show_periodic_summary(self):
        """Show periodic performance summary"""
        try:
            performance = self.handler.get_trading_performance_summary()
            
            if 'error' not in performance and 'message' not in performance:
                print("\n📊 PERFORMANCE SUMMARY")
                print("-" * 30)
                print(f"Total trades: {performance['total_trades']}")
                print(f"Win rate: {performance['win_rate']:.1f}%")
                print(f"Total P&L: ${performance['total_pnl']:+,.2f}")
                print(f"Portfolio value: ${performance['portfolio_value']:,.2f}")
                print(f"Total return: {performance['total_return_pct']:+.2f}%")
                print("-" * 30)
            
        except Exception as e:
            print(f"❌ Error showing summary: {e}")

def main():
    """Main function"""
    print("🤖 Live Prediction Monitor")
    print("Connects your ML predictions to paper trading automatically")
    print()
    
    # Parse command line arguments
    check_interval = 30  # Default 30 seconds
    
    if len(sys.argv) > 1:
        try:
            check_interval = int(sys.argv[1])
        except ValueError:
            print("Error: Check interval must be a number (seconds)")
            sys.exit(1)
    
    # Start monitoring
    monitor = LivePredictionMonitor()
    monitor.start_monitoring(check_interval)

if __name__ == "__main__":
    main()
