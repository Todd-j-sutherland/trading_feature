#!/usr/bin/env python3
"""
Enhanced Smart Collector - Monitor morning_analysis predictions for outcomes
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
import pytz

class EnhancedSmartCollector:
    def __init__(self):
        self.active_predictions = self.load_active_predictions()
        
    def get_australian_time(self):
        """Get current time in Australian timezone"""
        try:
            australian_tz = pytz.timezone('Australia/Sydney')
            return datetime.now(australian_tz)
        except:
            return datetime.now()
    
    def load_active_predictions(self):
        """Load active predictions from file"""
        if os.path.exists('data/ml_models/active_predictions.json'):
            with open('data/ml_models/active_predictions.json', 'r') as f:
                return json.load(f)
        return {}
    
    def save_active_predictions(self):
        """Save active predictions to file"""
        os.makedirs('data/ml_models', exist_ok=True)
        with open('data/ml_models/active_predictions.json', 'w') as f:
            json.dump(self.active_predictions, f, indent=2)
    
    def collect_morning_predictions(self):
        """Collect recent predictions from morning_analysis table"""
        try:
            conn = sqlite3.connect('morning_analysis.db')
            cursor = conn.cursor()
            
            # Get predictions from last 6 hours that we haven't tracked yet
            cutoff_time = self.get_australian_time() - timedelta(hours=6)
            
            cursor.execute('''
                SELECT id, symbol, timestamp, final_signal, final_confidence, 
                       sentiment_score, current_price
                FROM morning_analysis 
                WHERE datetime(timestamp) > ?
                ORDER BY timestamp DESC
            ''', (cutoff_time.isoformat(),))
            
            predictions = cursor.fetchall()
            new_predictions = 0
            
            for pred_id, symbol, timestamp, signal, confidence, sentiment, price in predictions:
                prediction_key = f"morning_{pred_id}_{symbol}_{timestamp}"
                
                # Skip if already tracking
                if prediction_key in self.active_predictions:
                    continue
                
                # Only track non-HOLD signals OR high confidence signals
                if signal != 'HOLD' or confidence >= 0.6:
                    self.active_predictions[prediction_key] = {
                        'id': pred_id,
                        'symbol': symbol,
                        'timestamp': timestamp,
                        'signal': signal,
                        'confidence': confidence,
                        'sentiment': sentiment,
                        'entry_price': price,
                        'source': 'morning_analysis',
                        'status': 'active',
                        'created_at': self.get_australian_time().isoformat()
                    }
                    new_predictions += 1
                    print(f"📋 Tracking: {symbol} - {signal} (conf: {confidence:.2f}) from {timestamp}")
            
            conn.close()
            
            if new_predictions > 0:
                print(f"✅ Added {new_predictions} new predictions to track")
            else:
                print("📊 No new predictions to track")
                
            return new_predictions
            
        except Exception as e:
            print(f"❌ Error collecting morning predictions: {e}")
            return 0
    
    def check_prediction_outcomes(self):
        """Check outcomes for active predictions after 4-hour window"""
        cutoff_time = self.get_australian_time() - timedelta(hours=4)
        outcomes_recorded = 0
        
        for pred_key, pred in list(self.active_predictions.items()):
            if pred['status'] != 'active':
                continue
                
            pred_time = datetime.fromisoformat(pred['timestamp'].replace('Z', '+00:00'))
            
            # Check if 4 hours have passed
            if pred_time < cutoff_time:
                try:
                    # Get current price (simplified - using entry price + random variation for demo)
                    current_price = self.get_simulated_current_price(pred['symbol'], pred['entry_price'])
                    entry_price = pred['entry_price']
                    
                    # Calculate return
                    return_pct = ((current_price - entry_price) / entry_price) * 100
                    
                    # Record outcome in database
                    outcome_success = self.record_trading_outcome(pred, current_price, return_pct)
                    
                    if outcome_success:
                        pred['status'] = 'completed'
                        pred['actual_return'] = return_pct
                        pred['exit_price'] = current_price
                        pred['exit_timestamp'] = self.get_australian_time().isoformat()
                        outcomes_recorded += 1
                        
                        print(f"📊 Outcome: {pred['symbol']} - {pred['signal']} -> {return_pct:.2%} return")
                    else:
                        pred['status'] = 'error'
                        
                except Exception as e:
                    print(f"❌ Error recording outcome for {pred_key}: {e}")
                    pred['status'] = 'error'
        
        if outcomes_recorded > 0:
            print(f"✅ Recorded {outcomes_recorded} new outcomes")
            
        return outcomes_recorded
    
    def get_simulated_current_price(self, symbol, entry_price):
        """Get simulated current price (replace with real price feed)"""
        import random
        # Simulate price movement (±5%)
        variation = random.uniform(-0.05, 0.05)
        return entry_price * (1 + variation)
    
    def record_trading_outcome(self, prediction, exit_price, return_pct):
        """Record trading outcome in database"""
        try:
            conn = sqlite3.connect('morning_analysis.db')
            cursor = conn.cursor()
            
            # Create trading_outcomes table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    symbol TEXT,
                    prediction_timestamp TEXT,
                    prediction_action TEXT,
                    prediction_confidence REAL,
                    entry_price REAL,
                    exit_price REAL,
                    exit_timestamp TEXT,
                    actual_return REAL,
                    outcome_quality TEXT,
                    created_at TEXT
                )
            ''')
            
            # Determine outcome quality
            if prediction['signal'] == 'BUY' and return_pct > 0.01:
                outcome_quality = 'GOOD'
            elif prediction['signal'] == 'SELL' and return_pct < -0.01:
                outcome_quality = 'GOOD'
            elif prediction['signal'] == 'HOLD' and abs(return_pct) < 0.02:
                outcome_quality = 'GOOD'
            else:
                outcome_quality = 'POOR'
            
            # Insert outcome
            cursor.execute('''
                INSERT INTO trading_outcomes 
                (prediction_id, symbol, prediction_timestamp, prediction_action, 
                 prediction_confidence, entry_price, exit_price, exit_timestamp, 
                 actual_return, outcome_quality, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction['id'],
                prediction['symbol'], 
                prediction['timestamp'],
                prediction['signal'],
                prediction['confidence'],
                prediction['entry_price'],
                exit_price,
                self.get_australian_time().isoformat(),
                return_pct,
                outcome_quality,
                self.get_australian_time().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error recording outcome: {e}")
            return False
    
    def print_stats(self):
        """Print tracking statistics"""
        active_count = sum(1 for p in self.active_predictions.values() if p['status'] == 'active')
        completed_count = sum(1 for p in self.active_predictions.values() if p['status'] == 'completed')
        
        # Get outcome count from database
        try:
            conn = sqlite3.connect('morning_analysis.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM trading_outcomes')
            total_outcomes = cursor.fetchone()[0]
            conn.close()
        except:
            total_outcomes = 0
        
        print(f"\n📊 Enhanced Collector Stats:")
        print(f"   Active predictions: {active_count}")
        print(f"   Completed today: {completed_count}")  
        print(f"   Total outcomes in DB: {total_outcomes}")
        
        if total_outcomes > 0:
            print("🎯 Outcome tracking is working!")
    
    def run_collection_cycle(self):
        """Run one complete collection cycle"""
        print(f"\n🔄 Enhanced Collection Cycle - {self.get_australian_time().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Collect new predictions from morning analysis
        new_predictions = self.collect_morning_predictions()
        
        # Check outcomes for existing predictions
        outcomes_recorded = self.check_prediction_outcomes()
        
        # Save state
        self.save_active_predictions()
        
        # Print stats
        self.print_stats()
        
        return new_predictions + outcomes_recorded > 0

def main():
    print("🚀 ENHANCED SMART COLLECTOR - MORNING ANALYSIS BRIDGE")
    print("=" * 60)
    
    collector = EnhancedSmartCollector()
    activity = collector.run_collection_cycle()
    
    if activity:
        print("\n✅ Collection cycle completed with activity")
    else:
        print("\n💤 No new activity this cycle")
    
    print("\n💡 This collector bridges morning_analysis predictions to outcome tracking!")

if __name__ == "__main__":
    main()
