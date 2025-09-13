#!/usr/bin/env python3
"""
Historical Paper Trading Performance Analysis
Analyze existing trading data to understand system performance before today's HOLD bias issue
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

class HistoricalPerformanceAnalyzer:
    """Analyze historical paper trading performance from local databases"""
    
    def __init__(self):
        self.databases = self._find_databases()
        self.performance_data = {}
        
    def _find_databases(self):
        """Find all available database files"""
        base_path = Path(".")
        
        db_paths = {
            'enhanced_outcomes': 'data/enhanced_outcomes.db',
            'ig_markets': 'data/ig_markets_paper_trades.db', 
            'outcomes': 'data/outcomes.db',
            'training_data': 'data/ml_models/training_data.db'
        }
        
        available_dbs = {}
        for name, path in db_paths.items():
            full_path = base_path / path
            if full_path.exists():
                available_dbs[name] = str(full_path)
                print(f"✅ Found database: {name} at {path}")
            else:
                print(f"❌ Missing database: {name} at {path}")
        
        return available_dbs
    
    def analyze_enhanced_outcomes(self):
        """Analyze enhanced outcomes database for ML performance"""
        if 'enhanced_outcomes' not in self.databases:
            return None
        
        try:
            conn = sqlite3.connect(self.databases['enhanced_outcomes'])
            
            # Get table schema first
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            print(f"\n📊 Enhanced Outcomes Database Tables: {list(tables['name'])}")
            
            # Try to get all data from main table
            try:
                query = "SELECT * FROM enhanced_outcomes ORDER BY created_at DESC LIMIT 100"
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    print("❌ No data in enhanced_outcomes table")
                    conn.close()
                    return None
                
                print(f"✅ Found {len(df)} enhanced outcome records")
                print(f"📅 Date range: {df['created_at'].min()} to {df['created_at'].max()}")
                
                # Analyze performance metrics
                performance = self._analyze_outcome_performance(df)
                conn.close()
                return performance
                
            except Exception as e:
                print(f"❌ Error querying enhanced_outcomes: {e}")
                # Try alternative queries
                conn.close()
                return None
                
        except Exception as e:
            print(f"❌ Error connecting to enhanced_outcomes database: {e}")
            return None
    
    def analyze_ig_markets_trades(self):
        """Analyze IG Markets paper trading database"""
        if 'ig_markets' not in self.databases:
            return None
        
        try:
            conn = sqlite3.connect(self.databases['ig_markets'])
            
            # Get table schema
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            print(f"\n💼 IG Markets Database Tables: {list(tables['name'])}")
            
            # Analyze trades if available
            for table in ['paper_trades', 'trades', 'positions']:
                try:
                    query = f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 50"
                    df = pd.read_sql_query(query, conn)
                    
                    if not df.empty:
                        print(f"✅ Found {len(df)} records in {table}")
                        performance = self._analyze_trade_performance(df, table)
                        conn.close()
                        return performance
                        
                except Exception as e:
                    print(f"❌ No {table} table or error: {e}")
                    continue
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"❌ Error connecting to IG Markets database: {e}")
            return None
    
    def analyze_general_outcomes(self):
        """Analyze general outcomes database"""
        if 'outcomes' not in self.databases:
            return None
        
        try:
            conn = sqlite3.connect(self.databases['outcomes'])
            
            # Get table schema
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            print(f"\n📈 General Outcomes Database Tables: {list(tables['name'])}")
            
            # Try outcomes table
            try:
                query = "SELECT * FROM outcomes ORDER BY rowid DESC LIMIT 100"
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    print(f"✅ Found {len(df)} outcome records")
                    performance = self._analyze_general_outcomes(df)
                    conn.close()
                    return performance
                    
            except Exception as e:
                print(f"❌ Error querying outcomes: {e}")
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"❌ Error connecting to outcomes database: {e}")
            return None
    
    def _analyze_outcome_performance(self, df):
        """Analyze performance from enhanced outcomes data"""
        performance = {
            'database': 'enhanced_outcomes',
            'total_records': len(df),
            'date_range': {
                'start': df['created_at'].min(),
                'end': df['created_at'].max()
            }
        }
        
        # Try to identify key columns for analysis
        columns = df.columns.tolist()
        print(f"📋 Available columns: {columns}")
        
        # Look for prediction accuracy indicators
        if 'actual_return' in columns and 'predicted_action' in columns:
            # Calculate success rate
            df['actual_return'] = pd.to_numeric(df['actual_return'], errors='coerce')
            
            # Define success based on predicted action
            successful_predictions = 0
            total_predictions = 0
            
            for _, row in df.iterrows():
                if pd.notna(row['actual_return']) and pd.notna(row['predicted_action']):
                    total_predictions += 1
                    actual_return = row['actual_return']
                    predicted_action = row['predicted_action']
                    
                    # Define success criteria
                    if predicted_action == 'BUY' and actual_return > 0:
                        successful_predictions += 1
                    elif predicted_action == 'SELL' and actual_return < 0:
                        successful_predictions += 1
                    elif predicted_action == 'HOLD' and abs(actual_return) < 1.0:
                        successful_predictions += 1
            
            if total_predictions > 0:
                success_rate = successful_predictions / total_predictions
                performance['ml_accuracy'] = {
                    'success_rate': success_rate,
                    'successful_predictions': successful_predictions,
                    'total_predictions': total_predictions
                }
        
        # Analyze returns distribution
        if 'actual_return' in columns:
            returns = pd.to_numeric(df['actual_return'], errors='coerce').dropna()
            if len(returns) > 0:
                performance['return_analysis'] = {
                    'mean_return': returns.mean(),
                    'median_return': returns.median(),
                    'std_return': returns.std(),
                    'positive_returns': (returns > 0).sum(),
                    'negative_returns': (returns < 0).sum(),
                    'total_returns': len(returns)
                }
        
        # Analyze prediction distribution
        if 'predicted_action' in columns:
            action_counts = df['predicted_action'].value_counts()
            performance['prediction_distribution'] = action_counts.to_dict()
        
        return performance
    
    def _analyze_trade_performance(self, df, table_name):
        """Analyze performance from trading data"""
        performance = {
            'database': 'ig_markets',
            'table': table_name,
            'total_records': len(df)
        }
        
        columns = df.columns.tolist()
        print(f"📋 {table_name} columns: {columns}")
        
        # Look for common trading columns
        profit_columns = [col for col in columns if 'profit' in col.lower() or 'pnl' in col.lower()]
        if profit_columns:
            profit_col = profit_columns[0]
            profits = pd.to_numeric(df[profit_col], errors='coerce').dropna()
            
            if len(profits) > 0:
                performance['trading_performance'] = {
                    'total_profit': profits.sum(),
                    'average_profit': profits.mean(),
                    'profitable_trades': (profits > 0).sum(),
                    'losing_trades': (profits < 0).sum(),
                    'total_trades': len(profits),
                    'win_rate': (profits > 0).sum() / len(profits)
                }
        
        return performance
    
    def _analyze_general_outcomes(self, df):
        """Analyze general outcomes data"""
        performance = {
            'database': 'outcomes',
            'total_records': len(df)
        }
        
        columns = df.columns.tolist()
        print(f"📋 Outcomes columns: {columns}")
        
        # Basic analysis of available data
        for col in columns:
            if df[col].dtype in ['int64', 'float64']:
                values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(values) > 0:
                    performance[f'{col}_stats'] = {
                        'mean': values.mean(),
                        'min': values.min(),
                        'max': values.max(),
                        'count': len(values)
                    }
        
        return performance
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("🏆 Historical Paper Trading Performance Analysis")
        print("=" * 55)
        
        # Analyze all available databases
        results = {}
        
        print("\n1. Enhanced Outcomes Analysis:")
        results['enhanced_outcomes'] = self.analyze_enhanced_outcomes()
        
        print("\n2. IG Markets Trading Analysis:")
        results['ig_markets'] = self.analyze_ig_markets_trades()
        
        print("\n3. General Outcomes Analysis:")
        results['outcomes'] = self.analyze_general_outcomes()
        
        # Generate summary
        self._generate_summary(results)
        
        # Save report
        self._save_report(results)
        
        return results
    
    def _generate_summary(self, results):
        """Generate performance summary"""
        print("\n📊 PERFORMANCE SUMMARY")
        print("-" * 25)
        
        # Check for ML accuracy data
        ml_accuracy = None
        for db_name, data in results.items():
            if data and 'ml_accuracy' in data:
                ml_accuracy = data['ml_accuracy']
                print(f"✅ ML Model Performance (from {db_name}):")
                print(f"   Success Rate: {ml_accuracy['success_rate']:.1%}")
                print(f"   Successful Predictions: {ml_accuracy['successful_predictions']}")
                print(f"   Total Predictions: {ml_accuracy['total_predictions']}")
                break
        
        if not ml_accuracy:
            print("❌ No ML accuracy data found in available databases")
        
        # Check for trading performance
        trading_performance = None
        for db_name, data in results.items():
            if data and 'trading_performance' in data:
                trading_performance = data['trading_performance']
                print(f"✅ Trading Performance (from {db_name}):")
                print(f"   Win Rate: {trading_performance['win_rate']:.1%}")
                print(f"   Total Profit: ${trading_performance['total_profit']:.2f}")
                print(f"   Average Trade: ${trading_performance['average_profit']:.2f}")
                print(f"   Total Trades: {trading_performance['total_trades']}")
                break
        
        if not trading_performance:
            print("❌ No trading performance data found in available databases")
        
        # Check for prediction distribution
        prediction_dist = None
        for db_name, data in results.items():
            if data and 'prediction_distribution' in data:
                prediction_dist = data['prediction_distribution']
                print(f"✅ Prediction Distribution (from {db_name}):")
                total_preds = sum(prediction_dist.values())
                for action, count in prediction_dist.items():
                    percentage = count / total_preds * 100
                    print(f"   {action}: {count} ({percentage:.1f}%)")
                break
        
        if not prediction_dist:
            print("❌ No prediction distribution data found")
        
        # Overall assessment
        print(f"\n🎯 SYSTEM ASSESSMENT:")
        if ml_accuracy and ml_accuracy['success_rate'] > 0.6:
            print("✅ Strong ML Performance: >60% accuracy")
        elif ml_accuracy and ml_accuracy['success_rate'] > 0.5:
            print("⚠️ Moderate ML Performance: >50% accuracy")
        elif ml_accuracy:
            print("❌ Poor ML Performance: <50% accuracy")
        else:
            print("❓ ML Performance: Unknown (no data)")
        
        if trading_performance and trading_performance['win_rate'] > 0.6:
            print("✅ Strong Trading Performance: >60% win rate")
        elif trading_performance and trading_performance['win_rate'] > 0.5:
            print("⚠️ Moderate Trading Performance: >50% win rate")
        elif trading_performance:
            print("❌ Poor Trading Performance: <50% win rate")
        else:
            print("❓ Trading Performance: Unknown (no data)")
    
    def _save_report(self, results):
        """Save detailed report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"historical_performance_report_{timestamp}.json"
        
        # Prepare report data
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'databases_analyzed': list(self.databases.keys()),
            'results': results,
            'summary': {
                'has_ml_accuracy': any('ml_accuracy' in (data or {}) for data in results.values()),
                'has_trading_performance': any('trading_performance' in (data or {}) for data in results.values()),
                'total_databases': len(self.databases)
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 Detailed report saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Error saving report: {e}")

def main():
    """Main analysis function"""
    print("📈 Historical Paper Trading Performance Analysis")
    print("=" * 50)
    
    analyzer = HistoricalPerformanceAnalyzer()
    
    if not analyzer.databases:
        print("❌ No trading databases found!")
        print("Make sure you're running from the correct directory with database files.")
        return
    
    try:
        results = analyzer.generate_performance_report()
        
        print(f"\n🎯 CONCLUSION:")
        print("This analysis shows historical performance before today's HOLD bias issue.")
        print("Compare this baseline with current 100% HOLD predictions to measure impact.")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()