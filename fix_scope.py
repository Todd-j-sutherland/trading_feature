#!/usr/bin/env python3
"""
Quick fix for volume calculation variable scope issue
"""

def fix_variable_scope():
    """Fix the variable scope issue in volume calculation"""
    
    file_path = "/root/test/enhanced_efficient_system_market_aware.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the variable reference issue
        old_line = '        "volume_change_pct": volume_change_pct_for_analysis,  # Store original percentage'
        new_line = '        "volume_change_pct": volume_change_pct,  # Store original percentage'
        
        content = content.replace(old_line, new_line)
        
        # Also fix it in the details section
        old_detail = '        "volume_change_pct": volume_change_pct_for_analysis,  # Store original percentage'
        new_detail = '        "volume_change_pct": volume_change_pct,  # Store original percentage'
        
        content = content.replace(old_detail, new_detail)
        
        # Remove the redundant assignment line
        old_assignment = '        volume_change_pct_for_analysis = volume_change_pct  # Keep original for analysis'
        content = content.replace(old_assignment, '')
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed variable scope issue")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing scope: {e}")
        return False

if __name__ == "__main__":
    fix_variable_scope()