#!/usr/bin/env python3
"""
Mock Test Script for Return Calculations
Tests the return calculation logic with known values
"""

import sqlite3
import pandas as pd
from datetime import datetime

def test_return_calculations():
    """Test return calculation logic with mock data"""
    
    print("🧪 RETURN CALCULATION MOCK TESTS")
    print("=" * 40)
    
    # Test cases with known entry/exit prices and expected returns
    test_cases = [
        {
            "symbol": "TEST1",
            "entry_price": 100.0,
            "exit_price": 105.0,
            "expected_return": 5.0,
            "description": "Simple 5% gain"
        },
        {
            "symbol": "TEST2", 
            "entry_price": 200.0,
            "exit_price": 190.0,
            "expected_return": -5.0,
            "description": "Simple 5% loss"
        },
        {
            "symbol": "TEST3",
            "entry_price": 50.0,
            "exit_price": 50.0,
            "expected_return": 0.0,
            "description": "No change"
        },
        {
            "symbol": "TEST4",
            "entry_price": 33.33,
            "exit_price": 36.66,
            "expected_return": 9.99,
            "description": "Decimal precision test"
        }
    ]
    
    print("📊 Test Cases:")
    print("-" * 50)
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        # Calculate return using the same formula as the system
        calculated_return = ((test["exit_price"] - test["entry_price"]) / test["entry_price"]) * 100
        
        # Check if it matches expected (within 0.01% tolerance)
        tolerance = 0.01
        matches = abs(calculated_return - test["expected_return"]) <= tolerance
        
        status = "✅ PASS" if matches else "❌ FAIL"
        
        print(f"Test {i}: {test['description']}")
        print(f"  Entry: ${test['entry_price']:.2f}")
        print(f"  Exit:  ${test['exit_price']:.2f}")
        print(f"  Expected: {test['expected_return']:.2f}%")
        print(f"  Calculated: {calculated_return:.2f}%")
        print(f"  Result: {status}")
        print()
        
        if not matches:
            all_passed = False
    
    print("🔍 ACTUAL DATABASE RETURN VERIFICATION")
    print("-" * 45)
    
    # Check some actual database records for calculation accuracy
    conn = sqlite3.connect('data/trading_unified.db')
    
    verification_query = """
    SELECT 
        symbol,
        entry_price,
        exit_price_1d,
        return_pct as stored_return,
        ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4) as calculated_return,
        optimal_action,
        prediction_timestamp
    FROM enhanced_outcomes 
    WHERE exit_price_1d IS NOT NULL 
        AND return_pct IS NOT NULL
        AND optimal_action IN ('BUY', 'SELL')
    ORDER BY ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) DESC
    LIMIT 10
    """
    
    verification_df = pd.read_sql_query(verification_query, conn)
    
    if len(verification_df) > 0:
        print("Top 10 records with largest calculation discrepancies:")
        print()
        
        for _, row in verification_df.iterrows():
            stored = row['stored_return']
            calculated = row['calculated_return']
            difference = abs(stored - calculated)
            
            status = "✅ OK" if difference <= 0.01 else "❌ ERROR"
            
            print(f"{row['symbol']} ({row['optimal_action']}):")
            print(f"  Entry: ${row['entry_price']:.4f}")
            print(f"  Exit:  ${row['exit_price_1d']:.4f}")
            print(f"  Stored Return: {stored:.4f}%")
            print(f"  Calculated Return: {calculated:.4f}%")
            print(f"  Difference: {difference:.4f}% {status}")
            print()
            
            if difference > 0.01:
                all_passed = False
    else:
        print("No records found for verification")
    
    conn.close()
    
    print("📋 SUMMARY")
    print("-" * 20)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Return calculations appear to be working correctly")
    else:
        print("❌ SOME TESTS FAILED") 
        print("Return calculations need attention")
    
    return all_passed

def test_trading_logic_consistency():
    """Test that trading logic makes sense"""
    
    print("\n🎯 TRADING LOGIC CONSISTENCY TEST")
    print("=" * 35)
    
    conn = sqlite3.connect('data/trading_unified.db')
    
    # Check if BUY positions with positive returns and SELL positions with negative returns
    # make logical sense (this might indicate incorrect data)
    logic_query = """
    SELECT 
        optimal_action,
        COUNT(*) as total_positions,
        SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as profitable_positions,
        SUM(CASE WHEN return_pct <= 0 THEN 1 ELSE 0 END) as unprofitable_positions,
        AVG(return_pct) as avg_return,
        MIN(return_pct) as worst_return,
        MAX(return_pct) as best_return
    FROM enhanced_outcomes 
    WHERE exit_price_1d IS NOT NULL 
        AND return_pct IS NOT NULL
        AND optimal_action IN ('BUY', 'SELL', 'HOLD')
    GROUP BY optimal_action
    ORDER BY optimal_action
    """
    
    logic_df = pd.read_sql_query(logic_query, conn)
    
    for _, row in logic_df.iterrows():
        action = row['optimal_action']
        total = row['total_positions']
        profitable = row['profitable_positions']
        unprofitable = row['unprofitable_positions']
        win_rate = (profitable / total) * 100
        
        print(f"{action} Positions:")
        print(f"  Total: {total}")
        print(f"  Profitable: {profitable} ({win_rate:.1f}%)")
        print(f"  Unprofitable: {unprofitable} ({100-win_rate:.1f}%)")
        print(f"  Avg Return: {row['avg_return']:.4f}%")
        print(f"  Range: {row['worst_return']:.4f}% to {row['best_return']:.4f}%")
        
        # Flag suspicious patterns
        if action == 'BUY' and win_rate == 100:
            print("  ⚠️  WARNING: 100% win rate for BUY positions seems unlikely")
        elif action == 'SELL' and win_rate == 0:
            print("  ⚠️  WARNING: 0% win rate for SELL positions seems unlikely")
        elif action == 'HOLD' and abs(row['avg_return']) > 2:
            print("  ⚠️  WARNING: HOLD positions showing large average returns")
        else:
            print("  ✅ Results seem reasonable")
        
        print()
    
    conn.close()

if __name__ == "__main__":
    calculation_tests_passed = test_return_calculations()
    test_trading_logic_consistency()
    
    if calculation_tests_passed:
        print("\n🎉 Ready for mock trading cycle test!")
    else:
        print("\n🔧 Fix calculation issues before proceeding")
