#!/usr/bin/env python3
"""
Evening Temporal Guard - Data Quality & Outcomes Validation
===========================================================

Comprehensive evening validation to detect and prevent temporal integrity issues
in trading outcomes, data consistency, and prediction quality.

Features:
- Outcomes data validation and cleanup
- Data leakage detection and prevention
- Consistency checks between predictions and features
- Duplicate prediction detection
- Null data validation
- Evening-specific temporal constraints

Usage:
    python3 evening_temporal_guard.py
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class EveningTemporalGuard:
    """Evening-specific temporal integrity and data quality validation"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.validation_time = datetime.now()
        self.issues_found = []
        self.warnings = []
        
    def run_comprehensive_evening_guard(self) -> bool:
        """Run complete evening temporal and data quality validation"""
        
        print("🌆 EVENING ROUTINE TEMPORAL INTEGRITY GUARD")
        print("=" * 55)
        print(f"🕐 Validation time: {self.validation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_checks_passed = True
        
        # 1. Trading Outcomes Validation
        print("\n🔍 VALIDATING TRADING OUTCOMES...")
        outcomes_valid = self._validate_trading_outcomes()
        if not outcomes_valid:
            all_checks_passed = False
        
        # 2. Data Consistency Checks
        print("\n🔍 CHECKING DATA CONSISTENCY...")
        consistency_valid = self._check_data_consistency()
        if not consistency_valid:
            all_checks_passed = False
        
        # 3. Data Leakage Detection
        print("\n🔍 DETECTING DATA LEAKAGE...")
        leakage_valid = self._detect_data_leakage()
        if not leakage_valid:
            all_checks_passed = False
        
        # 4. Duplicate Prediction Detection
        print("\n🔍 CHECKING FOR DUPLICATE PREDICTIONS...")
        duplicates_valid = self._check_duplicate_predictions()
        if not duplicates_valid:
            all_checks_passed = False
        
        # 5. Database Integrity Validation
        print("\n🔍 VALIDATING DATABASE INTEGRITY...")
        db_valid = self._validate_database_integrity()
        if not db_valid:
            all_checks_passed = False
        
        # Generate report
        self._generate_evening_report(all_checks_passed)
        
        # Print summary
        print("\n" + "=" * 55)
        if all_checks_passed:
            print("🏆 EVENING GUARD PASSED: SAFE FOR OUTCOMES PROCESSING")
            print("✅ All temporal integrity checks passed")
            print("✅ Data quality validated")
            print("✅ No data leakage detected")
            print("✅ Database consistency confirmed")
        else:
            print("🚨 EVENING GUARD FAILED: ISSUES DETECTED")
            print("❌ Critical data quality issues found")
            print("🔧 Review evening_guard_report.json for details")
            print("💡 Run evening temporal fixes before proceeding")
        
        print(f"\n📄 Detailed report: evening_guard_report.json")
        print("=" * 55)
        
        return all_checks_passed
    
    def _validate_trading_outcomes(self) -> bool:
        """Validate trading outcomes data quality"""
        
        outcomes_issues = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if outcomes table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='outcomes'
                """)
                if not cursor.fetchone():
                    outcomes_issues.append("Outcomes table does not exist")
                    print("❌ Trading Outcomes: Table missing")
                    return False
                
                # Check for outcomes data
                cursor.execute("SELECT COUNT(*) FROM outcomes")
                outcomes_count = cursor.fetchone()[0]
                
                if outcomes_count == 0:
                    print("⚠️ Trading Outcomes: No outcomes data available")
                    self.warnings.append("No outcomes data available")
                else:
                    print(f"✅ Trading Outcomes: {outcomes_count} outcomes found")
                
                # Check for NULL actual returns
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes 
                    WHERE actual_return IS NULL OR actual_return = 0
                """)
                null_returns = cursor.fetchone()[0]
                
                if null_returns > 0:
                    outcomes_issues.append(f"{null_returns} outcomes with null/zero actual returns")
                    print(f"  ⚠️ Found {null_returns} outcomes with null/zero returns")
                
                # Check for temporal consistency in outcomes
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes o
                    JOIN predictions p ON o.prediction_id = p.prediction_id
                    WHERE o.evaluation_timestamp < p.prediction_timestamp
                """)
                temporal_violations = cursor.fetchone()[0]
                
                if temporal_violations > 0:
                    outcomes_issues.append(f"{temporal_violations} outcomes evaluated before prediction")
                    print(f"  ❌ Found {temporal_violations} temporal violations in outcomes")
                
                # Check for missing outcome_ids
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes 
                    WHERE outcome_id IS NULL OR outcome_id = ''
                """)
                missing_ids = cursor.fetchone()[0]
                
                if missing_ids > 0:
                    outcomes_issues.append(f"{missing_ids} outcomes with missing IDs")
                    print(f"  ⚠️ Found {missing_ids} outcomes with missing IDs")
                
        except Exception as e:
            outcomes_issues.append(f"Error validating outcomes: {e}")
            print(f"❌ Trading Outcomes: Validation error - {e}")
        
        if outcomes_issues:
            self.issues_found.extend([f"OUTCOMES: {issue}" for issue in outcomes_issues])
            return False
        
        return True
    
    def _check_data_consistency(self) -> bool:
        """Check consistency between predictions and features"""
        
        consistency_issues = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check predictions vs features mismatch
                cursor.execute("SELECT COUNT(*) FROM predictions")
                predictions_count = cursor.fetchone()[0]
                
                # Try to count features (handle potential table naming issues)
                feature_tables = ['sentiment_features', 'enhanced_features', 'features', 'prediction_features', 'technical_features']
                features_count = 0
                feature_table_found = None
                
                for table_name in feature_tables:
                    try:
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                        if cursor.fetchone():
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            features_count = cursor.fetchone()[0]
                            feature_table_found = table_name
                            break
                    except:
                        continue
                
                if feature_table_found:
                    if predictions_count != features_count:
                        consistency_issues.append(f"Mismatch: {predictions_count} predictions vs {features_count} features")
                        print(f"  ❌ Mismatch: {predictions_count} predictions vs {features_count} features")
                    else:
                        print(f"✅ Data Consistency: {predictions_count} predictions match {features_count} features")
                else:
                    consistency_issues.append("No feature table found")
                    print("  ❌ No feature table found")
                
                # Check for orphaned predictions (predictions without features)
                if feature_table_found:
                    # Features tables use symbol+timestamp instead of prediction_id
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM predictions p
                        LEFT JOIN {feature_table_found} f ON p.symbol = f.symbol 
                            AND date(p.prediction_timestamp) = date(f.timestamp)
                        WHERE f.symbol IS NULL
                    """)
                    orphaned = cursor.fetchone()[0]
                    
                    if orphaned > 0:
                        consistency_issues.append(f"{orphaned} predictions without features")
                        print(f"  ⚠️ Found {orphaned} predictions without features")
                
                # Check for predictions without symbols
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions 
                    WHERE symbol IS NULL OR symbol = ''
                """)
                missing_symbols = cursor.fetchone()[0]
                
                if missing_symbols > 0:
                    consistency_issues.append(f"{missing_symbols} predictions without symbols")
                    print(f"  ⚠️ Found {missing_symbols} predictions without symbols")
                
        except Exception as e:
            consistency_issues.append(f"Error checking consistency: {e}")
            print(f"❌ Data Consistency: Check error - {e}")
        
        if consistency_issues:
            self.issues_found.extend([f"CONSISTENCY: {issue}" for issue in consistency_issues])
            return False
        
        return True
    
    def _detect_data_leakage(self) -> bool:
        """Detect potential data leakage issues"""
        
        leakage_issues = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check for future predictions (predictions made for past dates)
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions 
                    WHERE prediction_timestamp > datetime('now')
                """)
                future_predictions = cursor.fetchone()[0]
                
                if future_predictions > 0:
                    leakage_issues.append(f"{future_predictions} predictions with future timestamps")
                    print(f"  ❌ Found {future_predictions} predictions with future timestamps")
                
                # Check for predictions using future features (simplified check)
                # Look for predictions where feature calculation might use future data
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions 
                    WHERE date(prediction_timestamp) < date('now', '-1 day')
                    AND prediction_timestamp > date(prediction_timestamp, '+1 day')
                """)
                potential_leakage = cursor.fetchone()[0]
                
                if potential_leakage > 0:
                    leakage_issues.append(f"{potential_leakage} potential feature leakage instances")
                    print(f"  ⚠️ Found {potential_leakage} potential feature leakage instances")
                
                # Check for analysis_timestamp column existence and validate
                try:
                    cursor.execute("PRAGMA table_info(predictions)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if 'analysis_timestamp' in columns:
                        # Check for predictions analyzed before they were made
                        cursor.execute("""
                            SELECT COUNT(*) FROM predictions 
                            WHERE analysis_timestamp < prediction_timestamp
                        """)
                        early_analysis = cursor.fetchone()[0]
                        
                        if early_analysis > 0:
                            leakage_issues.append(f"{early_analysis} predictions analyzed before creation")
                            print(f"  ❌ Found {early_analysis} predictions analyzed before creation")
                    else:
                        print("  ℹ️ analysis_timestamp column not found (this is normal)")
                
                except Exception as col_e:
                    print(f"  ⚠️ Could not check analysis_timestamp: {col_e}")
                
        except Exception as e:
            leakage_issues.append(f"Error detecting leakage: {e}")
            print(f"❌ Data Leakage: Detection error - {e}")
        
        if leakage_issues:
            self.issues_found.extend([f"LEAKAGE: {issue}" for issue in leakage_issues])
            return False
        
        print("✅ Data Leakage: No leakage detected")
        return True
    
    def _check_duplicate_predictions(self) -> bool:
        """Check for duplicate predictions"""
        
        duplicate_issues = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check for duplicate predictions by symbol and date
                cursor.execute("""
                    SELECT symbol, date(prediction_timestamp) as pred_date, COUNT(*) as count
                    FROM predictions 
                    GROUP BY symbol, date(prediction_timestamp)
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                
                if duplicates:
                    total_duplicate_days = len(duplicates)
                    duplicate_issues.append(f"Found {total_duplicate_days} days with duplicate predictions")
                    print(f"  ❌ Found {total_duplicate_days} days with duplicate predictions")
                    
                    # Show details for first few duplicates
                    for symbol, date, count in duplicates[:3]:
                        print(f"    • {symbol} on {date}: {count} predictions")
                    
                    if len(duplicates) > 3:
                        print(f"    • ... and {len(duplicates) - 3} more")
                else:
                    print("✅ Duplicate Predictions: No duplicates found")
                
                # Check for duplicate prediction_ids
                cursor.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT prediction_id, COUNT(*) as count 
                        FROM predictions 
                        GROUP BY prediction_id 
                        HAVING COUNT(*) > 1
                    )
                """)
                duplicate_ids = cursor.fetchone()[0]
                
                if duplicate_ids > 0:
                    duplicate_issues.append(f"{duplicate_ids} duplicate prediction IDs")
                    print(f"  ❌ Found {duplicate_ids} duplicate prediction IDs")
                
        except Exception as e:
            duplicate_issues.append(f"Error checking duplicates: {e}")
            print(f"❌ Duplicate Check: Error - {e}")
        
        if duplicate_issues:
            self.issues_found.extend([f"DUPLICATES: {issue}" for issue in duplicate_issues])
            return False
        
        return True
    
    def _validate_database_integrity(self) -> bool:
        """Validate overall database integrity"""
        
        integrity_issues = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check database file integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result != 'ok':
                    integrity_issues.append(f"Database integrity check failed: {integrity_result}")
                    print(f"❌ Database Integrity: {integrity_result}")
                else:
                    print("✅ Database Integrity: Database file is intact")
                
                # Check for foreign key violations
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if fk_violations:
                    integrity_issues.append(f"{len(fk_violations)} foreign key violations")
                    print(f"  ❌ Found {len(fk_violations)} foreign key violations")
                
                # Check table schemas
                required_tables = ['predictions']
                for table in required_tables:
                    cursor.execute(f"""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='{table}'
                    """)
                    if not cursor.fetchone():
                        integrity_issues.append(f"Required table {table} missing")
                        print(f"  ❌ Required table {table} missing")
                
        except Exception as e:
            integrity_issues.append(f"Error validating integrity: {e}")
            print(f"❌ Database Integrity: Validation error - {e}")
        
        if integrity_issues:
            self.issues_found.extend([f"INTEGRITY: {issue}" for issue in integrity_issues])
            return False
        
        return True
    
    def _generate_evening_report(self, guard_passed: bool):
        """Generate detailed evening validation report"""
        
        report = {
            "validation_time": self.validation_time.isoformat(),
            "guard_passed": guard_passed,
            "validation_type": "evening_temporal_guard",
            "issues_found": self.issues_found,
            "warnings": self.warnings,
            "recommendations": self._generate_recommendations(),
            "summary": {
                "total_issues": len(self.issues_found),
                "total_warnings": len(self.warnings),
                "critical_failures": len([issue for issue in self.issues_found if "❌" in str(issue)]),
                "validation_categories": {
                    "outcomes_validation": "PASSED" if not any("OUTCOMES" in issue for issue in self.issues_found) else "FAILED",
                    "data_consistency": "PASSED" if not any("CONSISTENCY" in issue for issue in self.issues_found) else "FAILED", 
                    "leakage_detection": "PASSED" if not any("LEAKAGE" in issue for issue in self.issues_found) else "FAILED",
                    "duplicate_check": "PASSED" if not any("DUPLICATES" in issue for issue in self.issues_found) else "FAILED",
                    "database_integrity": "PASSED" if not any("INTEGRITY" in issue for issue in self.issues_found) else "FAILED"
                }
            }
        }
        
        try:
            with open("evening_guard_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Could not save evening report: {e}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on issues found"""
        
        recommendations = []
        
        if any("duplicate" in issue.lower() for issue in self.issues_found):
            recommendations.extend([
                "Implement idempotent operations with date-based deduplication",
                "Add unique constraints on (symbol, date) combinations", 
                "Use transaction rollback on duplicate detection"
            ])
        
        if any("null" in issue.lower() for issue in self.issues_found):
            recommendations.extend([
                "Add NOT NULL constraints on critical columns",
                "Implement data validation before insertion",
                "Set up automated data quality checks"
            ])
        
        if any("leakage" in issue.lower() for issue in self.issues_found):
            recommendations.extend([
                "Review feature calculation timestamps",
                "Implement strict temporal validation in data pipeline",
                "Add analysis_timestamp validation triggers"
            ])
        
        if any("consistency" in issue.lower() for issue in self.issues_found):
            recommendations.extend([
                "Implement transactional prediction+feature insertion",
                "Add referential integrity constraints",
                "Set up automated consistency monitoring"
            ])
        
        if not recommendations:
            recommendations.append("Continue regular evening validation monitoring")
        
        return recommendations

def main():
    """Main function for evening temporal guard"""
    
    guard = EveningTemporalGuard()
    success = guard.run_comprehensive_evening_guard()
    
    # Exit with appropriate code
    if success:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
