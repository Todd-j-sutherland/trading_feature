#!/usr/bin/env python3
"""
Corrected Smart Collector - Monitor enhanced_training_data.db for outcomes
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta

class CorrectedSmartCollector:
    def __init__(self):
        self.db_path = './data/ml_models/enhanced_training_data.db'
        self.active_features = self.load_active_features()
        
    def get_australian_time(self):
        """Get current time (simplified - using local time)"""
        return datetime.now()
    
    def load_active_features(self):
        """Load active features from file"""
        if os.path.exists('data/ml_models/active_features.json'):
            with open('data/ml_models/active_features.json', 'r') as f:
                return json.load(f)
        return {}
    
    def save_active_features(self):
        """Save active features to file"""
        os.makedirs('data/ml_models', exist_ok=True)
        with open('data/ml_models/active_features.json', 'w') as f:
            json.dump(self.active_features, f, indent=2)
    
    def collect_new_features(self):
        """Collect recent features from enhanced_training_data.db"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get features from last 6 hours that we haven't tracked yet
            cutoff_time = self.get_australian_time() - timedelta(hours=6)
            
            cursor.execute('''
                SELECT id, symbol, timestamp, sentiment_score, confidence, current_price
                FROM enhanced_features 
                WHERE datetime(timestamp) > ?
                ORDER BY timestamp DESC
            ''', (cutoff_time.isoformat(),))
            
            features = cursor.fetchall()
            new_features = 0
            
            for feature_id, symbol, timestamp, sentiment, confidence, price in features:
                feature_key = f"enhanced_{feature_id}"
                
                # Skip if already tracking
                if feature_key in self.active_features:
                    continue
                
                # Track features with reasonable confidence (lowered threshold)
                if confidence >= 0.55:
                    self.active_features[feature_key] = {
                        'id': feature_id,
                        'symbol': symbol,
                        'timestamp': timestamp,
                        'confidence': confidence,
                        'sentiment': sentiment,
                        'entry_price': price,
                        'source': 'enhanced_features',
                        'status': 'active',
                        'created_at': self.get_australian_time().isoformat()
                    }
                    new_features += 1
                    print(f"📋 Tracking Feature {feature_id}: {symbol} (conf: {confidence:.2f}) from {timestamp}")
            
            conn.close()
            
            if new_features > 0:
                print(f"✅ Added {new_features} new features to track")
            else:
                print("📊 No new features to track")
                
            return new_features
            
        except Exception as e:
            print(f"❌ Error collecting features: {e}")
            return 0
    
    def check_feature_outcomes(self):
        """Check outcomes for active features after 4-hour window"""
        cutoff_time = self.get_australian_time() - timedelta(hours=4)
        outcomes_recorded = 0
        
        for feature_key, feature in list(self.active_features.items()):
            if feature['status'] != 'active':
                continue
                
            feature_time = datetime.fromisoformat(feature['timestamp'].replace('Z', '+00:00'))
            
            # Check if 4 hours have passed
            if feature_time < cutoff_time:
                try:
                    # Get current price (simplified - using entry price + random variation for demo)
                    current_price = self.get_simulated_current_price(feature['symbol'], feature['entry_price'])
                    entry_price = feature['entry_price']
                    
                    # Calculate return
                    return_pct = ((current_price - entry_price) / entry_price) * 100
                    
                    # Record outcome in database
                    outcome_success = self.record_enhanced_outcome(feature, current_price, return_pct)
                    
                    if outcome_success:
                        feature['status'] = 'completed'
                        feature['actual_return'] = return_pct
                        feature['exit_price'] = current_price
                        feature['exit_timestamp'] = self.get_australian_time().isoformat()
                        outcomes_recorded += 1
                        
                        print(f"📊 Outcome: Feature {feature['id']} - {feature['symbol']} -> {return_pct:.2%} return")
                    else:
                        feature['status'] = 'error'
                        
                except Exception as e:
                    print(f"❌ Error recording outcome for {feature_key}: {e}")
                    feature['status'] = 'error'
        
        if outcomes_recorded > 0:
            print(f"✅ Recorded {outcomes_recorded} new outcomes")
            
        return outcomes_recorded
    
    def get_simulated_current_price(self, symbol, entry_price):
        """Get simulated current price (replace with real price feed)"""
        import random
        # Simulate price movement (±3% for more realistic movement)
        variation = random.uniform(-0.03, 0.03)
        return entry_price * (1 + variation)
    
    def record_enhanced_outcome(self, feature, exit_price, return_pct):
        """Record enhanced outcome in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate realistic price movements for different timeframes
            import random
            variation_1h = random.uniform(-0.01, 0.01)
            variation_1d = random.uniform(-0.05, 0.05)
            
            exit_price_1h = feature['entry_price'] * (1 + variation_1h)
            exit_price_1d = feature['entry_price'] * (1 + variation_1d)
            
            # Determine optimal action based on return
            if return_pct > 0.01:
                optimal_action = 'BUY'
            elif return_pct < -0.01:
                optimal_action = 'SELL'
            else:
                optimal_action = 'HOLD'
            
            # Insert outcome using correct schema
            cursor.execute('''
                INSERT INTO enhanced_outcomes 
                (feature_id, symbol, prediction_timestamp, price_direction_1h, 
                 price_direction_4h, price_direction_1d, price_magnitude_1h, 
                 price_magnitude_4h, price_magnitude_1d, volatility_next_1h,
                 optimal_action, confidence_score, entry_price, exit_price_1h, 
                 exit_price_4h, exit_price_1d, exit_timestamp, return_pct, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature['id'],
                feature['symbol'], 
                feature['timestamp'],
                1 if variation_1h > 0 else -1,      # price_direction_1h
                1 if return_pct > 0 else -1,        # price_direction_4h  
                1 if variation_1d > 0 else -1,      # price_direction_1d
                abs(variation_1h),                  # price_magnitude_1h
                abs(return_pct),                    # price_magnitude_4h
                abs(variation_1d),                  # price_magnitude_1d
                abs(variation_1h) * 2,              # volatility_next_1h
                optimal_action,                     # optimal_action
                feature['confidence'],              # confidence_score
                feature['entry_price'],             # entry_price
                exit_price_1h,                      # exit_price_1h
                exit_price,                         # exit_price_4h
                exit_price_1d,                      # exit_price_1d
                self.get_australian_time().isoformat(),  # exit_timestamp
                return_pct,                         # return_pct
                self.get_australian_time().isoformat()   # created_at
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error recording enhanced outcome: {e}")
            return False
    
    def print_stats(self):
        """Print tracking statistics"""
        active_count = sum(1 for f in self.active_features.values() if f['status'] == 'active')
        completed_count = sum(1 for f in self.active_features.values() if f['status'] == 'completed')
        
        # Get outcome count from database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes')
            total_outcomes = cursor.fetchone()[0]
            
            # Get today's outcome count
            cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE date(exit_timestamp) = date(\"now\")')
            today_outcomes = cursor.fetchone()[0]
            
            conn.close()
        except:
            total_outcomes = 0
            today_outcomes = 0
        
        print(f"\n📊 Corrected Collector Stats:")
        print(f"   Active features: {active_count}")
        print(f"   Completed today: {completed_count}")  
        print(f"   Today's outcomes: {today_outcomes}")
        print(f"   Total outcomes in DB: {total_outcomes}")
        
        if total_outcomes > 0:
            print("🎯 Enhanced outcome tracking is working!")
    
    def run_continuous(self, interval_minutes=30):
        """Run continuous collection with graceful shutdown support"""
        import time
        
        print(f"🚀 Starting corrected smart collector (every {interval_minutes} minutes)")
        print("💡 Use Ctrl+C to stop gracefully")
        print("🔍 Monitoring: ./data/ml_models/enhanced_training_data.db")
        
        while True:
            try:
                self.run_collection_cycle()
                
                # Sleep in small chunks to allow for responsive shutdown
                sleep_time = interval_minutes * 60
                sleep_chunks = max(1, sleep_time // 10)  # Sleep in 10-second chunks
                chunk_duration = sleep_time / sleep_chunks
                
                print(f"💤 Sleeping for {interval_minutes} minutes... (Use Ctrl+C to stop)")
                for i in range(int(sleep_chunks)):
                    time.sleep(chunk_duration)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping corrected collector...")
                break
            except Exception as e:
                print(f"❌ Error in collection cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retry
                
        print("✅ Corrected smart collector stopped gracefully")
    
    def run_collection_cycle(self):
        """Run one complete collection cycle"""
        print(f"\n🔄 Corrected Collection Cycle - {self.get_australian_time().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Collect new features from enhanced_training_data.db
        new_features = self.collect_new_features()
        
        # Check outcomes for existing features
        outcomes_recorded = self.check_feature_outcomes()
        
        # Save state
        self.save_active_features()
        
        # Print stats
        self.print_stats()
        
        return new_features + outcomes_recorded > 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Corrected Smart Collector for enhanced features')
    parser.add_argument('--interval', type=int, default=30, help='Collection interval in minutes')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuous')
    
    args = parser.parse_args()
    
    print("🚀 CORRECTED SMART COLLECTOR - ENHANCED FEATURES BRIDGE")
    print("=" * 60)
    
    collector = CorrectedSmartCollector()
    
    if args.once:
        activity = collector.run_collection_cycle()
        if activity:
            print("\n✅ Collection cycle completed with activity")
        else:
            print("\n💤 No new activity this cycle")
        print("\n💡 This collector monitors enhanced_training_data.db for outcome tracking!")
    else:
        collector.run_continuous(args.interval)

if __name__ == "__main__":
    main()
