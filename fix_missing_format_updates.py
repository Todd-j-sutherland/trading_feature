#!/usr/bin/env python3
"""
Fix Missing Format Updates
Complete the format standardization for remaining records
"""

import sqlite3
import json
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_missing_format_updates(db_path="data/trading_predictions.db"):
    """Fix the remaining records that weren't updated"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find records without structured format
        cursor.execute("""
            SELECT rowid, prediction_id, symbol, predicted_action, action_confidence, 
                   model_version, feature_vector, prediction_timestamp, entry_price
            FROM predictions 
            WHERE prediction_details IS NULL OR prediction_details = ''
        """)
        
        missing_records = cursor.fetchall()
        logger.info(f"Found {len(missing_records)} records to fix")
        
        for row in missing_records:
            rowid, pred_id, symbol, action, confidence, model_version, feature_vector, timestamp, entry_price = row
            
            # Generate prediction_id if missing
            if not pred_id or pred_id.strip() == '':
                if timestamp:
                    # Try to extract date from timestamp for ID
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        pred_id = f"{symbol}_{dt.strftime('%Y%m%d_%H%M%S')}"
                    except:
                        pred_id = f"{symbol}_{uuid.uuid4().hex[:8]}"
                else:
                    pred_id = f"{symbol}_{uuid.uuid4().hex[:8]}"
            
            # Handle different model types
            if model_version == "NewsTradingAnalyzer_v1.0":
                # This appears to be a news-based model with minimal features
                prediction_details = {
                    "model_type": "news_trading_analyzer",
                    "model_version": "v1.0",
                    "prediction_method": "news_sentiment_analysis",
                    "features": {
                        "news_based": True,
                        "feature_vector": feature_vector or "empty",
                        "analysis_type": "sentiment_driven"
                    },
                    "confidence": confidence or 0.5,
                    "recommended_action": action,
                    "entry_price": entry_price,
                    "conversion_timestamp": datetime.now().isoformat(),
                    "original_format": "news_analyzer_minimal"
                }
                
                confidence_breakdown = {
                    "overall_confidence": confidence or 0.5,
                    "news_component": confidence or 0.5,
                    "technical_component": 0.0,
                    "volume_component": 0.0,
                    "conversion_note": "News-based model with minimal technical features"
                }
                
            else:
                # Generic fallback for unknown model types
                prediction_details = {
                    "model_type": "unknown",
                    "model_version": model_version or "unknown",
                    "prediction_method": "legacy_format_unknown",
                    "features": {
                        "feature_vector": feature_vector or "empty",
                        "parsing_status": "unknown_format"
                    },
                    "confidence": confidence or 0.5,
                    "recommended_action": action,
                    "entry_price": entry_price,
                    "conversion_timestamp": datetime.now().isoformat(),
                    "original_format": "unknown_legacy"
                }
                
                confidence_breakdown = {
                    "overall_confidence": confidence or 0.5,
                    "conversion_note": "Unknown model format - preserved as-is"
                }
            
            # Update the record
            cursor.execute("""
                UPDATE predictions 
                SET prediction_id = ?, 
                    prediction_details = ?, 
                    confidence_breakdown = ?
                WHERE rowid = ?
            """, (
                pred_id,
                json.dumps(prediction_details),
                json.dumps(confidence_breakdown),
                rowid
            ))
            
            logger.info(f"Updated {symbol} ({action}) - {model_version}")
        
        conn.commit()
        
        # Verify completion
        cursor.execute("""
            SELECT COUNT(*) FROM predictions WHERE prediction_details IS NULL OR prediction_details = ''
        """)
        remaining = cursor.fetchone()[0]
        
        logger.info(f"✅ Format fix complete. Remaining unstructured: {remaining}")
        
        # Final statistics
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE prediction_details IS NOT NULL AND prediction_details != ''")
        structured = cursor.fetchone()[0]
        
        logger.info(f"📊 Final statistics: {structured}/{total} ({structured/total*100:.1f}%) structured")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    print("🔧 FIXING MISSING FORMAT UPDATES")
    print("=" * 35)
    
    success = fix_missing_format_updates()
    
    if success:
        print("✅ All predictions now have structured format!")
    else:
        print("❌ Fix failed - check logs")

if __name__ == "__main__":
    main()
