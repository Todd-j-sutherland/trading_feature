#!/usr/bin/env python3
"""
ML Prediction API Fix
Patches the API server to handle enhanced ML prediction errors gracefully
"""

import os
import sys

def create_enhanced_ml_wrapper():
    """Create a wrapper for the enhanced ML prediction to handle errors"""
    wrapper_content = '''
"""
Enhanced ML Prediction Wrapper
Provides safe fallback for ML predictions with proper error handling
"""

def safe_enhanced_ml_predict(sentiment_data, symbol):
    """
    Safely call enhanced ML prediction with proper error handling
    
    Args:
        sentiment_data: Dictionary with sentiment analysis data
        symbol: Stock symbol (e.g., 'CBA.AX')
        
    Returns:
        Dictionary with standardized prediction format
    """
    try:
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        enhanced_pipeline = EnhancedMLTrainingPipeline()
        
        # Ensure sentiment_data has required structure
        safe_sentiment_data = {
            'overall_sentiment': sentiment_data.get('sentiment_score', 0.0),
            'confidence': sentiment_data.get('confidence', 0.5),
            'news_count': sentiment_data.get('news_count', 0),
            'reddit_sentiment': sentiment_data.get('reddit_sentiment', 0.0),
            'event_score': sentiment_data.get('event_score', 0.0),
            'sentiment_components': {},
            'timestamp': sentiment_data.get('timestamp', '2025-07-30T00:00:00')
        }
        
        # Call enhanced prediction
        result = enhanced_pipeline.predict_enhanced(safe_sentiment_data, symbol)
        
        # Handle different response types
        if result is None:
            return {"error": "Enhanced ML returned None"}
        
        if isinstance(result, (int, float)):
            return {
                "prediction": float(result),
                "confidence": 0.5,
                "method": "enhanced_scalar"
            }
        
        if isinstance(result, dict):
            if "error" in result:
                return result
            
            # Extract prediction value
            prediction = 0.0
            confidence = 0.5
            
            # Try various prediction keys
            for key in ['predicted_direction', 'direction', 'prediction', 'sentiment_score', 'overall_sentiment']:
                if key in result:
                    prediction = float(result[key])
                    break
            
            # Try direction predictions
            if prediction == 0.0 and 'direction_predictions' in result:
                dir_pred = result['direction_predictions']
                if isinstance(dir_pred, dict):
                    prediction = dir_pred.get('1h', dir_pred.get('1d', 0.0))
            
            # Try confidence
            for key in ['confidence', 'avg_confidence', 'overall_confidence']:
                if key in result:
                    confidence = float(result[key])
                    break
            
            # Try confidence scores
            if confidence == 0.5 and 'confidence_scores' in result:
                conf_scores = result['confidence_scores']
                if isinstance(conf_scores, dict):
                    confidence = conf_scores.get('average', conf_scores.get('1h', 0.5))
            
            return {
                "prediction": prediction,
                "confidence": confidence,
                "method": "enhanced_dict",
                "original_keys": list(result.keys())
            }
        
        return {"error": f"Unexpected result type: {type(result)}"}
        
    except ImportError as e:
        return {"error": f"Enhanced ML module not available: {e}"}
    except Exception as e:
        return {"error": f"Enhanced ML prediction failed: {e}"}

def simple_fallback_predict(ml_features, symbol):
    """
    Simple fallback prediction using basic sentiment and technical indicators
    
    Args:
        ml_features: Dictionary with ML features
        symbol: Stock symbol
        
    Returns:
        Dictionary with prediction and confidence
    """
    try:
        # Extract key features
        sentiment_score = ml_features.get('sentiment_score', 0.0)
        rsi = ml_features.get('rsi', 50.0)
        price_change = ml_features.get('price_change_pct', 0.0)
        volume_ratio = ml_features.get('volume_ratio', 1.0)
        
        # Simple rule-based prediction
        # Combine sentiment and technical indicators
        technical_signal = (rsi - 50) / 50  # Normalize RSI to -1 to 1
        momentum_signal = min(max(price_change / 5, -1), 1)  # Normalize price change
        volume_signal = min(max((volume_ratio - 1) * 2, -1), 1)  # Volume above/below normal
        
        # Weighted combination
        prediction = (
            sentiment_score * 0.4 +
            technical_signal * 0.3 +
            momentum_signal * 0.2 +
            volume_signal * 0.1
        )
        
        # Calculate confidence based on signal alignment
        signals = [abs(sentiment_score), abs(technical_signal), abs(momentum_signal)]
        confidence = min(max(sum(signals) / len(signals), 0.3), 0.9)
        
        return {
            "prediction": float(prediction),
            "confidence": float(confidence),
            "method": "simple_fallback",
            "components": {
                "sentiment": sentiment_score,
                "technical": technical_signal,
                "momentum": momentum_signal,
                "volume": volume_signal
            }
        }
        
    except Exception as e:
        return {
            "prediction": 0.0,
            "confidence": 0.5,
            "method": "error_fallback",
            "error": str(e)
        }
'''
    
    wrapper_path = "helpers/enhanced_ml_wrapper.py"
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    
    print(f"✅ Enhanced ML wrapper created at {wrapper_path}")

def main():
    """Create the ML prediction wrapper"""
    print("🤖 Creating Enhanced ML Prediction Wrapper...")
    print("=" * 50)
    
    try:
        create_enhanced_ml_wrapper()
        
        print("\n✅ ML prediction wrapper created successfully!")
        print("\nTo use this wrapper in your API server:")
        print("1. Import: from helpers.enhanced_ml_wrapper import safe_enhanced_ml_predict")
        print("2. Replace enhanced ML calls with safe_enhanced_ml_predict()")
        print("3. The wrapper handles all error cases and provides consistent output")
        
    except Exception as e:
        print(f"❌ Error creating wrapper: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
