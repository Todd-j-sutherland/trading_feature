#!/usr/bin/env python3
"""
Trading System Verification Summary
Summary of all validation tests and recommendations
"""

import sqlite3

def generate_verification_summary():
    """Generate a comprehensive summary of the trading system validation"""
    
    print("📋 TRADING SYSTEM VERIFICATION SUMMARY")
    print("=" * 45)
    
    conn = sqlite3.connect('data/trading_unified.db')
    cursor = conn.cursor()
    
    # Basic system statistics
    cursor.execute("SELECT COUNT(*) FROM enhanced_features")
    total_features = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
    total_outcomes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE exit_price_1d IS NOT NULL")
    outcomes_with_exits = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE return_pct IS NOT NULL")
    outcomes_with_returns = cursor.fetchone()[0]
    
    print(f"🔢 SYSTEM STATISTICS")
    print("-" * 25)
    print(f"Total Features: {total_features}")
    print(f"Total Outcomes: {total_outcomes}")
    print(f"Outcomes with Exit Prices: {outcomes_with_exits}")
    print(f"Outcomes with Returns: {outcomes_with_returns}")
    print(f"Exit Price Completion: {(outcomes_with_exits/total_outcomes)*100:.1f}%")
    print(f"Return Calculation Completion: {(outcomes_with_returns/total_outcomes)*100:.1f}%")
    
    # Return calculation accuracy check
    cursor.execute("""
    SELECT 
        COUNT(*) as total_checked,
        SUM(CASE WHEN ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) <= 0.01 THEN 1 ELSE 0 END) as accurate_calculations,
        SUM(CASE WHEN ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) > 0.01 THEN 1 ELSE 0 END) as inaccurate_calculations
    FROM enhanced_outcomes 
    WHERE exit_price_1d IS NOT NULL 
        AND return_pct IS NOT NULL
    """)
    
    calc_check = cursor.fetchone()
    total_checked, accurate, inaccurate = calc_check
    
    if total_checked > 0:
        accuracy_rate = (accurate / total_checked) * 100
        
        print(f"\n🎯 CALCULATION ACCURACY")
        print("-" * 30)
        print(f"Records Checked: {total_checked}")
        print(f"Accurate Calculations: {accurate}")
        print(f"Inaccurate Calculations: {inaccurate}")
        print(f"Accuracy Rate: {accuracy_rate:.1f}%")
        
        if accuracy_rate >= 95:
            print("✅ Return calculations are ACCURATE")
        else:
            print("❌ Return calculations need FIXING")
    
    # Trading performance analysis
    cursor.execute("""
    SELECT 
        optimal_action,
        COUNT(*) as count,
        SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as winners,
        SUM(CASE WHEN return_pct <= 0 THEN 1 ELSE 0 END) as losers,
        AVG(return_pct) as avg_return,
        MIN(return_pct) as min_return,
        MAX(return_pct) as max_return
    FROM enhanced_outcomes 
    WHERE exit_price_1d IS NOT NULL 
        AND return_pct IS NOT NULL
        AND optimal_action IN ('BUY', 'SELL', 'HOLD')
    GROUP BY optimal_action
    ORDER BY optimal_action
    """)
    
    performance_data = cursor.fetchall()
    
    print(f"\n📈 TRADING PERFORMANCE ANALYSIS")
    print("-" * 40)
    
    suspicious_patterns = []
    
    for action, count, winners, losers, avg_return, min_return, max_return in performance_data:
        win_rate = (winners / count) * 100 if count > 0 else 0
        
        print(f"\n{action} Positions:")
        print(f"  Total: {count}")
        print(f"  Winners: {winners} ({win_rate:.1f}%)")
        print(f"  Losers: {losers} ({100-win_rate:.1f}%)")
        print(f"  Average Return: {avg_return:.4f}%")
        print(f"  Range: {min_return:.4f}% to {max_return:.4f}%")
        
        # Flag suspicious patterns
        if action == 'BUY' and win_rate == 100:
            suspicious_patterns.append(f"BUY positions show 100% win rate ({count} trades)")
        elif action == 'SELL' and win_rate == 0:
            suspicious_patterns.append(f"SELL positions show 0% win rate ({count} trades)")
        elif action == 'HOLD' and abs(avg_return) > 1:
            suspicious_patterns.append(f"HOLD positions show high average return ({avg_return:.2f}%)")
    
    # Summary and recommendations
    print(f"\n⚠️ SUSPICIOUS PATTERNS DETECTED")
    print("-" * 35)
    
    if suspicious_patterns:
        for pattern in suspicious_patterns:
            print(f"❌ {pattern}")
    else:
        print("✅ No suspicious patterns detected")
    
    print(f"\n🔧 RECOMMENDATIONS")
    print("-" * 25)
    
    if inaccurate > 0:
        print("1. ❌ FIX RETURN CALCULATIONS:")
        print("   - Many stored return_pct values don't match actual calculations")
        print("   - This explains the unrealistic BUY/SELL performance")
        print("   - Need to recalculate all return_pct values properly")
    else:
        print("1. ✅ Return calculations are accurate")
    
    if outcomes_with_exits < total_outcomes * 0.8:
        print("2. ❌ IMPROVE EXIT PRICE TRACKING:")
        print(f"   - Only {(outcomes_with_exits/total_outcomes)*100:.1f}% of outcomes have exit prices")
        print("   - Target should be >80% completion")
    else:
        print("2. ✅ Exit price tracking is adequate")
    
    if len(suspicious_patterns) > 0:
        print("3. ❌ INVESTIGATE TRADING LOGIC:")
        print("   - Perfect win rates suggest data quality issues")
        print("   - Review trading action classification algorithm")
    else:
        print("3. ✅ Trading performance patterns look realistic")
    
    print(f"\n🎯 NEXT STEPS")
    print("-" * 15)
    
    if inaccurate > 0:
        print("PRIORITY 1: Fix return calculation bugs before running new analysis")
        print("PRIORITY 2: Re-validate system with mock tests")
        print("PRIORITY 3: Run new trading cycle to verify fixes")
    else:
        print("✅ System ready for production trading cycles")
    
    conn.close()

if __name__ == "__main__":
    generate_verification_summary()
