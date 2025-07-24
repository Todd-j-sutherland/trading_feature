#!/usr/bin/env python3
"""
ML Models Diagnostic and Test Script

This script tests the ML pipeline functionality and training status
to ensure models are properly loaded and can make predictions.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_ml_models():
    """Test ML models functionality"""
    print("🔬 ML Models Diagnostic Report")
    print("=" * 50)
    
    try:
        from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
        
        # Initialize pipeline
        print("1️⃣ Initializing ML Pipeline...")
        pipeline = EnhancedMLPipeline()
        print(f"   ✅ Pipeline initialized with {len(pipeline.models)} models")
        
        # Test model loading
        print("\n2️⃣ Testing Model Loading...")
        loaded_models = []
        failed_models = []
        
        for name in pipeline.models.keys():
            model, scaler = pipeline._load_model(name)
            if model is not None:
                loaded_models.append(name)
                print(f"   ✅ {name}: Loaded successfully (type: {type(model).__name__})")
            else:
                failed_models.append(name)
                print(f"   ❌ {name}: Failed to load")
        
        print(f"\n   📊 Summary: {len(loaded_models)}/{len(pipeline.models)} models loaded")
        
        if not loaded_models:
            print("   🚨 ERROR: No models loaded! Training may be required.")
            return False
        
        # Test predictions
        print("\n3️⃣ Testing Predictions...")
        test_data = {
            'CBA': {
                'sentiment_score': 0.65,
                'confidence': 0.8,
                'news_count': 5,
                'overall_sentiment': 0.65,
                'signal': 'BUY'
            }
        }
        
        predictions = pipeline.predict(test_data)
        
        if 'error' in predictions:
            print(f"   ❌ Prediction failed: {predictions['error']}")
            return False
        else:
            print(f"   ✅ Predictions successful!")
            print(f"   📈 Ensemble prediction: {predictions.get('ensemble_prediction', 'N/A')}")
            print(f"   🎯 Confidence: {predictions.get('ensemble_confidence', 'N/A'):.3f}")
            print(f"   🔢 Features used: {predictions.get('feature_count', 'N/A')}")
        
        # Check training samples
        print("\n4️⃣ Checking Training Data...")
        try:
            # Check if training database exists
            training_db = Path('data/ml_models/training_data.db')
            if training_db.exists():
                print(f"   ✅ Training database found: {training_db.stat().st_size} bytes")
                
                # Try to get training count (simplified check)
                import sqlite3
                conn = sqlite3.connect(training_db)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if tables:
                    # Try to count rows in first table
                    table_name = tables[0][0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   📊 Training samples in {table_name}: {count}")
                else:
                    print("   ⚠️ No tables found in training database")
                
                conn.close()
            else:
                print("   ❌ Training database not found")
        except Exception as e:
            print(f"   ⚠️ Could not check training data: {e}")
        
        print("\n🎉 ML Models Status: OPERATIONAL")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   💡 Ensure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_locations():
    """Check if model files are in the correct locations"""
    print("\n📁 File Location Check")
    print("=" * 30)
    
    base_path = Path('data/ml_models')
    required_files = [
        'feature_columns.json',
        'random_forest_model.pkl',
        'random_forest_scaler.pkl',
        'gradient_boosting_model.pkl', 
        'gradient_boosting_scaler.pkl',
        'neural_network_model.pkl',
        'neural_network_scaler.pkl',
        'xgboost_model.pkl',
        'xgboost_scaler.pkl'
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - MISSING")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n🚨 Missing {len(missing_files)} required files!")
        print("💡 Run the model conversion script to fix this.")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files found!")
        return True

if __name__ == "__main__":
    print("🚀 Starting ML Models Diagnostic...")
    
    # Set working directory
    os.chdir(project_root)
    
    # Check files first
    files_ok = check_file_locations()
    
    # Test ML functionality
    ml_ok = test_ml_models()
    
    print("\n" + "=" * 50)
    if files_ok and ml_ok:
        print("🎉 ALL TESTS PASSED - ML Models are ready!")
        print("🚀 The dashboard should now show ML predictions.")
    else:
        print("❌ SOME TESTS FAILED - ML Models need attention.")
        print("💡 Check the error messages above for solutions.")
    
    print("=" * 50)
