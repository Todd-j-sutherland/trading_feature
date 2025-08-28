#!/usr/bin/env python3
"""
Database Integrity Audit Tool
Step 1.1-1.4: Complete database integrity analysis
"""

import sqlite3
import json
from datetime import datetime

def audit_database_integrity():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    audit_results = {
        'timestamp': datetime.now().isoformat(),
        'schema_issues': [],
        'data_type_issues': [],
        'corrupted_records': [],
        'range_violations': [],
        'summary': {}
    }
    
    print("="*60)
    print("DATABASE INTEGRITY AUDIT")
    print("="*60)
    
    # Step 1.1: Schema Validation
    print("\n1.1 SCHEMA VALIDATION:")
    print("-" * 30)
    
    # Check predictions table structure
    cursor.execute("PRAGMA table_info(predictions)")
    pred_schema = cursor.fetchall()
    print("PREDICTIONS table structure:")
    for col in pred_schema:
        print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
    
    # Check outcomes table structure
    cursor.execute("PRAGMA table_info(outcomes)")
    out_schema = cursor.fetchall()
    print("\nOUTCOMES table structure:")
    for col in out_schema:
        print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
    
    # Step 1.2: Data Type Consistency Check
    print("\n1.2 DATA TYPE CONSISTENCY:")
    print("-" * 30)
    
    # Check for string values in confidence field (should be REAL)
    cursor.execute("""
    SELECT prediction_id, symbol, action_confidence, 
           CASE 
               WHEN typeof(action_confidence) != 'real' THEN typeof(action_confidence)
               ELSE NULL 
           END as wrong_type
    FROM predictions 
    WHERE typeof(action_confidence) != 'real'
    """)
    
    type_issues = cursor.fetchall()
    print(f"Action confidence type issues: {len(type_issues)}")
    for issue in type_issues[:5]:  # Show first 5
        print(f"  {issue[1]}: {issue[2]} (type: {issue[3]})")
        audit_results['data_type_issues'].append({
            'prediction_id': issue[0],
            'symbol': issue[1],
            'value': str(issue[2]),
            'wrong_type': issue[3]
        })
    
    # Step 1.3: Corrupted Record Detection
    print("\n1.3 CORRUPTED RECORD DETECTION:")
    print("-" * 30)
    
    # Find confidence values with commas (corrupted)
    cursor.execute("""
    SELECT prediction_id, symbol, action_confidence
    FROM predictions 
    WHERE CAST(action_confidence AS TEXT) LIKE '%,%'
    """)
    
    corrupted_conf = cursor.fetchall()
    print(f"Corrupted confidence records: {len(corrupted_conf)}")
    for record in corrupted_conf:
        print(f"  {record[1]}: {record[2]}")
        audit_results['corrupted_records'].append({
            'type': 'confidence_corruption',
            'prediction_id': record[0],
            'symbol': record[1],
            'value': str(record[2])
        })
    
    # Find impossible return values
    cursor.execute("""
    SELECT o.prediction_id, p.symbol, o.actual_return
    FROM outcomes o
    JOIN predictions p ON o.prediction_id = p.prediction_id
    WHERE ABS(o.actual_return) > 10.0  -- More than 1000% return
    """)
    
    impossible_returns = cursor.fetchall()
    print(f"Impossible return values: {len(impossible_returns)}")
    for record in impossible_returns:
        print(f"  {record[1]}: {record[2]*100:.1f}% return")
        audit_results['corrupted_records'].append({
            'type': 'impossible_return',
            'prediction_id': record[0],
            'symbol': record[1],
            'value': record[2]
        })
    
    # Check for duplicate prediction IDs
    cursor.execute("""
    SELECT prediction_id, COUNT(*) as count
    FROM predictions
    GROUP BY prediction_id
    HAVING count > 1
    """)
    
    duplicates = cursor.fetchall()
    print(f"Duplicate prediction IDs: {len(duplicates)}")
    
    # Step 1.4: Data Range Validation
    print("\n1.4 DATA RANGE VALIDATION:")
    print("-" * 30)
    
    # Check confidence ranges (should be 0.0-1.0)
    cursor.execute("""
    SELECT prediction_id, symbol, action_confidence
    FROM predictions 
    WHERE CAST(action_confidence AS REAL) < 0.0 
       OR CAST(action_confidence AS REAL) > 1.0
    """)
    
    conf_range_issues = cursor.fetchall()
    print(f"Confidence range violations: {len(conf_range_issues)}")
    for issue in conf_range_issues:
        print(f"  {issue[1]}: {issue[2]}")
        audit_results['range_violations'].append({
            'type': 'confidence_range',
            'prediction_id': issue[0],
            'symbol': issue[1],
            'value': str(issue[2])
        })
    
    # Check for zero or negative prices
    cursor.execute("""
    SELECT prediction_id, symbol, entry_price
    FROM predictions 
    WHERE entry_price <= 0
    """)
    
    price_issues = cursor.fetchall()
    print(f"Invalid entry prices: {len(price_issues)}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("AUDIT SUMMARY:")
    print("="*60)
    
    total_predictions = cursor.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    total_outcomes = cursor.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
    
    audit_results['summary'] = {
        'total_predictions': total_predictions,
        'total_outcomes': total_outcomes,
        'data_type_issues': len(type_issues),
        'corrupted_records': len(corrupted_conf) + len(impossible_returns),
        'range_violations': len(conf_range_issues) + len(price_issues)
    }
    
    print(f"Total predictions: {total_predictions}")
    print(f"Total outcomes: {total_outcomes}")
    print(f"Data type issues: {len(type_issues)}")
    print(f"Corrupted records: {len(corrupted_conf) + len(impossible_returns)}")
    print(f"Range violations: {len(conf_range_issues) + len(price_issues)}")
    
    coverage = (total_outcomes / total_predictions * 100) if total_predictions > 0 else 0
    print(f"Outcome coverage: {coverage:.1f}%")
    
    conn.close()
    return audit_results

if __name__ == "__main__":
    results = audit_database_integrity()
    
    # Save results to file
    with open('audit_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nAudit results saved to audit_results.json")
