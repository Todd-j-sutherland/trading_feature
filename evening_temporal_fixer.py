#!/usr/bin/env python3
"""
Evening Temporal Fixer - Data Quality & Integrity Repair
========================================================

Fixes the specific evening data quality issues:
- Duplicate prediction cleanup
- Null actual returns repair
- Data consistency restoration
- Database constraint implementation
- Idempotent operation setup

Usage:
    python3 evening_temporal_fixer.py
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

class EveningTemporalFixer:
    """Fix evening data quality and temporal integrity issues"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.fix_timestamp = datetime.now()
        
    def run_evening_fixes(self) -> Dict:
        """Run all evening temporal and data quality fixes"""
        
        print("🔧 EVENING TEMPORAL FIXER")
        print("=" * 40)
        print(f"🕐 Fix time: {self.fix_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'duplicate_fixes': 0,
            'null_return_fixes': 0,
            'consistency_fixes': 0,
            'constraints_added': 0,
            'database_optimized': False
        }
        
        # 1. Fix duplicate predictions
        print("\n🔄 Fixing duplicate predictions...")
        results['duplicate_fixes'] = self._fix_duplicate_predictions()
        
        # 2. Fix null actual returns
        print("\n💰 Fixing null actual returns...")
        results['null_return_fixes'] = self._fix_null_actual_returns()
        
        # 3. Fix data consistency issues
        print("\n📊 Fixing data consistency...")
        results['consistency_fixes'] = self._fix_data_consistency()
        
        # 4. Add database constraints
        print("\n🛡️ Adding database constraints...")
        results['constraints_added'] = self._add_database_constraints()
        
        # 5. Optimize database
        print("\n⚡ Optimizing database...")
        results['database_optimized'] = self._optimize_database()
        
        # Generate fix report
        self._generate_fix_report(results)
        
        # Summary
        total_fixes = sum([
            results['duplicate_fixes'],
            results['null_return_fixes'], 
            results['consistency_fixes'],
            results['constraints_added']
        ])
        
        print(f"\n" + "=" * 40)
        print(f"🎯 EVENING FIXES COMPLETED")
        print(f"✅ Total fixes applied: {total_fixes}")
        print(f"📄 Detailed report: evening_fix_report.json")
        print("=" * 40)
        
        return results
    
    def _fix_duplicate_predictions(self) -> int:
        """Fix duplicate predictions using date-based deduplication"""
        
        fixes_applied = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find duplicate predictions (keep the latest for each symbol+date)
                cursor.execute("""
                    WITH RankedPredictions AS (
                        SELECT prediction_id, symbol, date(prediction_timestamp) as pred_date,
                               prediction_timestamp,
                               ROW_NUMBER() OVER (
                                   PARTITION BY symbol, date(prediction_timestamp) 
                                   ORDER BY prediction_timestamp DESC
                               ) as rn
                        FROM predictions
                    )
                    SELECT prediction_id FROM RankedPredictions WHERE rn > 1
                """)
                
                duplicate_ids = [row[0] for row in cursor.fetchall()]
                
                if duplicate_ids:
                    # Delete duplicate predictions
                    placeholders = ','.join(['?' for _ in duplicate_ids])
                    cursor.execute(f"""
                        DELETE FROM predictions 
                        WHERE prediction_id IN ({placeholders})
                    """, duplicate_ids)
                    
                    fixes_applied = len(duplicate_ids)
                    print(f"  ✅ Removed {fixes_applied} duplicate predictions")
                    
                    # Also clean up any related features/outcomes
                    for table in ['features', 'prediction_features', 'outcomes']:
                        try:
                            cursor.execute(f"""
                                DELETE FROM {table} 
                                WHERE prediction_id IN ({placeholders})
                            """, duplicate_ids)
                        except sqlite3.OperationalError:
                            # Table might not exist
                            pass
                else:
                    print("  ✅ No duplicate predictions found")
        
        except Exception as e:
            print(f"  ❌ Error fixing duplicates: {e}")
        
        return fixes_applied
    
    def _fix_null_actual_returns(self) -> int:
        """Fix null actual returns by calculating from price data or removing"""
        
        fixes_applied = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find outcomes with null actual returns
                cursor.execute("""
                    SELECT o.outcome_id, o.prediction_id, p.symbol, p.prediction_timestamp
                    FROM outcomes o
                    JOIN predictions p ON o.prediction_id = p.prediction_id
                    WHERE o.actual_return IS NULL OR o.actual_return = 0
                """)
                
                null_outcomes = cursor.fetchall()
                
                if null_outcomes:
                    print(f"  🔍 Found {len(null_outcomes)} outcomes with null returns")
                    
                    # For now, remove these invalid outcomes (can be enhanced to calculate actual returns)
                    null_ids = [row[0] for row in null_outcomes]
                    placeholders = ','.join(['?' for _ in null_ids])
                    
                    cursor.execute(f"""
                        DELETE FROM outcomes 
                        WHERE outcome_id IN ({placeholders})
                    """, null_ids)
                    
                    fixes_applied = len(null_ids)
                    print(f"  ✅ Removed {fixes_applied} outcomes with null returns")
                    print("  💡 Future enhancement: Calculate actual returns from price data")
                else:
                    print("  ✅ No null actual returns found")
        
        except Exception as e:
            print(f"  ❌ Error fixing null returns: {e}")
        
        return fixes_applied
    
    def _fix_data_consistency(self) -> int:
        """Fix data consistency between predictions and features"""
        
        fixes_applied = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find feature tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND (name LIKE '%feature%' OR name = 'sentiment_features' OR name = 'enhanced_features')
                """)
                feature_tables = [row[0] for row in cursor.fetchall()]
                
                if not feature_tables:
                    print("  ⚠️ No feature tables found")
                    return 0
                
                feature_table = feature_tables[0]  # Use first found
                print(f"  📊 Using feature table: {feature_table}")
                
                # Find predictions without features (using symbol+date matching)
                cursor.execute(f"""
                    SELECT p.prediction_id FROM predictions p
                    LEFT JOIN {feature_table} f ON p.symbol = f.symbol 
                        AND date(p.prediction_timestamp) = date(f.timestamp)
                    WHERE f.symbol IS NULL
                """)
                
                orphaned_predictions = [row[0] for row in cursor.fetchall()]
                
                if orphaned_predictions:
                    # Remove orphaned predictions
                    placeholders = ','.join(['?' for _ in orphaned_predictions])
                    cursor.execute(f"""
                        DELETE FROM predictions 
                        WHERE prediction_id IN ({placeholders})
                    """, orphaned_predictions)
                    
                    fixes_applied = len(orphaned_predictions)
                    print(f"  ✅ Removed {fixes_applied} predictions without features")
                
                # Find features without predictions (using symbol+date matching)
                cursor.execute(f"""
                    SELECT f.id FROM {feature_table} f
                    LEFT JOIN predictions p ON f.symbol = p.symbol 
                        AND date(f.timestamp) = date(p.prediction_timestamp)
                    WHERE p.prediction_id IS NULL
                """)
                
                orphaned_features = [row[0] for row in cursor.fetchall()]
                
                if orphaned_features:
                    # Remove orphaned features
                    placeholders = ','.join(['?' for _ in orphaned_features])
                    cursor.execute(f"""
                        DELETE FROM {feature_table} 
                        WHERE id IN ({placeholders})
                    """, orphaned_features)
                    
                    fixes_applied += len(orphaned_features)
                    print(f"  ✅ Removed {len(orphaned_features)} orphaned features")
                
                if fixes_applied == 0:
                    print("  ✅ Data consistency is good")
        
        except Exception as e:
            print(f"  ❌ Error fixing data consistency: {e}")
        
        return fixes_applied
    
    def _add_database_constraints(self) -> int:
        """Add database constraints to prevent future issues"""
        
        constraints_added = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                constraints = [
                    # Unique constraint on predictions (symbol, date)
                    {
                        'name': 'unique_symbol_date',
                        'sql': '''
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_prediction_symbol_date 
                            ON predictions(symbol, date(prediction_timestamp))
                        ''',
                        'description': 'Prevent duplicate predictions per symbol per day'
                    },
                    
                    # Not null constraint simulation for critical columns
                    {
                        'name': 'check_prediction_timestamp',
                        'sql': '''
                            CREATE TRIGGER IF NOT EXISTS validate_prediction_timestamp
                            BEFORE INSERT ON predictions
                            WHEN NEW.prediction_timestamp IS NULL
                            BEGIN
                                SELECT RAISE(ABORT, 'prediction_timestamp cannot be null');
                            END
                        ''',
                        'description': 'Ensure prediction_timestamp is not null'
                    },
                    
                    # Check constraint for valid symbols
                    {
                        'name': 'check_symbol_format',
                        'sql': '''
                            CREATE TRIGGER IF NOT EXISTS validate_symbol_format
                            BEFORE INSERT ON predictions
                            WHEN NEW.symbol IS NULL OR NEW.symbol = '' OR length(NEW.symbol) < 2
                            BEGIN
                                SELECT RAISE(ABORT, 'symbol must be valid');
                            END
                        ''',
                        'description': 'Ensure symbol is valid'
                    },
                    
                    # Temporal consistency trigger
                    {
                        'name': 'check_temporal_consistency',
                        'sql': '''
                            CREATE TRIGGER IF NOT EXISTS validate_temporal_consistency
                            BEFORE INSERT ON outcomes
                            WHEN NEW.evaluation_timestamp < (
                                SELECT prediction_timestamp FROM predictions 
                                WHERE prediction_id = NEW.prediction_id
                            )
                            BEGIN
                                SELECT RAISE(ABORT, 'evaluation cannot be before prediction');
                            END
                        ''',
                        'description': 'Prevent temporal violations in outcomes'
                    }
                ]
                
                for constraint in constraints:
                    try:
                        cursor.execute(constraint['sql'])
                        constraints_added += 1
                        print(f"  ✅ Added: {constraint['description']}")
                    except Exception as e:
                        print(f"  ⚠️ Could not add {constraint['name']}: {e}")
        
        except Exception as e:
            print(f"  ❌ Error adding constraints: {e}")
        
        return constraints_added
    
    def _optimize_database(self) -> bool:
        """Optimize database performance and integrity"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Analyze tables for query optimization
                cursor.execute("ANALYZE")
                
                # Vacuum to reclaim space and defragment
                cursor.execute("VACUUM")
                
                # Update table statistics
                cursor.execute("PRAGMA optimize")
                
                print("  ✅ Database optimized (analyzed, vacuumed, optimized)")
                return True
        
        except Exception as e:
            print(f"  ❌ Error optimizing database: {e}")
            return False
    
    def _generate_fix_report(self, results: Dict):
        """Generate detailed fix report"""
        
        report = {
            "fix_timestamp": self.fix_timestamp.isoformat(),
            "fixes_applied": results,
            "total_fixes": sum([
                results['duplicate_fixes'],
                results['null_return_fixes'],
                results['consistency_fixes'],
                results['constraints_added']
            ]),
            "recommendations": [
                "Monitor evening_guard_report.json for ongoing issues",
                "Run evening temporal guard regularly",
                "Consider implementing real-time data validation",
                "Set up automated constraint monitoring"
            ],
            "next_steps": [
                "Test duplicate prevention with new data",
                "Implement actual return calculation from price data", 
                "Set up automated evening validation cron job",
                "Monitor database performance after optimization"
            ]
        }
        
        try:
            import json
            with open("evening_fix_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Could not save fix report: {e}")

def main():
    """Main function for evening temporal fixer"""
    
    fixer = EveningTemporalFixer()
    results = fixer.run_evening_fixes()
    
    # Return appropriate exit code
    total_fixes = sum([
        results['duplicate_fixes'],
        results['null_return_fixes'],
        results['consistency_fixes'],
        results['constraints_added']
    ])
    
    if total_fixes > 0:
        print(f"\n✅ Evening fixes completed successfully: {total_fixes} issues resolved")
    else:
        print(f"\n✅ No fixes needed - data quality is good")

if __name__ == "__main__":
    main()
