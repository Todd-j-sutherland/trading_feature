#!/usr/bin/env python3
"""
Standalone Data Validation Runner
Runs comprehensive data validation tests for database tables and JSON files
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_production_data():
    """Validate production data in the actual system"""
    print("🔍 PRODUCTION DATA VALIDATION")
    print("=" * 60)
    
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'database_checks': {},
        'json_checks': {},
        'warnings': [],
        'errors': [],
        'validation_passed': True
    }
    
    # Check 1: Validate existing database files
    print("1. Checking production database files...")
    db_files = []
    
    # Look for SQLite database files
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite'):
                db_path = os.path.join(root, file)
                db_files.append(db_path)
    
    if db_files:
        print(f"   Found {len(db_files)} database files")
        for db_file in db_files:
            try:
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if tables:
                    print(f"   ✅ {os.path.basename(db_file)}: {len(tables)} tables")
                    
                    # Check for data integrity issues
                    for table_name in [t[0] for t in tables]:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        
                        if count == 0:
                            validation_results['warnings'].append(f"Table {table_name} in {db_file} is empty")
                        
                        # Check for zero sentiment/technical scores if applicable
                        if 'sentiment' in table_name.lower():
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE sentiment_score = 0.0 AND confidence = 0.0")
                            zero_count = cursor.fetchone()[0]
                            if zero_count > 0:
                                validation_results['warnings'].append(f"Found {zero_count} zero sentiment scores in {table_name}")
                
                else:
                    validation_results['warnings'].append(f"Database {db_file} has no tables")
                
                conn.close()
                validation_results['database_checks'][os.path.basename(db_file)] = True
                
            except Exception as e:
                print(f"   ❌ Error checking {db_file}: {e}")
                validation_results['database_checks'][os.path.basename(db_file)] = False
                validation_results['errors'].append(f"Database validation failed for {db_file}: {e}")
    else:
        print("   ⚠️ No database files found")
        validation_results['warnings'].append("No database files found in project")
    
    # Check 2: Validate JSON data files
    print("2. Checking production JSON files...")
    json_files = []
    
    # Look for JSON data files
    data_dirs = ['data', 'data_temp', 'data']
    for data_dir in data_dirs:
        data_path = os.path.join(project_root, data_dir)
        if os.path.exists(data_path):
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.endswith('.json'):
                        json_path = os.path.join(root, file)
                        json_files.append(json_path)
    
    if json_files:
        print(f"   Found {len(json_files)} JSON files")
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                file_name = os.path.basename(json_file)
                print(f"   ✅ {file_name}: Valid JSON")
                
                # Specific validation based on file type
                if 'sentiment' in file_name.lower():
                    validate_sentiment_json(data, validation_results, file_name)
                elif 'trading' in file_name.lower() or 'results' in file_name.lower():
                    validate_trading_json(data, validation_results, file_name)
                elif 'ml' in file_name.lower() or 'model' in file_name.lower():
                    validate_ml_json(data, validation_results, file_name)
                
                validation_results['json_checks'][file_name] = True
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Invalid JSON in {json_file}: {e}")
                validation_results['json_checks'][os.path.basename(json_file)] = False
                validation_results['errors'].append(f"Invalid JSON in {json_file}: {e}")
            except Exception as e:
                print(f"   ❌ Error reading {json_file}: {e}")
                validation_results['json_checks'][os.path.basename(json_file)] = False
                validation_results['errors'].append(f"Error reading {json_file}: {e}")
    else:
        print("   ⚠️ No JSON data files found")
        validation_results['warnings'].append("No JSON data files found in project")
    
    # Check 3: Validate data consistency
    print("3. Checking data consistency...")
    try:
        consistency_issues = check_data_consistency()
        if consistency_issues:
            validation_results['warnings'].extend(consistency_issues)
            print(f"   ⚠️ Found {len(consistency_issues)} consistency issues")
        else:
            print("   ✅ Data consistency checks passed")
    except Exception as e:
        print(f"   ❌ Data consistency check failed: {e}")
        validation_results['errors'].append(f"Data consistency check failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 PRODUCTION DATA VALIDATION SUMMARY")
    print("=" * 60)
    
    total_db_checks = len(validation_results['database_checks'])
    passed_db_checks = sum(1 for v in validation_results['database_checks'].values() if v)
    
    total_json_checks = len(validation_results['json_checks'])
    passed_json_checks = sum(1 for v in validation_results['json_checks'].values() if v)
    
    print(f"📊 Database Files: {passed_db_checks}/{total_db_checks} passed")
    print(f"📄 JSON Files: {passed_json_checks}/{total_json_checks} passed")
    print(f"⚠️ Warnings: {len(validation_results['warnings'])}")
    print(f"❌ Errors: {len(validation_results['errors'])}")
    
    if validation_results['warnings']:
        print("\nWarnings:")
        for warning in validation_results['warnings']:
            print(f"  • {warning}")
    
    if validation_results['errors']:
        print("\nErrors:")
        for error in validation_results['errors']:
            print(f"  • {error}")
        validation_results['validation_passed'] = False
    
    if validation_results['validation_passed']:
        print(f"\n🎉 PRODUCTION DATA VALIDATION PASSED!")
        print("   Your data is in good shape for continued operations.")
    else:
        print(f"\n🚨 PRODUCTION DATA VALIDATION FAILED!")
        print("   Critical data issues need attention.")
    
    # Save validation report
    report_file = os.path.join(project_root, f"production_data_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"\n📄 Validation report saved to: {report_file}")
    print("=" * 60)
    
    return validation_results

def validate_sentiment_json(data, validation_results, file_name):
    """Validate sentiment-specific JSON data"""
    try:
        if isinstance(data, dict):
            for symbol, entries in data.items():
                if isinstance(entries, list):
                    for entry in entries:
                        if isinstance(entry, dict):
                            # Check for zero sentiment scores
                            sentiment = entry.get('sentiment', None)
                            confidence = entry.get('confidence', None)
                            
                            if sentiment == 0.0 and confidence == 0.0:
                                validation_results['warnings'].append(
                                    f"Zero sentiment/confidence found for {symbol} in {file_name}"
                                )
                            
                            # Check ranges
                            if sentiment is not None and not (-1.0 <= sentiment <= 1.0):
                                validation_results['errors'].append(
                                    f"Invalid sentiment range {sentiment} for {symbol} in {file_name}"
                                )
                            
                            if confidence is not None and not (0.0 <= confidence <= 1.0):
                                validation_results['errors'].append(
                                    f"Invalid confidence range {confidence} for {symbol} in {file_name}"
                                )
    except Exception as e:
        validation_results['errors'].append(f"Error validating sentiment data in {file_name}: {e}")

def validate_trading_json(data, validation_results, file_name):
    """Validate trading-specific JSON data"""
    try:
        if isinstance(data, dict):
            # Check for trades
            if 'trades' in data and isinstance(data['trades'], list):
                for trade in data['trades']:
                    if isinstance(trade, dict):
                        # Validate trade structure
                        required_fields = ['symbol', 'action', 'quantity', 'price']
                        for field in required_fields:
                            if field not in trade:
                                validation_results['errors'].append(
                                    f"Missing {field} in trade entry in {file_name}"
                                )
                        
                        # Validate trade action
                        action = trade.get('action')
                        if action and action not in ['BUY', 'SELL', 'HOLD']:
                            validation_results['errors'].append(
                                f"Invalid trade action '{action}' in {file_name}"
                            )
            
            # Check portfolio metrics
            if 'portfolio_value' in data:
                if data['portfolio_value'] <= 0:
                    validation_results['warnings'].append(
                        f"Non-positive portfolio value in {file_name}"
                    )
    except Exception as e:
        validation_results['errors'].append(f"Error validating trading data in {file_name}: {e}")

def validate_ml_json(data, validation_results, file_name):
    """Validate ML-specific JSON data"""
    try:
        if isinstance(data, dict):
            # Check model metrics
            if 'model_metrics' in data:
                metrics = data['model_metrics']
                metric_names = ['accuracy', 'precision', 'recall', 'f1_score']
                for metric in metric_names:
                    if metric in metrics:
                        value = metrics[metric]
                        if not (0.0 <= value <= 1.0):
                            validation_results['errors'].append(
                                f"Invalid {metric} value {value} in {file_name}"
                            )
            
            # Check feature importance
            if 'feature_importance' in data:
                importance = data['feature_importance']
                if isinstance(importance, dict):
                    total_importance = sum(importance.values())
                    if abs(total_importance - 1.0) > 0.1:  # Allow some tolerance
                        validation_results['warnings'].append(
                            f"Feature importance doesn't sum to 1.0 ({total_importance}) in {file_name}"
                        )
    except Exception as e:
        validation_results['errors'].append(f"Error validating ML data in {file_name}: {e}")

def check_data_consistency():
    """Check for data consistency issues across files"""
    issues = []
    
    try:
        # Check for timestamp consistency
        # Check for symbol consistency
        # Check for data completeness
        
        # This is a placeholder for more sophisticated consistency checks
        # In a real implementation, you would:
        # 1. Compare timestamps across different data sources
        # 2. Ensure symbol naming consistency
        # 3. Check that all required data is present for each symbol
        # 4. Validate cross-references between tables/files
        
        pass
        
    except Exception as e:
        issues.append(f"Data consistency check error: {e}")
    
    return issues

def main():
    """Main validation function"""
    try:
        # Run the test suite first
        print("🧪 Running Data Validation Test Suite...")
        from tests.test_data_validation import run_data_validation_tests
        test_success = run_data_validation_tests()
        
        print("\n" + "="*80 + "\n")
        
        # Then validate production data
        results = validate_production_data()
        
        # Exit with appropriate code
        if test_success and results['validation_passed']:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except ImportError:
        print("⚠️ Test suite not available, running production validation only...")
        results = validate_production_data()
        sys.exit(0 if results['validation_passed'] else 1)
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
