#!/usr/bin/env python3
"""
Preview of Phase 1 ML Integration
Hybrid approach: ML predictions + rule-based confidence
"""

import pickle
import numpy as np

class MLEnhancedPredictor:
    def __init__(self):
        self.load_models()
    
    def load_models(self):
        """Load trained ML models"""
        try:
            with open("models/current_direction_model.pkl", "rb") as f:
                self.direction_model = pickle.load(f)
            
            with open("models/current_magnitude_model.pkl", "rb") as f:
                self.magnitude_model = pickle.load(f)
            
            print("✅ ML models loaded successfully")
            return True
        except Exception as e:
            print("❌ Error loading models:", e)
            return False
    
    def predict_with_ml(self, feature_vector_str):
        """Make predictions using ML models"""
        try:
            # Parse feature vector
            features = [float(x) for x in feature_vector_str.split(",")]
            
            # Convert to ML model format (9 features expected)
            if len(features) >= 9:
                ml_features = np.array([features[:9]])  # Use first 9 features
                
                # ML Predictions
                ml_direction = self.direction_model.predict(ml_features)[0]
                ml_magnitude = self.magnitude_model.predict(ml_features)[0]
                
                # Convert ML output to trading actions
                if ml_direction == 1:
                    ml_action = "BUY"
                elif ml_direction == -1:
                    ml_action = "SELL"
                else:
                    ml_action = "HOLD"
                
                return {
                    "ml_action": ml_action,
                    "ml_direction": ml_direction,
                    "ml_magnitude": ml_magnitude,
                    "ml_confidence": min(0.95, 0.6 + abs(ml_magnitude) * 2)
                }
            else:
                return None
                
        except Exception as e:
            print("ML prediction error:", e)
            return None

# Demo with current data
if __name__ == "__main__":
    predictor = MLEnhancedPredictor()
    
    # Test with MQG.AX data (highest confidence stock)
    feature_vector = "77.8,75.0,222.14,216.98,225.14,0.73,0.72,65.0,45.0"
    
    result = predictor.predict_with_ml(feature_vector)
    if result:
        print("🤖 ML Prediction for MQG.AX:")
        print("   Action:", result["ml_action"])
        print("   Direction:", result["ml_direction"])
        print("   Magnitude:", round(result["ml_magnitude"], 4))
        print("   ML Confidence:", round(result["ml_confidence"], 3))
        
        print("\n📊 Compare with current rule-based:")
        print("   Rule Action: BUY")
        print("   Rule Confidence: 0.950")
        print("   Rule Magnitude: 0.0125")
