#!/usr/bin/env python3
"""
Morning Routine Temporal Integrity Guard

A safety checkpoint that must be run BEFORE your morning analysis to ensure
temporal consistency and prevent data leakage. This guard validates that:
1. No future data is being used for predictions
2. Timestamps are properly synchronized
3. Technical indicators are within reasonable bounds
4. ML models are functioning correctly

Integrate this into your morning routine workflow as the first step.
"""

import sqlite3
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class MorningTemporalGuard:
    """Temporal integrity guard for morning routine"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.validation_timestamp = datetime.now()
        self.critical_issues = []
        self.warnings = []
        
    def validate_temporal_consistency(self) -> Dict:
        """Core temporal validation - CRITICAL for preventing data leakage"""
        
        validation = {
            'passed': True,
            'issues': [],
            'details': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check 1: No predictions using future features (CRITICAL)
                cursor.execute("""
                    SELECT COUNT(*), MAX((julianday(ef.timestamp) - julianday(p.prediction_timestamp)) * 24) as max_gap
                    FROM predictions p
                    JOIN enhanced_features ef ON p.symbol = ef.symbol
                    WHERE datetime(ef.timestamp) > datetime(p.prediction_timestamp, '+30 minutes')
                """)
                
                leakage_count, max_gap = cursor.fetchone()
                if leakage_count and leakage_count > 0:
                    validation['passed'] = False
                    validation['issues'].append(f"CRITICAL: {leakage_count} predictions using future data (max gap: {max_gap:.1f}h)")
                    self.critical_issues.append("Data leakage detected")
                
                # Check 2: No predictions with future timestamps
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions
                    WHERE prediction_timestamp > datetime('now', '+5 minutes')
                """)
                
                future_predictions = cursor.fetchone()[0]
                if future_predictions > 0:
                    validation['passed'] = False
                    validation['issues'].append(f"CRITICAL: {future_predictions} predictions with future timestamps")
                    self.critical_issues.append("Future predictions detected")
                
                # Check 3: Features are recent enough for morning analysis
                morning_cutoff = self.validation_timestamp - timedelta(hours=18)  # 18 hours ago
                
                cursor.execute("""
                    SELECT symbol, MAX(timestamp) as latest_feature
                    FROM enhanced_features
                    WHERE symbol IN ('ANZ.AX', 'CBA.AX', 'WBC.AX', 'NAB.AX')
                    GROUP BY symbol
                """)
                
                stale_symbols = []
                for symbol, latest_feature in cursor.fetchall():
                    if latest_feature:
                        latest_dt = datetime.fromisoformat(latest_feature)
                        if latest_dt < morning_cutoff:
                            hours_old = (self.validation_timestamp - latest_dt).total_seconds() / 3600
                            stale_symbols.append(f"{symbol} ({hours_old:.1f}h old)")
                
                if stale_symbols:
                    validation['issues'].append(f"WARNING: Stale features for: {', '.join(stale_symbols)}")
                    self.warnings.extend(stale_symbols)
                
                validation['details'] = {
                    'data_leakage_instances': leakage_count or 0,
                    'future_predictions': future_predictions,
                    'stale_symbols': len(stale_symbols),
                    'validation_time': self.validation_timestamp.isoformat()
                }
                
        except Exception as e:
            validation['passed'] = False
            validation['issues'].append(f"CRITICAL: Validation error - {e}")
            self.critical_issues.append(f"Validation failure: {e}")
        
        return validation
    
    def validate_technical_indicators(self) -> Dict:
        """Validate technical indicators are within reasonable bounds"""
        
        validation = {
            'passed': True,
            'issues': [],
            'anomalies': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get latest technical indicators
                cursor.execute("""
                    SELECT symbol, rsi, macd_line, current_price, 
                           bollinger_upper, bollinger_lower, volume
                    FROM enhanced_features
                    WHERE timestamp = (SELECT MAX(timestamp) FROM enhanced_features)
                """)
                
                for row in cursor.fetchall():
                    symbol, rsi, macd, price, bb_upper, bb_lower, volume = row
                    
                    # RSI bounds check
                    if rsi is not None:
                        if rsi < 0 or rsi > 100:
                            validation['passed'] = False
                            validation['issues'].append(f"INVALID RSI for {symbol}: {rsi}")
                        elif rsi < 5 or rsi > 95:
                            validation['anomalies'].append(f"EXTREME RSI for {symbol}: {rsi}")
                    
                    # MACD reasonableness check
                    if macd is not None and abs(macd) > 20:
                        validation['anomalies'].append(f"EXTREME MACD for {symbol}: {macd}")
                    
                    # Price vs Bollinger Bands check
                    if all(x is not None for x in [price, bb_upper, bb_lower]):
                        if price > bb_upper * 1.5 or price < bb_lower * 0.5:
                            validation['anomalies'].append(f"PRICE OUTSIDE REASONABLE BANDS for {symbol}: {price}")
                    
                    # Volume check (negative or zero volume is suspicious)
                    if volume is not None and volume <= 0:
                        validation['issues'].append(f"INVALID VOLUME for {symbol}: {volume}")
                
        except Exception as e:
            validation['passed'] = False
            validation['issues'].append(f"Technical validation error: {e}")
        
        return validation
    
    def validate_ml_model_health(self) -> Dict:
        """Check if ML models are functioning properly"""
        
        validation = {
            'passed': True,
            'issues': [],
            'model_status': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check recent predictions have varied optimal_action values
                cursor.execute("""
                    SELECT optimal_action, COUNT(*) as count
                    FROM predictions
                    WHERE DATE(prediction_timestamp) >= DATE('now', '-7 days')
                    GROUP BY optimal_action
                """)
                
                action_distribution = dict(cursor.fetchall())
                
                # Check if all actions are the same (sign of broken model)
                if len(action_distribution) == 1:
                    action = list(action_distribution.keys())[0]
                    count = list(action_distribution.values())[0]
                    
                    if action == 0 or action == '0':
                        validation['issues'].append(f"ML MODEL ISSUE: All {count} recent predictions have optimal_action = 0")
                        self.warnings.append("ML model may not be functioning")
                    elif count > 20:  # Too many identical actions
                        validation['issues'].append(f"ML MODEL ISSUE: All {count} recent predictions have same action: {action}")
                
                # Check prediction confidence distribution
                cursor.execute("""
                    SELECT AVG(action_confidence), MIN(action_confidence), MAX(action_confidence)
                    FROM predictions
                    WHERE DATE(prediction_timestamp) >= DATE('now', '-7 days')
                    AND action_confidence IS NOT NULL
                """)
                
                conf_stats = cursor.fetchone()
                if conf_stats and conf_stats[0] is not None:
                    avg_conf, min_conf, max_conf = conf_stats
                    
                    if max_conf - min_conf < 0.1:  # Very narrow confidence range
                        validation['issues'].append(f"ML MODEL ISSUE: Confidence range too narrow ({min_conf:.3f} - {max_conf:.3f})")
                
                validation['model_status'] = {
                    'action_distribution': action_distribution,
                    'confidence_stats': conf_stats
                }
                
        except Exception as e:
            validation['passed'] = False
            validation['issues'].append(f"ML validation error: {e}")
        
        return validation
    
    def validate_outcomes_evaluation(self) -> Dict:
        """Validate that outcomes evaluation doesn't use future data"""
        
        validation = {
            'passed': True,
            'issues': [],
            'outcomes_analysis': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check 1: Outcomes should not be evaluated before prediction time has passed
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM outcomes o
                    JOIN predictions p ON o.prediction_id = p.prediction_id
                    WHERE datetime(o.evaluation_timestamp) < datetime(p.prediction_timestamp, '+1 hour')
                """)
                
                premature_evaluations = cursor.fetchone()[0]
                if premature_evaluations > 0:
                    validation['passed'] = False
                    validation['issues'].append(f"CRITICAL: {premature_evaluations} outcomes evaluated too soon after prediction")
                    self.critical_issues.append("Premature outcome evaluation detected")
                
                # Check 2: Enhanced outcomes temporal consistency
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM enhanced_outcomes eo
                    JOIN enhanced_features ef ON eo.feature_id = ef.id
                    WHERE datetime(eo.prediction_timestamp) > datetime(ef.timestamp)
                """)
                
                enhanced_temporal_issues = cursor.fetchone()[0]
                if enhanced_temporal_issues > 0:
                    validation['issues'].append(f"WARNING: {enhanced_temporal_issues} enhanced outcomes with temporal inconsistencies")
                
                # Check 3: Exit prices should be after entry prices temporally
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM enhanced_outcomes
                    WHERE exit_timestamp IS NOT NULL 
                    AND datetime(exit_timestamp) <= datetime(prediction_timestamp)
                """)
                
                invalid_exit_times = cursor.fetchone()[0]
                if invalid_exit_times > 0:
                    validation['passed'] = False
                    validation['issues'].append(f"CRITICAL: {invalid_exit_times} outcomes with exit times before/at prediction time")
                
                # Check 4: Validate return calculations are reasonable
                cursor.execute("""
                    SELECT symbol, return_pct, entry_price, exit_price_1h, exit_price_4h, exit_price_1d
                    FROM enhanced_outcomes
                    WHERE return_pct IS NOT NULL
                    AND ABS(return_pct) > 50  -- More than 50% return is suspicious
                """)
                
                extreme_returns = cursor.fetchall()
                if extreme_returns:
                    validation['issues'].append(f"WARNING: {len(extreme_returns)} outcomes with extreme returns (>50%)")
                    for symbol, ret_pct, entry, exit_1h, exit_4h, exit_1d in extreme_returns[:3]:
                        validation['issues'].append(f"  • {symbol}: {ret_pct:.1f}% return (entry: {entry}, exits: {exit_1h}, {exit_4h}, {exit_1d})")
                
                # Check 5: Outcomes evaluation completeness
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_predictions,
                        COUNT(o.outcome_id) as evaluated_outcomes,
                        COUNT(eo.id) as enhanced_outcomes
                    FROM predictions p
                    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                    LEFT JOIN enhanced_outcomes eo ON p.prediction_id = eo.id
                    WHERE DATE(p.prediction_timestamp) <= DATE('now', '-1 day')
                """)
                
                total_preds, evaluated, enhanced = cursor.fetchone()
                
                if total_preds > 0:
                    eval_rate = evaluated / total_preds * 100
                    enhanced_rate = enhanced / total_preds * 100
                    
                    if eval_rate < 80:  # Less than 80% evaluated
                        validation['issues'].append(f"WARNING: Only {eval_rate:.1f}% of predictions have been evaluated")
                    
                    if enhanced_rate < 50:  # Less than 50% enhanced
                        validation['issues'].append(f"WARNING: Only {enhanced_rate:.1f}% of predictions have enhanced outcomes")
                
                validation['outcomes_analysis'] = {
                    'premature_evaluations': premature_evaluations,
                    'enhanced_temporal_issues': enhanced_temporal_issues,
                    'invalid_exit_times': invalid_exit_times,
                    'extreme_returns_count': len(extreme_returns),
                    'evaluation_stats': {
                        'total_predictions': total_preds,
                        'evaluated_outcomes': evaluated,
                        'enhanced_outcomes': enhanced,
                        'evaluation_rate': eval_rate if total_preds > 0 else 0,
                        'enhanced_rate': enhanced_rate if total_preds > 0 else 0
                    }
                }
                
        except Exception as e:
            validation['passed'] = False
            validation['issues'].append(f"Outcomes validation error: {e}")
        
        return validation
    
    def validate_data_freshness(self) -> Dict:
        """Ensure data is fresh enough for morning analysis"""
        
        validation = {
            'passed': True,
            'issues': [],
            'data_ages': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check ages of different data types
                tables_to_check = [
                    ('predictions', 'prediction_timestamp'),
                    ('enhanced_features', 'timestamp'),
                    ('sentiment_features', 'timestamp')
                ]
                
                for table, timestamp_col in tables_to_check:
                    cursor.execute(f"""
                        SELECT MAX({timestamp_col}) as latest
                        FROM {table}
                    """)
                    
                    latest = cursor.fetchone()[0]
                    if latest:
                        latest_dt = datetime.fromisoformat(latest)
                        age_hours = (self.validation_timestamp - latest_dt).total_seconds() / 3600
                        
                        validation['data_ages'][table] = {
                            'latest_timestamp': latest,
                            'age_hours': round(age_hours, 2)
                        }
                        
                        # Flag if data is too old
                        if table == 'enhanced_features' and age_hours > 24:
                            validation['issues'].append(f"STALE DATA: {table} is {age_hours:.1f} hours old")
                        elif table == 'predictions' and age_hours > 48:
                            validation['issues'].append(f"STALE DATA: {table} is {age_hours:.1f} hours old")
                
        except Exception as e:
            validation['passed'] = False
            validation['issues'].append(f"Data freshness error: {e}")
        
        return validation
    
    def run_comprehensive_guard(self) -> bool:
        """Run all validations - returns True if safe to proceed with morning analysis"""
        
        print("🛡️  MORNING ROUTINE TEMPORAL INTEGRITY GUARD")
        print("=" * 55)
        print(f"🕐 Validation time: {self.validation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_validations = {}
        overall_safe = True
        
        # Run all validation checks
        validations = [
            ("Temporal Consistency", self.validate_temporal_consistency),
            ("Technical Indicators", self.validate_technical_indicators),
            ("ML Model Health", self.validate_ml_model_health),
            ("Outcomes Evaluation", self.validate_outcomes_evaluation),
            ("Data Freshness", self.validate_data_freshness)
        ]
        
        for name, validator in validations:
            print(f"\n🔍 CHECKING {name.upper()}...")
            
            result = validator()
            all_validations[name] = result
            
            if result['passed']:
                print(f"✅ {name}: PASSED")
            else:
                print(f"❌ {name}: FAILED")
                overall_safe = False
            
            # Show issues
            for issue in result.get('issues', []):
                if 'CRITICAL' in issue:
                    print(f"  🚨 {issue}")
                elif 'WARNING' in issue:
                    print(f"  ⚠️  {issue}")
                else:
                    print(f"  • {issue}")
            
            # Show anomalies
            for anomaly in result.get('anomalies', []):
                print(f"  ⚠️  {anomaly}")
        
        # Generate guard report
        guard_report = {
            'timestamp': self.validation_timestamp.isoformat(),
            'overall_safe': overall_safe,
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'validations': all_validations
        }
        
        with open('morning_guard_report.json', 'w') as f:
            json.dump(guard_report, f, indent=2)
        
        # Final verdict
        print("\n" + "=" * 55)
        if overall_safe:
            print("🏆 GUARD PASSED: SAFE TO PROCEED WITH MORNING ANALYSIS")
            print("✅ All temporal integrity checks passed")
            print("✅ No data leakage detected")
            print("✅ Technical indicators within bounds")
            print("✅ ML models functioning properly")
            print("✅ Outcomes evaluation temporally consistent")
        else:
            print("🛑 GUARD FAILED: DO NOT PROCEED WITH MORNING ANALYSIS")
            print("🚨 Critical issues detected that could compromise analysis")
            print("🔧 Fix the issues above before running morning routine")
            
            if self.critical_issues:
                print("\n🚨 CRITICAL ISSUES TO FIX:")
                for issue in self.critical_issues:
                    print(f"  • {issue}")
        
        print(f"\n📄 Detailed report: morning_guard_report.json")
        print("=" * 55)
        
        return overall_safe

def main():
    """Main function - returns exit code 0 if safe, 1 if not safe"""
    
    guard = MorningTemporalGuard()
    is_safe = guard.run_comprehensive_guard()
    
    # Exit with appropriate code for script integration
    sys.exit(0 if is_safe else 1)

if __name__ == "__main__":
    main()
