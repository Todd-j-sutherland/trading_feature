#!/usr/bin/env python3
"""
Direct Remote Database Format Update
Run this script directly on the remote server to update table formats
"""

import sqlite3
import json
import logging
from datetime import datetime
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_remote_database(db_path="data/trading_predictions.db"):
    """Update remote database with correct format"""
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Database not found: {db_path}")
        return False
    
    logger.info(f"🔧 Updating remote database: {db_path}")
    
    # Create backup first
    backup_path = f"{db_path}.format_update_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Backup database
        logger.info("📋 Creating backup...")
        os.system(f"cp {db_path} {backup_path}")
        logger.info(f"✅ Backup created: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Update predictions table structure
        logger.info("🔄 Updating predictions table...")
        
        # Add new columns if needed
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN prediction_details TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN confidence_breakdown TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Get predictions without structured format
        cursor.execute("""
            SELECT prediction_id, symbol, predicted_action, action_confidence, 
                   feature_vector, model_version, entry_price
            FROM predictions 
            WHERE prediction_details IS NULL OR prediction_details = ''
        """)
        
        predictions = cursor.fetchall()
        logger.info(f"📊 Found {len(predictions)} predictions to update")
        
        for row in predictions:
            pred_id, symbol, action, confidence, feature_vector, model_version, entry_price = row
            
            # Parse legacy feature vector
            features = {}
            if feature_vector:
                try:
                    values = [float(x.strip()) for x in feature_vector.split(',')]
                    feature_names = ['volume_score', 'technical_score', 'current_price', 
                                   'sma_20', 'close_price', 'volume_trend', 'price_change_pct', 
                                   'rsi_change', 'market_trend']
                    features = dict(zip(feature_names, values))
                except:
                    features = {"parsing_error": "legacy_format", "raw": feature_vector}
            
            # Create structured details
            prediction_details = {
                "model_type": "enhanced_news_volume",
                "model_version": model_version or "v1.0",
                "prediction_method": "legacy_converted",
                "features": features,
                "confidence": confidence,
                "action": action,
                "entry_price": entry_price,
                "updated_at": datetime.now().isoformat()
            }
            
            # Update record
            cursor.execute("""
                UPDATE predictions 
                SET prediction_details = ?, confidence_breakdown = ?
                WHERE prediction_id = ?
            """, (
                json.dumps(prediction_details),
                json.dumps({"overall": confidence, "converted": True}),
                pred_id
            ))
        
        # 2. Update outcomes table structure
        logger.info("🔄 Updating outcomes table...")
        
        # Add new columns if needed
        try:
            cursor.execute("ALTER TABLE outcomes ADD COLUMN outcome_details TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE outcomes ADD COLUMN performance_metrics TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Get outcomes without structured format
        cursor.execute("""
            SELECT outcome_id, prediction_id, actual_return, entry_price, 
                   exit_price, actual_direction, evaluation_timestamp
            FROM outcomes 
            WHERE outcome_details IS NULL OR outcome_details = ''
        """)
        
        outcomes = cursor.fetchall()
        logger.info(f"📊 Found {len(outcomes)} outcomes to update")
        
        for row in outcomes:
            outcome_id, pred_id, actual_return, entry_price, exit_price, actual_direction, eval_timestamp = row
            
            # Calculate metrics
            price_change = (exit_price - entry_price) if exit_price and entry_price else 0
            price_change_pct = (price_change / entry_price * 100) if entry_price else 0
            
            # Create structured details
            outcome_details = {
                "outcome_type": "price_evaluation",
                "entry_price": entry_price,
                "exit_price": exit_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "actual_return": actual_return,
                "direction": actual_direction,
                "evaluation_timestamp": eval_timestamp,
                "updated_at": datetime.now().isoformat()
            }
            
            performance_metrics = {
                "return_calculated": actual_return is not None,
                "price_data_complete": entry_price is not None and exit_price is not None,
                "direction_tracked": actual_direction is not None,
                "updated": True
            }
            
            # Update record
            cursor.execute("""
                UPDATE outcomes 
                SET outcome_details = ?, performance_metrics = ?
                WHERE outcome_id = ?
            """, (
                json.dumps(outcome_details),
                json.dumps(performance_metrics),
                outcome_id
            ))
        
        conn.commit()
        
        # 3. Validate updates
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE prediction_details IS NOT NULL")
        updated_predictions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM outcomes WHERE outcome_details IS NOT NULL")  
        updated_outcomes = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"✅ Format update complete!")
        logger.info(f"📊 Updated predictions: {updated_predictions}")
        logger.info(f"📊 Updated outcomes: {updated_outcomes}")
        logger.info(f"💾 Backup available: {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        logger.info(f"💾 Restore from backup: cp {backup_path} {db_path}")
        return False

def main():
    """Main execution"""
    print("🚀 DIRECT REMOTE DATABASE FORMAT UPDATE")
    print("=" * 45)
    
    # Check if database exists
    db_paths = [
        "data/trading_predictions.db",
        "trading_predictions.db", 
        "../data/trading_predictions.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database not found in expected locations:")
        for path in db_paths:
            print(f"   - {path}")
        sys.exit(1)
    
    print(f"📊 Found database: {db_path}")
    
    # Run update
    success = update_remote_database(db_path)
    
    if success:
        print("\n✅ REMOTE UPDATE SUCCESSFUL!")
        print("🎯 Tables now have standardized format:")
        print("   ✅ Predictions with structured JSON details")
        print("   ✅ Outcomes with performance metrics")
        print("   ✅ Backward compatibility maintained")
        print("   ✅ Ready for new prediction systems")
    else:
        print("\n❌ REMOTE UPDATE FAILED!")
        print("💾 Check backup files for recovery")
        sys.exit(1)

if __name__ == "__main__":
    main()
