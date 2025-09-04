#!/usr/bin/env python3
"""
Emergency ML Model Recovery and Retraining Script
Fixes missing metadata and retrains models with enhanced format
"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database is accessible"""
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions")
        count = cursor.fetchone()[0]
        conn.close()
        logger.info(f"✅ Database accessible with {count} predictions")
        return True
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

def check_model_directories():
    """Check model directories and metadata"""
    symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
    issues = []
    
    for symbol in symbols:
        model_dir = f"models/{symbol}"
        if not os.path.exists(model_dir):
            issues.append(f"Missing directory: {model_dir}")
            continue
            
        # Check required files
        required_files = ['direction_model.pkl', 'magnitude_model.pkl', 'metadata.json']
        for file in required_files:
            file_path = os.path.join(model_dir, file)
            if not os.path.exists(file_path):
                issues.append(f"Missing file: {file_path}")
            else:
                # Check metadata format
                if file == 'metadata.json':
                    try:
                        with open(file_path, 'r') as f:
                            metadata = json.load(f)
                        
                        # Check for enhanced metadata fields
                        required_fields = ['symbol', 'model_version', 'performance', 'feature_names']
                        enhanced_fields = ['training_date', 'data_samples', 'feature_count', 'model_type']
                        
                        missing_enhanced = [f for f in enhanced_fields if f not in metadata]
                        if missing_enhanced:
                            issues.append(f"{symbol}: Missing enhanced metadata fields: {missing_enhanced}")
                            
                    except Exception as e:
                        issues.append(f"{symbol}: Invalid metadata format: {e}")
    
    return issues

def update_metadata_format():
    """Update metadata to enhanced format"""
    symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
    
    for symbol in symbols:
        metadata_path = f"models/{symbol}/metadata.json"
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Add enhanced fields
                metadata.update({
                    'training_date': datetime.now().isoformat(),
                    'data_samples': metadata.get('performance', {}).get('samples', 0),
                    'feature_count': len(metadata.get('feature_names', [])),
                    'model_type': 'enhanced_ensemble',
                    'last_updated': datetime.now().isoformat(),
                    'status': 'active'
                })
                
                # Write updated metadata
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"✅ Updated metadata for {symbol}")
                
            except Exception as e:
                logger.error(f"❌ Failed to update metadata for {symbol}: {e}")

def run_emergency_training():
    """Run emergency model training"""
    logger.info("🚀 Starting emergency model retraining...")
    
    try:
        # Try enhanced training first
        result = os.system("python3 enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py")
        if result == 0:
            logger.info("✅ Enhanced training completed successfully")
            return True
        else:
            logger.warning("⚠️ Enhanced training failed, trying manual training...")
            
        # Fallback to manual training
        result = os.system("python3 manual_retrain_models.py")
        if result == 0:
            logger.info("✅ Manual training completed successfully")
            return True
        else:
            logger.error("❌ All training methods failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Training error: {e}")
        return False

def test_market_aware_system():
    """Test the market-aware prediction system"""
    logger.info("🧪 Testing market-aware system...")
    
    try:
        result = os.system("python3 -m app.main_enhanced test-predictor")
        if result == 0:
            logger.info("✅ Market-aware system test passed")
            return True
        else:
            logger.error("❌ Market-aware system test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

def main():
    """Main recovery process"""
    logger.info("🔧 EMERGENCY ML MODEL RECOVERY")
    logger.info("=" * 50)
    
    # Step 1: Check database
    if not check_database_connection():
        logger.error("❌ Database issues detected. Please fix database first.")
        return False
    
    # Step 2: Check model directories
    issues = check_model_directories()
    if issues:
        logger.warning("⚠️ Model issues detected:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    # Step 3: Update metadata format
    logger.info("📝 Updating metadata format...")
    update_metadata_format()
    
    # Step 4: Run emergency training
    if not run_emergency_training():
        logger.error("❌ Training failed. Manual intervention required.")
        return False
    
    # Step 5: Test system
    if not test_market_aware_system():
        logger.error("❌ System test failed. Check logs for details.")
        return False
    
    logger.info("✅ Emergency recovery completed successfully!")
    logger.info("💡 Next steps:")
    logger.info("  1. Monitor predictions during next market hours")
    logger.info("  2. Check logs for any remaining issues")
    logger.info("  3. Verify cron jobs are running correctly")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
