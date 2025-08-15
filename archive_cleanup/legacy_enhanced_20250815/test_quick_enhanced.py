#!/usr/bin/env python3
"""
Quick test of enhanced ML components
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
from datetime import datetime

def test_enhanced_pipeline():
    """Test the enhanced ML pipeline with fallback"""
    print("🧪 Testing Enhanced ML Pipeline...")
    
    try:
        # Initialize pipeline
        pipeline = EnhancedMLTrainingPipeline()
        print("✅ Pipeline initialized")
        
        # Test fallback prediction (no models needed)
        mock_features = {
            'rsi': 65,
            'momentum_score': 15,
            'current_price': 100.0,
            'volume_ratio': 1.2
        }
        
        mock_sentiment = {
            'overall_sentiment': 0.3,
            'confidence': 0.8,
            'news_count': 5
        }
        
        prediction = pipeline._fallback_prediction(mock_features, mock_sentiment, 'CBA.AX')
        print("✅ Fallback prediction generated:")
        print(f"   Action: {prediction.get('optimal_action', 'UNKNOWN')}")
        print(f"   Confidence: {prediction.get('confidence_scores', {}).get('average', 0):.2f}")
        print(f"   Method: {prediction.get('prediction_method', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_pipeline()
    print(f"\n{'✅ All tests passed!' if success else '❌ Tests failed!'}")
