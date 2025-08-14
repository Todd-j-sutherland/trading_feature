#!/usr/bin/env python3
"""
Outcomes Evaluation Temporal Fixer

Fixes temporal consistency issues in the outcomes evaluation process.
Ensures that prediction outcomes are evaluated using proper temporal logic.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

class OutcomesTemporalFixer:
    """Fixes temporal issues in outcomes evaluation"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.fixes_applied = []
        
    def analyze_outcomes_temporal_issues(self) -> Dict:
        """Analyze temporal consistency issues in outcomes evaluation"""
        
        analysis = {
            'premature_evaluations': [],
            'temporal_inconsistencies': [],
            'invalid_exit_times': [],
            'extreme_returns': [],
            'evaluation_gaps': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find premature evaluations (evaluated too soon after prediction)
                cursor.execute("""
                    SELECT 
                        o.outcome_id,
                        p.prediction_id,
                        p.symbol,
                        p.prediction_timestamp,
                        o.evaluation_timestamp,
                        (julianday(o.evaluation_timestamp) - julianday(p.prediction_timestamp)) * 24 as hours_gap
                    FROM outcomes o
                    JOIN predictions p ON o.prediction_id = p.prediction_id
                    WHERE datetime(o.evaluation_timestamp) < datetime(p.prediction_timestamp, '+1 hour')
                """)
                
                for row in cursor.fetchall():
                    outcome_id, pred_id, symbol, pred_time, eval_time, hours_gap = row
                    analysis['premature_evaluations'].append({
                        'outcome_id': outcome_id,
                        'prediction_id': pred_id,
                        'symbol': symbol,
                        'prediction_time': pred_time,
                        'evaluation_time': eval_time,
                        'hours_gap': round(hours_gap, 2)
                    })
                
                # Find enhanced outcomes with temporal inconsistencies
                cursor.execute("""
                    SELECT 
                        eo.id,
                        eo.symbol,
                        eo.prediction_timestamp,
                        ef.timestamp as feature_timestamp,
                        (julianday(ef.timestamp) - julianday(eo.prediction_timestamp)) * 24 as hours_gap
                    FROM enhanced_outcomes eo
                    JOIN enhanced_features ef ON eo.feature_id = ef.id
                    WHERE datetime(ef.timestamp) > datetime(eo.prediction_timestamp, '+30 minutes')
                    ORDER BY hours_gap DESC
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    eo_id, symbol, pred_time, feat_time, hours_gap = row
                    analysis['temporal_inconsistencies'].append({
                        'enhanced_outcome_id': eo_id,
                        'symbol': symbol,
                        'prediction_time': pred_time,
                        'feature_time': feat_time,
                        'hours_gap': round(hours_gap, 2)
                    })
                
                # Find invalid exit times (exit before entry)
                cursor.execute("""
                    SELECT 
                        id,
                        symbol,
                        prediction_timestamp,
                        exit_timestamp,
                        entry_price,
                        exit_price_1h
                    FROM enhanced_outcomes
                    WHERE exit_timestamp IS NOT NULL 
                    AND datetime(exit_timestamp) <= datetime(prediction_timestamp)
                """)
                
                for row in cursor.fetchall():
                    eo_id, symbol, pred_time, exit_time, entry_price, exit_price = row
                    analysis['invalid_exit_times'].append({
                        'enhanced_outcome_id': eo_id,
                        'symbol': symbol,
                        'prediction_time': pred_time,
                        'exit_time': exit_time,
                        'entry_price': entry_price,
                        'exit_price': exit_price
                    })
                
                # Find extreme returns that might indicate calculation errors
                cursor.execute("""
                    SELECT 
                        id,
                        symbol,
                        return_pct,
                        entry_price,
                        exit_price_1h,
                        exit_price_4h,
                        exit_price_1d
                    FROM enhanced_outcomes
                    WHERE return_pct IS NOT NULL
                    AND ABS(return_pct) > 50
                    ORDER BY ABS(return_pct) DESC
                """)
                
                for row in cursor.fetchall():
                    eo_id, symbol, ret_pct, entry, exit_1h, exit_4h, exit_1d = row
                    analysis['extreme_returns'].append({
                        'enhanced_outcome_id': eo_id,
                        'symbol': symbol,
                        'return_pct': ret_pct,
                        'entry_price': entry,
                        'exit_prices': {
                            '1h': exit_1h,
                            '4h': exit_4h,
                            '1d': exit_1d
                        }
                    })
                
                # Find predictions that should have outcomes but don't
                cursor.execute("""
                    SELECT 
                        p.prediction_id,
                        p.symbol,
                        p.prediction_timestamp,
                        (julianday('now') - julianday(p.prediction_timestamp)) * 24 as hours_old
                    FROM predictions p
                    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                    WHERE o.outcome_id IS NULL
                    AND datetime(p.prediction_timestamp) < datetime('now', '-4 hours')
                    ORDER BY p.prediction_timestamp DESC
                    LIMIT 10
                """)
                
                for row in cursor.fetchall():
                    pred_id, symbol, pred_time, hours_old = row
                    analysis['evaluation_gaps'].append({
                        'prediction_id': pred_id,
                        'symbol': symbol,
                        'prediction_time': pred_time,
                        'hours_old': round(hours_old, 2)
                    })
                
        except Exception as e:
            print(f"Error analyzing outcomes: {e}")
        
        return analysis
    
    def fix_outcomes_temporal_issues(self) -> List[str]:
        """Fix identified temporal issues in outcomes evaluation"""
        
        fixes = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fix 1: Remove premature evaluations (evaluated too soon)
                cursor.execute("""
                    DELETE FROM outcomes 
                    WHERE outcome_id IN (
                        SELECT o.outcome_id 
                        FROM outcomes o
                        JOIN predictions p ON o.prediction_id = p.prediction_id
                        WHERE datetime(o.evaluation_timestamp) < datetime(p.prediction_timestamp, '+1 hour')
                    )
                """)
                deleted_premature = cursor.rowcount
                if deleted_premature > 0:
                    fix_msg = f"Removed {deleted_premature} premature outcome evaluations"
                    fixes.append(fix_msg)
                    self.fixes_applied.append(fix_msg)
                
                # Fix 2: Update invalid exit timestamps
                cursor.execute("""
                    UPDATE enhanced_outcomes 
                    SET exit_timestamp = datetime(prediction_timestamp, '+1 hour')
                    WHERE exit_timestamp IS NOT NULL 
                    AND datetime(exit_timestamp) <= datetime(prediction_timestamp)
                """)
                fixed_exit_times = cursor.rowcount
                if fixed_exit_times > 0:
                    fix_msg = f"Fixed {fixed_exit_times} invalid exit timestamps"
                    fixes.append(fix_msg)
                    self.fixes_applied.append(fix_msg)
                
                # Fix 3: Recalculate extreme returns (might be calculation errors)
                cursor.execute("""
                    UPDATE enhanced_outcomes 
                    SET return_pct = CASE 
                        WHEN entry_price > 0 AND exit_price_1h > 0 
                        THEN ((exit_price_1h - entry_price) / entry_price) * 100
                        ELSE NULL
                    END
                    WHERE ABS(return_pct) > 100
                    AND entry_price IS NOT NULL 
                    AND exit_price_1h IS NOT NULL
                """)
                recalculated_returns = cursor.rowcount
                if recalculated_returns > 0:
                    fix_msg = f"Recalculated {recalculated_returns} extreme return percentages"
                    fixes.append(fix_msg)
                    self.fixes_applied.append(fix_msg)
                
                # Fix 4: Clean up enhanced outcomes with temporal inconsistencies
                cursor.execute("""
                    DELETE FROM enhanced_outcomes 
                    WHERE id IN (
                        SELECT eo.id
                        FROM enhanced_outcomes eo
                        JOIN enhanced_features ef ON eo.feature_id = ef.id
                        WHERE datetime(ef.timestamp) > datetime(eo.prediction_timestamp, '+2 hours')
                    )
                """)
                deleted_inconsistent = cursor.rowcount
                if deleted_inconsistent > 0:
                    fix_msg = f"Removed {deleted_inconsistent} enhanced outcomes with temporal inconsistencies"
                    fixes.append(fix_msg)
                    self.fixes_applied.append(fix_msg)
                
                conn.commit()
                
        except Exception as e:
            error_msg = f"Error applying outcomes fixes: {e}"
            fixes.append(error_msg)
            self.fixes_applied.append(error_msg)
        
        return fixes
    
    def create_outcomes_temporal_constraints(self) -> List[str]:
        """Create database constraints to prevent future temporal issues in outcomes"""
        
        constraints = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create trigger to prevent premature outcome evaluation
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_premature_evaluation
                    BEFORE INSERT ON outcomes
                    BEGIN
                        SELECT CASE
                            WHEN EXISTS (
                                SELECT 1 FROM predictions p
                                WHERE p.prediction_id = NEW.prediction_id
                                AND datetime(NEW.evaluation_timestamp) < datetime(p.prediction_timestamp, '+1 hour')
                            )
                            THEN RAISE(ABORT, 'Cannot evaluate outcome less than 1 hour after prediction')
                        END;
                    END
                """)
                constraints.append("Created trigger to prevent premature outcome evaluation")
                
                # Create view for temporal-safe enhanced outcomes
                cursor.execute("""
                    CREATE VIEW IF NOT EXISTS temporal_safe_enhanced_outcomes AS
                    SELECT eo.*
                    FROM enhanced_outcomes eo
                    JOIN enhanced_features ef ON eo.feature_id = ef.id
                    WHERE datetime(ef.timestamp) <= datetime(eo.prediction_timestamp, '+30 minutes')
                    OR ef.timestamp IS NULL
                """)
                constraints.append("Created temporal-safe enhanced outcomes view")
                
                # Create trigger to validate exit times
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS validate_exit_times
                    BEFORE INSERT ON enhanced_outcomes
                    BEGIN
                        SELECT CASE
                            WHEN NEW.exit_timestamp IS NOT NULL
                            AND datetime(NEW.exit_timestamp) <= datetime(NEW.prediction_timestamp)
                            THEN RAISE(ABORT, 'Exit timestamp cannot be before or at prediction timestamp')
                        END;
                    END
                """)
                constraints.append("Created trigger to validate exit times")
                
                conn.commit()
                
        except Exception as e:
            error_msg = f"Error creating outcomes constraints: {e}"
            constraints.append(error_msg)
        
        return constraints
    
    def run_complete_outcomes_fix(self) -> None:
        """Run complete outcomes temporal fixing process"""
        
        print("📊 OUTCOMES EVALUATION TEMPORAL FIXER")
        print("=" * 50)
        print(f"🕐 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Analyze current issues
        print("\n🔍 ANALYZING OUTCOMES TEMPORAL ISSUES...")
        analysis = self.analyze_outcomes_temporal_issues()
        
        issues_found = sum(len(issues) for issues in analysis.values())
        
        if issues_found == 0:
            print("✅ No outcomes temporal issues found!")
        else:
            print(f"⚠️  Found {issues_found} outcomes temporal issues:")
            
            for issue_type, issues in analysis.items():
                if issues:
                    print(f"  • {issue_type.replace('_', ' ').title()}: {len(issues)}")
        
        # Step 2: Apply fixes
        print("\n🔧 APPLYING OUTCOMES TEMPORAL FIXES...")
        fixes = self.fix_outcomes_temporal_issues()
        
        if fixes:
            for fix in fixes:
                print(f"  ✅ {fix}")
        else:
            print("  ℹ️  No fixes needed")
        
        # Step 3: Create constraints
        print("\n🛡️  CREATING OUTCOMES TEMPORAL CONSTRAINTS...")
        constraints = self.create_outcomes_temporal_constraints()
        
        for constraint in constraints:
            print(f"  ✅ {constraint}")
        
        # Step 4: Generate report
        print("\n📋 GENERATING OUTCOMES FIX REPORT...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'fixes_applied': fixes,
            'constraints_created': constraints,
            'issues_before': issues_found,
            'fixes_count': len(fixes)
        }
        
        with open('outcomes_temporal_fix_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📄 Report saved to: outcomes_temporal_fix_report.json")
        
        # Step 5: Summary
        print("\n" + "=" * 50)
        print("📈 OUTCOMES TEMPORAL FIX SUMMARY:")
        print(f"🎯 Issues found: {issues_found}")
        print(f"🔧 Fixes applied: {len(fixes)}")
        print(f"🛡️  Constraints created: {len(constraints)}")
        
        if issues_found == 0:
            print("\n🏆 OUTCOMES EVALUATION IS TEMPORALLY CONSISTENT!")
        elif len(fixes) > 0:
            print("\n✅ OUTCOMES TEMPORAL ISSUES FIXED!")
            print("🛡️  Future issues prevented by constraints")
        else:
            print("\n⚠️  Some issues may require manual review")
        
        print("=" * 50)

def main():
    """Main function for outcomes temporal fixing"""
    
    fixer = OutcomesTemporalFixer()
    fixer.run_complete_outcomes_fix()

if __name__ == "__main__":
    main()
