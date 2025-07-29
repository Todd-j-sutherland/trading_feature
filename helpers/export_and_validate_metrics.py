#!/usr/bin/env python3
"""
Dashboard Metrics Export and Validation System

This script exports all dashboard metrics to JSON and performs comprehensive validation
to ensure data accuracy and consistency.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import traceback

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from dashboard import (
    fetch_ml_performance_metrics, 
    fetch_current_sentiment_scores, 
    fetch_ml_feature_analysis,
    get_database_connection
)

class MetricsValidator:
    """Comprehensive validation for dashboard metrics"""
    
    def __init__(self, output_dir: str = "metrics_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.validation_errors = []
        self.validation_warnings = []
        
    def export_all_metrics(self) -> Dict[str, Any]:
        """Export all dashboard metrics to a structured format"""
        
        print("🔄 Exporting all dashboard metrics...")
        
        try:
            # Export ML Performance Metrics
            print("   📊 Exporting ML performance metrics...")
            ml_metrics = fetch_ml_performance_metrics()
            
            # Export Current Sentiment Scores
            print("   📈 Exporting sentiment scores...")
            sentiment_df = fetch_current_sentiment_scores()
            sentiment_data = sentiment_df.to_dict('records') if not sentiment_df.empty else []
            
            # Export ML Feature Analysis
            print("   🔍 Exporting ML feature analysis...")
            feature_analysis = fetch_ml_feature_analysis()
            
            # Export Raw Database Statistics
            print("   🗄️ Exporting database statistics...")
            db_stats = self._get_database_statistics()
            
            # Combine all metrics
            exported_metrics = {
                'export_metadata': {
                    'timestamp': self.timestamp,
                    'export_time': datetime.now().isoformat(),
                    'dashboard_version': '1.0.0',
                    'python_version': sys.version,
                    'database_path': 'data/ml_models/training_data.db'
                },
                'ml_performance': ml_metrics,
                'sentiment_scores': sentiment_data,
                'feature_analysis': feature_analysis,
                'database_statistics': db_stats,
                'validation_metadata': {
                    'total_records_exported': len(sentiment_data),
                    'export_success': True,
                    'export_duration_seconds': None  # Will be calculated
                }
            }
            
            print(f"✅ Successfully exported {len(sentiment_data)} sentiment records and all metrics")
            return exported_metrics
            
        except Exception as e:
            error_msg = f"Failed to export metrics: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"📋 Traceback: {traceback.format_exc()}")
            return {
                'export_metadata': {
                    'timestamp': self.timestamp,
                    'export_time': datetime.now().isoformat(),
                    'export_success': False,
                    'error': error_msg,
                    'traceback': traceback.format_exc()
                }
            }
    
    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        
        try:
            conn = get_database_connection()
            stats = {}
            
            # Table row counts
            tables = ['sentiment_features', 'trading_outcomes', 'model_performance']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                row = cursor.fetchone()
                stats[f'{table}_count'] = row['count'] if row else 0
            
            # Date ranges
            cursor = conn.execute("""
                SELECT 
                    MIN(timestamp) as earliest_sentiment,
                    MAX(timestamp) as latest_sentiment,
                    COUNT(DISTINCT symbol) as unique_symbols
                FROM sentiment_features
            """)
            sentiment_stats = cursor.fetchone()
            
            cursor = conn.execute("""
                SELECT 
                    MIN(signal_timestamp) as earliest_trade,
                    MAX(exit_timestamp) as latest_trade,
                    COUNT(CASE WHEN exit_timestamp IS NOT NULL THEN 1 END) as completed_trades,
                    COUNT(CASE WHEN exit_timestamp IS NULL THEN 1 END) as pending_trades
                FROM trading_outcomes
            """)
            trade_stats = cursor.fetchone()
            
            # Recent activity (last 7 days)
            cursor = conn.execute("""
                SELECT COUNT(*) as recent_predictions
                FROM sentiment_features 
                WHERE timestamp >= date('now', '-7 days')
            """)
            recent_activity = cursor.fetchone()
            
            stats.update({
                'sentiment_date_range': {
                    'earliest': sentiment_stats['earliest_sentiment'] if sentiment_stats else None,
                    'latest': sentiment_stats['latest_sentiment'] if sentiment_stats else None,
                    'unique_symbols': sentiment_stats['unique_symbols'] if sentiment_stats else 0
                },
                'trading_date_range': {
                    'earliest_trade': trade_stats['earliest_trade'] if trade_stats else None,
                    'latest_trade': trade_stats['latest_trade'] if trade_stats else None,
                    'completed_trades': trade_stats['completed_trades'] if trade_stats else 0,
                    'pending_trades': trade_stats['pending_trades'] if trade_stats else 0
                },
                'recent_activity': {
                    'predictions_last_7_days': recent_activity['recent_predictions'] if recent_activity else 0
                }
            })
            
            conn.close()
            return stats
            
        except Exception as e:
            return {'error': f"Failed to get database statistics: {str(e)}"}
    
    def validate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive validation of exported metrics"""
        
        print("🔍 Validating exported metrics...")
        
        validation_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'passed_validations': [],
            'failed_validations': [],
            'warnings': [],
            'summary': {
                'total_validations': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        # Validate ML Performance Metrics
        self._validate_ml_performance(metrics.get('ml_performance', {}), validation_results)
        
        # Validate Sentiment Scores
        self._validate_sentiment_scores(metrics.get('sentiment_scores', []), validation_results)
        
        # Validate Feature Analysis
        self._validate_feature_analysis(metrics.get('feature_analysis', {}), validation_results)
        
        # Validate Database Statistics
        self._validate_database_stats(metrics.get('database_statistics', {}), validation_results)
        
        # Calculate summary
        validation_results['summary']['total_validations'] = (
            len(validation_results['passed_validations']) + 
            len(validation_results['failed_validations'])
        )
        validation_results['summary']['passed'] = len(validation_results['passed_validations'])
        validation_results['summary']['failed'] = len(validation_results['failed_validations'])
        validation_results['summary']['warnings'] = len(validation_results['warnings'])
        
        # Overall status
        validation_results['overall_status'] = (
            'PASS' if len(validation_results['failed_validations']) == 0 else 'FAIL'
        )
        
        return validation_results
    
    def _validate_ml_performance(self, ml_metrics: Dict, results: Dict):
        """Validate ML performance metrics"""
        
        # Success rate validation
        if 'success_rate' in ml_metrics:
            success_rate = ml_metrics['success_rate']
            if 0 <= success_rate <= 1:
                results['passed_validations'].append(f"Success rate {success_rate:.1%} is within valid range (0-100%)")
            else:
                results['failed_validations'].append(f"Success rate {success_rate:.1%} is outside valid range (0-100%)")
        
        # Confidence validation
        if 'avg_confidence' in ml_metrics:
            confidence = ml_metrics['avg_confidence']
            if 0 <= confidence <= 1:
                results['passed_validations'].append(f"Average confidence {confidence:.1%} is within valid range (0-100%)")
            else:
                results['failed_validations'].append(f"Average confidence {confidence:.1%} is outside valid range (0-100%)")
        
        # Trade counts validation
        if 'completed_trades' in ml_metrics:
            trades = ml_metrics['completed_trades']
            if trades >= 0:
                results['passed_validations'].append(f"Completed trades count {trades} is non-negative")
                if trades < 10:
                    results['warnings'].append(f"Low number of completed trades ({trades}) - results may not be statistically significant")
            else:
                results['failed_validations'].append(f"Completed trades count {trades} is negative")
        
        # Return validation
        if 'avg_return' in ml_metrics:
            avg_return = ml_metrics['avg_return']
            if -100 <= avg_return <= 100:  # Reasonable return range
                results['passed_validations'].append(f"Average return {avg_return:.2f}% is within reasonable range")
            else:
                results['warnings'].append(f"Average return {avg_return:.2f}% seems unusually high/low")
    
    def _validate_sentiment_scores(self, sentiment_data: List, results: Dict):
        """Validate sentiment scores data"""
        
        if not sentiment_data:
            results['failed_validations'].append("No sentiment scores data found")
            return
        
        # Check for expected ASX banks
        expected_banks = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]
        found_symbols = [item.get('Symbol', '') for item in sentiment_data]
        
        for bank in expected_banks:
            if bank in found_symbols:
                results['passed_validations'].append(f"Found data for expected bank: {bank}")
            else:
                results['warnings'].append(f"Missing data for expected bank: {bank}")
        
        # Validate individual sentiment records
        for i, record in enumerate(sentiment_data[:5]):  # Check first 5 records
            symbol = record.get('Symbol', 'Unknown')
            
            # Sentiment score range
            if 'Sentiment Score' in record:
                score = record['Sentiment Score']
                if -1 <= score <= 1:
                    results['passed_validations'].append(f"{symbol}: Sentiment score {score:.3f} within valid range")
                else:
                    results['failed_validations'].append(f"{symbol}: Sentiment score {score:.3f} outside valid range (-1 to 1)")
            
            # Confidence range
            if 'Confidence' in record:
                confidence = record['Confidence']
                if 0 <= confidence <= 1:
                    results['passed_validations'].append(f"{symbol}: Confidence {confidence:.3f} within valid range")
                else:
                    results['failed_validations'].append(f"{symbol}: Confidence {confidence:.3f} outside valid range (0 to 1)")
    
    def _validate_feature_analysis(self, feature_data: Dict, results: Dict):
        """Validate feature analysis data"""
        
        # Feature usage rates
        if 'feature_usage' in feature_data:
            usage = feature_data['feature_usage']
            for feature, rate in usage.items():
                if 0 <= rate <= 100:
                    results['passed_validations'].append(f"Feature usage {feature}: {rate:.1f}% within valid range")
                else:
                    results['failed_validations'].append(f"Feature usage {feature}: {rate:.1f}% outside valid range (0-100%)")
        
        # Total records check
        if 'total_records' in feature_data:
            total = feature_data['total_records']
            if total > 0:
                results['passed_validations'].append(f"Feature analysis based on {total} records")
            else:
                results['failed_validations'].append(f"Feature analysis has no records ({total})")
    
    def _validate_database_stats(self, db_stats: Dict, results: Dict):
        """Validate database statistics"""
        
        # Check table counts
        tables = ['sentiment_features_count', 'trading_outcomes_count', 'model_performance_count']
        for table in tables:
            if table in db_stats:
                count = db_stats[table]
                if count >= 0:
                    results['passed_validations'].append(f"Table {table.replace('_count', '')}: {count} records")
                    if count == 0:
                        results['warnings'].append(f"Table {table.replace('_count', '')} is empty")
                else:
                    results['failed_validations'].append(f"Invalid count for {table}: {count}")
        
        # Check recent activity
        if 'recent_activity' in db_stats:
            recent = db_stats['recent_activity'].get('predictions_last_7_days', 0)
            if recent > 0:
                results['passed_validations'].append(f"Recent activity: {recent} predictions in last 7 days")
            else:
                results['warnings'].append("No recent predictions found in last 7 days")
    
    def save_export(self, metrics: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
        """Save exported metrics and validation results to files"""
        
        # Save metrics export
        metrics_file = self.output_dir / f"dashboard_metrics_{self.timestamp}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        # Save validation results
        validation_file = self.output_dir / f"validation_results_{self.timestamp}.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        # Create summary report
        summary_file = self.output_dir / f"validation_summary_{self.timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Dashboard Metrics Validation Summary\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            
            f.write(f"Overall Status: {validation_results.get('overall_status', 'UNKNOWN')}\n")
            f.write(f"Total Validations: {validation_results['summary']['total_validations']}\n")
            f.write(f"Passed: {validation_results['summary']['passed']}\n")
            f.write(f"Failed: {validation_results['summary']['failed']}\n")
            f.write(f"Warnings: {validation_results['summary']['warnings']}\n\n")
            
            if validation_results['failed_validations']:
                f.write("FAILED VALIDATIONS:\n")
                for failure in validation_results['failed_validations']:
                    f.write(f"❌ {failure}\n")
                f.write("\n")
            
            if validation_results['warnings']:
                f.write("WARNINGS:\n")
                for warning in validation_results['warnings']:
                    f.write(f"⚠️ {warning}\n")
                f.write("\n")
            
            f.write("PASSED VALIDATIONS:\n")
            for passed in validation_results['passed_validations']:
                f.write(f"✅ {passed}\n")
        
        return str(metrics_file)

def main():
    """Main execution function"""
    
    print("🚀 Dashboard Metrics Export and Validation System")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Initialize validator
        validator = MetricsValidator()
        
        # Export all metrics
        metrics = validator.export_all_metrics()
        
        if not metrics.get('validation_metadata', {}).get('export_success', False):
            print("❌ Export failed, cannot proceed with validation")
            return 1
        
        # Calculate export duration
        export_duration = (datetime.now() - start_time).total_seconds()
        metrics['validation_metadata']['export_duration_seconds'] = export_duration
        
        # Validate metrics
        validation_results = validator.validate_metrics(metrics)
        
        # Save results
        metrics_file = validator.save_export(metrics, validation_results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {validation_results.get('overall_status', 'UNKNOWN')}")
        print(f"Total Validations: {validation_results['summary']['total_validations']}")
        print(f"✅ Passed: {validation_results['summary']['passed']}")
        print(f"❌ Failed: {validation_results['summary']['failed']}")
        print(f"⚠️ Warnings: {validation_results['summary']['warnings']}")
        print(f"📁 Results saved to: {metrics_file}")
        
        # Show critical issues
        if validation_results['failed_validations']:
            print("\n🚨 CRITICAL ISSUES:")
            for failure in validation_results['failed_validations']:
                print(f"❌ {failure}")
        
        if validation_results['warnings']:
            print("\n⚠️ WARNINGS:")
            for warning in validation_results['warnings'][:5]:  # Show first 5 warnings
                print(f"⚠️ {warning}")
            if len(validation_results['warnings']) > 5:
                print(f"   ... and {len(validation_results['warnings']) - 5} more warnings")
        
        print(f"\n⏱️ Total execution time: {(datetime.now() - start_time).total_seconds():.2f} seconds")
        
        return 0 if validation_results.get('overall_status') == 'PASS' else 1
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
