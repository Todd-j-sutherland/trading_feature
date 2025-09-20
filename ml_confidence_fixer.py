#!/usr/bin/env python3
"""
ML Confidence Fixer - Post-process database to apply ML component to action_confidence
"""
import sqlite3
import re
from datetime import datetime

def extract_ml_component(breakdown_details):
    """Extract ML component value from breakdown string"""
    if not breakdown_details or "ML:" not in breakdown_details:
        return 0.0
    
    # Extract ML component value using regex
    ml_match = re.search(r"ML:([0-9.]+)", breakdown_details)
    if ml_match:
        return float(ml_match.group(1))
    return 0.0

def extract_final_confidence(breakdown_details):
    """Extract the final calculated confidence from breakdown string"""
    if not breakdown_details:
        return None
    
    # Extract final result after = sign
    final_match = re.search(r"= ([0-9.]+)$", breakdown_details)
    if final_match:
        return float(final_match.group(1))
    return None

def fix_ml_confidence():
    """Fix action_confidence values by applying ML component"""
    
    conn = sqlite3.connect("predictions.db")
    cursor = conn.cursor()
    
    # Find records with ML component but low action_confidence
    cursor.execute("""
        SELECT id, symbol, action_confidence, confidence_breakdown, predicted_action 
        FROM predictions 
        WHERE confidence_breakdown LIKE %ML:% 
        AND action_confidence < 0.8
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    records = cursor.fetchall()
    print(f"Found {len(records)} records with ML component and low confidence")
    
    fixed_count = 0
    for record_id, symbol, current_confidence, breakdown, action in records:
        # Extract ML component and final confidence
        ml_component = extract_ml_component(breakdown)
        final_confidence = extract_final_confidence(breakdown)
        
        if ml_component > 0 and final_confidence and final_confidence > current_confidence:
            # Update the action_confidence to the ML-enhanced value
            new_confidence = final_confidence
            
            print(f"í´§ FIXING {symbol}: {current_confidence:.3f} â†’ {new_confidence:.3f} (ML: {ml_component:.3f})")
            
            cursor.execute("""
                UPDATE predictions 
                SET action_confidence = ?
                WHERE id = ?
            """, (new_confidence, record_id))
            
            fixed_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"âœ… Fixed {fixed_count} records with ML-enhanced confidence")
    return fixed_count

if __name__ == "__main__":
    print("í·  ML Confidence Fixer - Applying ML component to action_confidence")
    fix_ml_confidence()
