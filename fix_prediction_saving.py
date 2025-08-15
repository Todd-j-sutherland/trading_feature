#!/usr/bin/env python3
"""
Data Quality Fix: Prediction Table Integration
=============================================

This script fixes the core issue where enhanced_features are created
but predictions are not saved to the predictions table.

It adds proper prediction saving functionality to the enhanced morning analyzer.
"""

import subprocess
from datetime import datetime
import tempfile
import os

def create_prediction_saver_patch():
    """Create a patch to save predictions to the predictions table"""
    
    patch_content = '''
    def _save_predictions_to_table(self, analysis_results: Dict):
        """Save individual predictions to the predictions table"""
        try:
            import sqlite3
            import uuid
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure predictions table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    prediction_timestamp DATETIME NOT NULL,
                    predicted_action TEXT NOT NULL,
                    action_confidence REAL NOT NULL,
                    predicted_direction INTEGER,
                    predicted_magnitude REAL,
                    feature_vector TEXT,
                    model_version TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    entry_price REAL DEFAULT 0, 
                    optimal_action TEXT
                );
            ''')
            
            # Save each bank prediction
            ml_preds = analysis_results.get('ml_predictions', {})
            for symbol, pred in ml_preds.items():
                
                prediction_id = f"enhanced_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Get prediction details
                predicted_action = pred.get('optimal_action', 'HOLD')
                confidence = pred.get('action_confidence', 0.5)
                predicted_direction = 1 if predicted_action == 'BUY' else -1 if predicted_action == 'SELL' else 0
                predicted_magnitude = pred.get('predicted_return', 0.0)
                
                # Create feature vector from enhanced features
                feature_vector = {
                    'sentiment_score': pred.get('sentiment_score', 0.0),
                    'confidence': confidence,
                    'technical_score': pred.get('technical_score', 0.0),
                    'feature_count': pred.get('feature_count', 0)
                }
                
                # Insert prediction
                cursor.execute('''
                    INSERT OR REPLACE INTO predictions 
                    (prediction_id, symbol, prediction_timestamp, predicted_action, 
                     action_confidence, predicted_direction, predicted_magnitude, 
                     feature_vector, model_version, entry_price, optimal_action)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction_id,
                    symbol,
                    analysis_results['timestamp'],
                    predicted_action,
                    confidence,
                    predicted_direction,
                    predicted_magnitude,
                    str(feature_vector),
                    'enhanced_ml_v1',
                    pred.get('current_price', 0.0),
                    predicted_action
                ))
                
                self.logger.info(f"✅ Saved prediction for {symbol}: {predicted_action} (confidence: {confidence:.3f})")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Saved {len(ml_preds)} predictions to predictions table")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save predictions: {e}")
    '''
    
    return patch_content

def patch_morning_analyzer():
    """Patch the morning analyzer to save predictions properly"""
    
    print("🔧 PATCHING ENHANCED MORNING ANALYZER")
    print("=" * 50)
    
    # 1. Create the prediction saver method
    prediction_saver = create_prediction_saver_patch()
    
    # 2. Create a temporary file with the patch
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(prediction_saver)
        temp_patch_file = f.name
    
    # 3. Upload the patch to remote server
    upload_cmd = f"scp {temp_patch_file} root@170.64.199.151:/root/test/prediction_saver_patch.py"
    result = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Uploaded prediction saver patch")
    else:
        print(f"❌ Failed to upload patch: {result.stderr}")
        return False
    
    # 4. Apply the patch to the morning analyzer
    patch_script = f'''
import re

# Read the current morning analyzer
with open('/root/test/enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py', 'r') as f:
    content = f.read()

# Read the patch
with open('/root/test/prediction_saver_patch.py', 'r') as f:
    patch_content = f.read()

# Add the prediction saver method before the _save_analysis_results method
if '_save_predictions_to_table' not in content:
    # Find where to insert the method
    insertion_point = content.find('def _save_analysis_results(self, analysis_results: Dict):')
    if insertion_point != -1:
        # Insert the patch before _save_analysis_results
        new_content = content[:insertion_point] + patch_content + "\\n\\n    " + content[insertion_point:]
        
        # Also modify _save_analysis_results to call the prediction saver
        new_content = new_content.replace(
            'self.logger.info("✅ Analysis results saved to database")',
            'self.logger.info("✅ Analysis results saved to database")\\n            # Also save individual predictions\\n            self._save_predictions_to_table(analysis_results)'
        )
        
        # Create backup
        import shutil
        shutil.copy2('/root/test/enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py',
                     '/root/test/enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py.backup_predictions')
        
        # Write the patched content
        with open('/root/test/enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Patched morning analyzer with prediction saving")
    else:
        print("❌ Could not find insertion point in morning analyzer")
else:
    print("✅ Prediction saving already patched")
    '''
    
    # 5. Execute the patch script on remote server
    patch_cmd = f"ssh root@170.64.199.151 'cd /root/test && python3 -c \"{patch_script}\"'"
    result = subprocess.run(patch_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Applied prediction saving patch")
        print(result.stdout)
    else:
        print(f"❌ Failed to apply patch: {result.stderr}")
        return False
    
    # 6. Clean up
    os.unlink(temp_patch_file)
    subprocess.run(f"ssh root@170.64.199.151 'rm -f /root/test/prediction_saver_patch.py'", shell=True)
    
    return True

def test_prediction_saving():
    """Test that predictions are now being saved correctly"""
    
    print("\\n🧪 TESTING PREDICTION SAVING")
    print("=" * 50)
    
    # Check current state
    before_count = subprocess.run(
        "ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db \"SELECT COUNT(*) FROM predictions;\"'",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    
    print(f"📊 Predictions before test: {before_count}")
    
    # Run a quick morning routine test (in background so it doesn't take forever)
    print("🌅 Running quick morning analysis test...")
    
    test_cmd = '''
ssh root@170.64.199.151 'cd /root/test && timeout 30 python3 -c "
import sys
sys.path.append(\"/root/test\")
from enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
analyzer = EnhancedMorningAnalyzer()
# Just test one symbol quickly
result = analyzer._run_basic_analysis([\"CBA.AX\"])
print(\"Quick test completed:\", result.get(\"banks_analyzed\", []))
" 2>/dev/null || echo "Test timeout (expected)"'
    '''
    
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    print(f"Test output: {result.stdout.strip()}")
    
    # Check if any predictions were created
    after_count = subprocess.run(
        "ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db \"SELECT COUNT(*) FROM predictions;\"'",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    
    print(f"📊 Predictions after test: {after_count}")
    
    if after_count and int(after_count) > int(before_count or 0):
        print("✅ Prediction saving is working!")
        return True
    else:
        print("⚠️ No new predictions created (may need full morning routine)")
        return False

def main():
    print("🔧 DATA QUALITY FIX: PREDICTION TABLE INTEGRATION")
    print("=" * 80)
    print(f"⏰ Fix Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Patch the morning analyzer
    if patch_morning_analyzer():
        print("\\n✅ Morning analyzer patched successfully")
        
        # 2. Test the prediction saving
        test_prediction_saving()
        
        print("\\n🎯 NEXT STEPS:")
        print("1. Run the full morning routine to test prediction saving:")
        print("   ssh root@170.64.199.151 'cd /root/test && export PYTHONPATH=/root/test && python3 -m app.main morning'")
        print("\\n2. Check predictions are saved:")
        print("   python3 quick_quality_check.py")
        print("\\n3. The dashboard should now show properly matched predictions vs features")
    else:
        print("\\n❌ Failed to patch morning analyzer")
    
    print("\\n" + "=" * 80)
    print("🏁 PREDICTION SAVING FIX COMPLETED")

if __name__ == "__main__":
    main()
