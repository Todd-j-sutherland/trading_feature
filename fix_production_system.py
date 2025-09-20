#!/usr/bin/env python3
"""
Update Volume Veto Logic to Handle Mixed Data Formats
Handle both old percentage format (-100 to +100) and new normalized format (0.0 to 1.0)
"""

def fix_volume_veto_logic():
    """Update the volume veto logic to handle mixed data formats"""
    
    file_path = "/root/test/production/cron/enhanced_fixed_price_mapping_system.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the old volume veto logic
        old_veto_logic = '''    # VOLUME VETO POWER - If volume disagrees strongly, override
    if action == 'BUY' and volume_trend < 0.3:
        print(f"🚫 VOLUME VETO: {symbol} BUY -> HOLD (volume_trend={volume_trend:.3f} too low)")
        return 'HOLD', max(0.4, rebalanced_confidence * 0.7), {'veto': 'volume_low', 'original_action': action}
    
    if action == 'SELL' and volume_trend > 0.7:
        print(f"🚫 VOLUME VETO: {symbol} SELL -> HOLD (volume_trend={volume_trend:.3f} too high)")
        return 'HOLD', max(0.4, rebalanced_confidence * 0.7), {'veto': 'volume_high', 'original_action': action}'''
        
        new_veto_logic = '''    # VOLUME VETO POWER - Handle both old percentage format and new normalized format
    # Detect format: if abs(volume_trend) > 2.0, it's likely percentage format
    if abs(volume_trend) > 2.0:
        # Old percentage format (-100 to +100) - convert to normalized 0.0-1.0
        # Map -50% to 0.0, 0% to 0.5, +50% to 1.0
        if volume_trend <= -50.0:
            normalized_volume = 0.0
        elif volume_trend >= 50.0:
            normalized_volume = 1.0
        else:
            normalized_volume = (volume_trend + 50.0) / 100.0
        print(f"📊 VOLUME CONVERSION: {symbol} {volume_trend:.1f}% → {normalized_volume:.3f} normalized")
    else:
        # Already normalized format (0.0 to 1.0)
        normalized_volume = volume_trend
    
    # Apply veto logic with RELAXED thresholds for bullish markets
    if action == 'BUY' and normalized_volume < 0.2:  # Lowered from 0.3 to 0.2
        print(f"🚫 VOLUME VETO: {symbol} BUY -> HOLD (volume={normalized_volume:.3f} < 0.2, original={volume_trend:.3f})")
        return 'HOLD', max(0.4, rebalanced_confidence * 0.7), {'veto': 'volume_low', 'original_action': action}
    
    if action == 'SELL' and normalized_volume > 0.8:  # Raised from 0.7 to 0.8
        print(f"🚫 VOLUME VETO: {symbol} SELL -> HOLD (volume={normalized_volume:.3f} > 0.8, original={volume_trend:.3f})")
        return 'HOLD', max(0.4, rebalanced_confidence * 0.7), {'veto': 'volume_high', 'original_action': action}'''
        
        if old_veto_logic in content:
            content = content.replace(old_veto_logic, new_veto_logic)
            print("✅ Updated volume veto logic to handle mixed formats")
        else:
            print("❌ Could not find exact volume veto pattern")
            return False
        
        # Also update the confidence thresholds to be more reasonable
        old_threshold = '''        # Stricter BUY requirements
        min_confidence = 0.65'''
        
        new_threshold = '''        # Adjusted BUY requirements for bullish markets
        min_confidence = 0.55  # Lowered from 0.65 to account for volume-heavy weighting'''
        
        if old_threshold in content:
            content = content.replace(old_threshold, new_threshold)
            print("✅ Lowered BUY confidence threshold from 65% to 55%")
        
        # Update SELL threshold too
        old_sell_threshold = '''        # Stricter SELL requirements
        min_confidence = 0.60'''
        
        new_sell_threshold = '''        # Adjusted SELL requirements
        min_confidence = 0.55  # Lowered from 0.60 for consistency'''
        
        if old_sell_threshold in content:
            content = content.replace(old_sell_threshold, new_sell_threshold)
            print("✅ Lowered SELL confidence threshold from 60% to 55%")
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated production system: {file_path}")
        print("   Changes made:")
        print("   • Volume veto: Handles both percentage and normalized formats")
        print("   • BUY volume threshold: 0.3 → 0.2 (more lenient)")
        print("   • SELL volume threshold: 0.7 → 0.8 (more lenient)")
        print("   • BUY confidence threshold: 65% → 55%")
        print("   • SELL confidence threshold: 60% → 55%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating volume veto logic: {e}")
        return False

if __name__ == "__main__":
    fix_volume_veto_logic()