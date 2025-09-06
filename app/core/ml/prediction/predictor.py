"""
Price prediction module
Uses ML models to predict future price movements
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

from ....config.settings import Settings

logger = logging.getLogger(__name__)

class PricePrediction:
    """Represents a price prediction"""
    
    def __init__(
        self,
        symbol: str,
        current_price: float,
        predicted_price: float,
        prediction_horizon_days: int,
        confidence: float,
        timestamp: datetime,
        model_used: str,
        supporting_features: Optional[Dict] = None
    ):
        self.symbol = symbol
        self.current_price = current_price
        self.predicted_price = predicted_price
        self.prediction_horizon_days = prediction_horizon_days
        self.confidence = confidence
        self.timestamp = timestamp
        self.model_used = model_used
        self.supporting_features = supporting_features or {}
        
        # Extract prediction_details if present in supporting_features
        self.prediction_details = self.supporting_features.get("prediction_details", {})
        
        # Calculate derived metrics
        self.price_change = predicted_price - current_price
        self.price_change_pct = (self.price_change / current_price) * 100 if current_price > 0 else 0
        self.direction = "UP" if self.price_change > 0 else "DOWN" if self.price_change < 0 else "FLAT"

class PricePredictor:
    """
    ML-based price prediction system
    """
    
    def __init__(self):
        self.prediction_history = []
        self.model_performance = {}
        
    def predict_price(
        self,
        symbol: str,
        current_price: float,
        features: Dict,
        horizon_days: int = 5,
        model_name: str = "ensemble"
    ) -> PricePrediction:
        """
        Predict future price for a symbol
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            features: Feature vector for prediction
            horizon_days: Prediction horizon in days
            model_name: Model to use for prediction
            
        Returns:
            PricePrediction object
        """
        try:
            # For now, use a simple heuristic-based prediction
            # In a real implementation, this would use trained ML models
            predicted_price, confidence = self._simple_prediction(
                current_price, features, horizon_days
            )
            
            prediction = PricePrediction(
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                prediction_horizon_days=horizon_days,
                confidence=confidence,
                timestamp=datetime.now(),
                model_used=model_name,
                supporting_features=features
            )
            
            # Store in history
            self.prediction_history.append(prediction)
            
            logger.info(f"Predicted {symbol}: ${current_price:.2f} -> ${predicted_price:.2f} "
                       f"({prediction.price_change_pct:+.2f}%) in {horizon_days} days")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {e}")
            # Return neutral prediction on error
            return PricePrediction(
                symbol=symbol,
                current_price=current_price,
                predicted_price=current_price,
                prediction_horizon_days=horizon_days,
                confidence=0.5,
                timestamp=datetime.now(),
                model_used="error_fallback",
                supporting_features={'error': str(e)}
            )
    
    def _simple_prediction(
        self,
        current_price: float,
        features: Dict,
        horizon_days: int
    ) -> Tuple[float, float]:
        """
        Simple heuristic-based prediction
        This would be replaced with actual ML model predictions
        """
        
        # Extract key features
        sentiment_score = features.get('sentiment_score', 50)
        technical_score = features.get('technical_score', 50) 
        volatility = features.get('volatility', 0.02)
        volume_ratio = features.get('volume_ratio', 1.0)
        market_trend = features.get('market_trend', 0)
        
        # Calculate base direction and magnitude
        sentiment_impact = (sentiment_score - 50) / 100  # -0.5 to +0.5
        technical_impact = (technical_score - 50) / 100   # -0.5 to +0.5
        
        # Combine impacts with weights
        combined_impact = (
            sentiment_impact * 0.4 +
            technical_impact * 0.6
        )
        
        # Adjust for time horizon (longer horizons = less certainty)
        time_decay = 1.0 / (1.0 + 0.1 * horizon_days)
        adjusted_impact = combined_impact * time_decay
        
        # Calculate price change
        base_change_pct = adjusted_impact * 0.1  # Max 10% change
        
        # Add volatility consideration
        volatility_factor = min(volatility * 5, 0.5)  # Cap at 50%
        
        # Volume confirmation
        volume_boost = min((volume_ratio - 1.0) * 0.02, 0.05) if volume_ratio > 1.0 else 0
        
        total_change_pct = base_change_pct + volume_boost
        
        # Apply market trend influence
        market_influence = market_trend * 0.3 * time_decay
        total_change_pct += market_influence
        
        # Calculate predicted price
        predicted_price = current_price * (1 + total_change_pct)
        
        # Calculate confidence based on feature quality
        confidence = self._calculate_confidence(features, abs(total_change_pct))
        
        return predicted_price, confidence
    
    def _calculate_confidence(self, features: Dict, predicted_change: float) -> float:
        """Calculate prediction confidence based on feature quality"""
        
        base_confidence = 0.6
        
        # Higher confidence for stronger signals
        signal_strength = features.get('sentiment_confidence', 0.5)
        base_confidence += signal_strength * 0.2
        
        # Lower confidence for extreme predictions
        if predicted_change > 0.15:  # >15% change
            base_confidence -= 0.2
        
        # Feature completeness bonus
        required_features = ['sentiment_score', 'technical_score', 'volatility']
        completeness = sum(1 for f in required_features if f in features) / len(required_features)
        base_confidence += completeness * 0.1
        
        # Volume confirmation bonus
        if features.get('volume_ratio', 1.0) > 1.2:
            base_confidence += 0.1
        
        return max(0.1, min(0.95, base_confidence))
    
    def predict_portfolio(
        self,
        portfolio_data: Dict[str, Dict],
        horizon_days: int = 5
    ) -> Dict[str, PricePrediction]:
        """Predict prices for a portfolio of symbols"""
        
        predictions = {}
        
        for symbol, data in portfolio_data.items():
            try:
                current_price = data.get('current_price', 0)
                features = data.get('features', {})
                
                if current_price > 0:
                    prediction = self.predict_price(
                        symbol, current_price, features, horizon_days
                    )
                    predictions[symbol] = prediction
                    
            except Exception as e:
                logger.error(f"Error predicting {symbol}: {e}")
                continue
        
        return predictions
    
    def get_portfolio_summary(self, predictions: Dict[str, PricePrediction]) -> Dict:
        """Generate summary statistics for portfolio predictions"""
        
        if not predictions:
            return {}
        
        # Calculate summary metrics
        total_predictions = len(predictions)
        positive_predictions = sum(1 for p in predictions.values() if p.price_change > 0)
        negative_predictions = sum(1 for p in predictions.values() if p.price_change < 0)
        
        avg_change_pct = np.mean([p.price_change_pct for p in predictions.values()])
        avg_confidence = np.mean([p.confidence for p in predictions.values()])
        
        # Find best and worst predictions
        best_prediction = max(predictions.values(), key=lambda x: x.price_change_pct)
        worst_prediction = min(predictions.values(), key=lambda x: x.price_change_pct)
        
        return {
            'total_predictions': total_predictions,
            'positive_predictions': positive_predictions,
            'negative_predictions': negative_predictions,
            'neutral_predictions': total_predictions - positive_predictions - negative_predictions,
            'average_change_pct': avg_change_pct,
            'average_confidence': avg_confidence,
            'best_prediction': {
                'symbol': best_prediction.symbol,
                'change_pct': best_prediction.price_change_pct,
                'confidence': best_prediction.confidence
            },
            'worst_prediction': {
                'symbol': worst_prediction.symbol,
                'change_pct': worst_prediction.price_change_pct,
                'confidence': worst_prediction.confidence
            }
        }
    
    def evaluate_predictions(self, cutoff_date: datetime) -> Dict:
        """Evaluate accuracy of past predictions"""
        
        if not self.prediction_history:
            return {'error': 'No predictions to evaluate'}
        
        # Filter predictions older than cutoff
        old_predictions = [
            p for p in self.prediction_history 
            if p.timestamp < cutoff_date
        ]
        
        if not old_predictions:
            return {'error': 'No predictions old enough to evaluate'}
        
        # This would normally fetch actual prices and compare
        # For now, return placeholder evaluation metrics
        return {
            'total_evaluated': len(old_predictions),
            'accuracy_placeholder': 0.65,  # Would calculate actual accuracy
            'avg_error_placeholder': 3.2,   # Average prediction error %
            'note': 'Evaluation requires actual price data integration'
        }
