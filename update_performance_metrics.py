import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_existing_outcomes():
    """Update existing outcomes with performance_metrics"""
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get outcomes missing performance_metrics
    cursor.execute("""
        SELECT o.outcome_id, o.prediction_id, o.actual_return, o.outcome_details,
               p.action_confidence, p.predicted_action
        FROM outcomes o
        JOIN predictions p ON o.prediction_id = p.prediction_id  
        WHERE o.performance_metrics = '{}' OR o.performance_metrics IS NULL
        ORDER BY o.evaluation_timestamp DESC
        LIMIT 100
    """)
    
    outcomes = cursor.fetchall()
    logger.info(f"Found {len(outcomes)} outcomes to update with performance_metrics")
    
    updated_count = 0
    for outcome in outcomes:
        outcome_id, prediction_id, actual_return, outcome_details, confidence, predicted_action = outcome
        
        # Parse outcome details to get success status
        try:
            details = json.loads(outcome_details) if outcome_details else {}
            success = details.get('success', False)
        except:
            success = False
            
        # Create performance metrics
        performance_metrics = {
            "confidence": round(float(confidence or 0.0), 3),
            "success": success,
            "return": round(float(actual_return or 0.0) / 100, 6),  # Convert percentage to decimal
            "entry_validation": "stored",
            "evaluation_method": "timezone_corrected",
            "backfill": True
        }
        
        # Update the outcome
        cursor.execute("""
            UPDATE outcomes 
            SET performance_metrics = ?
            WHERE outcome_id = ?
        """, (json.dumps(performance_metrics), outcome_id))
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            logger.info(f"Updated {updated_count} outcomes...")
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Updated {updated_count} outcomes with performance_metrics")
    return updated_count

if __name__ == "__main__":
    update_existing_outcomes()
