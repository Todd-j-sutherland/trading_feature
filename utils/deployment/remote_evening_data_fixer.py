#!/usr/bin/env python3
"""
Remote Evening Data Quality Fixer

Comprehensive fix for remote database issues detected in evening routine:
- Mismatch: 15 predictions vs 8 features
- 11 outcomes with null actual returns
- Found 1 days with duplicate predictions
- Error checking data leakage: no such column: f2.analysis_timestamp
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import json

class RemoteEveningDataFixer:
    """Fix remote database issues for evening routine"""
    
    def __init__(self, db_path: str = "/root/test/data/trading_predictions.db"):
        self.db_path = Path(db_path)
        
    def analyze_remote_issues(self) -> dict:
        """Analyze the specific issues on remote database"""
        
        analysis = {
            'predictions_count': 0,
            'features_count': 0,
            'outcomes_count': 0,
            'null_outcomes': 0,
            'duplicate_predictions': 0,
            'schema_issues': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count predictions
                cursor.execute("SELECT COUNT(*) FROM predictions")
                analysis['predictions_count'] = cursor.fetchone()[0]
                
                # Count features  
                cursor.execute("SELECT COUNT(*) FROM enhanced_features")
                analysis['features_count'] = cursor.fetchone()[0]
                
                # Count outcomes
                cursor.execute("SELECT COUNT(*) FROM outcomes")
                analysis['outcomes_count'] = cursor.fetchone()[0]
                
                # Count null outcomes
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes 
                    WHERE actual_return IS NULL OR actual_return = 0
                """)
                analysis['null_outcomes'] = cursor.fetchone()[0]
                
                # Check for duplicates
                cursor.execute("""
                    SELECT COUNT(*) - COUNT(DISTINCT symbol, DATE(prediction_timestamp))
                    FROM predictions
                """)
                analysis['duplicate_predictions'] = cursor.fetchone()[0]
                
                # Check schema issues
                try:
                    cursor.execute("SELECT analysis_timestamp FROM enhanced_features LIMIT 1")
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e):
                        analysis['schema_issues'].append("Missing analysis_timestamp column in enhanced_features")
                
                try:
                    cursor.execute("SELECT f2.analysis_timestamp FROM enhanced_features f2 LIMIT 1")
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e):
                        analysis['schema_issues'].append("Missing analysis_timestamp column - affects data leakage checks")
                
        except Exception as e:
            print(f"Error analyzing remote issues: {e}")
            
        return analysis
    
    def fix_schema_issues(self) -> dict:
        """Fix schema-related issues"""
        
        fixes = {
            'schema_fixes': 0,
            'columns_added': [],
            'indexes_created': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Add missing analysis_timestamp column if needed
                try:
                    cursor.execute("SELECT analysis_timestamp FROM enhanced_features LIMIT 1")
                except sqlite3.OperationalError:
                    print("🔧 Adding missing analysis_timestamp column...")
                    cursor.execute("""
                        ALTER TABLE enhanced_features 
                        ADD COLUMN analysis_timestamp TEXT
                    """)
                    
                    # Populate with timestamp values
                    cursor.execute("""
                        UPDATE enhanced_features 
                        SET analysis_timestamp = timestamp 
                        WHERE analysis_timestamp IS NULL
                    """)
                    
                    fixes['columns_added'].append('analysis_timestamp')
                    fixes['schema_fixes'] += 1
                
                # Add missing columns to outcomes if needed
                try:
                    cursor.execute("SELECT evaluation_timestamp FROM outcomes LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("""
                        ALTER TABLE outcomes 
                        ADD COLUMN evaluation_timestamp TEXT
                    """)
                    
                    # Set evaluation timestamp to current time for existing records
                    current_time = datetime.now().isoformat()
                    cursor.execute("""
                        UPDATE outcomes 
                        SET evaluation_timestamp = ? 
                        WHERE evaluation_timestamp IS NULL
                    """, (current_time,))
                    
                    fixes['columns_added'].append('evaluation_timestamp')
                    fixes['schema_fixes'] += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"Error fixing schema: {e}")
            
        return fixes
    
    def fix_duplicate_predictions(self) -> dict:
        """Remove duplicate predictions"""
        
        fixes = {
            'duplicates_removed': 0,
            'predictions_kept': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find and remove duplicates, keeping the latest one
                cursor.execute("""
                    DELETE FROM predictions 
                    WHERE prediction_id NOT IN (
                        SELECT prediction_id 
                        FROM (
                            SELECT prediction_id,
                                   ROW_NUMBER() OVER (
                                       PARTITION BY symbol, DATE(prediction_timestamp) 
                                       ORDER BY prediction_timestamp DESC
                                   ) as rn
                            FROM predictions
                        ) ranked
                        WHERE rn = 1
                    )
                """)
                
                fixes['duplicates_removed'] = cursor.rowcount
                
                # Count remaining predictions
                cursor.execute("SELECT COUNT(*) FROM predictions")
                fixes['predictions_kept'] = cursor.fetchone()[0]
                
                conn.commit()
                
        except Exception as e:
            print(f"Error fixing duplicates: {e}")
            
        return fixes
    
    def fix_null_outcomes(self) -> dict:
        """Fix outcomes with null actual returns"""
        
        fixes = {
            'outcomes_calculated': 0,
            'outcomes_removed': 0,
            'missing_prices': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get outcomes with null returns but valid prices
                cursor.execute("""
                    SELECT o.outcome_id, o.entry_price, o.exit_price
                    FROM outcomes o
                    WHERE (o.actual_return IS NULL OR o.actual_return = 0)
                    AND o.entry_price IS NOT NULL 
                    AND o.exit_price IS NOT NULL
                    AND o.entry_price > 0
                    AND o.exit_price > 0
                """)
                
                null_outcomes = cursor.fetchall()
                
                for outcome_id, entry_price, exit_price in null_outcomes:
                    # Calculate actual return
                    actual_return = ((exit_price - entry_price) / entry_price) * 100
                    
                    # Update the outcome
                    cursor.execute("""
                        UPDATE outcomes 
                        SET actual_return = ?
                        WHERE outcome_id = ?
                    """, (actual_return, outcome_id))
                    
                    fixes['outcomes_calculated'] += 1
                
                # Remove outcomes with missing price data (can't be calculated)
                cursor.execute("""
                    DELETE FROM outcomes 
                    WHERE (actual_return IS NULL OR actual_return = 0)
                    AND (entry_price IS NULL OR exit_price IS NULL 
                         OR entry_price <= 0 OR exit_price <= 0)
                """)
                
                fixes['outcomes_removed'] = cursor.rowcount
                
                conn.commit()
                
        except Exception as e:
            print(f"Error fixing null outcomes: {e}")
            
        return fixes
    
    def align_predictions_features(self) -> dict:
        """Align predictions with features to fix mismatch"""
        
        fixes = {
            'orphaned_predictions': 0,
            'orphaned_features': 0,
            'aligned_records': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove predictions without corresponding features
                cursor.execute("""
                    DELETE FROM predictions 
                    WHERE NOT EXISTS (
                        SELECT 1 FROM enhanced_features ef
                        WHERE ef.symbol = predictions.symbol
                        AND DATE(ef.timestamp) = DATE(predictions.prediction_timestamp)
                    )
                """)
                
                fixes['orphaned_predictions'] = cursor.rowcount
                
                # Count aligned records
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions p
                    INNER JOIN enhanced_features ef 
                    ON p.symbol = ef.symbol 
                    AND DATE(p.prediction_timestamp) = DATE(ef.timestamp)
                """)
                
                fixes['aligned_records'] = cursor.fetchone()[0]
                
                conn.commit()
                
        except Exception as e:
            print(f"Error aligning predictions and features: {e}")
            
        return fixes
    
    def add_database_constraints(self) -> dict:
        """Add constraints to prevent future issues"""
        
        constraints = {
            'constraints_added': 0,
            'indexes_created': 0,
            'triggers_created': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Add unique constraint on predictions (symbol, date)
                try:
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_symbol_date 
                        ON predictions(symbol, DATE(prediction_timestamp))
                    """)
                    constraints['indexes_created'] += 1
                except sqlite3.OperationalError:
                    pass  # Index might already exist
                
                # Add constraint on outcomes
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_outcomes_prediction 
                        ON outcomes(prediction_id)
                    """)
                    constraints['indexes_created'] += 1
                except sqlite3.OperationalError:
                    pass
                
                # Add timestamp indexes for performance
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_features_timestamp 
                        ON enhanced_features(timestamp)
                    """)
                    constraints['indexes_created'] += 1
                except sqlite3.OperationalError:
                    pass
                
                conn.commit()
                
        except Exception as e:
            print(f"Error adding constraints: {e}")
            
        return constraints
    
    def run_comprehensive_fix(self) -> dict:
        """Run all fixes in correct order"""
        
        print("🔧 REMOTE EVENING DATA QUALITY FIXER")
        print("=" * 50)
        
        # Step 1: Analyze issues
        print("🔍 Analyzing remote database issues...")
        analysis = self.analyze_remote_issues()
        
        print(f"   📊 Predictions: {analysis['predictions_count']}")
        print(f"   📊 Features: {analysis['features_count']}")
        print(f"   📊 Outcomes: {analysis['outcomes_count']}")
        print(f"   ❌ Null outcomes: {analysis['null_outcomes']}")
        print(f"   🔄 Duplicates: {analysis['duplicate_predictions']}")
        print(f"   🏗️ Schema issues: {len(analysis['schema_issues'])}")
        
        # Step 2: Fix schema issues
        print("\n🏗️ Fixing schema issues...")
        schema_fixes = self.fix_schema_issues()
        print(f"   ✅ Columns added: {schema_fixes['columns_added']}")
        
        # Step 3: Remove duplicates
        print("\n🔄 Removing duplicate predictions...")
        duplicate_fixes = self.fix_duplicate_predictions()
        print(f"   ✅ Duplicates removed: {duplicate_fixes['duplicates_removed']}")
        print(f"   📊 Predictions remaining: {duplicate_fixes['predictions_kept']}")
        
        # Step 4: Fix null outcomes
        print("\n💰 Fixing null outcomes...")
        outcome_fixes = self.fix_null_outcomes()
        print(f"   ✅ Returns calculated: {outcome_fixes['outcomes_calculated']}")
        print(f"   🗑️ Invalid outcomes removed: {outcome_fixes['outcomes_removed']}")
        
        # Step 5: Align predictions and features
        print("\n🔗 Aligning predictions with features...")
        alignment_fixes = self.align_predictions_features()
        print(f"   ✅ Orphaned predictions removed: {alignment_fixes['orphaned_predictions']}")
        print(f"   📊 Aligned records: {alignment_fixes['aligned_records']}")
        
        # Step 6: Add constraints
        print("\n🛡️ Adding database constraints...")
        constraint_fixes = self.add_database_constraints()
        print(f"   ✅ Indexes created: {constraint_fixes['indexes_created']}")
        
        # Final analysis
        print("\n🔍 Final verification...")
        final_analysis = self.analyze_remote_issues()
        
        print("\n" + "=" * 50)
        print("🎯 REMOTE FIX SUMMARY")
        print(f"   📊 Final predictions: {final_analysis['predictions_count']}")
        print(f"   📊 Final features: {final_analysis['features_count']}")
        print(f"   💰 Final outcomes: {final_analysis['outcomes_count']}")
        print(f"   ❌ Remaining null outcomes: {final_analysis['null_outcomes']}")
        print(f"   🔄 Remaining duplicates: {final_analysis['duplicate_predictions']}")
        print(f"   🏗️ Remaining schema issues: {len(final_analysis['schema_issues'])}")
        
        if (final_analysis['null_outcomes'] == 0 and 
            final_analysis['duplicate_predictions'] == 0 and 
            len(final_analysis['schema_issues']) == 0):
            print("🏆 ALL REMOTE ISSUES RESOLVED!")
        else:
            print("⚠️ Some issues remain - check details above")
        
        print("=" * 50)
        
        # Save comprehensive report
        report = {
            'initial_analysis': analysis,
            'schema_fixes': schema_fixes,
            'duplicate_fixes': duplicate_fixes,
            'outcome_fixes': outcome_fixes,
            'alignment_fixes': alignment_fixes,
            'constraint_fixes': constraint_fixes,
            'final_analysis': final_analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('/root/test/remote_evening_fix_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    """Main function to run remote evening data fixer"""
    
    fixer = RemoteEveningDataFixer()
    report = fixer.run_comprehensive_fix()
    
    print(f"\n📄 Detailed report saved: /root/test/remote_evening_fix_report.json")

if __name__ == "__main__":
    main()
