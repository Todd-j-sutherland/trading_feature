#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def populate_enhanced_outcomes():
    conn = sqlite3.connect("data/trading_predictions.db")
    cursor = conn.cursor()
    
    print("Populating enhanced_outcomes table...")
    
    # Get enhanced_features that dont have outcomes yet
    cursor.execute("""
        SELECT ef.id, ef.symbol, ef.timestamp 
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE eo.feature_id IS NULL
        ORDER BY ef.timestamp
    """)
    
    unlinked_features = cursor.fetchall()
    print(f"Found {len(unlinked_features)} enhanced_features without outcomes")
    
    populated_count = 0
    
    for feature_id, symbol, feature_timestamp in unlinked_features:
        feature_dt = datetime.fromisoformat(feature_timestamp)
        feature_date = feature_dt.date()
        
        print(f"Processing feature {feature_id}: {symbol} on {feature_date}")
        
        # Find corresponding prediction and outcome
        cursor.execute("""
            SELECT o.actual_direction, o.actual_return, o.entry_price, o.exit_price
            FROM predictions p
            INNER JOIN outcomes o ON p.prediction_id = o.prediction_id  
            WHERE p.symbol = ? 
            AND DATE(p.prediction_timestamp) = ?
            ORDER BY p.prediction_timestamp DESC
            LIMIT 1
        """, (symbol, feature_date))
        
        outcome_result = cursor.fetchone()
        
        if outcome_result:
            actual_direction, actual_return, entry_price, exit_price = outcome_result
            
            price_direction = 1 if actual_direction == 1 else 0
            price_magnitude = abs(actual_return) if actual_return else 0.0
            
            cursor.execute("""
                INSERT INTO enhanced_outcomes (
                    feature_id, price_direction_1h, price_direction_4h, price_direction_1d,
                    price_magnitude_1h, price_magnitude_4h, price_magnitude_1d,
                    optimal_action, confidence_score, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feature_id,
                price_direction,  
                price_direction,  
                price_direction,  
                price_magnitude,  
                price_magnitude,  
                price_magnitude,  
                "HOLD",           
                0.7,             
                feature_timestamp
            ))
            
            populated_count += 1
            direction_str = "UP" if actual_direction == 1 else "DOWN"
            print(f"  ✅ Linked to outcome: {direction_str} {actual_return:.4f}")
        else:
            print(f"  ❌ No outcome found for {symbol} on {feature_date}")
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
    final_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\nPopulation complete!")
    print(f"  Successfully populated: {populated_count} records")
    print(f"  Enhanced outcomes total: {final_count} records")
    
    return populated_count

if __name__ == "__main__":
    result = populate_enhanced_outcomes()
    print(f"Done! Populated {result} enhanced_outcomes records")
