#!/usr/bin/env python3
"""
Recent Predictions Deep Dive Tool
Step 3.1-3.3: Focus on August 25-27 data analysis
"""

import sqlite3
import json
from datetime import datetime

def analyze_recent_data():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    analysis_results = {
        'timestamp': datetime.now().isoformat(),
        'recent_data_quality': {},
        'symbol_specific_issues': {},
        'model_performance_issues': {},
        'summary': {}
    }
    
    print("="*60)
    print("RECENT PREDICTIONS DEEP DIVE (AUG 25-27)")
    print("="*60)
    
    # Step 3.1: Recent Data Quality Assessment
    print("\n3.1 RECENT DATA QUALITY ASSESSMENT:")
    print("-" * 30)
    
    # Get all recent predictions
    cursor.execute("""
    SELECT DATE(prediction_timestamp) as pred_date, COUNT(*) as count
    FROM predictions
    WHERE DATE(prediction_timestamp) >= '2025-08-25'
    GROUP BY DATE(prediction_timestamp)
    ORDER BY pred_date
    """)
    
    daily_counts = cursor.fetchall()
    print("Daily prediction counts:")
    for date, count in daily_counts:
        print(f"  {date}: {count} predictions")
    
    # Check recent data completeness
    cursor.execute("""
    SELECT p.symbol, COUNT(p.prediction_id) as predictions, COUNT(o.outcome_id) as outcomes
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
    GROUP BY p.symbol
    ORDER BY predictions DESC
    """)
    
    symbol_coverage = cursor.fetchall()
    print(f"\nSymbol coverage (predictions vs outcomes):")
    for symbol, preds, outcomes in symbol_coverage:
        coverage_pct = (outcomes / preds * 100) if preds > 0 else 0
        print(f"  {symbol}: {preds} predictions, {outcomes} outcomes ({coverage_pct:.1f}%)")
    
    # Step 3.2: Symbol-Specific Analysis
    print("\n3.2 SYMBOL-SPECIFIC ANALYSIS:")
    print("-" * 30)
    
    # ANZ.AX deep dive (0% success rate)
    print("ANZ.AX Analysis:")
    cursor.execute("""
    SELECT p.prediction_timestamp, p.predicted_action, p.action_confidence,
           p.entry_price, o.actual_return, o.exit_price
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.symbol = 'ANZ.AX'
      AND DATE(p.prediction_timestamp) >= '2025-08-25'
    ORDER BY p.prediction_timestamp
    """)
    
    anz_data = cursor.fetchall()
    print(f"  Total ANZ predictions: {len(anz_data)}")
    
    anz_buys = [row for row in anz_data if row[1] == 'BUY']
    anz_sells = [row for row in anz_data if row[1] == 'SELL']
    anz_holds = [row for row in anz_data if row[1] == 'HOLD']
    
    print(f"  BUY signals: {len(anz_buys)}")
    print(f"  SELL signals: {len(anz_sells)}")
    print(f"  HOLD signals: {len(anz_holds)}")
    
    # Check if returns are calculated correctly for ANZ
    if anz_buys:
        print("  Sample BUY signals:")
        for i, buy in enumerate(anz_buys[:3], 1):
            timestamp, action, conf, entry, actual_ret, exit_price = buy
            if entry and exit_price and actual_ret is not None:
                expected_ret = (exit_price - entry) / entry
                print(f"    {i}. Entry: ${entry:.2f}, Exit: ${exit_price:.2f}")
                print(f"       Expected return: {expected_ret*100:.2f}%, Actual: {actual_ret*100:.2f}%")
    
    # MQG.AX Analysis (extreme losses)
    print("\nMQG.AX Analysis:")
    cursor.execute("""
    SELECT p.prediction_timestamp, p.predicted_action, p.action_confidence,
           p.entry_price, o.actual_return, o.exit_price
    FROM predictions p
    LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.symbol = 'MQG.AX'
      AND DATE(p.prediction_timestamp) >= '2025-08-25'
      AND o.actual_return IS NOT NULL
    ORDER BY o.actual_return ASC
    LIMIT 5
    """)
    
    mqg_data = cursor.fetchall()
    print(f"  MQG records with outcomes: {len(mqg_data)}")
    for i, record in enumerate(mqg_data, 1):
        timestamp, action, conf, entry, actual_ret, exit_price = record
        if entry and exit_price:
            expected_ret = (exit_price - entry) / entry
            print(f"    {i}. {action} - Entry: ${entry:.2f}, Exit: ${exit_price:.2f}")
            print(f"       Expected: {expected_ret*100:.2f}%, Stored: {actual_ret*100:.2f}%")
    
    # Step 3.3: Model Performance Validation
    print("\n3.3 MODEL PERFORMANCE VALIDATION:")
    print("-" * 30)
    
    # Check model versions used recently
    cursor.execute("""
    SELECT model_version, COUNT(*) as count
    FROM predictions
    WHERE DATE(prediction_timestamp) >= '2025-08-25'
      AND model_version IS NOT NULL
    GROUP BY model_version
    ORDER BY count DESC
    """)
    
    model_versions = cursor.fetchall()
    print("Model versions used:")
    for version, count in model_versions:
        print(f"  {version}: {count} predictions")
    
    # Check feature vector integrity
    cursor.execute("""
    SELECT symbol, COUNT(*) as total,
           SUM(CASE WHEN feature_vector IS NULL THEN 1 ELSE 0 END) as null_features,
           SUM(CASE WHEN LENGTH(feature_vector) < 10 THEN 1 ELSE 0 END) as short_features
    FROM predictions
    WHERE DATE(prediction_timestamp) >= '2025-08-25'
    GROUP BY symbol
    ORDER BY total DESC
    """)
    
    feature_integrity = cursor.fetchall()
    print("\nFeature vector integrity:")
    for symbol, total, null_feat, short_feat in feature_integrity[:10]:
        null_pct = (null_feat / total * 100) if total > 0 else 0
        short_pct = (short_feat / total * 100) if total > 0 else 0
        print(f"  {symbol}: {null_pct:.1f}% null, {short_pct:.1f}% short vectors")
    
    # Check prediction timestamp accuracy
    cursor.execute("""
    SELECT prediction_timestamp, COUNT(*) as count
    FROM predictions
    WHERE DATE(prediction_timestamp) >= '2025-08-25'
    GROUP BY prediction_timestamp
    ORDER BY count DESC
    LIMIT 10
    """)
    
    timestamp_freq = cursor.fetchall()
    print("\nMost frequent prediction timestamps:")
    for timestamp, count in timestamp_freq:
        print(f"  {timestamp}: {count} predictions")
    
    # Identify the return calculation error pattern
    print("\n" + "="*60)
    print("RETURN CALCULATION ERROR ANALYSIS:")
    print("="*60)
    
    cursor.execute("""
    SELECT p.symbol, p.entry_price, o.exit_price, o.actual_return,
           (o.exit_price - p.entry_price) / p.entry_price as correct_return
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
      AND p.entry_price > 0
      AND o.exit_price > 0
      AND ABS(o.actual_return) > 1.0  -- Focus on extreme returns
    LIMIT 10
    """)
    
    error_samples = cursor.fetchall()
    print("Sample calculation errors:")
    for symbol, entry, exit, stored_return, correct_return in error_samples:
        error_factor = stored_return / correct_return if correct_return != 0 else float('inf')
        print(f"  {symbol}: Entry ${entry:.2f}, Exit ${exit:.2f}")
        print(f"    Stored: {stored_return*100:.2f}%, Correct: {correct_return*100:.2f}%")
        print(f"    Error factor: {error_factor:.1f}x")
    
    # Summary
    analysis_results['summary'] = {
        'total_recent_predictions': sum(count for _, count in daily_counts),
        'symbols_analyzed': len(symbol_coverage),
        'model_versions': len(model_versions),
        'return_calculation_errors': len(error_samples)
    }
    
    conn.close()
    return analysis_results

if __name__ == "__main__":
    results = analyze_recent_data()
    
    # Save results
    with open('recent_data_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nRecent data analysis saved to recent_data_analysis.json")
