#!/usr/bin/env python3
"""
🚀 Enhanced Trading Process with Fixed Prediction Engine
Integrates your existing data collection with the new true prediction system
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime, timezone
import logging
import traceback

# Add the path to use the new prediction engine
sys.path.append('/root/test/data_quality_system/core')

try:
    from true_prediction_engine import TruePredictionEngine, OutcomeEvaluator
    NEW_SYSTEM_AVAILABLE = True
    print("✅ New prediction engine available")
except ImportError as e:
    print(f"⚠️  New prediction system not available: {e}")
    NEW_SYSTEM_AVAILABLE = False

class EnhancedTradingProcess:
    def __init__(self):
        self.db_path = '/root/test/trading_unified.db'
        self.prediction_engine = None
        self.outcome_evaluator = None
        
        if NEW_SYSTEM_AVAILABLE:
            try:
                self.prediction_engine = TruePredictionEngine()
                self.outcome_evaluator = OutcomeEvaluator()
                print("✅ New prediction system initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize new system: {e}")
                
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def fix_datetime_issues(self):
        """Fix datetime comparison issues in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all records with datetime issues
            cursor.execute("""
                SELECT symbol, created_at, entry_timestamp 
                FROM trading_positions 
                WHERE created_at IS NOT NULL
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            records = cursor.fetchall()
            self.logger.info(f"Found {len(records)} recent records to check")
            
            # Check for timezone issues
            for record in records:
                symbol, created_at, entry_timestamp = record
                try:
                    # Try to parse the datetime
                    if isinstance(created_at, str):
                        dt = pd.to_datetime(created_at)
                        # Ensure it's timezone-naive for SQLite compatibility
                        if dt.tz is not None:
                            dt = dt.tz_localize(None)
                except Exception as e:
                    self.logger.warning(f"Datetime issue for {symbol}: {e}")
                    
            conn.close()
            self.logger.info("✅ Datetime check completed")
            
        except Exception as e:
            self.logger.error(f"Error fixing datetime issues: {e}")
            
    def get_latest_features(self, symbol):
        """Extract latest features for a symbol from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get the most recent analysis for this symbol
            query = """
                SELECT * FROM trading_positions 
                WHERE symbol = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            df = pd.read_sql(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return None
                
            # Extract features that match the new prediction engine
            features = {}
            row = df.iloc[0]
            
            # Map your existing columns to the expected features
            feature_mapping = {
                'sentiment_score': 'sentiment_score',
                'rsi': 'rsi',
                'macd_histogram': 'macd_histogram', 
                'volume_ratio': 'volume_ratio',
                'news_count': 'news_count',
                'confidence': 'confidence',
                'macd_line': 'macd_line',
                'bb_position': 'bb_position',
                'bb_width': 'bb_width',
                'atr': 'atr',
                'obv': 'obv',
                'vwap': 'vwap'
            }
            
            for new_key, old_key in feature_mapping.items():
                if old_key in row and pd.notna(row[old_key]):
                    features[new_key] = float(row[old_key])
                else:
                    # Provide default values for missing features
                    defaults = {
                        'sentiment_score': 0.0,
                        'rsi': 50.0,
                        'macd_histogram': 0.0,
                        'volume_ratio': 1.0,
                        'news_count': 0,
                        'confidence': 0.5,
                        'macd_line': 0.0,
                        'bb_position': 0.5,
                        'bb_width': 0.02,
                        'atr': 0.01,
                        'obv': 0.0,
                        'vwap': 0.0
                    }
                    features[new_key] = defaults.get(new_key, 0.0)
                    
            return features
            
        except Exception as e:
            self.logger.error(f"Error getting features for {symbol}: {e}")
            return None
            
    def make_predictions_for_all_symbols(self):
        """Make predictions for all symbols with recent data"""
        if not self.prediction_engine:
            self.logger.warning("Prediction engine not available")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all symbols with recent data (last 24 hours)
            query = """
                SELECT DISTINCT symbol 
                FROM trading_positions 
                WHERE datetime(created_at) > datetime('now', '-1 day')
                ORDER BY symbol
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            symbols = df['symbol'].tolist()
            self.logger.info(f"Making predictions for {len(symbols)} symbols: {symbols}")
            
            predictions_made = 0
            for symbol in symbols:
                try:
                    # Get latest features
                    features = self.get_latest_features(symbol)
                    if features is None:
                        self.logger.warning(f"No features available for {symbol}")
                        continue
                        
                    # Make prediction
                    prediction = self.prediction_engine.make_prediction(symbol, features)
                    
                    self.logger.info(f"✅ Prediction for {symbol}:")
                    self.logger.info(f"   Action: {prediction['predicted_action']}")
                    self.logger.info(f"   Confidence: {prediction['action_confidence']:.1%}")
                    self.logger.info(f"   Direction: {'UP' if prediction['predicted_direction'] == 1 else 'DOWN'}")
                    self.logger.info(f"   Expected Change: {prediction['predicted_magnitude']:.2f}%")
                    
                    predictions_made += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to make prediction for {symbol}: {e}")
                    
            self.logger.info(f"✅ Made {predictions_made} predictions successfully")
            
        except Exception as e:
            self.logger.error(f"Error making predictions: {e}")
            traceback.print_exc()
            
    def evaluate_past_predictions(self):
        """Evaluate predictions made 24+ hours ago"""
        if not self.outcome_evaluator:
            self.logger.warning("Outcome evaluator not available")
            return
            
        try:
            count = self.outcome_evaluator.evaluate_pending_predictions()
            self.logger.info(f"✅ Evaluated {count} pending predictions")
            
        except Exception as e:
            self.logger.error(f"Error evaluating predictions: {e}")
            
    def run_enhanced_process(self):
        """Run the complete enhanced trading process"""
        self.logger.info("🚀 Starting Enhanced Trading Process")
        
        # Step 1: Fix any datetime issues
        self.logger.info("🔧 Step 1: Fixing datetime issues...")
        self.fix_datetime_issues()
        
        # Step 2: Evaluate past predictions
        self.logger.info("📊 Step 2: Evaluating past predictions...")
        self.evaluate_past_predictions()
        
        # Step 3: Make new predictions based on latest data
        self.logger.info("🎯 Step 3: Making new predictions...")
        self.make_predictions_for_all_symbols()
        
        self.logger.info("✅ Enhanced trading process completed!")
        
        # Step 4: Show summary
        self.show_prediction_summary()
        
    def show_prediction_summary(self):
        """Show a summary of recent predictions"""
        try:
            import sqlite3
            conn = sqlite3.connect('/root/test/data/trading_predictions.db')
            
            # Recent predictions
            df = pd.read_sql("""
                SELECT symbol, predicted_action, action_confidence, 
                       predicted_direction, predicted_magnitude, prediction_timestamp
                FROM predictions 
                ORDER BY prediction_timestamp DESC 
                LIMIT 10
            """, conn)
            
            print("\n📊 RECENT PREDICTIONS SUMMARY")
            print("=" * 50)
            
            if not df.empty:
                for _, row in df.iterrows():
                    direction = "UP" if row['predicted_direction'] == 1 else "DOWN"
                    print(f"{row['symbol']:>8} | {row['predicted_action']:>4} | {row['action_confidence']:>6.1%} | {direction:>4} | {row['predicted_magnitude']:>+6.2f}%")
            else:
                print("No recent predictions found")
                
            # Accuracy summary
            outcome_df = pd.read_sql("""
                SELECT COUNT(*) as total_evaluated,
                       AVG(CASE WHEN 
                           (p.predicted_action = 'BUY' AND o.actual_return > 0) OR
                           (p.predicted_action = 'SELL' AND o.actual_return < 0) OR
                           (p.predicted_action = 'HOLD')
                       THEN 1 ELSE 0 END) as accuracy
                FROM predictions p
                JOIN outcomes o ON p.prediction_id = o.prediction_id
            """, conn)
            
            if not outcome_df.empty and outcome_df.iloc[0]['total_evaluated'] > 0:
                accuracy = outcome_df.iloc[0]['accuracy']
                total = outcome_df.iloc[0]['total_evaluated']
                print(f"\n📈 Current Accuracy: {accuracy:.1%} ({total} predictions evaluated)")
            else:
                print("\n📈 No predictions evaluated yet")
                
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error showing summary: {e}")

def main():
    """Main function"""
    try:
        processor = EnhancedTradingProcess()
        processor.run_enhanced_process()
        
    except Exception as e:
        print(f"❌ Process failed: {e}")
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
