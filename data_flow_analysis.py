#!/usr/bin/env python3
"""
Comprehensive Data Flow Analysis Tool

This script analyzes the complete data flow from morning routine to evening routine,
identifies all database tables and their relationships, and creates a comprehensive
dashboard showing the current state of all data systems.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class DataFlowAnalyzer:
    """Analyzes the complete data flow through the trading system"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.databases = {}
        self.data_sources = {}
        self.processes = {}
        
        print("🔍 COMPREHENSIVE DATA FLOW ANALYSIS")
        print("=" * 60)
        
    def discover_databases(self):
        """Discover all databases in the project"""
        print("\n📊 DISCOVERING DATABASES...")
        
        # Find all .db files (excluding archive)
        db_files = []
        for db_file in self.root_dir.rglob("*.db"):
            if "archive" not in str(db_file):
                db_files.append(db_file)
        
        print(f"Found {len(db_files)} database files:")
        
        for db_file in db_files:
            rel_path = db_file.relative_to(self.root_dir)
            print(f"  📁 {rel_path}")
            
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get record counts for each table
                table_info = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        
                        # Get column info
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        table_info[table] = {
                            'count': count,
                            'columns': columns
                        }
                    except Exception as e:
                        table_info[table] = {'count': 0, 'columns': [], 'error': str(e)}
                
                self.databases[str(rel_path)] = {
                    'path': db_file,
                    'tables': table_info
                }
                
                conn.close()
                
            except Exception as e:
                print(f"    ❌ Error reading {rel_path}: {e}")
                self.databases[str(rel_path)] = {
                    'path': db_file,
                    'error': str(e)
                }
        
        return self.databases
    
    def analyze_morning_routine_data_flow(self):
        """Analyze the morning routine data flow"""
        print("\n🌅 MORNING ROUTINE DATA FLOW ANALYSIS...")
        
        morning_processes = {
            "1. Market Data Collection": {
                "source": "Yahoo Finance API / ASX Data Feed",
                "process": "app.core.data.collectors.market_data.ASXDataFeed",
                "output_tables": ["market_data", "current_prices"],
                "data_types": ["price", "volume", "change_percent", "technical_indicators"]
            },
            "2. News Sentiment Collection": {
                "source": "News APIs / Smart Collector", 
                "process": "app.core.data.collectors.news_collector.SmartCollector",
                "output_tables": ["sentiment_features", "news_analysis"],
                "data_types": ["headlines", "sentiment_scores", "confidence_levels"]
            },
            "3. Technical Analysis": {
                "source": "Historical price data",
                "process": "technical_analysis_engine.TechnicalAnalysisEngine", 
                "output_tables": ["technical_indicators", "signals"],
                "data_types": ["rsi", "macd", "bollinger_bands", "moving_averages"]
            },
            "4. Enhanced ML Analysis": {
                "source": "Combined features",
                "process": "enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml",
                "output_tables": ["enhanced_features", "enhanced_outcomes", "predictions"],
                "data_types": ["ml_scores", "confidence_levels", "optimal_actions"]
            },
            "5. Economic Context": {
                "source": "Economic indicators",
                "process": "app.core.analysis.economic.EconomicSentimentAnalyzer",
                "output_tables": ["economic_indicators"],
                "data_types": ["interest_rates", "inflation", "market_regime"]
            }
        }
        
        for step, details in morning_processes.items():
            print(f"\n  {step}")
            print(f"    📥 Source: {details['source']}")
            print(f"    ⚙️ Process: {details['process']}")
            print(f"    📊 Output Tables: {', '.join(details['output_tables'])}")
            print(f"    🔍 Data Types: {', '.join(details['data_types'])}")
        
        self.processes['morning'] = morning_processes
        return morning_processes
    
    def analyze_evening_routine_data_flow(self):
        """Analyze the evening routine data flow"""
        print("\n🌆 EVENING ROUTINE DATA FLOW ANALYSIS...")
        
        evening_processes = {
            "1. Position Evaluation": {
                "source": "Current prices + Entry prices",
                "process": "Position evaluation logic",
                "output_tables": ["outcomes", "trading_history"],
                "data_types": ["actual_returns", "profit_loss", "win_rates"]
            },
            "2. Model Training": {
                "source": "enhanced_features + enhanced_outcomes",
                "process": "enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml",
                "output_tables": ["model_performance", "training_metrics"],
                "data_types": ["accuracy", "loss", "validation_scores"]
            },
            "3. Backtesting": {
                "source": "Historical data + ML predictions",
                "process": "Backtesting simulation",
                "output_tables": ["backtest_results", "strategy_performance"],
                "data_types": ["simulated_returns", "sharpe_ratio", "max_drawdown"]
            },
            "4. Next-Day Predictions": {
                "source": "Trained models + Current features",
                "process": "ML prediction pipeline",
                "output_tables": ["next_day_predictions", "confidence_scores"],
                "data_types": ["predicted_actions", "confidence_levels", "risk_scores"]
            }
        }
        
        for step, details in evening_processes.items():
            print(f"\n  {step}")
            print(f"    📥 Source: {details['source']}")
            print(f"    ⚙️ Process: {details['process']}")
            print(f"    📊 Output Tables: {', '.join(details['output_tables'])}")
            print(f"    🔍 Data Types: {', '.join(details['data_types'])}")
        
        self.processes['evening'] = evening_processes
        return evening_processes
    
    def check_data_consistency(self):
        """Check for data consistency issues across databases"""
        print("\n🔍 CHECKING DATA CONSISTENCY...")
        
        issues = []
        
        # Check main trading database
        main_db_path = self.root_dir / "data" / "trading_predictions.db"
        if main_db_path.exists():
            try:
                conn = sqlite3.connect(main_db_path)
                cursor = conn.cursor()
                
                # Check for missing relationships
                print("\n  📊 Checking table relationships...")
                
                # Check predictions vs outcomes
                cursor.execute("SELECT COUNT(*) FROM predictions")
                pred_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM enhanced_features")
                features_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes") 
                outcomes_count = cursor.fetchone()[0]
                
                print(f"    Predictions: {pred_count}")
                print(f"    Enhanced Features: {features_count}")
                print(f"    Enhanced Outcomes: {outcomes_count}")
                
                if pred_count != features_count:
                    issues.append(f"Mismatch: {pred_count} predictions vs {features_count} features")
                
                if features_count != outcomes_count:
                    issues.append(f"Mismatch: {features_count} features vs {outcomes_count} outcomes")
                
                # Check for null entry prices
                cursor.execute("SELECT COUNT(*) FROM predictions WHERE entry_price IS NULL OR entry_price = 0")
                null_prices = cursor.fetchone()[0]
                if null_prices > 0:
                    issues.append(f"{null_prices} predictions with null/zero entry prices")
                
                # Check for null actual returns in outcomes
                cursor.execute("SELECT COUNT(*) FROM outcomes WHERE actual_return IS NULL")
                null_returns = cursor.fetchone()[0]
                if null_returns > 0:
                    issues.append(f"{null_returns} outcomes with null actual returns")
                
                conn.close()
                
            except Exception as e:
                issues.append(f"Error checking main database: {e}")
        else:
            issues.append("Main trading database not found")
        
        if issues:
            print("\n  ⚠️ Data consistency issues found:")
            for issue in issues:
                print(f"    • {issue}")
        else:
            print("\n  ✅ No data consistency issues found")
        
        return issues
    
    def identify_data_leakage_risks(self):
        """Identify potential data leakage risks when running multiple times"""
        print("\n🚨 IDENTIFYING DATA LEAKAGE RISKS...")
        
        risks = []
        
        # Check for duplicate prevention mechanisms
        main_db_path = self.root_dir / "data" / "trading_predictions.db"
        if main_db_path.exists():
            try:
                conn = sqlite3.connect(main_db_path)
                cursor = conn.cursor()
                
                # Check for duplicate predictions on same day
                cursor.execute("""
                    SELECT symbol, DATE(prediction_timestamp), COUNT(*) 
                    FROM predictions 
                    GROUP BY symbol, DATE(prediction_timestamp)
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                
                if duplicates:
                    risks.append(f"Found {len(duplicates)} days with duplicate predictions")
                    for symbol, date, count in duplicates[:5]:  # Show first 5
                        print(f"    • {symbol} on {date}: {count} predictions")
                
                # Check for overlapping time periods in features
                cursor.execute("""
                    SELECT COUNT(*) as overlapping_features
                    FROM enhanced_features f1, enhanced_features f2 
                    WHERE f1.id != f2.id 
                    AND f1.symbol = f2.symbol 
                    AND ABS(julianday(f1.analysis_timestamp) - julianday(f2.analysis_timestamp)) < 0.25
                """)
                overlapping = cursor.fetchone()[0]
                if overlapping > 0:
                    risks.append(f"{overlapping} potentially overlapping feature records")
                
                # Check for future data leakage (outcomes recorded before prediction)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM enhanced_features f
                    JOIN enhanced_outcomes o ON f.id = o.feature_id
                    WHERE o.created_at < f.analysis_timestamp
                """)
                future_leakage = cursor.fetchone()[0]
                if future_leakage > 0:
                    risks.append(f"{future_leakage} outcomes recorded before their features")
                
                conn.close()
                
            except Exception as e:
                risks.append(f"Error checking data leakage: {e}")
        
        if risks:
            print("\n  ⚠️ Potential data leakage risks:")
            for risk in risks:
                print(f"    • {risk}")
            
            print("\n  💡 Recommendations:")
            print("    • Implement idempotent operations with date-based deduplication")
            print("    • Add unique constraints on (symbol, date) combinations")
            print("    • Use transaction rollback on duplicate detection")
            print("    • Implement feature extraction versioning")
        else:
            print("\n  ✅ No obvious data leakage risks detected")
        
        return risks
    
    def generate_table_dashboard_data(self):
        """Generate data for comprehensive table dashboard"""
        print("\n📊 GENERATING TABLE DASHBOARD DATA...")
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'databases': {},
            'summary': {
                'total_databases': 0,
                'total_tables': 0,
                'total_records': 0,
                'main_tables': {},
                'data_flow_health': 'UNKNOWN'
            }
        }
        
        total_records = 0
        total_tables = 0
        
        for db_name, db_info in self.databases.items():
            if 'error' not in db_info:
                db_summary = {
                    'tables': {},
                    'total_records': 0,
                    'last_updated': None
                }
                
                for table_name, table_info in db_info['tables'].items():
                    if 'error' not in table_info:
                        count = table_info['count']
                        columns = table_info['columns']
                        
                        db_summary['tables'][table_name] = {
                            'record_count': count,
                            'columns': columns,
                            'column_count': len(columns)
                        }
                        
                        db_summary['total_records'] += count
                        total_records += count
                        total_tables += 1
                        
                        # Check for timestamp columns to determine last update
                        timestamp_cols = [col for col in columns if 'timestamp' in col.lower() or 'created_at' in col.lower()]
                        if timestamp_cols and count > 0:
                            try:
                                conn = sqlite3.connect(db_info['path'])
                                cursor = conn.cursor()
                                cursor.execute(f"SELECT MAX({timestamp_cols[0]}) FROM {table_name}")
                                last_update = cursor.fetchone()[0]
                                if last_update:
                                    db_summary['last_updated'] = last_update
                                conn.close()
                            except:
                                pass
                
                dashboard_data['databases'][db_name] = db_summary
        
        dashboard_data['summary']['total_databases'] = len(self.databases)
        dashboard_data['summary']['total_tables'] = total_tables
        dashboard_data['summary']['total_records'] = total_records
        
        # Focus on main trading database
        main_db_key = None
        for db_name in self.databases.keys():
            if 'trading_predictions.db' in db_name and 'data/' in db_name:
                main_db_key = db_name
                break
        
        if main_db_key and main_db_key in dashboard_data['databases']:
            main_tables = dashboard_data['databases'][main_db_key]['tables']
            dashboard_data['summary']['main_tables'] = {
                'predictions': main_tables.get('predictions', {}).get('record_count', 0),
                'enhanced_features': main_tables.get('enhanced_features', {}).get('record_count', 0),
                'enhanced_outcomes': main_tables.get('enhanced_outcomes', {}).get('record_count', 0),
                'outcomes': main_tables.get('outcomes', {}).get('record_count', 0)
            }
            
            # Determine data flow health
            pred_count = dashboard_data['summary']['main_tables']['predictions']
            features_count = dashboard_data['summary']['main_tables']['enhanced_features']
            outcomes_count = dashboard_data['summary']['main_tables']['enhanced_outcomes']
            
            if pred_count > 0 and features_count > 0 and outcomes_count > 0:
                if abs(pred_count - features_count) <= 1 and abs(features_count - outcomes_count) <= 1:
                    dashboard_data['summary']['data_flow_health'] = 'EXCELLENT'
                else:
                    dashboard_data['summary']['data_flow_health'] = 'GOOD'
            elif pred_count > 0 and features_count > 0:
                dashboard_data['summary']['data_flow_health'] = 'FAIR'
            elif pred_count > 0:
                dashboard_data['summary']['data_flow_health'] = 'POOR'
            else:
                dashboard_data['summary']['data_flow_health'] = 'NO_DATA'
        
        return dashboard_data
    
    def run_comprehensive_analysis(self):
        """Run the complete data flow analysis"""
        print("Starting comprehensive data flow analysis...")
        
        # Step 1: Discover all databases
        self.discover_databases()
        
        # Step 2: Analyze morning routine data flow
        self.analyze_morning_routine_data_flow()
        
        # Step 3: Analyze evening routine data flow  
        self.analyze_evening_routine_data_flow()
        
        # Step 4: Check data consistency
        consistency_issues = self.check_data_consistency()
        
        # Step 5: Identify data leakage risks
        leakage_risks = self.identify_data_leakage_risks()
        
        # Step 6: Generate dashboard data
        dashboard_data = self.generate_table_dashboard_data()
        
        # Save analysis results
        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'databases': self.databases,
            'processes': self.processes,
            'consistency_issues': consistency_issues,
            'leakage_risks': leakage_risks,
            'dashboard_data': dashboard_data
        }
        
        # Save to file
        output_file = self.root_dir / "data_flow_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n💾 Analysis results saved to: {output_file}")
        
        # Print summary
        print("\n📋 ANALYSIS SUMMARY")
        print("=" * 40)
        print(f"Databases discovered: {len(self.databases)}")
        print(f"Total tables: {dashboard_data['summary']['total_tables']}")
        print(f"Total records: {dashboard_data['summary']['total_records']:,}")
        print(f"Data flow health: {dashboard_data['summary']['data_flow_health']}")
        print(f"Consistency issues: {len(consistency_issues)}")
        print(f"Data leakage risks: {len(leakage_risks)}")
        
        return analysis_results

def main():
    """Main function to run the analysis"""
    analyzer = DataFlowAnalyzer()
    results = analyzer.run_comprehensive_analysis()
    
    print("\n✅ Data flow analysis complete!")
    print("💡 Next step: Create comprehensive table dashboard")
    
    return results

if __name__ == "__main__":
    main()
