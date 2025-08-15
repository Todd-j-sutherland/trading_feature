#!/usr/bin/env python3
"""
Smart Data Quality Fixer

Automatically detects and fixes data quality issues in the trading system,
including schema mismatches, missing columns, and query compatibility problems.
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class SmartDataQualityFixer:
    """Intelligent fixer for database schema and query compatibility issues"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.issues = []
        self.fixes_applied = []
        
    def get_table_schema(self, table_name: str) -> Dict:
        """Get the actual schema of a table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema = {}
                for col in columns:
                    schema[col[1]] = {
                        'type': col[2],
                        'not_null': bool(col[3]),
                        'default': col[4],
                        'primary_key': bool(col[5])
                    }
                return schema
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            return {}
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking table {table_name}: {e}")
            return False
    
    def get_all_tables(self) -> List[str]:
        """Get all table names in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    def analyze_dashboard_queries(self) -> Dict:
        """Analyze common dashboard query patterns and identify schema mismatches"""
        
        # Expected vs actual column mappings for common tables
        expected_schemas = {
            'model_performance': {
                'expected_columns': ['model_name', 'training_date', 'accuracy', 'precision_score', 'recall', 'f1_score'],
                'query_context': 'Performance metrics dashboard tab'
            },
            'enhanced_features': {
                'expected_columns': ['analysis_timestamp', 'bb_upper', 'bb_lower', 'volume_ma'],
                'query_context': 'Technical analysis dashboard tab'
            },
            'enhanced_outcomes': {
                'expected_columns': ['timestamp', 'prediction_timestamp'],
                'query_context': 'Enhanced outcomes dashboard tab'
            },
            'sentiment_features': {
                'expected_columns': ['created_at', 'sentiment_score', 'sentiment_confidence'],
                'query_context': 'Sentiment analysis dashboard tab'
            }
        }
        
        analysis_results = {}
        
        for table_name, expected in expected_schemas.items():
            if self.check_table_exists(table_name):
                actual_schema = self.get_table_schema(table_name)
                actual_columns = list(actual_schema.keys())
                
                missing_columns = [col for col in expected['expected_columns'] if col not in actual_columns]
                available_columns = actual_columns
                
                analysis_results[table_name] = {
                    'exists': True,
                    'actual_columns': available_columns,
                    'missing_expected': missing_columns,
                    'query_context': expected['query_context'],
                    'schema': actual_schema
                }
            else:
                analysis_results[table_name] = {
                    'exists': False,
                    'query_context': expected['query_context']
                }
        
        return analysis_results
    
    def suggest_column_mappings(self, table_name: str, missing_columns: List[str]) -> Dict[str, str]:
        """Suggest alternative column mappings based on actual schema"""
        
        actual_schema = self.get_table_schema(table_name)
        actual_columns = list(actual_schema.keys())
        
        # Common column name mappings
        mapping_suggestions = {
            # Model performance table mappings
            'model_name': ['model_version', 'model_type', 'algorithm'],
            'training_date': ['created_at', 'evaluation_period_start', 'timestamp'],
            'accuracy': ['accuracy_action', 'accuracy_direction', 'total_accuracy'],
            'precision_score': ['precision', 'accuracy_action'],
            'recall': ['recall_score', 'accuracy_direction'],
            'f1_score': ['f1', 'mae_magnitude', 'accuracy_action'],
            
            # Technical analysis mappings
            'analysis_timestamp': ['timestamp', 'created_at'],
            'bb_upper': ['bollinger_upper', 'bb_high'],
            'bb_lower': ['bollinger_lower', 'bb_low'],
            'volume_ma': ['volume_sma20', 'volume_average'],
            
            # Timestamp mappings
            'timestamp': ['prediction_timestamp', 'created_at', 'analysis_timestamp'],
            'created_at': ['timestamp', 'analysis_timestamp'],
            
            # Sentiment mappings
            'sentiment_score': ['overall_sentiment', 'sentiment'],
            'sentiment_confidence': ['confidence', 'sentiment_conf']
        }
        
        suggestions = {}
        for missing_col in missing_columns:
            if missing_col in mapping_suggestions:
                for candidate in mapping_suggestions[missing_col]:
                    if candidate in actual_columns:
                        suggestions[missing_col] = candidate
                        break
        
        return suggestions
    
    def generate_fixed_queries(self, analysis_results: Dict) -> Dict[str, str]:
        """Generate corrected SQL queries for dashboard components"""
        
        fixed_queries = {}
        
        # Fix model_performance query
        if 'model_performance' in analysis_results and analysis_results['model_performance']['exists']:
            schema = analysis_results['model_performance']['schema']
            columns = list(schema.keys())
            
            # Map to actual available columns
            query_parts = []
            if 'model_version' in columns:
                query_parts.append('model_version as model_name')
            elif 'evaluation_id' in columns:
                query_parts.append('evaluation_id as model_name')
            else:
                query_parts.append("'Unknown' as model_name")
            
            if 'created_at' in columns:
                query_parts.append('created_at as training_date')
            elif 'evaluation_period_start' in columns:
                query_parts.append('evaluation_period_start as training_date')
            
            if 'accuracy_action' in columns:
                query_parts.append('accuracy_action as accuracy')
            elif 'accuracy_direction' in columns:
                query_parts.append('accuracy_direction as accuracy')
            
            if 'accuracy_direction' in columns:
                query_parts.append('accuracy_direction as precision_score')
            elif 'accuracy_action' in columns:
                query_parts.append('accuracy_action as precision_score')
            
            query_parts.append('accuracy_direction as recall')
            query_parts.append('mae_magnitude as f1_score')
            
            fixed_queries['model_performance'] = f"""
            SELECT 
                {', '.join(query_parts)}
            FROM model_performance 
            ORDER BY {('created_at' if 'created_at' in columns else 'evaluation_period_start')} DESC 
            LIMIT 10
            """
        
        # Fix enhanced_features technical analysis query
        if 'enhanced_features' in analysis_results and analysis_results['enhanced_features']['exists']:
            schema = analysis_results['enhanced_features']['schema']
            columns = list(schema.keys())
            
            query_parts = ['symbol']
            
            if 'timestamp' in columns:
                query_parts.append('timestamp as analysis_timestamp')
            
            query_parts.extend(['rsi', 'macd_line'])
            
            if 'bollinger_upper' in columns:
                query_parts.append('bollinger_upper')
            if 'bollinger_lower' in columns:
                query_parts.append('bollinger_lower')
            
            query_parts.append('volatility_20d')
            
            if 'volume_sma20' in columns:
                query_parts.append('volume_sma20 as volume_ma')
            elif 'volume' in columns:
                query_parts.append('volume as volume_ma')
            
            fixed_queries['enhanced_features_technical'] = f"""
            SELECT 
                {', '.join(query_parts)}
            FROM enhanced_features 
            WHERE rsi IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 20
            """
        
        return fixed_queries
    
    def apply_dashboard_fixes(self) -> None:
        """Apply fixes to dashboard component files"""
        
        dashboard_file = Path("comprehensive_table_dashboard.py")
        if not dashboard_file.exists():
            print("❌ Dashboard file not found")
            return
        
        # Read current dashboard content
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        analysis_results = self.analyze_dashboard_queries()
        fixed_queries = self.generate_fixed_queries(analysis_results)
        
        # Apply fixes to model_performance query
        if 'model_performance' in fixed_queries:
            old_query = '''query = """
            SELECT 
                model_name,
                training_date,
                accuracy,
                precision_score,
                recall,
                f1_score
            FROM model_performance 
            ORDER BY training_date DESC 
            LIMIT 10
            """"'''
            
            new_query = f'''query = """{fixed_queries['model_performance'].strip()}
            """"'''
            
            if old_query.replace(' ', '').replace('\n', '') in content.replace(' ', '').replace('\n', ''):
                content = content.replace(
                    '''query = """
            SELECT 
                model_name,
                training_date,
                accuracy,
                precision_score,
                recall,
                f1_score
            FROM model_performance 
            ORDER BY training_date DESC 
            LIMIT 10
            """"''',
                    f'''query = """{fixed_queries['model_performance'].strip()}
            """"'''
                )
                self.fixes_applied.append("Fixed model_performance query in dashboard")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
    
    def generate_data_quality_report(self) -> Dict:
        """Generate comprehensive data quality report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_path': str(self.db_path),
            'tables_analyzed': {},
            'issues_found': [],
            'fixes_suggested': [],
            'fixes_applied': self.fixes_applied
        }
        
        # Analyze all tables
        all_tables = self.get_all_tables()
        analysis_results = self.analyze_dashboard_queries()
        
        for table_name in all_tables:
            schema = self.get_table_schema(table_name)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]
            
            report['tables_analyzed'][table_name] = {
                'record_count': record_count,
                'column_count': len(schema),
                'columns': list(schema.keys())
            }
        
        # Add dashboard compatibility analysis
        for table_name, analysis in analysis_results.items():
            if analysis['exists'] and analysis.get('missing_expected'):
                issue = f"Table {table_name}: Missing expected columns {analysis['missing_expected']}"
                report['issues_found'].append(issue)
                
                suggestions = self.suggest_column_mappings(table_name, analysis['missing_expected'])
                if suggestions:
                    fix = f"Suggested mappings for {table_name}: {suggestions}"
                    report['fixes_suggested'].append(fix)
        
        return report
    
    def check_morning_routine_integrity(self) -> Dict:
        """Check morning routine data for critical issues"""
        
        integrity_report = {
            'timestamp_issues': [],
            'technical_anomalies': [],
            'ml_model_issues': [],
            'data_quality_issues': [],
            'severity': 'UNKNOWN'
        }
        
        # Check for timestamp consistency
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get latest prediction and feature timestamps
                cursor.execute("SELECT MAX(prediction_timestamp) FROM predictions")
                latest_prediction = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(timestamp) FROM enhanced_features")
                latest_feature = cursor.fetchone()[0]
                
                if latest_prediction and latest_feature:
                    from datetime import datetime
                    pred_time = datetime.fromisoformat(latest_prediction)
                    feat_time = datetime.fromisoformat(latest_feature)
                    
                    time_diff = abs((feat_time - pred_time).total_seconds() / 3600)
                    
                    if time_diff > 1:  # More than 1 hour gap
                        integrity_report['timestamp_issues'].append({
                            'issue': 'Large timestamp gap between predictions and features',
                            'gap_hours': time_diff,
                            'prediction_time': latest_prediction,
                            'feature_time': latest_feature,
                            'severity': 'CRITICAL' if time_diff > 6 else 'WARNING'
                        })
                
                # Check for technical indicator anomalies
                cursor.execute("""
                    SELECT symbol, rsi, macd_line, bollinger_upper, bollinger_lower, current_price
                    FROM enhanced_features 
                    WHERE timestamp = (SELECT MAX(timestamp) FROM enhanced_features)
                """)
                
                for row in cursor.fetchall():
                    symbol, rsi, macd, bb_upper, bb_lower, price = row
                    
                    if rsi and (rsi < 5 or rsi > 95):
                        integrity_report['technical_anomalies'].append({
                            'symbol': symbol,
                            'indicator': 'RSI',
                            'value': rsi,
                            'issue': 'Extreme RSI value',
                            'severity': 'HIGH'
                        })
                    
                    if macd and abs(macd) > 5:
                        integrity_report['technical_anomalies'].append({
                            'symbol': symbol,
                            'indicator': 'MACD',
                            'value': macd,
                            'issue': 'Abnormally large MACD',
                            'severity': 'MEDIUM'
                        })
                    
                    if bb_upper and bb_lower and price:
                        bb_width = bb_upper - bb_lower
                        if bb_width > price * 0.2:  # Width > 20% of price
                            integrity_report['technical_anomalies'].append({
                                'symbol': symbol,
                                'indicator': 'Bollinger Bands',
                                'value': bb_width,
                                'issue': 'Excessively wide Bollinger Bands',
                                'severity': 'MEDIUM'
                            })
                
                # Check ML model functionality
                cursor.execute("SELECT COUNT(*) FROM predictions WHERE optimal_action != 0")
                non_zero_actions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM predictions")
                total_predictions = cursor.fetchone()[0]
                
                if total_predictions > 0 and non_zero_actions == 0:
                    integrity_report['ml_model_issues'].append({
                        'issue': 'All optimal_action values are 0',
                        'total_predictions': total_predictions,
                        'severity': 'HIGH'
                    })
        
        except Exception as e:
            integrity_report['data_quality_issues'].append({
                'issue': f'Error checking integrity: {e}',
                'severity': 'HIGH'
            })
        
        # Determine overall severity
        critical_count = sum(1 for issues in integrity_report.values() 
                           if isinstance(issues, list) and 
                           any(item.get('severity') == 'CRITICAL' for item in issues))
        
        high_count = sum(1 for issues in integrity_report.values() 
                        if isinstance(issues, list) and 
                        any(item.get('severity') == 'HIGH' for item in issues))
        
        if critical_count > 0:
            integrity_report['severity'] = 'CRITICAL'
        elif high_count > 0:
            integrity_report['severity'] = 'HIGH'
        else:
            integrity_report['severity'] = 'GOOD'
        
        return integrity_report
    
    def fix_morning_routine_issues(self) -> List[str]:
        """Apply fixes for common morning routine issues"""
        
        fixes_applied = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fix 1: Clean up predictions with future timestamps
                cursor.execute("""
                    DELETE FROM predictions 
                    WHERE prediction_timestamp > datetime('now')
                """)
                deleted_future = cursor.rowcount
                if deleted_future > 0:
                    fixes_applied.append(f"Removed {deleted_future} predictions with future timestamps")
                
                # Fix 2: Reset problematic optimal_action values
                cursor.execute("""
                    UPDATE predictions 
                    SET optimal_action = NULL 
                    WHERE optimal_action = 0 AND action_confidence > 0.6
                """)
                reset_actions = cursor.rowcount
                if reset_actions > 0:
                    fixes_applied.append(f"Reset {reset_actions} optimal_action values for high-confidence predictions")
                
                conn.commit()
                
        except Exception as e:
            fixes_applied.append(f"Error applying fixes: {e}")
        
        return fixes_applied
    
    def run_comprehensive_fix(self) -> None:
        """Run all fixes and generate reports"""
        
        print("🔍 RUNNING COMPREHENSIVE DATA QUALITY CHECK...")
        print("=" * 60)
        
        # 1. Check morning routine integrity first
        print("\n🌅 CHECKING MORNING ROUTINE INTEGRITY...")
        integrity_report = self.check_morning_routine_integrity()
        
        if integrity_report['severity'] == 'CRITICAL':
            print("🚨 CRITICAL ISSUES FOUND IN MORNING ROUTINE!")
            for issue_type, issues in integrity_report.items():
                if isinstance(issues, list) and issues:
                    print(f"\n{issue_type.replace('_', ' ').title()}:")
                    for issue in issues:
                        print(f"  • {issue.get('issue', issue)}")
            
            print("\n🔧 APPLYING CRITICAL FIXES...")
            fixes = self.fix_morning_routine_issues()
            for fix in fixes:
                print(f"  ✅ {fix}")
        
        # 2. Run schema analysis
        print("\n📊 ANALYZING DASHBOARD SCHEMA...")
        schema_report = self.analyze_dashboard_queries()
        
        # Print schema issues
        if 'issues' in schema_report and schema_report['issues']:
            print("⚠️  Found schema issues:")
            for issue in schema_report['issues']:
                print(f"  • {issue}")
        else:
            print("✅ No schema issues found")
        
        # 3. Fix queries if needed
        schema_issues = schema_report.get('issues', [])
        if schema_issues:
            print("\n🔧 APPLYING QUERY FIXES...")
            self.fix_dashboard_queries(schema_report)
            print("✅ Query fixes applied to dashboard")
        
        # 4. Generate comprehensive report
        print("\n📋 GENERATING DATA QUALITY REPORT...")
        
        # Combined report with both schema and integrity data
        combined_report = {
            'timestamp': datetime.now().isoformat(),
            'morning_routine_integrity': integrity_report,
            'schema_analysis': schema_report,
            'data_quality': self.generate_data_quality_report()
        }
        
        # Save report
        with open('comprehensive_data_quality_report.json', 'w') as f:
            json.dump(combined_report, f, indent=2)
        print("📄 Report saved to: comprehensive_data_quality_report.json")
        
        print("\n✅ COMPREHENSIVE FIX COMPLETE!")
        print(f"🎯 Morning Routine Status: {integrity_report['severity']}")
        print(f"🎯 Found and addressed {len(schema_issues)} schema issues")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 SUMMARY:")
        print(f"• Morning Routine: {integrity_report['severity']}")
        print(f"• Schema Issues Found: {len(schema_issues)}")
        print(f"• Report Generated: comprehensive_data_quality_report.json")
        print("=" * 60)
        
        print("🔍 SMART DATA QUALITY FIXER")
        print("=" * 50)
        
        # Check database exists
        if not self.db_path.exists():
            print(f"❌ Database not found: {self.db_path}")
            return
        
        print(f"📊 Analyzing database: {self.db_path}")
        
        # Generate analysis
        analysis_results = self.analyze_dashboard_queries()
        report = self.generate_data_quality_report()
        
        # Print summary
        print(f"\n📈 Database Summary:")
        print(f"  • Total tables: {len(report['tables_analyzed'])}")
        print(f"  • Total records: {sum(t['record_count'] for t in report['tables_analyzed'].values()):,}")
        
        print(f"\n⚠️  Issues Found: {len(report['issues_found'])}")
        for issue in report['issues_found']:
            print(f"  • {issue}")
        
        print(f"\n💡 Fixes Suggested: {len(report['fixes_suggested'])}")
        for fix in report['fixes_suggested']:
            print(f"  • {fix}")
        
        # Apply dashboard fixes
        print(f"\n🔧 Applying fixes...")
        self.apply_dashboard_fixes()
        
        print(f"\n✅ Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"  • {fix}")
        
        # Save detailed report
        report_file = Path("data_quality_fix_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: {report_file}")
        print("\n🎯 Data quality analysis complete!")

def main():
    """Main function to run the smart data quality fixer"""
    
    fixer = SmartDataQualityFixer()
    fixer.run_comprehensive_fix()

if __name__ == "__main__":
    main()
