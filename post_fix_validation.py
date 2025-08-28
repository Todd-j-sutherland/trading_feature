#!/usr/bin/env python3
"""
Post-Fix Validation and Performance Check
Verify all fixes and measure improvement
"""

import sqlite3
from datetime import datetime

def validate_fixes():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    print("="*60)
    print("POST-FIX VALIDATION & PERFORMANCE CHECK")
    print("="*60)
    
    # 1. Check data quality improvements
    print("\n1. DATA QUALITY VALIDATION:")
    print("-" * 30)
    
    # Check confidence ranges
    cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN action_confidence < 0 OR action_confidence > 1 THEN 1 ELSE 0 END) as invalid
    FROM predictions
    WHERE CAST(action_confidence AS TEXT) NOT LIKE '%,%'
    """)
    
    conf_check = cursor.fetchone()
    print(f"Confidence values: {conf_check[0]} total, {conf_check[1]} invalid")
    
    # Check for remaining corrupted data
    cursor.execute("""
    SELECT COUNT(*)
    FROM predictions
    WHERE CAST(action_confidence AS TEXT) LIKE '%,%'
    """)
    
    corrupted_remaining = cursor.fetchone()[0]
    print(f"Remaining corrupted confidence records: {corrupted_remaining}")
    
    # 2. Validate return calculations
    print("\n2. RETURN CALCULATION VALIDATION:")
    print("-" * 30)
    
    cursor.execute("""
    SELECT COUNT(*) as total_with_prices,
           AVG(ABS(o.actual_return - (o.exit_price - COALESCE(o.entry_price, p.entry_price)) / COALESCE(o.entry_price, p.entry_price))) as avg_error
    FROM outcomes o
    JOIN predictions p ON o.prediction_id = p.prediction_id
    WHERE o.exit_price > 0 
      AND COALESCE(o.entry_price, p.entry_price) > 0
      AND COALESCE(o.entry_price, p.entry_price) < 1000  -- Exclude obvious errors
    """)
    
    calc_validation = cursor.fetchone()
    print(f"Records with complete price data: {calc_validation[0]}")
    print(f"Average calculation error: {calc_validation[1]*100:.3f}%" if calc_validation[1] else "N/A")
    
    # 3. Check recent prediction performance
    print("\n3. RECENT PREDICTION PERFORMANCE:")
    print("-" * 30)
    
    cursor.execute("""
    SELECT p.predicted_action, COUNT(*) as total,
           AVG(CASE WHEN o.actual_return > 0 THEN 1 ELSE 0 END) as success_rate
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
      AND ABS(o.actual_return) < 0.5  -- Reasonable returns only
    GROUP BY p.predicted_action
    """)
    
    performance_by_action = cursor.fetchall()
    print("Performance by action type (with fixed calculations):")
    for action, total, success_rate in performance_by_action:
        print(f"  {action}: {total} predictions, {success_rate*100:.1f}% success rate")
    
    # 4. Symbol-specific performance after fixes
    print("\n4. SYMBOL-SPECIFIC PERFORMANCE (FIXED):")
    print("-" * 30)
    
    cursor.execute("""
    SELECT p.symbol, 
           COUNT(*) as total_predictions,
           SUM(CASE WHEN p.predicted_action = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
           SUM(CASE WHEN p.predicted_action = 'BUY' AND o.actual_return > 0 THEN 1 ELSE 0 END) as successful_buys
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
      AND ABS(o.actual_return) < 0.5  -- Exclude extreme outliers
    GROUP BY p.symbol
    ORDER BY total_predictions DESC
    """)
    
    symbol_performance = cursor.fetchall()
    print("Symbol performance with corrected data:")
    for symbol, total, buys, successful_buys in symbol_performance:
        buy_success_rate = (successful_buys / buys * 100) if buys > 0 else 0
        print(f"  {symbol}: {total} total, {buys} BUYs, {successful_buys} successful ({buy_success_rate:.1f}%)")
    
    # 5. Check data consistency
    print("\n5. DATA CONSISTENCY CHECK:")
    print("-" * 30)
    
    # Check prediction-outcome coverage
    cursor.execute("""
    SELECT COUNT(DISTINCT p.prediction_id) as predictions,
           COUNT(DISTINCT o.prediction_id) as outcomes
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
    """)
    
    coverage = cursor.fetchone()
    coverage_pct = (coverage[1] / coverage[0] * 100) if coverage[0] > 0 else 0
    print(f"Prediction-outcome coverage: {coverage[1]}/{coverage[0]} ({coverage_pct:.1f}%)")
    
    # Check for remaining data quality issues
    cursor.execute("""
    SELECT 
        SUM(CASE WHEN action_confidence IS NULL THEN 1 ELSE 0 END) as null_confidence,
        SUM(CASE WHEN entry_price IS NULL OR entry_price <= 0 THEN 1 ELSE 0 END) as null_prices,
        SUM(CASE WHEN predicted_action NOT IN ('BUY', 'SELL', 'HOLD') THEN 1 ELSE 0 END) as invalid_actions
    FROM predictions
    WHERE DATE(prediction_timestamp) >= '2025-08-25'
    """)
    
    quality_check = cursor.fetchone()
    print(f"Remaining quality issues:")
    print(f"  Null confidence: {quality_check[0]}")
    print(f"  Invalid prices: {quality_check[1]}")
    print(f"  Invalid actions: {quality_check[2]}")
    
    # 6. Overall system health score
    print("\n6. SYSTEM HEALTH SCORE:")
    print("-" * 30)
    
    total_issues = (corrupted_remaining + quality_check[0] + quality_check[1] + quality_check[2])
    total_recent_predictions = coverage[0]
    
    health_score = max(0, (1 - total_issues / total_recent_predictions) * 100) if total_recent_predictions > 0 else 0
    
    print(f"Total recent predictions: {total_recent_predictions}")
    print(f"Total remaining issues: {total_issues}")
    print(f"System Health Score: {health_score:.1f}%")
    
    if health_score >= 95:
        print("🟢 EXCELLENT: System is in great shape")
    elif health_score >= 85:
        print("🟡 GOOD: Minor issues remain")
    elif health_score >= 70:
        print("🟠 FAIR: Some issues need attention")
    else:
        print("🔴 POOR: Significant issues remain")
    
    conn.close()

if __name__ == "__main__":
    validate_fixes()
