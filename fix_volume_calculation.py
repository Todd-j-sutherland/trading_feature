#!/usr/bin/env python3
"""
Fix Volume Trend Calculation
Normalize volume_trend from percentage change to 0.0-1.0 range
"""

def fix_volume_trend_calculation():
    """
    Fix the volume_trend calculation to return 0.0-1.0 values instead of percentage changes
    """
    
    print("🔧 FIXING VOLUME_TREND CALCULATION")
    print("=" * 50)
    
    # Read the current file
    file_path = "/root/test/enhanced_efficient_system_market_aware.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        print(f"✅ Read file: {file_path}")
        
        # Find and replace the volume_trend calculation
        old_calculation = """        # Volume trend (comparing recent vs older)
        recent_avg = sum(volumes[-5:]) / 5
        older_avg = sum(volumes[-20:-10]) / 10
        volume_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0"""
        
        new_calculation = """        # Volume trend (comparing recent vs older) - FIXED to return 0.0-1.0
        recent_avg = sum(volumes[-5:]) / 5
        older_avg = sum(volumes[-20:-10]) / 10
        
        # Calculate percentage change first
        volume_change_pct = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Normalize to 0.0-1.0 range for volume_trend
        # Map -100% to +100% change to 0.0 to 1.0 scale
        # -50% or worse = 0.0, +50% or better = 1.0, 0% = 0.5
        if volume_change_pct <= -0.5:
            volume_trend = 0.0  # Very low volume
        elif volume_change_pct >= 0.5:
            volume_trend = 1.0  # Very high volume  
        else:
            # Linear mapping: -0.5 to +0.5 becomes 0.0 to 1.0
            volume_trend = (volume_change_pct + 0.5) / 1.0
        
        # Store both the original percentage and normalized value
        volume_change_pct_for_analysis = volume_change_pct  # Keep original for analysis"""
        
        if old_calculation in content:
            content = content.replace(old_calculation, new_calculation)
            print("✅ Found and replaced volume_trend calculation")
        else:
            print("❌ Could not find the exact volume_trend calculation pattern")
            print("   Manual fix required")
            return False
        
        # Also need to update where volume_trend is stored in the volume_data dict
        # Look for the volume_data creation
        volume_data_pattern = '''        "volume_trend": volume_trend,'''
        volume_data_replacement = '''        "volume_trend": volume_trend,
        "volume_change_pct": volume_change_pct_for_analysis,  # Store original percentage'''
        
        if volume_data_pattern in content:
            content = content.replace(volume_data_pattern, volume_data_replacement)
            print("✅ Updated volume_data dictionary")
        
        # Write the fixed content back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed volume_trend calculation in {file_path}")
        print(f"   - Now returns 0.0-1.0 normalized values")
        print(f"   - Also stores original percentage for analysis")
        print(f"   - -50% volume change → 0.0")
        print(f"   -   0% volume change → 0.5") 
        print(f"   - +50% volume change → 1.0")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing volume calculation: {e}")
        return False

if __name__ == "__main__":
    fix_volume_trend_calculation()