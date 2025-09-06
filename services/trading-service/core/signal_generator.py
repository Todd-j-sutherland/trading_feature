"""
Signal Generator - Generates trading signals based on various inputs.
"""

from typing import Dict, Any
from datetime import datetime
import json

from shared.models import TradingSignal


class SignalGenerator:
    """Generates trading signals based on market data and analysis."""
    
    def __init__(self):
        self.signal_weights = {
            "technical": 0.4,
            "sentiment": 0.3,
            "ml_prediction": 0.3
        }
    
    def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> TradingSignal:
        """Generate a trading signal for a symbol based on market data."""
        
        # Extract different types of signals
        technical_signal = self._analyze_technical_indicators(market_data.get("technical", {}))
        sentiment_signal = self._analyze_sentiment(market_data.get("sentiment", {}))
        ml_signal = self._analyze_ml_prediction(market_data.get("ml_prediction", {}))
        
        # Combine signals with weights
        combined_score = (
            technical_signal * self.signal_weights["technical"] +
            sentiment_signal * self.signal_weights["sentiment"] +
            ml_signal * self.signal_weights["ml_prediction"]
        )
        
        # Convert score to trading signal
        return self._score_to_signal(combined_score)
    
    def _analyze_technical_indicators(self, technical_data: Dict[str, Any]) -> float:
        """Analyze technical indicators and return a signal score (-1 to 1)."""
        if not technical_data:
            return 0.0
        
        signals = []
        
        # RSI analysis
        rsi = technical_data.get("rsi", 50)
        if rsi < 30:
            signals.append(0.8)  # Oversold - buy signal
        elif rsi > 70:
            signals.append(-0.8)  # Overbought - sell signal
        else:
            signals.append(0.0)  # Neutral
        
        # Moving average analysis
        price = technical_data.get("current_price", 0)
        sma_20 = technical_data.get("sma_20", price)
        sma_50 = technical_data.get("sma_50", price)
        
        if price > sma_20 > sma_50:
            signals.append(0.6)  # Uptrend
        elif price < sma_20 < sma_50:
            signals.append(-0.6)  # Downtrend
        else:
            signals.append(0.0)  # Mixed
        
        # MACD analysis
        macd_line = technical_data.get("macd_line", 0)
        macd_signal = technical_data.get("macd_signal", 0)
        
        if macd_line > macd_signal:
            signals.append(0.4)  # Bullish momentum
        else:
            signals.append(-0.4)  # Bearish momentum
        
        # Volume analysis
        volume_ratio = technical_data.get("volume_ratio", 1.0)
        if volume_ratio > 1.5:
            # High volume - amplify other signals
            multiplier = 1.2
        elif volume_ratio < 0.7:
            # Low volume - dampen signals
            multiplier = 0.8
        else:
            multiplier = 1.0
        
        # Average the signals and apply volume multiplier
        avg_signal = sum(signals) / len(signals) if signals else 0.0
        return max(-1.0, min(1.0, avg_signal * multiplier))
    
    def _analyze_sentiment(self, sentiment_data: Dict[str, Any]) -> float:
        """Analyze sentiment data and return a signal score (-1 to 1)."""
        if not sentiment_data:
            return 0.0
        
        sentiment_score = sentiment_data.get("score", 0.0)
        confidence = sentiment_data.get("confidence", 0.5)
        news_count = sentiment_data.get("news_count", 0)
        
        # Adjust signal based on confidence and news volume
        confidence_factor = max(0.3, confidence)  # Minimum confidence factor
        
        # More news articles give more confidence in sentiment
        volume_factor = min(1.2, 1.0 + (news_count / 10) * 0.2)
        
        # Apply factors
        adjusted_signal = sentiment_score * confidence_factor * volume_factor
        
        return max(-1.0, min(1.0, adjusted_signal))
    
    def _analyze_ml_prediction(self, ml_data: Dict[str, Any]) -> float:
        """Analyze ML prediction and return a signal score (-1 to 1)."""
        if not ml_data:
            return 0.0
        
        predicted_direction = ml_data.get("predicted_direction", "HOLD")
        confidence = ml_data.get("confidence", 0.5)
        predicted_change = ml_data.get("predicted_price_change", 0.0)
        
        # Convert direction to base signal
        if predicted_direction == "BUY":
            base_signal = 0.7
        elif predicted_direction == "STRONG_BUY":
            base_signal = 1.0
        elif predicted_direction == "SELL":
            base_signal = -0.7
        elif predicted_direction == "STRONG_SELL":
            base_signal = -1.0
        else:  # HOLD
            base_signal = 0.0
        
        # Adjust based on confidence and predicted magnitude
        signal = base_signal * confidence
        
        # Factor in predicted price change magnitude
        if abs(predicted_change) > 0.02:  # > 2% predicted change
            signal *= 1.1  # Increase signal strength
        
        return max(-1.0, min(1.0, signal))
    
    def _score_to_signal(self, score: float) -> TradingSignal:
        """Convert a numerical score to a trading signal enum."""
        if score >= 0.7:
            return TradingSignal.STRONG_BUY
        elif score >= 0.3:
            return TradingSignal.BUY
        elif score <= -0.7:
            return TradingSignal.STRONG_SELL
        elif score <= -0.3:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Update signal combination weights."""
        # Ensure weights sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            self.signal_weights = {k: v/total for k, v in new_weights.items()}
    
    def get_signal_breakdown(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed breakdown of signal generation."""
        technical_signal = self._analyze_technical_indicators(market_data.get("technical", {}))
        sentiment_signal = self._analyze_sentiment(market_data.get("sentiment", {}))
        ml_signal = self._analyze_ml_prediction(market_data.get("ml_prediction", {}))
        
        combined_score = (
            technical_signal * self.signal_weights["technical"] +
            sentiment_signal * self.signal_weights["sentiment"] +
            ml_signal * self.signal_weights["ml_prediction"]
        )
        
        final_signal = self._score_to_signal(combined_score)
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "technical": {
                    "score": technical_signal,
                    "weight": self.signal_weights["technical"],
                    "contribution": technical_signal * self.signal_weights["technical"]
                },
                "sentiment": {
                    "score": sentiment_signal,
                    "weight": self.signal_weights["sentiment"],
                    "contribution": sentiment_signal * self.signal_weights["sentiment"]
                },
                "ml_prediction": {
                    "score": ml_signal,
                    "weight": self.signal_weights["ml_prediction"],
                    "contribution": ml_signal * self.signal_weights["ml_prediction"]
                }
            },
            "combined_score": combined_score,
            "final_signal": final_signal.value,
            "confidence": abs(combined_score)  # Use absolute value as confidence measure
        }