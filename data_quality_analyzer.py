#!/usr/bin/env python3
"""
Trading Data Quality Analysis Report
Analyzes predictions, outcomes, and ML performance for data integrity
"""

import sqlite3
import json
from datetime import datetime, timedelta
import sys

class DataQualityAnalyzer:
    def __init__(self, db_path="data/trading_predictions.db"):
        self.db_path = db_path
        self.issues = []
        self.warnings = []
        self.summary = {}
    
    def log_issue(self, severity, category, message, data=None):
        """Log data quality issues"""
        issue = {
            'severity': severity,
            'category': category, 
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        if severity == 'ERROR':
            self.issues.append(issue)
            print(f"❌ ERROR [{category}]: {message}")
        elif severity == 'WARNING':
            self.warnings.append(issue)
            print(f"⚠️ WARNING [{category}]: {message}")
        else:
            print(f"ℹ️ INFO [{category}]: {message}")
    
    def analyze_predictions_data(self):
        """Analyze predictions table for data quality issues"""
        print("\n🔍 Analyzing Predictions Data Quality")
        print("=" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic counts and date ranges
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(DATE(prediction_timestamp)), MAX(DATE(prediction_timestamp)) FROM predictions")
        date_range = cursor.fetchone()
        
        print(f"📊 Total predictions: {total_predictions}")
        print(f"📅 Date range: {date_range[0]} to {date_range[1]}")
        
        self.summary['total_predictions'] = total_predictions
        self.summary['prediction_date_range'] = date_range
        
        # Check for missing required fields
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE symbol IS NULL OR symbol = ''")
        missing_symbols = cursor.fetchone()[0]
        if missing_symbols > 0:
            self.log_issue('ERROR', 'DATA_INTEGRITY', f'{missing_symbols} predictions missing symbol')
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE predicted_action IS NULL OR predicted_action = ''")
        missing_actions = cursor.fetchone()[0]
        if missing_actions > 0:
            self.log_issue('ERROR', 'DATA_INTEGRITY', f'{missing_actions} predictions missing action')
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE action_confidence IS NULL")
        missing_confidence = cursor.fetchone()[0]
        if missing_confidence > 0:
            self.log_issue('ERROR', 'DATA_INTEGRITY', f'{missing_confidence} predictions missing confidence')
        
        # Check for invalid confidence values
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE action_confidence < 0 OR action_confidence > 1")
        invalid_confidence = cursor.fetchone()[0]
        if invalid_confidence > 0:
            self.log_issue('ERROR', 'DATA_VALIDATION', f'{invalid_confidence} predictions with invalid confidence (not 0-1)')
        
        # Check for duplicate predictions (same symbol, same day)
        cursor.execute("""
            SELECT symbol, DATE(prediction_timestamp), COUNT(*) as count
            FROM predictions 
            GROUP BY symbol, DATE(prediction_timestamp)
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            self.log_issue('WARNING', 'DATA_DUPLICATION', f'Found {len(duplicates)} dates with duplicate predictions', duplicates)
        
        # Analyze recent predictions
        cursor.execute("""
            SELECT symbol, predicted_action, action_confidence, predicted_direction, predicted_magnitude
            FROM predictions 
            WHERE DATE(prediction_timestamp) >= DATE('now', '-3 days')
            ORDER BY prediction_timestamp DESC
        """)
        recent_predictions = cursor.fetchall()
        
        if recent_predictions:
            print(f"\n📈 Recent Predictions Analysis ({len(recent_predictions)} records):")
            
            # Check for unusual patterns
            hold_count = sum(1 for p in recent_predictions if p[1] == 'HOLD')
            if hold_count == len(recent_predictions):
                self.log_issue('WARNING', 'PREDICTION_PATTERN', 'All recent predictions are HOLD - may indicate conservative bias')
            
            # Check confidence distribution
            confidences = [p[2] for p in recent_predictions if p[2] is not None]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence == 0.5:
                    self.log_issue('WARNING', 'CONFIDENCE_ANALYSIS', 'All recent confidences are 0.5 - may indicate default values')
                print(f"   Average confidence: {avg_confidence:.3f}")
            
            # Check magnitude distribution
            magnitudes = [p[4] for p in recent_predictions if p[4] is not None]
            if magnitudes:
                avg_magnitude = sum(magnitudes) / len(magnitudes)
                print(f"   Average magnitude: {avg_magnitude:.6f}")
                
                if all(m < 0.02 for m in magnitudes):  # Less than 2%
                    self.log_issue('INFO', 'MAGNITUDE_ANALYSIS', 'Recent predictions show low magnitude (<2%) - conservative model')
        
        conn.close()
    
    def analyze_outcomes_data(self):
        """Analyze outcomes table for data quality issues"""
        print("\n🎯 Analyzing Outcomes Data Quality")
        print("=" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic outcomes analysis
        cursor.execute("SELECT COUNT(*) FROM outcomes")
        total_outcomes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT prediction_id) FROM outcomes")
        unique_predictions_with_outcomes = cursor.fetchone()[0]
        
        print(f"📊 Total outcomes: {total_outcomes}")
        print(f"🔗 Predictions with outcomes: {unique_predictions_with_outcomes}")
        
        self.summary['total_outcomes'] = total_outcomes
        self.summary['predictions_with_outcomes'] = unique_predictions_with_outcomes
        
        if total_outcomes == 0:
            self.log_issue('WARNING', 'MISSING_DATA', 'No outcomes data found - cannot validate ML performance')
            return
        
        # Check for orphaned outcomes (outcomes without predictions)
        cursor.execute("""
            SELECT COUNT(*) FROM outcomes o 
            LEFT JOIN predictions p ON o.prediction_id = p.prediction_id 
            WHERE p.prediction_id IS NULL
        """)
        orphaned_outcomes = cursor.fetchone()[0]
        if orphaned_outcomes > 0:
            self.log_issue('ERROR', 'DATA_INTEGRITY', f'{orphaned_outcomes} outcomes without matching predictions')
        
        # Check for missing actual returns
        cursor.execute("SELECT COUNT(*) FROM outcomes WHERE actual_return IS NULL")
        missing_returns = cursor.fetchone()[0]
        if missing_returns > 0:
            self.log_issue('WARNING', 'MISSING_DATA', f'{missing_returns} outcomes missing actual_return')
        
        # Recent outcomes analysis
        cursor.execute("""
            SELECT MIN(DATE(evaluation_timestamp)), MAX(DATE(evaluation_timestamp)) 
            FROM outcomes 
            WHERE evaluation_timestamp IS NOT NULL
        """)
        outcome_date_range = cursor.fetchone()
        
        if outcome_date_range[0]:
            print(f"📅 Outcomes date range: {outcome_date_range[0]} to {outcome_date_range[1]}")
            
            # Check if outcomes are recent
            cursor.execute("SELECT MAX(DATE(evaluation_timestamp)) FROM outcomes")
            latest_outcome = cursor.fetchone()[0]
            if latest_outcome:
                from datetime import datetime
                latest_date = datetime.strptime(latest_outcome, '%Y-%m-%d').date()
                days_old = (datetime.now().date() - latest_date).days
                
                if days_old > 7:
                    self.log_issue('WARNING', 'STALE_DATA', f'Latest outcome is {days_old} days old ({latest_outcome})')
                elif days_old > 3:
                    self.log_issue('INFO', 'DATA_FRESHNESS', f'Latest outcome is {days_old} days old ({latest_outcome})')
        
        conn.close()
    
    def analyze_enhanced_outcomes(self):
        """Analyze enhanced outcomes for completeness"""
        print("\n🔬 Analyzing Enhanced Outcomes")
        print("=" * 30)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        enhanced_count = cursor.fetchone()[0]
        
        print(f"📊 Enhanced outcomes: {enhanced_count}")
        
        if enhanced_count == 0:
            self.log_issue('INFO', 'ENHANCED_DATA', 'No enhanced outcomes - using basic outcomes only')
        else:
            # Check for missing multi-timeframe data
            cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NULL")
            missing_1h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE optimal_action IS NULL")
            missing_action = cursor.fetchone()[0]
            
            if missing_1h > 0:
                self.log_issue('WARNING', 'ENHANCED_DATA', f'{missing_1h} enhanced outcomes missing 1h direction')
            
            if missing_action > 0:
                self.log_issue('WARNING', 'ENHANCED_DATA', f'{missing_action} enhanced outcomes missing optimal action')
        
        self.summary['enhanced_outcomes'] = enhanced_count
        conn.close()
    
    def analyze_ml_performance(self):
        """Analyze ML model performance and consistency"""
        print("\n🤖 Analyzing ML Performance")
        print("=" * 30)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check model performance table
        cursor.execute("SELECT COUNT(*) FROM model_performance")
        perf_records = cursor.fetchone()[0]
        
        print(f"📊 Performance records: {perf_records}")
        
        if perf_records == 0:
            self.log_issue('ERROR', 'ML_PERFORMANCE', 'No model performance data found')
            conn.close()
            return
        
        # Analyze model accuracy
        cursor.execute("""
            SELECT evaluation_id, accuracy_direction, total_predictions, created_at
            FROM model_performance 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_performance = cursor.fetchall()
        
        if recent_performance:
            print("📈 Recent Model Performance:")
            for record in recent_performance:
                eval_id, accuracy, total_preds, created = record
                symbol = eval_id.split('_')[0] if eval_id else 'Unknown'
                print(f"   {symbol}: {accuracy:.1%} accuracy ({total_preds} predictions)")
                
                # Check for concerning accuracy levels
                if accuracy < 0.60:
                    self.log_issue('WARNING', 'ML_PERFORMANCE', f'{symbol} accuracy below 60%: {accuracy:.1%}')
                elif accuracy > 0.98:
                    self.log_issue('WARNING', 'ML_PERFORMANCE', f'{symbol} accuracy suspiciously high: {accuracy:.1%} - possible overfitting')
        
        # Check for consistent model versions
        cursor.execute("""
            SELECT DISTINCT model_version FROM predictions 
            WHERE DATE(prediction_timestamp) >= DATE('now', '-7 days')
        """)
        recent_versions = cursor.fetchall()
        
        if len(recent_versions) > 1:
            versions = [v[0] for v in recent_versions]
            self.log_issue('INFO', 'MODEL_VERSIONS', f'Multiple model versions in use: {versions}')
        elif len(recent_versions) == 1:
            print(f"🔄 Current model version: {recent_versions[0][0]}")
        
        self.summary['model_performance_records'] = perf_records
        conn.close()
    
    def analyze_data_freshness(self):
        """Check data freshness and timing issues"""
        print("\n⏰ Analyzing Data Freshness")
        print("=" * 30)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check prediction timing patterns
        cursor.execute("""
            SELECT DATE(prediction_timestamp), COUNT(*), 
                   strftime('%H', prediction_timestamp) as hour
            FROM predictions 
            WHERE DATE(prediction_timestamp) >= DATE('now', '-7 days')
            GROUP BY DATE(prediction_timestamp), strftime('%H', prediction_timestamp)
            ORDER BY prediction_timestamp DESC
        """)
        timing_data = cursor.fetchall()
        
        if timing_data:
            print("📅 Recent prediction timing:")
            current_date = None
            for date, count, hour in timing_data:
                if date != current_date:
                    current_date = date
                    print(f"   {date}:")
                print(f"     {hour}:00 - {count} predictions")
                
                # Check for unusual timing
                hour_int = int(hour)
                if hour_int < 6 or hour_int > 22:  # Outside normal trading prep hours
                    self.log_issue('INFO', 'TIMING_PATTERN', f'Predictions made at unusual hour: {hour}:00 on {date}')
        
        # Check today's data
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = ?", (today,))
        today_predictions = cursor.fetchone()[0]
        
        print(f"\n📅 Today's data ({today}):")
        print(f"   Predictions: {today_predictions}")
        
        if today_predictions == 0:
            self.log_issue('INFO', 'DATA_FRESHNESS', 'No predictions for today - may be expected if market is closed')
        
        # Check for gaps in recent data
        cursor.execute("""
            SELECT DATE(prediction_timestamp) as date, COUNT(*) as count
            FROM predictions 
            WHERE DATE(prediction_timestamp) >= DATE('now', '-7 days')
            GROUP BY DATE(prediction_timestamp)
            ORDER BY date DESC
        """)
        daily_counts = cursor.fetchall()
        
        expected_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        for date, count in daily_counts:
            if count < len(expected_symbols):
                missing = len(expected_symbols) - count
                self.log_issue('WARNING', 'MISSING_PREDICTIONS', f'{date}: Only {count} predictions (missing {missing})')
        
        conn.close()
    
    def generate_summary_report(self):
        """Generate final summary report"""
        print("\n" + "="*60)
        print("📋 DATA QUALITY SUMMARY REPORT")
        print("="*60)
        
        print(f"\n📊 Data Overview:")
        print(f"   Total predictions: {self.summary.get('total_predictions', 0)}")
        print(f"   Total outcomes: {self.summary.get('total_outcomes', 0)}")
        print(f"   Enhanced outcomes: {self.summary.get('enhanced_outcomes', 0)}")
        print(f"   Performance records: {self.summary.get('model_performance_records', 0)}")
        
        if self.summary.get('prediction_date_range'):
            date_range = self.summary['prediction_date_range']
            print(f"   Prediction date range: {date_range[0]} to {date_range[1]}")
        
        print(f"\n🚨 Issues Found:")
        print(f"   Errors: {len(self.issues)}")
        print(f"   Warnings: {len(self.warnings)}")
        
        if self.issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   • {issue['category']}: {issue['message']}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning['category']}: {warning['message']}")
        
        if not self.issues and not self.warnings:
            print("\n✅ No significant data quality issues found!")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if self.summary.get('total_outcomes', 0) == 0:
            print("   • Set up outcome tracking to validate ML performance")
        
        if self.summary.get('total_predictions', 0) > 0 and self.summary.get('predictions_with_outcomes', 0) == 0:
            print("   • Link recent predictions with market outcomes")
        
        if len([w for w in self.warnings if 'STALE_DATA' in w['category']]) > 0:
            print("   • Update outcome data more frequently")
        
        if len([w for w in self.warnings if 'HOLD' in w['message']]) > 0:
            print("   • Review ML model for potential over-conservative bias")
        
        print("   • Deploy future-proof performance manager for automated monitoring")
        print("   • Set up automated daily data quality checks")
        
        return len(self.issues) == 0

def main():
    """Run comprehensive data quality analysis"""
    print("🔍 Trading System Data Quality Analysis")
    print("🕐 Analysis started at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    analyzer = DataQualityAnalyzer()
    
    try:
        analyzer.analyze_predictions_data()
        analyzer.analyze_outcomes_data()
        analyzer.analyze_enhanced_outcomes()
        analyzer.analyze_ml_performance()
        analyzer.analyze_data_freshness()
        
        success = analyzer.generate_summary_report()
        
        # Export detailed report
        report_file = f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': analyzer.summary,
                'issues': analyzer.issues,
                'warnings': analyzer.warnings
            }, f, indent=2)
        
        print(f"\n📁 Detailed report saved to: {report_file}")
        
        if success:
            print("\n✅ Data quality analysis completed successfully")
            return 0
        else:
            print("\n⚠️ Data quality issues found - review recommendations")
            return 1
            
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
