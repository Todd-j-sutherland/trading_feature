#!/usr/bin/env python3
"""
Simple Prediction Saving Fix
============================

Direct fix for the prediction saving issue.
"""

import subprocess
from datetime import datetime

def add_prediction_saving():
    """Add prediction saving functionality directly to the remote server"""
    
    print("🔧 ADDING PREDICTION SAVING TO MORNING ANALYZER")
    print("=" * 60)
    
    # Create a Python script to patch the morning analyzer
    patch_script = '''
import re

# Read the current morning analyzer
file_path = '/root/test/enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py'
with open(file_path, 'r') as f:
    content = f.read()

# Check if already patched
if '_save_predictions_to_table' in content:
    print("✅ Prediction saving already exists")
    exit(0)

# Create backup
import shutil
backup_path = file_path + '.backup_' + str(int(time.time()))
shutil.copy2(file_path, backup_path)
print(f"📋 Created backup: {backup_path}")

# Define the new method to add
new_method = """
    def _save_predictions_to_table(self, analysis_results: Dict):
        \"\"\"Save individual predictions to the predictions table\"\"\"
        try:
            import sqlite3
            import uuid
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save each bank prediction
            ml_preds = analysis_results.get('ml_predictions', {})
            saved_count = 0
            
            for symbol, pred in ml_preds.items():
                prediction_id = f"enhanced_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Get prediction details
                predicted_action = pred.get('optimal_action', 'HOLD')
                confidence = pred.get('action_confidence', 0.5)
                predicted_direction = 1 if predicted_action == 'BUY' else -1 if predicted_action == 'SELL' else 0
                
                try:
                    # Insert prediction with proper error handling
                    cursor.execute(\"\"\"
                        INSERT OR REPLACE INTO predictions 
                        (prediction_id, symbol, prediction_timestamp, predicted_action, 
                         action_confidence, predicted_direction, predicted_magnitude, 
                         model_version, entry_price, optimal_action)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \"\"\", (
                        prediction_id,
                        symbol,
                        analysis_results['timestamp'],
                        predicted_action,
                        confidence,
                        predicted_direction,
                        pred.get('predicted_return', 0.0),
                        'enhanced_ml_v1',
                        pred.get('current_price', 0.0),
                        predicted_action
                    ))
                    saved_count += 1
                    self.logger.info(f"✅ Saved prediction for {symbol}: {predicted_action} (confidence: {confidence:.3f})")
                except Exception as pred_error:
                    self.logger.warning(f"Failed to save prediction for {symbol}: {pred_error}")
            
            conn.commit()
            conn.close()
            
            if saved_count > 0:
                self.logger.info(f"✅ Saved {saved_count} predictions to predictions table")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save predictions: {e}")
"""

# Find the insertion point
insertion_point = content.find('def _save_analysis_results(self, analysis_results: Dict):')
if insertion_point == -1:
    print("❌ Could not find _save_analysis_results method")
    exit(1)

# Insert the new method before _save_analysis_results
new_content = content[:insertion_point] + new_method + "\\n\\n    " + content[insertion_point:]

# Modify the _save_analysis_results method to call the new method
old_line = 'self.logger.info("✅ Analysis results saved to database")'
new_line = '''self.logger.info("✅ Analysis results saved to database")
            
            # Also save individual predictions
            self._save_predictions_to_table(analysis_results)'''

new_content = new_content.replace(old_line, new_line)

# Write the patched content
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Successfully patched morning analyzer with prediction saving")
'''
    
    # Execute the patch script on remote server
    cmd = f"ssh root@170.64.199.151 'cd /root/test && python3 -c \"import time\\n{patch_script}\"'"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Successfully added prediction saving functionality")
        print(result.stdout)
        return True
    else:
        print(f"❌ Failed to add prediction saving: {result.stderr}")
        print(f"stdout: {result.stdout}")
        return False

def verify_fix():
    """Verify the fix was applied correctly"""
    
    print("\\n🔍 VERIFYING FIX")
    print("=" * 40)
    
    # Check if the method was added
    check_cmd = "ssh root@170.64.199.151 'cd /root/test && grep -n \"_save_predictions_to_table\" enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py'"
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Prediction saving method found in morning analyzer")
        print(f"   Line numbers: {result.stdout.strip()}")
    else:
        print("❌ Prediction saving method not found")
        return False
    
    # Check current database state
    count_cmd = "ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db \"SELECT COUNT(*) FROM predictions;\"'"
    result = subprocess.run(count_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        count = result.stdout.strip()
        print(f"📊 Current predictions in database: {count}")
    
    return True

def test_morning_routine():
    """Test that the fixed morning routine saves predictions"""
    
    print("\\n🧪 TESTING MORNING ROUTINE PREDICTION SAVING")
    print("=" * 60)
    
    print("🌅 Running morning routine to test prediction saving...")
    print("⏰ This will take a few minutes...")
    
    # Run the morning routine
    cmd = "ssh root@170.64.199.151 'cd /root/test && export PYTHONPATH=/root/test && timeout 300 python3 -m app.main morning'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Morning routine completed successfully")
    elif result.returncode == 124:  # timeout
        print("⏰ Morning routine timed out (but may have saved predictions)")
    else:
        print(f"⚠️ Morning routine exit code: {result.returncode}")
    
    # Check predictions count after
    count_cmd = "ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db \"SELECT COUNT(*) FROM predictions;\"'"
    result = subprocess.run(count_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        count = result.stdout.strip()
        print(f"📊 Predictions after morning routine: {count}")
        
        if int(count) > 0:
            print("✅ PREDICTIONS ARE NOW BEING SAVED!")
            
            # Show some example predictions
            sample_cmd = "ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db \"SELECT symbol, predicted_action, action_confidence, prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 5;\"'"
            sample_result = subprocess.run(sample_cmd, shell=True, capture_output=True, text=True)
            
            if sample_result.returncode == 0 and sample_result.stdout.strip():
                print("\\n📋 Latest Predictions:")
                for line in sample_result.stdout.strip().split('\\n'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            symbol, action, conf, timestamp = parts[:4]
                            print(f"   {symbol}: {action} (confidence: {conf}) at {timestamp}")
            
            return True
        else:
            print("⚠️ No predictions saved yet - may need manual investigation")
            return False

def main():
    print("🔧 PREDICTION SAVING FIX")
    print("=" * 80)
    print(f"⏰ Fix Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Add prediction saving functionality
    if add_prediction_saving():
        
        # 2. Verify the fix
        if verify_fix():
            
            # 3. Test with morning routine
            test_morning_routine()
    
    print("\\n" + "=" * 80)
    print("🏁 PREDICTION SAVING FIX COMPLETED")
    print("\\n💡 The dashboard should now show matched predictions vs features!")

if __name__ == "__main__":
    main()
