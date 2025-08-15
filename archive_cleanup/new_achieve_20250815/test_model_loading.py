#!/usr/bin/env python3
"""
Test script to diagnose model loading issues on remote server
"""

import os
import sys

def test_model_loading():
    """Test if models can be loaded properly"""
    print("=== Model Loading Diagnostic ===")
    
    # Add the app directory to Python path
    sys.path.append('/root/test/app')
    sys.path.append('/root/test')
    
    try:
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        print("✅ Successfully imported EnhancedMLTrainingPipeline")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return
    
    # Initialize pipeline
    try:
        pipeline = EnhancedMLTrainingPipeline()
        print(f"✅ Pipeline initialized")
        print(f"   Models directory: {pipeline.models_dir}")
        print(f"   Working directory: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return
    
    # Check model files
    direction_path = os.path.join(pipeline.models_dir, 'current_direction_model.pkl')
    magnitude_path = os.path.join(pipeline.models_dir, 'current_magnitude_model.pkl')
    metadata_path = os.path.join(pipeline.models_dir, 'current_enhanced_metadata.json')
    
    print(f"\n=== File Existence Check ===")
    print(f"Direction model: {direction_path}")
    print(f"  Exists: {os.path.exists(direction_path)}")
    print(f"Magnitude model: {magnitude_path}")
    print(f"  Exists: {os.path.exists(magnitude_path)}")
    print(f"Metadata: {metadata_path}")
    print(f"  Exists: {os.path.exists(metadata_path)}")
    
    # Test prediction
    print(f"\n=== Prediction Test ===")
    test_features = {
        'rsi': 45.0,
        'momentum_score': 0.1,
        'price_change_pct': 0.02
    }
    
    test_sentiment = {
        'overall_sentiment': 0.3,
        'confidence': 0.7
    }
    
    try:
        result = pipeline.predict_enhanced(test_sentiment, 'CBA')
        print(f"✅ Prediction successful")
        print(f"   Action: {result.get('optimal_action', 'unknown')}")
        print(f"   Confidence: {result.get('confidence_scores', {}).get('average', 'unknown')}")
        print(f"   Has error: {'error' in result}")
        print(f"   Has timestamp: {'timestamp' in result}")
        print(f"   Has direction_predictions: {'direction_predictions' in result}")
        print(f"   Has magnitude_predictions: {'magnitude_predictions' in result}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
        elif 'direction_predictions' in result:
            print("✅ Using trained ML models (has model output structure)")
            print(f"   Direction predictions: {result.get('direction_predictions')}")
            print(f"   Magnitude predictions: {result.get('magnitude_predictions')}")
            print(f"   Confidence scores: {result.get('confidence_scores')}")
        else:
            print("⚠️  Likely using fallback prediction (missing model structure)")
            
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_loading()
