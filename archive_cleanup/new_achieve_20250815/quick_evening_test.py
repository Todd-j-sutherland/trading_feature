#!/usr/bin/env python3
"""
Quick Evening Routine Test

Test just the training data portion that was failing.
"""

import sys
import logging
sys.path.append('.')

# Set up logging to capture warnings
logging.basicConfig(level=logging.INFO)

def test_training_data_warnings():
    """Test the training data access that was causing warnings"""
    print("🧪 Testing Enhanced Training Data Access")
    print("=" * 50)
    
    try:
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        
        pipeline = EnhancedMLTrainingPipeline()
        print(f"✅ Pipeline initialized")
        print(f"✅ Database path: {pipeline.db_path}")
        
        # Test the exact method that was failing
        X, y = pipeline.prepare_enhanced_training_dataset(min_samples=50)
        
        if X is not None:
            print(f"✅ SUCCESS: Training data loaded with {len(X)} samples")
            print(f"✅ This should eliminate the 'Insufficient enhanced training data: 0 samples' warning")
            print(f"✅ Features available: {len(X.columns)}")
            print(f"✅ Target variables: {list(y.keys())}")
            return True
        else:
            print("❌ FAILED: No training data returned")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_file():
    """Test the metadata file that was missing"""
    import os
    
    metadata_path = "data/ml_models/models/current_enhanced_metadata.json"
    print(f"\n🔍 Testing Metadata File")
    print(f"Path: {metadata_path}")
    print(f"Exists: {os.path.exists(metadata_path)}")
    
    if os.path.exists(metadata_path):
        print("✅ This should eliminate the 'No such file or directory: current_enhanced_metadata.json' errors")
        return True
    else:
        print("❌ Metadata file still missing")
        return False

if __name__ == "__main__":
    print("🚀 Quick Evening Routine Issue Test")
    print("Testing the specific issues found in output.log")
    print()
    
    training_ok = test_training_data_warnings()
    metadata_ok = test_metadata_file()
    
    print("\n📊 SUMMARY:")
    print(f"Training Data Issue: {'✅ FIXED' if training_ok else '❌ STILL BROKEN'}")
    print(f"Metadata File Issue: {'✅ FIXED' if metadata_ok else '❌ STILL BROKEN'}")
    
    if training_ok and metadata_ok:
        print("\n🎉 ALL CRITICAL ISSUES HAVE BEEN RESOLVED!")
        print("The evening routine should now work without the major errors.")
    else:
        print("\n⚠️ Some issues remain to be fixed.")