#!/usr/bin/env python3
"""
Outcome Cleanup and Re-evaluation Script
Cleans up duplicate pricing outcomes and re-evaluates with correct logic
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from corrected_outcome_evaluator import CorrectedOutcomeEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/outcome_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OutcomeCleanup:
    """Cleanup and re-evaluate recent outcomes with correct pricing"""
    
    def __init__(self, db_path: str = 'predictions.db'):
        self.db_path = db_path
        self.evaluator = CorrectedOutcomeEvaluator(db_path)
    
    def backup_outcomes(self):
        """Create backup of current outcomes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create backup table
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_table = f'outcomes_backup_{timestamp}'
            
            cursor.execute(f"""
                CREATE TABLE {backup_table} AS 
                SELECT * FROM outcomes
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Created backup table: {backup_table}")
            return backup_table
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def delete_recent_outcomes(self, days_ago: int = 2):
        """Delete recent outcomes to re-evaluate with correct pricing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get count before deletion
            cursor.execute("""
                SELECT COUNT(*) FROM outcomes 
                WHERE evaluation_timestamp >= datetime('now', '-{} days')
            """.format(days_ago))
            before_count = cursor.fetchone()[0]
            
            # Delete recent outcomes
            cursor.execute("""
                DELETE FROM outcomes 
                WHERE evaluation_timestamp >= datetime('now', '-{} days')
            """.format(days_ago))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️  Deleted {deleted_count} outcomes from last {days_ago} days (expected: {before_count})")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting outcomes: {e}")
            return 0
    
    def get_predictions_needing_reevaluation(self, days_ago: int = 2):
        """Get predictions that need re-evaluation after cleanup"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.prediction_id, p.symbol, p.prediction_timestamp, 
                       p.predicted_action, p.action_confidence, p.entry_price
                FROM predictions p
                LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE o.prediction_id IS NULL
                AND datetime(substr(p.prediction_timestamp, 1, 19)) >= datetime('now', '-{} days')
                AND datetime(substr(p.prediction_timestamp, 1, 19)) < datetime('now', '-4 hours')
                ORDER BY p.prediction_timestamp DESC
            """.format(days_ago))
            
            results = cursor.fetchall()
            conn.close()
            
            return [dict(zip([col[0] for col in cursor.description], row)) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting predictions for re-evaluation: {e}")
            return []
    
    def run_cleanup_and_reevaluation(self, days_ago: int = 2):
        """Full cleanup and re-evaluation process"""
        logger.info("🧹 Starting outcome cleanup and re-evaluation...")
        
        # Step 1: Create backup
        backup_table = self.backup_outcomes()
        if not backup_table:
            logger.error("❌ Backup failed - aborting cleanup")
            return False
        
        # Step 2: Delete recent outcomes with duplicate pricing
        deleted_count = self.delete_recent_outcomes(days_ago)
        if deleted_count == 0:
            logger.warning("⚠️  No outcomes deleted")
            return False
        
        # Step 3: Get predictions that need re-evaluation
        predictions = self.get_predictions_needing_reevaluation(days_ago)
        logger.info(f"📊 Found {len(predictions)} predictions needing re-evaluation")
        
        # Step 4: Re-evaluate with corrected pricing logic
        success_count = 0
        for prediction in predictions:
            try:
                # Use corrected evaluation logic
                outcome = self.evaluator.evaluate_prediction_with_correct_pricing(prediction)
                if outcome and self.evaluator.save_outcome(outcome):
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error re-evaluating prediction {prediction['prediction_id']}: {e}")
        
        logger.info(f"✅ Cleanup complete: {success_count}/{len(predictions)} predictions re-evaluated")
        logger.info(f"📁 Backup saved as: {backup_table}")
        
        return success_count > 0
    
    def verify_cleanup_results(self):
        """Verify that cleanup eliminated duplicate pricing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for remaining duplicate pricing patterns
            cursor.execute("""
                SELECT entry_price, exit_price, COUNT(*) as count 
                FROM outcomes 
                WHERE evaluation_timestamp >= datetime('now', '-1 day')
                GROUP BY entry_price, exit_price 
                HAVING COUNT(*) > 3
                ORDER BY COUNT(*) DESC
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                logger.warning(f"⚠️  Still found {len(duplicates)} duplicate pricing patterns:")
                for entry, exit, count in duplicates:
                    logger.warning(f"  {entry} → {exit}: {count} occurrences")
            else:
                logger.info("✅ No duplicate pricing patterns found - cleanup successful!")
            
            # Show sample of new outcomes
            cursor.execute("""
                SELECT symbol, entry_price, exit_price, actual_return
                FROM outcomes 
                WHERE evaluation_timestamp >= datetime('now', '-2 hours')
                ORDER BY evaluation_timestamp DESC
                LIMIT 10
            """)
            
            recent = cursor.fetchall()
            if recent:
                logger.info("📊 Sample of new corrected outcomes:")
                for symbol, entry, exit, return_pct in recent:
                    logger.info(f"  {symbol}: ${entry} → ${exit} = {return_pct:+.2f}%")
            
            conn.close()
            return len(duplicates) == 0
            
        except Exception as e:
            logger.error(f"Error verifying cleanup: {e}")
            return False

def main():
    """Run the cleanup process"""
    cleanup = OutcomeCleanup()
    
    print("🧹 OUTCOME CLEANUP AND RE-EVALUATION")
    print("=" * 50)
    
    # Run cleanup for last 2 days
    success = cleanup.run_cleanup_and_reevaluation(days_ago=2)
    
    if success:
        print("\n🔍 Verifying cleanup results...")
        cleanup.verify_cleanup_results()
        print("\n✅ Cleanup process completed!")
    else:
        print("\n❌ Cleanup process failed!")

if __name__ == "__main__":
    main()
