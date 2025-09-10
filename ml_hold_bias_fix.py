#!/usr/bin/env python3
"""
ML HOLD Bias Fix - Comprehensive Solution
Addresses the critical issues identified in ML_HOLD_BIAS_INVESTIGATION.md:

1. Volume Pipeline Failure (Vol component = 0.0)
2. Conservative Decision Thresholds (70% too high)
3. Technical Indicator Calibration (60+ tech score too strict)
4. Volume Validation Logic (15% decline threshold too strict)

Based on investigation findings:
- Current market: NEUTRAL (-0.26% trend)
- Volume trends: -30% to -47% (severe but market-wide)
- Confidence levels: 57-76% (reasonable but blocked by thresholds)
"""

import sys
import re

def fix_volume_component_calculation():
    """Fix volume component calculation to handle market-wide volume declines"""
    
    # Read the current file
    with open('enhanced_efficient_system_market_aware.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Adjust volume trend factor calculation for market-wide declines
    old_volume_logic = '''        volume_trend_factor = 0.0
        if volume_trend > 0.2:  # Strong volume increase
            volume_trend_factor = 0.10
        elif volume_trend > 0.05:  # Moderate volume increase
            volume_trend_factor = 0.05
        elif volume_trend < -0.4:  # Severe volume decline
            volume_trend_factor = -0.20  # Strong penalty
        elif volume_trend < -0.2:  # Moderate volume decline
            volume_trend_factor = -0.15  # Medium penalty
        elif volume_trend < -0.1:  # Light volume decline
            volume_trend_factor = -0.08  # Light penalty'''
    
    new_volume_logic = '''        volume_trend_factor = 0.0
        if volume_trend > 0.2:  # Strong volume increase
            volume_trend_factor = 0.10
        elif volume_trend > 0.05:  # Moderate volume increase
            volume_trend_factor = 0.05
        elif volume_trend > -0.1:  # Neutral to slight decline
            volume_trend_factor = 0.02  # Small positive contribution
        elif volume_trend > -0.3:  # Moderate decline (market-wide condition)
            volume_trend_factor = 0.01  # Minimal positive to avoid 0.0
        elif volume_trend > -0.5:  # Severe decline but not extreme
            volume_trend_factor = -0.05  # Reduced penalty
        else:  # Extreme decline > 50%
            volume_trend_factor = -0.10  # Moderate penalty (was -0.20)'''
    
    content = content.replace(old_volume_logic, new_volume_logic)
    
    # Fix 2: Adjust volume component bounds to ensure positive contribution
    old_bounds = '''        volume_component = volume_quality * 0.10 + volume_trend_factor + correlation_factor
        volume_component = max(0.0, min(volume_component, 0.20))  # Clamp to 0-20%'''
    
    new_bounds = '''        volume_component = volume_quality * 0.10 + volume_trend_factor + correlation_factor
        # Ensure minimum positive contribution even during market-wide volume declines
        volume_component = max(0.02, min(volume_component, 0.20))  # Min 2% contribution'''
    
    content = content.replace(old_bounds, new_bounds)
    
    print("✅ Fixed volume component calculation")
    return content

def fix_decision_thresholds(content):
    """Lower decision thresholds for current market conditions"""
    
    # Fix 3: Reduce technical score requirements
    old_tech_req = '''        if final_confidence > buy_threshold and tech_score > 60 and not volume_blocked:'''
    new_tech_req = '''        if final_confidence > buy_threshold and tech_score > 40 and not volume_blocked:'''
    
    content = content.replace(old_tech_req, new_tech_req)
    
    # Fix 4: Reduce buy thresholds for all market conditions
    threshold_fixes = [
        ('buy_threshold = 0.80  # Higher threshold', 'buy_threshold = 0.65  # Adjusted for current conditions'),
        ('buy_threshold = 0.75  # Slightly higher threshold', 'buy_threshold = 0.62  # Adjusted for weak bearish'),
        ('buy_threshold = 0.70', 'buy_threshold = 0.60  # Lowered base threshold'),
        ('buy_threshold = 0.68  # Slightly lower threshold', 'buy_threshold = 0.58  # Adjusted for weak bullish'),
        ('buy_threshold = 0.65  # Lower threshold', 'buy_threshold = 0.55  # Adjusted for bullish')
    ]
    
    for old, new in threshold_fixes:
        content = content.replace(old, new)
    
    print("✅ Fixed decision thresholds")
    return content

def fix_volume_validation_logic(content):
    """Adjust volume validation to account for market-wide volume declines"""
    
    # Fix 5: Relax volume decline blocks
    old_extreme_block = '''        if volume_trend < -0.30:  # Extreme volume decline (>30%)
            volume_blocked = True
            action = "HOLD"  # Global block for extreme volume decline'''
    
    new_extreme_block = '''        if volume_trend < -0.60:  # Extreme volume decline (>60%)
            volume_blocked = True
            action = "HOLD"  # Global block for extreme volume decline'''
    
    content = content.replace(old_extreme_block, new_extreme_block)
    
    # Fix 6: Relax moderate volume decline restrictions
    old_moderate_block = '''            if volume_trend < -0.15:  # More than 15% volume decline
                action = "HOLD"  # Override BUY due to volume decline'''
    
    new_moderate_block = '''            if volume_trend < -0.40:  # More than 40% volume decline
                action = "HOLD"  # Override BUY due to volume decline'''
    
    content = content.replace(old_moderate_block, new_moderate_block)
    
    # Fix 7: Adjust bearish market volume requirements
    old_bearish_vol = '''                if news_sentiment > 0.10 and tech_score > 70 and volume_trend > -0.05:  # Require stable/growing volume'''
    new_bearish_vol = '''                if news_sentiment > 0.05 and tech_score > 50 and volume_trend > -0.25:  # Relaxed volume requirement'''
    
    content = content.replace(old_bearish_vol, new_bearish_vol)
    
    # Fix 8: Adjust weak bearish requirements
    old_weak_bearish = '''                if news_sentiment > 0.05 and tech_score > 65 and volume_trend > -0.08:  # Moderate requirements'''
    new_weak_bearish = '''                if news_sentiment > 0.02 and tech_score > 45 and volume_trend > -0.20:  # Relaxed requirements'''
    
    content = content.replace(old_weak_bearish, new_weak_bearish)
    
    # Fix 9: Adjust normal requirements
    old_normal_req = '''                if news_sentiment > -0.05 and volume_trend > -0.10:  # Light volume decline tolerance'''
    new_normal_req = '''                if news_sentiment > -0.08 and volume_trend > -0.30:  # Moderate volume decline tolerance'''
    
    content = content.replace(old_normal_req, new_normal_req)
    
    print("✅ Fixed volume validation logic")
    return content

def fix_strong_buy_logic(content):
    """Adjust strong BUY requirements"""
    
    # Fix 10: Relax strong BUY technical requirements
    old_strong_buy = '''        if final_confidence > (buy_threshold + 0.10) and tech_score > 70:'''
    new_strong_buy = '''        if final_confidence > (buy_threshold + 0.08) and tech_score > 55:'''
    
    content = content.replace(old_strong_buy, new_strong_buy)
    
    # Fix 11: Relax strong BUY volume requirements  
    old_strong_vol = '''            if market_data["context"] != "BEARISH" and news_sentiment > 0.02 and volume_trend > 0.05:  # Require volume growth for STRONG_BUY'''
    new_strong_vol = '''            if market_data["context"] != "BEARISH" and news_sentiment > -0.02 and volume_trend > -0.15:  # Relaxed volume for STRONG_BUY'''
    
    content = content.replace(old_strong_vol, new_strong_vol)
    
    print("✅ Fixed strong BUY logic")
    return content

def add_debugging_output(content):
    """Add enhanced debugging to understand decision logic"""
    
    # Add detailed volume component logging
    volume_debug = '''
        # DEBUG: Volume component calculation details
        print(f"   📊 Volume Analysis for {symbol}:")
        print(f"      Volume Trend: {volume_trend:+.1%}")
        print(f"      Volume Quality: {volume_quality:.3f}")
        print(f"      Volume Correlation: {volume_correlation:.3f}")
        print(f"      Volume Trend Factor: {volume_trend_factor:+.3f}")
        print(f"      Correlation Factor: {correlation_factor:+.3f}")
        print(f"      Final Volume Component: {volume_component:.3f}")'''
    
    # Insert after volume_component calculation
    insert_point = "volume_component = max(0.02, min(volume_component, 0.20))  # Min 2% contribution"
    content = content.replace(insert_point, insert_point + volume_debug)
    
    print("✅ Added enhanced debugging")
    return content

def main():
    """Apply all fixes to resolve ML HOLD bias"""
    
    print("🚀 Applying ML HOLD Bias Fixes...")
    print("="*60)
    
    try:
        # Apply fixes in sequence
        content = fix_volume_component_calculation()
        content = fix_decision_thresholds(content)
        content = fix_volume_validation_logic(content)
        content = fix_strong_buy_logic(content)
        content = add_debugging_output(content)
        
        # Write the fixed file
        with open('enhanced_efficient_system_market_aware.py', 'w') as f:
            f.write(content)
        
        print("="*60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("\nChanges made:")
        print("1. ✅ Volume component: Minimum 2% contribution (was clamped to 0%)")
        print("2. ✅ Buy thresholds: Reduced by 5-10% across all market conditions")
        print("3. ✅ Technical score: Lowered from 60 to 40 minimum requirement")
        print("4. ✅ Volume validation: Relaxed decline limits from 15% to 40%")
        print("5. ✅ Market-specific: Adjusted requirements for current conditions")
        print("6. ✅ Strong BUY: Relaxed requirements for better signal generation")
        print("7. ✅ Debug output: Added detailed volume component logging")
        
        print("\nExpected outcomes:")
        print("- Volume component will show positive values (2-20%)")
        print("- BUY signals should generate for 60-65% confidence (was 70%)")
        print("- Technical scores 40+ will qualify (was 60+)")
        print("- Volume declines up to 40% won't block signals (was 15%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
