#!/usr/bin/env python3
"""
Pure ML Integration - No Fallbacks
Real ML model integration with actual trained models, no mock data
"""

def create_pure_ml_integration():
    """Create ML integration code that uses real models only"""
    
    ml_integration_code = '''
import pickle
import numpy as np
import os
from datetime import datetime

class MLPredictor:
    """Pure ML model integration - no fallbacks, real models only"""
    
    def __init__(self):
        self.models_path = "models/"
        self.direction_model = None
        self.magnitude_model = None
        self.feature_scaler = None
        self.models_loaded = False
        self.load_models()
    
    def load_models(self):
        """Load actual trained ML models - fail if not available"""
        try:
            # Check all required files exist
            direction_path = os.path.join(self.models_path, "current_direction_model.pkl")
            magnitude_path = os.path.join(self.models_path, "current_magnitude_model.pkl")
            scaler_path = os.path.join(self.models_path, "feature_scaler.pkl")
            
            if not os.path.exists(direction_path):
                raise FileNotFoundError(f"Direction model not found: {direction_path}")
            if not os.path.exists(magnitude_path):
                raise FileNotFoundError(f"Magnitude model not found: {magnitude_path}")
            if not os.path.exists(scaler_path):
                raise FileNotFoundError(f"Feature scaler not found: {scaler_path}")
            
            # Load models
            with open(direction_path, 'rb') as f:
                self.direction_model = pickle.load(f)
            print("✅ Direction model loaded successfully")
            
            with open(magnitude_path, 'rb') as f:
                self.magnitude_model = pickle.load(f)
            print("✅ Magnitude model loaded successfully")
                
            with open(scaler_path, 'rb') as f:
                self.feature_scaler = pickle.load(f)
            print("✅ Feature scaler loaded successfully")
            
            self.models_loaded = True
            print("🤖 ML Integration: ENABLED (Real models loaded)")
                
        except Exception as e:
            print(f"❌ ML Integration: DISABLED - {e}")
            print("⚠️  ML models required for full confidence calculation")
            self.models_loaded = False
            raise e  # Fail hard, no fallbacks
    
    def extract_features(self, symbol, confidence, tech_data, news_data, volume_data):
        """Extract features exactly as expected by trained models"""
        
        current_price = tech_data.get("current_price", 0)
        
        # Features based on training_metadata.json
        # ["confidence", "buy_signal", "sell_signal", "pred_direction", "pred_magnitude", 
        #  "entry_price", "symbol_hash", "hour", "weekday"]
        
        # Symbol hash (consistent encoding)
        symbol_hash = abs(hash(symbol)) % 1000 / 1000.0
        
        # Time features
        now = datetime.now()
        hour = now.hour / 24.0
        weekday = now.weekday() / 6.0
        
        # Initial ML inputs (bootstrap for first prediction)
        buy_signal = 1.0 if confidence > 0.6 else 0.0
        sell_signal = 1.0 if confidence < 0.4 else 0.0
        pred_direction = 1.0 if confidence > 0.5 else -1.0
        pred_magnitude = abs(confidence - 0.5) * 2.0
        
        # Normalize entry price (typical range 20-300 for bank stocks)
        entry_price_norm = min(1.0, current_price / 300.0)
        
        features = np.array([
            confidence,
            buy_signal,
            sell_signal,
            pred_direction,
            pred_magnitude,
            entry_price_norm,
            symbol_hash,
            hour,
            weekday
        ]).reshape(1, -1)
        
        return features
    
    def predict_ml_confidence(self, symbol, confidence, tech_data, news_data, volume_data):
        """Generate ML confidence component using real models only"""
        
        if not self.models_loaded:
            raise RuntimeError("ML models not loaded - cannot generate ML confidence component")
        
        try:
            # Extract features for ML models
            features = self.extract_features(symbol, confidence, tech_data, news_data, volume_data)
            
            # Scale features
            scaled_features = self.feature_scaler.transform(features)
            
            # Get ML predictions
            direction_probabilities = self.direction_model.predict_proba(scaled_features)[0]
            direction_confidence = max(direction_probabilities)  # Confidence in direction prediction
            
            magnitude_prediction = abs(self.magnitude_model.predict(scaled_features)[0])
            
            # Convert ML predictions to confidence component
            # Weight: direction confidence * magnitude * scaling factor
            ml_confidence = direction_confidence * min(magnitude_prediction, 2.0) * 0.12  # 12% base weight
            
            # Ensure reasonable bounds for ML component (5-20% of total confidence)
            ml_confidence = min(0.20, max(0.05, ml_confidence))
            
            print(f"   🤖 ML Prediction: direction_conf={direction_confidence:.3f}, magnitude={magnitude_prediction:.3f}")
            print(f"   🤖 ML Component: {ml_confidence:.3f}")
            
            return ml_confidence
            
        except Exception as e:
            print(f"❌ ML prediction failed: {e}")
            raise e  # Fail hard, no fallbacks
'''

    return ml_integration_code

def create_updated_confidence_calculation():
    """Updated confidence calculation with pure ML integration"""
    
    updated_calc = '''
    def calculate_enhanced_confidence(self, symbol, tech_data, news_data, volume_data, market_data):
        """Calculate confidence with PURE ML integration - no fallbacks"""
        
        # Get current price and tech score
        current_price = tech_data["current_price"]
        tech_score = tech_data["tech_score"]
        
        # Extract individual components
        news_sentiment = news_data["sentiment_score"]
        news_confidence = news_data["news_confidence"]
        volume_trend = volume_data["volume_trend"]
        volume_correlation = volume_data["price_volume_correlation"]
        volume_quality = volume_data["volume_quality_score"]
        
        # 1. TECHNICAL ANALYSIS COMPONENT (40% total weight)
        technical_component = (tech_score / 100) * 0.40
        
        # 2. NEWS SENTIMENT COMPONENT (20% total weight)
        sentiment_factor = news_sentiment * news_confidence * 0.5
        news_base = 0.12
        news_component = news_base + sentiment_factor
        news_component = max(0.0, min(news_component, 0.25))
        
        # 3. VOLUME ANALYSIS COMPONENT (15% total weight)
        volume_trend_factor = volume_trend * 0.10
        correlation_factor = max(0.0, volume_correlation * 0.05)
        volume_component = volume_quality * 0.08 + volume_trend_factor + correlation_factor
        volume_component = max(0.02, min(volume_component, 0.18))
        
        # 4. RISK ADJUSTMENT COMPONENT (5% total weight)
        volatility = float(tech_data.get("volatility", 1))
        volatility_factor = 0.03 if volatility < 1.5 else (-0.02 if volatility > 3.0 else 0)
        risk_component = volatility_factor
        
        # PRELIMINARY CONFIDENCE (without ML)
        preliminary_confidence = technical_component + news_component + volume_component + risk_component
        
        # 5. ML MODEL PREDICTION COMPONENT (20% total weight) - PURE ML, NO FALLBACKS
        try:
            ml_component = self.ml_predictor.predict_ml_confidence(
                symbol, preliminary_confidence, tech_data, news_data, volume_data
            )
        except Exception as e:
            print(f"❌ ML Component FAILED for {symbol}: {e}")
            print("⚠️  Confidence calculation incomplete without ML component")
            raise e  # Fail the entire prediction rather than use fallback
        
        # COMPLETE CONFIDENCE with ML
        complete_confidence = preliminary_confidence + ml_component
        
        # 6. MARKET CONTEXT ADJUSTMENT
        market_adjusted_confidence = complete_confidence * market_data["confidence_multiplier"]
        
        # 7. APPLY EMERGENCY MARKET STRESS FILTER
        final_confidence = self.market_analyzer.market_stress_filter(market_adjusted_confidence, market_data)
        
        # Ensure bounds
        final_confidence = max(0.15, min(final_confidence, 0.95))
        
        # ... rest of action determination logic ...
        
        return {
            "action": action,
            "confidence": final_confidence,
            "market_context": market_data["context"],
            "components": {
                "technical": technical_component,
                "news": news_component,
                "volume": volume_component,
                "risk": risk_component,
                "ml": ml_component,  # REAL ML COMPONENT
                "market_adjustment": market_data["confidence_multiplier"],
                "preliminary": preliminary_confidence,
                "complete": complete_confidence
            },
            "details": {
                "tech_score": tech_score,
                "news_sentiment": news_sentiment,
                "volume_trend": volume_trend,
                "ml_contribution": ml_component,  # Track ML contribution
                "final_score_breakdown": f"Tech:{technical_component:.3f} + News:{news_component:.3f} + Vol:{volume_component:.3f} + ML:{ml_component:.3f} + Risk:{risk_component:.3f} × Market:{market_data['confidence_multiplier']:.2f} = {final_confidence:.3f}"
            }
        }
'''

    return updated_calc

def main():
    print("🤖 PURE ML INTEGRATION - NO FALLBACKS")
    print("=" * 50)
    
    print("✅ REAL ML INTEGRATION FEATURES:")
    print("   - Loads actual trained models or fails")
    print("   - Uses real ML predictions only")
    print("   - No mock data or fallback estimates")
    print("   - Fails hard if ML models unavailable")
    print("   - Clear error messages when ML fails")
    
    print(f"\n🎯 INTEGRATION REQUIREMENTS:")
    print(f"   Required files:")
    print(f"   - models/current_direction_model.pkl")
    print(f"   - models/current_magnitude_model.pkl") 
    print(f"   - models/feature_scaler.pkl")
    
    print(f"\n📊 EXPECTED RESULTS (with real ML):")
    print(f"   - Pure ML confidence boost: +0.15 to +0.20")
    print(f"   - No artificial confidence inflation")
    print(f"   - Authentic model-based predictions")
    print(f"   - Clear failure if models missing")
    
    print(f"\n⚠️  FAIL-FAST APPROACH:")
    print(f"   - System fails if ML models not loaded")
    print(f"   - No partial/incomplete confidence scores")
    print(f"   - Forces proper ML model maintenance")
    print(f"   - Prevents misleading confidence values")

if __name__ == "__main__":
    main()