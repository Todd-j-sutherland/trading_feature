#!/usr/bin/env python3
"""
Calculation Accuracy Verification Tool
Step 2.1-2.4: Verify all mathematical calculations
"""

import sqlite3
import json
from datetime import datetime

def verify_calculations():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    verification_results = {
        'timestamp': datetime.now().isoformat(),
        'return_calculation_errors': [],
        'confidence_calculation_errors': [],
        'price_data_errors': [],
        'magnitude_calculation_errors': [],
        'summary': {}
    }
    
    print("="*60)
    print("CALCULATION ACCURACY VERIFICATION")
    print("="*60)
    
    # Step 2.1: Return Calculation Audit
    print("\n2.1 RETURN CALCULATION AUDIT:")
    print("-" * 30)
    
    # Get records with entry/exit prices and actual returns
    cursor.execute("""
    SELECT o.prediction_id, p.symbol, p.entry_price, o.entry_price as outcome_entry,
           o.exit_price, o.actual_return
    FROM outcomes o
    JOIN predictions p ON o.prediction_id = p.prediction_id
    WHERE o.entry_price IS NOT NULL 
      AND o.exit_price IS NOT NULL
      AND o.actual_return IS NOT NULL
    ORDER BY ABS(o.actual_return) DESC
    LIMIT 20
    """)
    
    calculation_data = cursor.fetchall()
    print(f"Records with complete price data: {len(calculation_data)}")
    
    return_errors = 0
    for record in calculation_data:
        pred_id, symbol, pred_entry, out_entry, exit_price, actual_return = record
        
        # Use outcome entry price if available, otherwise prediction entry price
        entry_price = out_entry if out_entry and out_entry > 0 else pred_entry
        
        if entry_price and entry_price > 0 and exit_price and exit_price > 0:
            # Calculate expected return
            expected_return = (exit_price - entry_price) / entry_price
            difference = abs(actual_return - expected_return)
            
            if difference > 0.001:  # More than 0.1% difference
                return_errors += 1
                print(f"  ERROR {symbol}: Entry: ${entry_price:.2f}, Exit: ${exit_price:.2f}")
                print(f"    Expected: {expected_return*100:.2f}%, Actual: {actual_return*100:.2f}%, Diff: {difference*100:.2f}%")
                
                verification_results['return_calculation_errors'].append({
                    'prediction_id': pred_id,
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'expected_return': expected_return,
                    'actual_return': actual_return,
                    'difference': difference
                })
    
    print(f"Return calculation errors found: {return_errors}")
    
    # Step 2.2: Confidence Score Validation
    print("\n2.2 CONFIDENCE SCORE VALIDATION:")
    print("-" * 30)
    
    # Check for confidence values outside normal range
    cursor.execute("""
    SELECT prediction_id, symbol, action_confidence
    FROM predictions
    WHERE CAST(action_confidence AS TEXT) NOT LIKE '%,%'  -- Exclude corrupted ones
      AND (CAST(action_confidence AS REAL) < 0.0 OR CAST(action_confidence AS REAL) > 1.0)
    """)
    
    conf_errors = cursor.fetchall()
    print(f"Confidence range errors: {len(conf_errors)}")
    for error in conf_errors[:10]:
        print(f"  {error[1]}: {error[2]}")
    
    # Check confidence distribution
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        AVG(CAST(action_confidence AS REAL)) as avg_conf,
        MIN(CAST(action_confidence AS REAL)) as min_conf,
        MAX(CAST(action_confidence AS REAL)) as max_conf
    FROM predictions
    WHERE CAST(action_confidence AS TEXT) NOT LIKE '%,%'
      AND action_confidence != '-9999.0'
    """)
    
    conf_stats = cursor.fetchone()
    print(f"Valid confidence records: {conf_stats[0]}")
    print(f"Average confidence: {conf_stats[1]:.3f}")
    print(f"Range: {conf_stats[2]:.3f} to {conf_stats[3]:.3f}")
    
    # Step 2.3: Price Data Accuracy
    print("\n2.3 PRICE DATA ACCURACY:")
    print("-" * 30)
    
    # Check for price inconsistencies
    cursor.execute("""
    SELECT p.prediction_id, p.symbol, p.entry_price, o.entry_price, o.exit_price,
           p.prediction_timestamp, o.evaluation_timestamp
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE p.entry_price IS NOT NULL 
      AND o.entry_price IS NOT NULL
      AND ABS(p.entry_price - o.entry_price) > 0.01  -- More than 1 cent difference
    """)
    
    price_inconsistencies = cursor.fetchall()
    print(f"Entry price inconsistencies: {len(price_inconsistencies)}")
    for inconsistency in price_inconsistencies[:5]:
        pred_id, symbol, pred_entry, out_entry, exit_price, pred_time, eval_time = inconsistency
        print(f"  {symbol}: Pred: ${pred_entry:.2f}, Out: ${out_entry:.2f}, Diff: ${abs(pred_entry-out_entry):.2f}")
    
    # Check for zero or negative prices
    cursor.execute("""
    SELECT prediction_id, symbol, entry_price
    FROM predictions
    WHERE entry_price IS NOT NULL AND entry_price <= 0
    """)
    
    invalid_prices = cursor.fetchall()
    print(f"Invalid entry prices (<=0): {len(invalid_prices)}")
    
    # Step 2.4: Magnitude Prediction Accuracy
    print("\n2.4 MAGNITUDE PREDICTION ACCURACY:")
    print("-" * 30)
    
    # Analyze predicted vs actual magnitude
    cursor.execute("""
    SELECT p.prediction_id, p.symbol, p.predicted_magnitude, o.actual_return,
           p.predicted_direction, o.actual_direction
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = p.prediction_id
    WHERE p.predicted_magnitude IS NOT NULL
      AND o.actual_return IS NOT NULL
      AND ABS(o.actual_return) < 1.0  -- Exclude extreme outliers
    ORDER BY ABS(p.predicted_magnitude - ABS(o.actual_return)) DESC
    LIMIT 10
    """)
    
    magnitude_data = cursor.fetchall()
    print(f"Records with magnitude predictions: {len(magnitude_data)}")
    
    magnitude_errors = 0
    for record in magnitude_data:
        pred_id, symbol, pred_mag, actual_ret, pred_dir, actual_dir = record
        actual_mag = abs(actual_ret)
        magnitude_diff = abs(pred_mag - actual_mag) if pred_mag else float('inf')
        
        if magnitude_diff > 0.1:  # More than 10% magnitude difference
            magnitude_errors += 1
            print(f"  {symbol}: Predicted: {pred_mag:.3f}, Actual: {actual_mag:.3f}, Diff: {magnitude_diff:.3f}")
    
    # Summary
    print("\n" + "="*60)
    print("CALCULATION VERIFICATION SUMMARY:")
    print("="*60)
    
    verification_results['summary'] = {
        'total_records_checked': len(calculation_data),
        'return_calculation_errors': return_errors,
        'confidence_range_errors': len(conf_errors),
        'price_inconsistencies': len(price_inconsistencies),
        'invalid_prices': len(invalid_prices),
        'magnitude_errors': magnitude_errors
    }
    
    print(f"Return calculation errors: {return_errors}")
    print(f"Confidence range errors: {len(conf_errors)}")
    print(f"Price inconsistencies: {len(price_inconsistencies)}")
    print(f"Invalid prices: {len(invalid_prices)}")
    print(f"Magnitude prediction errors: {magnitude_errors}")
    
    conn.close()
    return verification_results

if __name__ == "__main__":
    results = verify_calculations()
    
    # Save results
    with open('calculation_verification.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nVerification results saved to calculation_verification.json")
