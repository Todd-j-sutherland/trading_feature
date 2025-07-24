#!/usr/bin/env python3
"""
Smart Collector - Enhanced live data collection with outcome tracking
Collects high-quality training samples with proper outcome validation
"""
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.core.data.processors.news_processor import NewsTradingAnalyzer
from app.core.ml.training.pipeline import MLTrainingPipeline
from app.core.data.collectors.market_data import ASXDataFeed
from app.core.data.collectors.keywords import KeywordManager
from app.config.settings import Settings

class SmartCollector:
    def __init__(self):
        self.settings = Settings()
        self.symbols = self.settings.BANK_SYMBOLS
        self.analyzer = NewsTradingAnalyzer()
        self.ml_pipeline = MLTrainingPipeline()
        self.data_feed = ASXDataFeed()
        self.keyword_manager = KeywordManager()
        self.active_signals = self.load_active_signals()
        self.collection_stats = {'signals_today': 0, 'outcomes_recorded': 0}
        
    def load_active_signals(self):
        """Load active signals from file"""
        if os.path.exists('data/ml_models/active_signals.json'):
            with open('data/ml_models/active_signals.json', 'r') as f:
                return json.load(f)
        return {}
    
    def save_active_signals(self):
        """Save active signals to file"""
        os.makedirs('data/ml_models', exist_ok=True)
        with open('data/ml_models/active_signals.json', 'w') as f:
            json.dump(self.active_signals, f, indent=2)
    
    def collect_high_quality_signals(self):
        """Collect only high-confidence signals for training"""
        print(f"🔍 Scanning for high-quality signals... {datetime.now().strftime('%H:%M:%S')}")
        
        for symbol in self.symbols:
            try:
                # Get keywords for the bank for targeted analysis
                keywords = self.keyword_manager.get_keywords_for_bank(symbol)
                
                # Get sentiment analysis with bank-specific keywords
                result = self.analyzer.analyze_and_track(symbol, keywords=keywords)
                
                # Filter for high-quality signals
                if self.is_high_quality_signal(result):
                    signal_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # Store signal for outcome tracking
                    self.active_signals[signal_id] = {
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'signal_type': result['signal'],
                        'sentiment_score': result['overall_sentiment'],
                        'confidence': result['confidence'],
                        'feature_id': result.get('ml_feature_id'),
                        'current_price': self.get_current_price(symbol),
                        'status': 'active'
                    }
                    
                    self.collection_stats['signals_today'] += 1
                    print(f"✅ High-quality signal: {symbol} - {result['signal']} (conf: {result['confidence']:.2f})")
                    
            except Exception as e:
                print(f"❌ Error collecting from {symbol}: {e}")
    
    def is_high_quality_signal(self, result):
        """Check if signal meets quality criteria"""
        return (
            result.get('signal') not in ['HOLD', None] and
            result.get('confidence', 0) >= 0.75 and  # High confidence
            result.get('news_count', 0) >= 5 and      # Good news volume
            abs(result.get('overall_sentiment', 0)) >= 0.3  # Strong sentiment
        )
    
    def get_current_price(self, symbol):
        """Get current price for outcome tracking"""
        try:
            price_data = self.data_feed.get_current_price(symbol)
            return price_data.get('price', 100.0)
        except:
            return 100.0  # Fallback
    
    def check_signal_outcomes(self):
        """Check outcomes for active signals (4-hour window)"""
        cutoff_time = datetime.now() - timedelta(hours=4)
        outcomes_recorded = 0
        
        for signal_id, signal in list(self.active_signals.items()):
            if signal['status'] != 'active':
                continue
                
            signal_time = datetime.fromisoformat(signal['timestamp'])
            
            if signal_time < cutoff_time:
                # Time to record outcome
                try:
                    current_price = self.get_current_price(signal['symbol'])
                    entry_price = signal['current_price']
                    
                    # Calculate return
                    return_pct = (current_price - entry_price) / entry_price
                    
                    # Record outcome
                    outcome_data = {
                        'symbol': signal['symbol'],
                        'signal_timestamp': signal['timestamp'],
                        'signal_type': signal['signal_type'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'exit_timestamp': datetime.now().isoformat(),
                        'max_drawdown': min(0, return_pct * 0.7)  # Estimate
                    }
                    
                    if signal.get('feature_id'):
                        self.ml_pipeline.record_trading_outcome(signal['feature_id'], outcome_data)
                        outcomes_recorded += 1
                        
                        print(f"📊 Outcome recorded: {signal['symbol']} - {return_pct:.2%} return")
                    
                    # Mark as complete
                    signal['status'] = 'completed'
                    signal['actual_return'] = return_pct
                    
                except Exception as e:
                    print(f"❌ Error recording outcome for {signal_id}: {e}")
                    signal['status'] = 'error'
        
        if outcomes_recorded > 0:
            self.collection_stats['outcomes_recorded'] += outcomes_recorded
            print(f"✅ Recorded {outcomes_recorded} outcomes")
    
    def cleanup_old_signals(self):
        """Remove old completed signals"""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for signal_id in list(self.active_signals.keys()):
            signal = self.active_signals[signal_id]
            signal_time = datetime.fromisoformat(signal['timestamp'])
            
            if signal_time < cutoff_time and signal['status'] in ['completed', 'error']:
                del self.active_signals[signal_id]
    
    def print_stats(self):
        """Print collection statistics"""
        # Get current sample count
        X, y = self.ml_pipeline.prepare_training_dataset(min_samples=1)
        total_samples = len(X) if X is not None else 0
        
        active_count = sum(1 for s in self.active_signals.values() if s['status'] == 'active')
        
        print(f"\n📊 Collection Stats:")
        print(f"   Active signals: {active_count}")
        print(f"   Signals today: {self.collection_stats['signals_today']}")
        print(f"   Outcomes recorded: {self.collection_stats['outcomes_recorded']}")
        print(f"   Total samples: {total_samples}")
        
        if total_samples >= 50:
            print("🚀 Ready for model training!")
    
    def run_collection_cycle(self):
        """Run one complete collection cycle"""
        print(f"\n🔄 Starting collection cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Collect new signals
        self.collect_high_quality_signals()
        
        # Check outcomes for existing signals
        self.check_signal_outcomes()
        
        # Cleanup old signals
        self.cleanup_old_signals()
        
        # Save state
        self.save_active_signals()
        
        # Print stats
        self.print_stats()
    
    def run_continuous(self, interval_minutes=30):
        """Run continuous collection"""
        print(f"🚀 Starting smart collector (every {interval_minutes} minutes)")
        
        while True:
            try:
                self.run_collection_cycle()
                print(f"💤 Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping collector...")
                break
            except Exception as e:
                print(f"❌ Error in collection cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart ML data collector')
    parser.add_argument('--interval', type=int, default=30, help='Collection interval in minutes')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuous')
    
    args = parser.parse_args()
    
    collector = SmartCollector()
    
    if args.once:
        collector.run_collection_cycle()
    else:
        collector.run_continuous(args.interval)
