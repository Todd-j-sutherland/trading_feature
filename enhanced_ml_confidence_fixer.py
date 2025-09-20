#!/usr/bin/env python3
"""
Enhanced ML Confidence Fixer with Risk Management
Applies ML boost while maintaining volume veto and market penalty logic
"""
import sqlite3
import re

def extract_ml_component(breakdown_details):
    """Extract ML component value from breakdown string"""
    if not breakdown_details or "ML:" not in breakdown_details:
        return 0.0
    
    ml_match = re.search(r"ML:([0-9.]+)", breakdown_details)
    if ml_match:
        return float(ml_match.group(1))
    return 0.0

def extract_final_confidence(breakdown_details):
    """Extract the final calculated confidence from breakdown string"""
    if not breakdown_details:
        return None
    
    final_match = re.search(r"= ([0-9.]+)$", breakdown_details)
    if final_match:
        return float(final_match.group(1))
    return None

def apply_risk_controls(symbol, action, ml_enhanced_confidence, volume_trend, market_trend):
    """Apply volume veto and market penalty controls"""
    
    original_confidence = ml_enhanced_confidence
    
    # 1. VOLUME VETO POWER
    # Convert percentage format (-100 to +100) to normalized format (0.0 to 1.0)
    if abs(volume_trend) > 2.0:
        # Percentage format - convert to normalized
        # volume_trend of -50% = very low volume = 0.0 normalized
        # volume_trend of +50% = high volume = 1.0 normalized
        normalized_volume = max(0.0, min(1.0, (volume_trend + 50.0) / 100.0))
    else:
        # Already normalized format
        normalized_volume = volume_trend
    
    # Apply volume veto
    if action in ["BUY", "STRONG_BUY"] and normalized_volume < 0.2:
        print(f"🚫 VOLUME VETO: {symbol} {action} -> HOLD (volume={normalized_volume:.3f} < 0.2)")
        return "HOLD", max(0.4, ml_enhanced_confidence * 0.7)
    
    if action in ["SELL", "STRONG_SELL"] and normalized_volume > 0.8:
        print(f"🚫 VOLUME VETO: {symbol} {action} -> HOLD (volume={normalized_volume:.3f} > 0.8)")
        return "HOLD", max(0.4, ml_enhanced_confidence * 0.7)
    
    # 2. MARKET PENALTY
    market_penalty = 0.0
    if market_trend < -2.0 and action in ["BUY", "STRONG_BUY"]:
        market_penalty = 0.15
        print(f"📉 MARKET PENALTY: {symbol} market_trend={market_trend:.1f}%, reducing BUY confidence by 15%")
    elif market_trend > 2.0 and action in ["SELL", "STRONG_SELL"]:
        market_penalty = 0.15
        print(f"📈 MARKET PENALTY: {symbol} market_trend={market_trend:.1f}%, reducing SELL confidence by 15%")
    
    # Apply market penalty
    final_confidence = max(0.3, ml_enhanced_confidence - market_penalty)
    
    # 3. THRESHOLD VALIDATION
    min_confidence = 0.55
    
    if action in ["BUY", "STRONG_BUY"] and final_confidence < min_confidence:
        print(f"❌ THRESHOLD FAIL: {symbol} {action} -> HOLD (confidence={final_confidence:.3f} < {min_confidence})")
        return "HOLD", final_confidence
    
    if action in ["SELL", "STRONG_SELL"] and final_confidence < min_confidence:
        print(f"❌ THRESHOLD FAIL: {symbol} {action} -> HOLD (confidence={final_confidence:.3f} < {min_confidence})")
        return "HOLD", final_confidence
    
    # All checks passed
    if market_penalty > 0 or final_confidence != original_confidence:
        print(f"✅ RISK ADJUSTED: {symbol} {action} confidence: {original_confidence:.3f} -> {final_confidence:.3f}")
    
    return action, final_confidence

def fix_ml_confidence_with_risk_controls():
    """Fix ML confidence while applying proper risk management"""
    
    conn = sqlite3.connect("predictions.db")
    cursor = conn.cursor()
    
    # Get recent predictions that need risk controls (both ML and non-ML)
    query = """
    SELECT prediction_id, symbol, predicted_action, action_confidence, confidence_breakdown, 
           volume_trend, market_trend_pct
    FROM predictions 
    WHERE predicted_action IN ('BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL')
    AND action_confidence > 0.7
    ORDER BY created_at DESC 
    LIMIT 50
    """
    cursor.execute(query)
    
    records = cursor.fetchall()
    print(f"Found {len(records)} BUY/SELL records to apply risk controls to")
    
    risk_adjusted_count = 0
    
    for pred_id, symbol, action, current_conf, breakdown, volume_trend, market_trend in records:
        print(f"\n🔍 CHECKING {symbol}: {action}@{current_conf:.3f} (vol={volume_trend:.1f}%, mkt={market_trend:.1f}%)")
        
        # Apply risk controls to any BUY/SELL action
        risk_adjusted_action, risk_adjusted_conf = apply_risk_controls(
            symbol, action, current_conf, volume_trend or 0.0, market_trend or 0.0
        )
            
        # Update if risk controls changed anything
        if risk_adjusted_action != action or abs(risk_adjusted_conf - current_conf) > 0.01:
            print(f"🔧 UPDATING {symbol}: {action}@{current_conf:.3f} -> {risk_adjusted_action}@{risk_adjusted_conf:.3f}")
            
            cursor.execute("""
                UPDATE predictions 
                SET predicted_action = ?, action_confidence = ?
                WHERE prediction_id = ?
            """, (risk_adjusted_action, risk_adjusted_conf, pred_id))
            
            risk_adjusted_count += 1
        else:
            print(f"✅ PASSED: {symbol} {action} passes all risk controls")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Applied risk controls to {risk_adjusted_count} records")
    return risk_adjusted_count

if __name__ == "__main__":
    print("🧠🛡️ Enhanced ML Confidence Fixer with Risk Management")
    print("Applying volume veto, market penalties, and threshold validation...")
    fix_ml_confidence_with_risk_controls()