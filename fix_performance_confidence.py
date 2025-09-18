import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_confidence_in_outcomes():
    """Update performance_metrics with corrected confidence values"""
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get outcomes that need confidence correction
    cursor.execute("""
        SELECT o.outcome_id, o.performance_metrics, p.action_confidence, p.symbol
        FROM outcomes o
        JOIN predictions p ON o.prediction_id = p.prediction_id  
        WHERE o.performance_metrics LIKE '%"confidence": 0.4,%'
        AND p.prediction_timestamp LIKE '2025-09-18%'
    """)
    
    outcomes = cursor.fetchall()
    logger.info(f"Found {len(outcomes)} outcomes to update with corrected confidence")
    
    updated_count = 0
    for outcome_id, perf_metrics_json, actual_confidence, symbol in outcomes:
        try:
            # Parse existing performance metrics
            perf_metrics = json.loads(perf_metrics_json) if perf_metrics_json else {}
            
            # Update confidence with actual value
            perf_metrics['confidence'] = round(float(actual_confidence), 4)
            perf_metrics['confidence_corrected'] = True
            
            # Update the outcome
            cursor.execute("""
                UPDATE outcomes 
                SET performance_metrics = ?
                WHERE outcome_id = ?
            """, (json.dumps(perf_metrics), outcome_id))
            
            updated_count += 1
            
            if updated_count <= 5:  # Log first 5 for verification
                logger.info(f"{symbol}: Confidence updated from 0.4 to {actual_confidence}")
                
        except Exception as e:
            logger.error(f"Error updating outcome {outcome_id}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Updated {updated_count} outcomes with corrected confidence values")
    return updated_count

if __name__ == "__main__":
    update_confidence_in_outcomes()
