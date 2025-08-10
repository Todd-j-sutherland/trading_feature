#!/usr/bin/env python3
"""
Simple Return Calculation Test
Test the basic return calculation logic without relying on future data
"""

import sqlite3
from datetime import datetime

def test_simple_return_calculation():
    """Test return calculation by creating test records with known values"""
    
    print("🧮 SIMPLE RETURN CALCULATION TEST")
    print("=" * 40)
    
    conn = sqlite3.connect('data/trading_unified.db')
    cursor = conn.cursor()
    
    # Test cases with known entry and exit prices
    test_cases = [
        {
            "symbol": "TEST_GAIN",
            "entry": 100.0,
            "exit": 105.0,
            "expected": 5.0,
            "action": "BUY"
        },
        {
            "symbol": "TEST_LOSS", 
            "entry": 200.0,
            "exit": 190.0,
            "expected": -5.0,
            "action": "SELL"
        },
        {
            "symbol": "TEST_FLAT",
            "entry": 50.0,
            "exit": 50.0,
            "expected": 0.0,
            "action": "HOLD"
        }
    ]
    
    print("Creating test outcomes with known values:")
    print("-" * 45)
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        # Insert test outcome
        cursor.execute("""
        INSERT INTO enhanced_outcomes (
            symbol, prediction_timestamp, optimal_action, 
            entry_price, exit_price_1d, return_pct, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test["symbol"],
            datetime.now().isoformat(),
            test["action"],
            test["entry"],
            test["exit"],
            test["expected"],  # Store the expected return
            datetime.now().isoformat()
        ))
        
        outcome_id = cursor.lastrowid
        
        # Verify the calculation by re-calculating
        cursor.execute("""
        SELECT 
            symbol,
            entry_price,
            exit_price_1d,
            return_pct as stored_return,
            ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4) as calculated_return
        FROM enhanced_outcomes 
        WHERE id = ?
        """, (outcome_id,))
        
        result = cursor.fetchone()
        
        if result:
            symbol, entry, exit_price, stored, calculated = result
            difference = abs(stored - calculated)
            
            status = "✅ PASS" if difference <= 0.01 else "❌ FAIL"
            
            print(f"Test {i}: {symbol}")
            print(f"  Entry: ${entry:.2f}")
            print(f"  Exit:  ${exit_price:.2f}")
            print(f"  Expected: {test['expected']:.2f}%")
            print(f"  Stored: {stored:.2f}%")
            print(f"  Calculated: {calculated:.2f}%")
            print(f"  Result: {status}")
            print()
            
            if difference > 0.01:
                all_passed = False
        else:
            print(f"❌ Failed to retrieve test result for {test['symbol']}")
            all_passed = False
    
    # Clean up test data
    cursor.execute("DELETE FROM enhanced_outcomes WHERE symbol LIKE 'TEST_%'")
    conn.commit()
    
    print("📊 EXISTING DATA VERIFICATION")
    print("-" * 35)
    
    # Check some real data for comparison
    cursor.execute("""
    SELECT 
        symbol,
        optimal_action,
        entry_price,
        exit_price_1d,
        return_pct as stored_return,
        ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4) as calculated_return,
        ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) as difference
    FROM enhanced_outcomes 
    WHERE exit_price_1d IS NOT NULL 
        AND return_pct IS NOT NULL
        AND optimal_action IN ('BUY', 'SELL')
    ORDER BY difference DESC
    LIMIT 5
    """)
    
    real_data = cursor.fetchall()
    
    print("Top 5 real records with largest calculation differences:")
    print()
    
    for record in real_data:
        symbol, action, entry, exit_price, stored, calculated, diff = record
        status = "✅ OK" if diff <= 0.01 else "❌ ERROR"
        
        print(f"{symbol} ({action}):")
        print(f"  Entry: ${entry:.4f}, Exit: ${exit_price:.4f}")
        print(f"  Stored: {stored:.4f}%, Calculated: {calculated:.4f}%")
        print(f"  Difference: {diff:.4f}% {status}")
        print()
        
        if diff > 0.01:
            all_passed = False
    
    conn.close()
    
    print("📋 FINAL RESULT")
    print("-" * 20)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Return calculation logic is working correctly!")
    else:
        print("❌ CALCULATION ERRORS DETECTED")
        print("The stored return_pct values don't match calculated values")
        print("This explains the suspicious trading performance patterns")
    
    return all_passed

if __name__ == "__main__":
    test_simple_return_calculation()
