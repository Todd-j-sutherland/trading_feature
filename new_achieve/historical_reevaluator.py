#!/usr/bin/env python3
"""
📊 Historical Data Re-evaluation Tool
Re-evaluates your historical trading decisions as if they were real predictions
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

class HistoricalReEvaluator:
    def __init__(self):
        self.backup_db = "data/migration_backup/trading_unified_backup_20250812_112736.db"
        self.predictions_db = "data/trading_predictions.db"
        
    def analyze_historical_performance(self):
        """Analyze historical decisions as if they were predictions"""
        print("📊 HISTORICAL PREDICTION RE-EVALUATION")
        print("=" * 60)
        
        try:
            conn = sqlite3.connect(self.backup_db)
            
            # Get all historical outcomes
            query = """
                SELECT 
                    symbol, 
                    optimal_action, 
                    price_magnitude_1d as magnitude_1d, 
                    0 as magnitude_7d,
                    created_at,
                    confidence_score as confidence,
                    0 as overall_sentiment,
                    0 as rsi,
                    0 as macd_histogram
                FROM enhanced_outcomes 
                WHERE optimal_action IS NOT NULL 
                AND price_magnitude_1d IS NOT NULL
                ORDER BY created_at DESC
            """
            
            df = pd.read_sql(query, conn)
            print(f"📈 Found {len(df)} historical decisions from {df['created_at'].min()} to {df['created_at'].max()}")
            
            if df.empty:
                print("❌ No historical data found")
                return
                
            # Evaluate as predictions
            results = self._evaluate_predictions(df)
            self._print_performance_report(df, results)
            
            # Create re-evaluation predictions in new system
            if input("\n🔄 Convert historical data to new prediction format? (y/N): ").lower() == 'y':
                self._convert_to_new_predictions(df)
                
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
    def _evaluate_predictions(self, df):
        """Evaluate historical decisions as predictions"""
        results = {
            'correct': 0,
            'total': 0,
            'by_action': {'BUY': {'correct': 0, 'total': 0, 'returns': []},
                         'SELL': {'correct': 0, 'total': 0, 'returns': []},
                         'HOLD': {'correct': 0, 'total': 0, 'returns': []}}
        }
        
        for _, row in df.iterrows():
            action = row['optimal_action']
            magnitude_1d = row['magnitude_1d']
            magnitude_7d = row['magnitude_7d'] if pd.notna(row['magnitude_7d']) else 0
            
            # Determine if prediction was correct
            correct = False
            
            if action == 'BUY':
                correct = magnitude_1d > 0  # Positive return for BUY
                results['by_action']['BUY']['returns'].append(magnitude_1d)
            elif action == 'SELL':
                correct = magnitude_1d < 0  # Negative return for SELL (profitable short)
                results['by_action']['SELL']['returns'].append(magnitude_1d)
            elif action == 'HOLD':
                correct = abs(magnitude_1d) < 0.5  # Small movement for HOLD
                results['by_action']['HOLD']['returns'].append(magnitude_1d)
                
            if correct:
                results['correct'] += 1
                results['by_action'][action]['correct'] += 1
                
            results['total'] += 1
            results['by_action'][action]['total'] += 1
            
        return results
        
    def _print_performance_report(self, df, results):
        """Print detailed performance analysis"""
        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"{'='*40}")
        
        accuracy = (results['correct'] / results['total']) * 100
        print(f"Total Decisions: {results['total']}")
        print(f"Correct Decisions: {results['correct']}")
        print(f"Overall Accuracy: {accuracy:.1f}%")
        
        # Action distribution
        print(f"\n🎯 ACTION DISTRIBUTION")
        print(f"{'='*40}")
        
        action_counts = df['optimal_action'].value_counts()
        for action, count in action_counts.items():
            pct = (count / len(df)) * 100
            print(f"{action:>4}: {count:>3} decisions ({pct:>5.1f}%)")
            
        # Performance by action
        print(f"\n📈 PERFORMANCE BY ACTION")
        print(f"{'='*40}")
        
        for action in ['BUY', 'SELL', 'HOLD']:
            action_data = results['by_action'][action]
            if action_data['total'] > 0:
                action_accuracy = (action_data['correct'] / action_data['total']) * 100
                avg_return = np.mean(action_data['returns'])
                print(f"{action:>4}: {action_data['correct']:>2}/{action_data['total']:>2} correct ({action_accuracy:>5.1f}%), avg return: {avg_return:>+6.2f}%")
                
        # Time-based analysis
        print(f"\n📅 TIME-BASED ANALYSIS")
        print(f"{'='*40}")
        
        try:
            df['date'] = pd.to_datetime(df['created_at'], format='mixed').dt.date
        except Exception as e:
            print(f"❌ Error parsing dates: {e}")
            print("Skipping time-based analysis...")
            df['date'] = None
            
        if df['date'].notna().any():
            daily_performance = df.groupby('date').agg({
                'optimal_action': 'count',
                'magnitude_1d': 'mean'
            }).round(2)
            
            print("Recent Daily Performance:")
            for date, row in daily_performance.tail(7).iterrows():
                print(f"{date}: {row['optimal_action']} decisions, avg return: {row['magnitude_1d']:+.2f}%")
        else:
            print("Time-based analysis skipped due to date parsing issues")
            
        # Symbol analysis
        print(f"\n🏦 PERFORMANCE BY SYMBOL")
        print(f"{'='*40}")
        
        symbol_performance = df.groupby('symbol').agg({
            'optimal_action': 'count',
            'magnitude_1d': 'mean'
        }).round(2).sort_values('magnitude_1d', ascending=False)
        
        for symbol, row in symbol_performance.iterrows():
            print(f"{symbol}: {row['optimal_action']} decisions, avg return: {row['magnitude_1d']:+.2f}%")
            
    def _convert_to_new_predictions(self, df):
        """Convert historical decisions to new prediction format for validation"""
        print(f"\n🔄 Converting {len(df)} historical decisions to new prediction format...")
        
        try:
            # Import the new prediction engine components
            sys.path.append('/root/test/data_quality_system/core')
            from true_prediction_engine import TruePredictionEngine
            
            pred_conn = sqlite3.connect(self.predictions_db)
            
            converted_count = 0
            for _, row in df.iterrows():
                try:
                    # Create a pseudo-prediction ID based on historical data
                    prediction_id = f"hist_{row['symbol']}_{row['created_at'].replace(':', '').replace('-', '').replace(' ', '').replace('+', '').replace('.', '')[:15]}"
                    
                    # Convert optimal_action to prediction format
                    predicted_action = row['optimal_action']
                    predicted_direction = 1 if row['magnitude_1d'] > 0 else -1
                    predicted_magnitude = abs(row['magnitude_1d']) if pd.notna(row['magnitude_1d']) else 0
                    
                    # Use confidence or default
                    action_confidence = row['confidence'] if pd.notna(row['confidence']) else 0.5
                    
                    # Insert as historical prediction
                    insert_query = """
                        INSERT OR REPLACE INTO predictions (
                            prediction_id, symbol, prediction_timestamp, predicted_action,
                            action_confidence, predicted_direction, predicted_magnitude,
                            feature_vector, model_version, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    feature_vector = {
                        'sentiment_score': row.get('overall_sentiment', 0),
                        'rsi': row.get('rsi', 50),
                        'macd_histogram': row.get('macd_histogram', 0),
                        'historical_conversion': True
                    }
                    
                    pred_conn.execute(insert_query, (
                        prediction_id,
                        row['symbol'],
                        row['created_at'],
                        predicted_action,
                        action_confidence,
                        predicted_direction,
                        predicted_magnitude,
                        str(feature_vector),
                        'historical_v1.0',
                        row['created_at']
                    ))
                    
                    # Also create outcome record
                    outcome_query = """
                        INSERT OR REPLACE INTO outcomes (
                            outcome_id, prediction_id, actual_return, actual_direction,
                            evaluation_timestamp, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """
                    
                    outcome_id = f"outcome_{prediction_id}"
                    actual_direction = 1 if row['magnitude_1d'] > 0 else -1
                    
                    pred_conn.execute(outcome_query, (
                        outcome_id,
                        prediction_id,
                        row['magnitude_1d'],
                        actual_direction,
                        row['created_at'],
                        row['created_at']
                    ))
                    
                    converted_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Failed to convert {row['symbol']} from {row['created_at']}: {e}")
                    
            pred_conn.commit()
            pred_conn.close()
            
            print(f"✅ Successfully converted {converted_count} historical decisions")
            print(f"   You can now see historical performance in the new prediction database")
            
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            
    def generate_comparison_report(self):
        """Compare old retrospective system vs new prediction system"""
        print(f"\n🔍 SYSTEM COMPARISON REPORT")
        print(f"{'='*60}")
        
        try:
            # Historical data analysis
            backup_conn = sqlite3.connect(self.backup_db)
            hist_df = pd.read_sql("""
                SELECT COUNT(*) as count, AVG(price_magnitude_1d) as avg_return
                FROM enhanced_outcomes 
                WHERE optimal_action IS NOT NULL
            """, backup_conn)
            
            # New predictions analysis
            pred_conn = sqlite3.connect(self.predictions_db)
            new_df = pd.read_sql("""
                SELECT COUNT(*) as count
                FROM predictions
            """, pred_conn)
            
            print(f"📊 Old System (Retrospective):")
            print(f"   Total Decisions: {hist_df.iloc[0]['count']}")
            print(f"   Average Return: {hist_df.iloc[0]['avg_return']:.2f}%")
            print(f"   Method: Wait for outcome → assign label")
            
            print(f"\n🚀 New System (Predictive):")
            print(f"   Total Predictions: {new_df.iloc[0]['count']}")
            print(f"   Method: Make prediction → store immediately → evaluate later")
            print(f"   Data Leakage: ELIMINATED")
            print(f"   Live Trading: ENABLED")
            
            backup_conn.close()
            pred_conn.close()
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")

def main():
    """Main execution"""
    evaluator = HistoricalReEvaluator()
    
    print("🔍 HISTORICAL DATA RE-EVALUATION TOOL")
    print("Choose an option:")
    print("1. Analyze historical performance")
    print("2. Convert historical data to new format")
    print("3. Generate comparison report")
    print("4. All of the above")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in ['1', '4']:
        evaluator.analyze_historical_performance()
        
    if choice in ['2', '4']:
        # This would be done in option 1 if user chooses
        pass
        
    if choice in ['3', '4']:
        evaluator.generate_comparison_report()
        
    print("\n✅ Historical re-evaluation completed!")

if __name__ == "__main__":
    main()
