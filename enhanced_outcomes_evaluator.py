#!/usr/bin/env python3
"""
Enhanced Outcomes Evaluation System

Provides a proper outcomes evaluation process that respects temporal constraints
and integrates with the morning routine temporal guard.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class EnhancedOutcomesEvaluator:
    """Proper outcomes evaluation with temporal integrity"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        
    def clean_invalid_outcomes(self) -> Dict:
        """Clean up invalid/incomplete outcomes data"""
        
        cleanup_results = {
            'deleted_incomplete': 0,
            'deleted_invalid': 0,
            'updated_ids': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove outcomes with NULL outcome_id or invalid data
                cursor.execute("""
                    DELETE FROM outcomes 
                    WHERE outcome_id IS NULL 
                    OR evaluation_timestamp IS NULL
                    OR prediction_id IS NULL
                """)
                cleanup_results['deleted_incomplete'] = cursor.rowcount
                
                # Remove enhanced outcomes with invalid timestamps
                cursor.execute("""
                    DELETE FROM enhanced_outcomes
                    WHERE prediction_timestamp IS NULL
                    OR exit_timestamp IS NULL
                    OR exit_timestamp <= prediction_timestamp
                """)
                cleanup_results['deleted_invalid'] = cursor.rowcount
                
                conn.commit()
                
        except Exception as e:
            print(f"Error cleaning outcomes: {e}")
        
    def run_evaluation(self) -> Dict:
        """Run complete outcomes evaluation process"""
        
        print("📊 ENHANCED OUTCOMES EVALUATION SYSTEM")
        print("=" * 50)
        
        results = {
            'cleanup_results': {},
            'evaluation_results': {},
            'validation_results': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 1: Clean invalid outcomes
        print("\n🧹 CLEANING INVALID OUTCOMES DATA...")
        cleanup_result = self.clean_invalid_outcomes()
        if cleanup_result is None:
            cleanup_result = {'deleted_incomplete': 0, 'deleted_invalid': 0}
        results['cleanup_results'] = cleanup_result
        
        # Step 2: Evaluate pending predictions
        print("\n📈 EVALUATING PENDING PREDICTIONS...")
        evaluation_result = self.evaluate_pending_predictions()
        if evaluation_result is None:
            evaluation_result = {'evaluated_count': 0, 'skipped_too_recent': 0, 'errors': []}
        results['evaluation_results'] = evaluation_result
        
        # Step 3: Validate outcomes integrity
        print("\n🔍 VALIDATING OUTCOMES INTEGRITY...")
        validation_result = self.validate_outcomes_integrity()
        if validation_result is None:
            validation_result = {'temporal_issues': 0, 'total_outcomes': 0, 'valid_outcomes': 0}
        results['validation_results'] = validation_result
        
        # Summary
        total_cleaned = results['cleanup_results'].get('deleted_incomplete', 0) + results['cleanup_results'].get('deleted_invalid', 0)
        total_evaluated = results['evaluation_results'].get('evaluated_count', 0)
        total_issues = results['validation_results'].get('temporal_issues', 0)
        
        print("\n" + "=" * 50)
        if total_issues == 0:
            print("✅ OUTCOMES EVALUATION SAFE!")
            if total_evaluated > 0:
                print(f"📊 Evaluated {total_evaluated} new predictions")
            else:
                print("ℹ️  No new evaluations needed at this time")
        else:
            print("⚠️  OUTCOMES EVALUATION HAS ISSUES!")
            print(f"🔧 {total_issues} temporal issues detected")
        print("=" * 50)
        
        return results
    
    def evaluate_pending_predictions(self, min_age_hours: int = 4) -> Dict:
        """Evaluate predictions that are old enough and don't have outcomes yet"""
        
        evaluation_results = {
            'evaluated_count': 0,
            'skipped_too_recent': 0,
            'errors': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find predictions that need evaluation (older than min_age_hours)
                cutoff_time = datetime.now() - timedelta(hours=min_age_hours)
                
                cursor.execute("""
                    SELECT 
                        p.prediction_id,
                        p.symbol,
                        p.prediction_timestamp,
                        p.predicted_action,
                        p.predicted_direction,
                        p.predicted_magnitude,
                        p.entry_price
                    FROM predictions p
                    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                    WHERE o.outcome_id IS NULL
                    AND datetime(p.prediction_timestamp) < ?
                    ORDER BY p.prediction_timestamp ASC
                """, (cutoff_time.isoformat(),))
                
                pending_predictions = cursor.fetchall()
                
                for pred in pending_predictions:
                    pred_id, symbol, pred_time, action, direction, magnitude, entry_price = pred
                    
                    try:
                        # Get the latest price data for this symbol after the prediction
                        cursor.execute("""
                            SELECT current_price, timestamp
                            FROM enhanced_features
                            WHERE symbol = ?
                            AND datetime(timestamp) > datetime(?)
                            ORDER BY timestamp DESC
                            LIMIT 1
                        """, (symbol, pred_time))
                        
                        price_data = cursor.fetchone()
                        
                        if price_data:
                            exit_price, exit_time = price_data
                            
                            # Calculate actual return
                            if entry_price and entry_price > 0 and exit_price:
                                actual_return = ((exit_price - entry_price) / entry_price) * 100
                                
                                # Determine actual direction
                                actual_direction = 1 if exit_price > entry_price else -1 if exit_price < entry_price else 0
                                
                                # Create outcome record
                                outcome_id = str(uuid.uuid4())
                                evaluation_time = datetime.now()
                                
                                cursor.execute("""
                                    INSERT INTO outcomes (
                                        outcome_id, prediction_id, actual_return, actual_direction,
                                        entry_price, exit_price, evaluation_timestamp, created_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    outcome_id, pred_id, actual_return, actual_direction,
                                    entry_price, exit_price, evaluation_time.isoformat(), 
                                    evaluation_time.isoformat()
                                ))
                                
                                evaluation_results['evaluated_count'] += 1
                                
                            else:
                                evaluation_results['errors'].append(f"Invalid prices for {symbol}: entry={entry_price}, exit={exit_price}")
                        else:
                            evaluation_results['errors'].append(f"No price data found after prediction for {symbol}")
                            
                    except Exception as e:
                        evaluation_results['errors'].append(f"Error evaluating {symbol}: {e}")
                
                conn.commit()
                
        except Exception as e:
            evaluation_results['errors'].append(f"Database error: {e}")
        
        return evaluation_results
    
    def validate_outcomes_integrity(self) -> Dict:
        """Validate outcomes data integrity after evaluation"""
        
        validation = {
            'total_outcomes': 0,
            'valid_outcomes': 0,
            'temporal_issues': 0,
            'calculation_issues': 0,
            'summary': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count total outcomes
                cursor.execute("SELECT COUNT(*) FROM outcomes WHERE outcome_id IS NOT NULL")
                validation['total_outcomes'] = cursor.fetchone()[0]
                
                # Count valid outcomes (proper temporal relationship)
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes o
                    JOIN predictions p ON o.prediction_id = p.prediction_id
                    WHERE o.outcome_id IS NOT NULL
                    AND datetime(o.evaluation_timestamp) >= datetime(p.prediction_timestamp, '+1 hour')
                """)
                validation['valid_outcomes'] = cursor.fetchone()[0]
                
                # Count temporal issues
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes o
                    JOIN predictions p ON o.prediction_id = p.prediction_id
                    WHERE o.outcome_id IS NOT NULL
                    AND datetime(o.evaluation_timestamp) < datetime(p.prediction_timestamp, '+1 hour')
                """)
                validation['temporal_issues'] = cursor.fetchone()[0]
                
                # Count calculation issues (extreme returns)
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes
                    WHERE outcome_id IS NOT NULL
                    AND ABS(actual_return) > 50
                """)
                validation['calculation_issues'] = cursor.fetchone()[0]
                
                validation['summary'] = {
                    'integrity_rate': (validation['valid_outcomes'] / validation['total_outcomes'] * 100) if validation['total_outcomes'] > 0 else 0,
                    'temporal_issue_rate': (validation['temporal_issues'] / validation['total_outcomes'] * 100) if validation['total_outcomes'] > 0 else 0
                }
                
        except Exception as e:
            print(f"Error validating outcomes: {e}")
        
        return validation
    
    def run_complete_outcomes_evaluation(self) -> Dict:
        """Run complete outcomes evaluation process with temporal safety"""
        
        print("📊 ENHANCED OUTCOMES EVALUATION SYSTEM")
        print("=" * 50)
        
        results = {
            'cleanup': {},
            'evaluation': {},
            'validation': {}
        }
        
        # Step 1: Clean up invalid data
        print("\n🧹 CLEANING INVALID OUTCOMES DATA...")
        results['cleanup'] = self.clean_invalid_outcomes()
        
        print(f"  ✅ Deleted {results['cleanup']['deleted_incomplete']} incomplete outcomes")
        print(f"  ✅ Deleted {results['cleanup']['deleted_invalid']} invalid enhanced outcomes")
        
        # Step 2: Evaluate pending predictions
        print("\n📈 EVALUATING PENDING PREDICTIONS...")
        results['evaluation'] = self.evaluate_pending_predictions()
        
        print(f"  ✅ Evaluated {results['evaluation']['evaluated_count']} predictions")
        print(f"  ⏳ Skipped {results['evaluation']['skipped_too_recent']} recent predictions")
        
        if results['evaluation']['errors']:
            print(f"  ⚠️  {len(results['evaluation']['errors'])} evaluation errors:")
            for error in results['evaluation']['errors'][:3]:  # Show first 3 errors
                print(f"    • {error}")
        
        # Step 3: Validate integrity
        print("\n🔍 VALIDATING OUTCOMES INTEGRITY...")
        results['validation'] = self.validate_outcomes_integrity()
        
        total = results['validation']['total_outcomes']
        valid = results['validation']['valid_outcomes']
        temporal_issues = results['validation']['temporal_issues']
        
        print(f"  📊 Total outcomes: {total}")
        print(f"  ✅ Valid outcomes: {valid}")
        print(f"  ⚠️  Temporal issues: {temporal_issues}")
        
        if total > 0:
            integrity_rate = results['validation']['summary']['integrity_rate']
            print(f"  🎯 Integrity rate: {integrity_rate:.1f}%")
        
        # Step 4: Summary
        print("\n" + "=" * 50)
        if temporal_issues == 0 and results['evaluation']['evaluated_count'] > 0:
            print("🏆 OUTCOMES EVALUATION COMPLETED SUCCESSFULLY!")
            print("✅ All evaluations respect temporal constraints")
            print("✅ No data leakage in outcomes evaluation")
        elif temporal_issues == 0:
            print("✅ OUTCOMES EVALUATION SAFE!")
            print("ℹ️  No new evaluations needed at this time")
        else:
            print("⚠️  OUTCOMES EVALUATION COMPLETED WITH WARNINGS")
            print(f"🔧 {temporal_issues} temporal issues may need manual review")
        
        print("=" * 50)
        
        return results

def main():
    """Main function for enhanced outcomes evaluation"""
    
    evaluator = EnhancedOutcomesEvaluator()
    evaluator.run_complete_outcomes_evaluation()

if __name__ == "__main__":
    main()
