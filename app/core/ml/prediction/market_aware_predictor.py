"""
Market-Aware Enhanced Prediction System
Integrates market context analysis with traditional prediction methods
Implements fixes from market investigation for better signal quality
"""

import logging
import sqlite3
import yfinance as yf
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
import warnings

from .predictor import PricePredictor, PricePrediction
from ....config.settings import Settings

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class MarketContextAnalyzer:
    """Analyzes broader market conditions for context-aware predictions"""
    
    def get_market_context(self) -> Dict[str, Any]:
        """Check broader ASX market conditions"""
        try:
            logger.info("🌐 Analyzing market context...")
            
            # Get ASX 200 data (5-day trend)
            asx200 = yf.Ticker("^AXJO")
            data = asx200.history(period="5d")
            
            if len(data) < 2:
                logger.warning("⚠️  Insufficient market data, defaulting to NEUTRAL")
                return {
                    "context": "NEUTRAL",
                    "trend_pct": 0.0,
                    "confidence_multiplier": 1.0,
                    "buy_threshold": 0.70,
                    "current_level": 0,
                    "market_data": data
                }
            
            # Calculate 5-day market trend
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            current_level = data['Close'].iloc[-1]
            
            # Determine market context
            if market_trend < -2:  # Market down >2%
                context = "BEARISH"
                confidence_multiplier = 0.7  # Reduce confidence by 30%
                buy_threshold = 0.80  # Higher threshold
            elif market_trend > 2:  # Market up >2%
                context = "BULLISH"
                confidence_multiplier = 1.1  # Boost confidence by 10%
                buy_threshold = 0.65  # Lower threshold
            else:  # Market flat
                context = "NEUTRAL"
                confidence_multiplier = 1.0  # No change
                buy_threshold = 0.70  # Standard threshold
            
            logger.info(f"📊 Market Context: {context} ({market_trend:+.2f}%)")
            
            return {
                "context": context,
                "trend_pct": market_trend,
                "confidence_multiplier": confidence_multiplier,
                "buy_threshold": buy_threshold,
                "current_level": current_level,
                "market_data": data
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market context: {e}")
            # Default to neutral on error
            return {
                "context": "NEUTRAL",
                "trend_pct": 0.0,
                "confidence_multiplier": 1.0,
                "buy_threshold": 0.70,
                "current_level": 0,
                "market_data": None
            }
    
    def market_stress_filter(self, confidence: float, market_data: Dict) -> float:
        """Apply emergency market stress filtering"""
        
        # Get market volatility (if data available)
        if market_data.get("market_data") is not None:
            data = market_data["market_data"]
            if len(data) >= 5:
                # Calculate 5-day volatility
                returns = data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # Annualized
                
                # Apply stress filter for high volatility
                if volatility > 0.4:  # >40% annualized volatility
                    logger.warning(f"⚠️  High market volatility detected: {volatility:.1%}")
                    confidence *= 0.8  # Reduce confidence by 20%
                
                # Emergency override for extreme conditions
                if market_data["trend_pct"] < -5 and volatility > 0.5:
                    logger.warning("🚨 EMERGENCY: Extreme market stress detected")
                    confidence *= 0.5  # Severe reduction
        
        return confidence

class MarketAwarePricePredictor(PricePredictor):
    """
    Enhanced price predictor with market context awareness
    Implements recommendations from market investigation
    """
    
    def __init__(self):
        super().__init__()
        self.market_analyzer = MarketContextAnalyzer()
        self.market_context_cache = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=30)  # Cache market data for 30 min
        
    def get_cached_market_context(self) -> Dict[str, Any]:
        """Get market context with caching to avoid excessive API calls"""
        now = datetime.now()
        
        if (self.market_context_cache is None or 
            self.cache_timestamp is None or 
            now - self.cache_timestamp > self.cache_duration):
            
            self.market_context_cache = self.market_analyzer.get_market_context()
            self.cache_timestamp = now
            
        return self.market_context_cache
    
    def predict_price_with_market_context(
        self,
        symbol: str,
        current_price: float,
        features: Dict,
        horizon_days: int = 5,
        model_name: str = "market_aware_ensemble"
    ) -> PricePrediction:
        """
        Enhanced prediction with market context awareness
        """
        try:
            # Get market context
            market_data = self.get_cached_market_context()
            
            # Calculate enhanced prediction with market awareness
            predicted_price, confidence, prediction_details = self._market_aware_prediction(
                current_price, features, horizon_days, market_data
            )
            
            # Create enhanced prediction object
            prediction = PricePrediction(
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                prediction_horizon_days=horizon_days,
                confidence=confidence,
                timestamp=datetime.now(),
                model_used=model_name,
                supporting_features={
                    **features,
                    'market_context': market_data['context'],
                    'market_trend_pct': market_data['trend_pct'],
                    'buy_threshold_used': market_data['buy_threshold'],
                    'prediction_details': prediction_details
                }
            )
            
            # Store in history
            self.prediction_history.append(prediction)
            
            # Enhanced logging
            logger.info(f"🎯 Market-Aware Prediction for {symbol}:")
            logger.info(f"   Current: ${current_price:.2f} -> Predicted: ${predicted_price:.2f}")
            logger.info(f"   Change: {prediction.price_change_pct:+.2f}% | Confidence: {confidence:.1%}")
            logger.info(f"   Market Context: {market_data['context']} ({market_data['trend_pct']:+.2f}%)")
            logger.info(f"   Action: {prediction_details.get('recommended_action', 'N/A')}")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in market-aware prediction for {symbol}: {e}")
            # Fallback to standard prediction
            return super().predict_price(symbol, current_price, features, horizon_days, "fallback")
    
    def _market_aware_prediction(
        self,
        current_price: float,
        features: Dict,
        horizon_days: int,
        market_data: Dict
    ) -> Tuple[float, float, Dict]:
        """
        Market-aware prediction logic implementing investigation fixes
        """
        
        # 1. REDUCED BASE CONFIDENCE (CRITICAL FIX)
        base_confidence = 0.10  # REDUCED from 0.20 (50% reduction)
        
        # 2. TECHNICAL ANALYSIS COMPONENT (40% weight)
        tech_score = features.get('technical_score', 50)
        rsi = features.get('rsi', 50)
        macd_signal = features.get('macd_signal', 0)
        
        # Technical scoring with market context
        tech_component = 0.0
        if tech_score > 70:
            tech_component = 0.30  # Strong technicals
        elif tech_score > 60:
            tech_component = 0.20  # Good technicals
        elif tech_score > 50:
            tech_component = 0.10  # Decent technicals
        else:
            tech_component = 0.05  # Weak technicals
        
        # RSI and MACD adjustments
        if 30 < rsi < 70 and macd_signal > 0:  # Healthy range + positive MACD
            tech_component += 0.10
        
        # 3. NEWS SENTIMENT COMPONENT (30% weight) - Enhanced for market context
        news_sentiment = features.get('sentiment_score', 0) / 100 - 0.5  # Convert to -0.5 to +0.5
        news_confidence = features.get('news_confidence', 0.5)
        
        # Base news factor - reduced from original
        news_base = news_confidence * 0.15  # Reduced from 0.20
        
        # ENHANCED: Sentiment adjustment with market context
        sentiment_factor = 0.0
        if market_data["context"] == "BEARISH":
            # Require stronger positive sentiment during bearish markets
            if news_sentiment > 0.15:  # Raised from 0.05
                sentiment_factor = min(news_sentiment * 30, 0.15)
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 60, -0.15)
        else:
            # Normal sentiment processing
            if news_sentiment > 0.05:
                sentiment_factor = min(news_sentiment * 50, 0.10)
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 50, -0.10)
        
        news_component = news_base + sentiment_factor
        news_component = max(0.0, min(news_component, 0.30))
        
        # 4. VOLUME ANALYSIS COMPONENT (20% weight)
        volume_ratio = features.get('volume_ratio', 1.0)
        volume_trend = features.get('volume_trend', 0)
        
        volume_component = 0.0
        if volume_ratio > 1.5:  # Strong volume
            volume_component = 0.15
        elif volume_ratio > 1.2:  # Good volume
            volume_component = 0.10
        elif volume_ratio > 1.0:  # Normal volume
            volume_component = 0.05
        
        # Volume trend adjustment
        if volume_trend > 0.1:
            volume_component += 0.05
        
        volume_component = min(volume_component, 0.20)
        
        # 5. RISK ADJUSTMENT COMPONENT (10% weight)
        volatility = features.get('volatility', 0.02)
        
        risk_component = 0.0
        if volatility < 0.015:  # Low volatility
            risk_component = 0.08
        elif volatility < 0.025:  # Normal volatility
            risk_component = 0.05
        elif volatility < 0.04:  # Moderate volatility
            risk_component = 0.02
        else:  # High volatility
            risk_component = -0.02
        
        # PRELIMINARY CONFIDENCE CALCULATION
        preliminary_confidence = base_confidence + tech_component + news_component + volume_component + risk_component
        
        # 6. MARKET CONTEXT ADJUSTMENT (NEW!)
        market_adjusted_confidence = preliminary_confidence * market_data["confidence_multiplier"]
        
        # 7. APPLY EMERGENCY MARKET STRESS FILTER
        final_confidence = self.market_analyzer.market_stress_filter(market_adjusted_confidence, market_data)
        
        # Ensure bounds
        final_confidence = max(0.15, min(final_confidence, 0.95))
        
        # 8. ENHANCED ACTION DETERMINATION WITH MARKET CONTEXT
        buy_threshold = market_data["buy_threshold"]
        recommended_action = "HOLD"
        
        # Standard BUY logic with market-aware thresholds
        if final_confidence > buy_threshold and tech_score > 60:
            if market_data["context"] == "BEARISH":
                # STRICTER requirements during bearish markets
                if news_sentiment > 0.10 and tech_score > 70:
                    recommended_action = "BUY"
            else:
                # Normal requirements
                if news_sentiment > -0.05:
                    recommended_action = "BUY"
        
        # Strong BUY signals
        if final_confidence > (buy_threshold + 0.10) and tech_score > 70:
            if market_data["context"] != "BEARISH" and news_sentiment > 0.02:
                recommended_action = "STRONG_BUY"
        
        # Safety override for very negative sentiment
        if news_sentiment < -0.15 or final_confidence < 0.30:
            recommended_action = "HOLD"
        
        # 9. PRICE PREDICTION CALCULATION
        # Base price movement from confidence
        confidence_impact = (final_confidence - 0.5) * 0.2  # Max 10% impact from confidence
        
        # Technical momentum
        tech_momentum = (tech_score - 50) / 100 * 0.15  # Max 7.5% from technicals
        
        # News impact (reduced in bearish markets)
        news_impact = news_sentiment * 0.1
        if market_data["context"] == "BEARISH":
            news_impact *= 0.5  # Reduce news impact in bearish markets
        
        # Market trend influence
        market_influence = market_data["trend_pct"] / 100 * 0.3  # 30% of market movement
        
        # Combine all factors
        total_change_pct = confidence_impact + tech_momentum + news_impact + market_influence
        
        # Apply time decay for longer horizons
        time_decay = 1.0 / (1.0 + 0.1 * horizon_days)
        total_change_pct *= time_decay
        
        # Cap extreme predictions
        total_change_pct = max(-0.20, min(total_change_pct, 0.20))  # ±20% max
        
        predicted_price = current_price * (1 + total_change_pct)
        
        # Prediction details for logging and analysis
        prediction_details = {
            'base_confidence': base_confidence,
            'technical_component': tech_component,
            'news_component': news_component,
            'volume_component': volume_component,
            'risk_component': risk_component,
            'preliminary_confidence': preliminary_confidence,
            'market_adjusted_confidence': market_adjusted_confidence,
            'final_confidence': final_confidence,
            'buy_threshold_used': buy_threshold,
            'recommended_action': recommended_action,
            'tech_score': tech_score,
            'news_sentiment': news_sentiment,
            'volume_trend': volume_trend,
            'price_change_pct': total_change_pct * 100,
            'market_context': market_data["context"],
            'market_trend_pct': market_data["trend_pct"]
        }
        
        return predicted_price, final_confidence, prediction_details
    
    def predict_portfolio_with_market_context(
        self,
        portfolio_data: Dict[str, Dict],
        horizon_days: int = 5
    ) -> Dict[str, PricePrediction]:
        """Predict prices for portfolio with market context awareness"""
        
        # Get market context once for all predictions
        market_data = self.get_cached_market_context()
        
        predictions = {}
        buy_signals = 0
        
        logger.info(f"🌐 Portfolio Analysis - Market Context: {market_data['context']}")
        
        for symbol, data in portfolio_data.items():
            try:
                current_price = data.get('current_price', 0)
                features = data.get('features', {})
                
                if current_price > 0:
                    prediction = self.predict_price_with_market_context(
                        symbol, current_price, features, horizon_days
                    )
                    predictions[symbol] = prediction
                    
                    # Count BUY signals
                    action = prediction.supporting_features.get('prediction_details', {}).get('recommended_action', 'HOLD')
                    if action in ['BUY', 'STRONG_BUY']:
                        buy_signals += 1
                    
            except Exception as e:
                logger.error(f"Error predicting {symbol}: {e}")
                continue
        
        # Alert if too many BUY signals during bearish market
        if market_data['context'] == 'BEARISH' and predictions:
            buy_rate = buy_signals / len(predictions)
            if buy_rate > 0.3:
                logger.warning(f"⚠️  WARNING: High BUY signal rate ({buy_signals}/{len(predictions)}) during BEARISH market!")
                logger.warning("   Consider manual review of signals")
        
        logger.info(f"📊 Portfolio Summary: {len(predictions)} analyzed, {buy_signals} BUY signals ({buy_signals/len(predictions)*100:.1f}%)" if predictions else "No predictions generated")
        
        return predictions
    
    def save_predictions_to_database(self, predictions: Dict[str, PricePrediction], db_path: str = "data/trading_predictions.db"):
        """Save predictions to database with enhanced market context"""
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create enhanced table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_aware_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    current_price REAL,
                    predicted_price REAL,
                    price_change_pct REAL,
                    confidence REAL,
                    market_context TEXT,
                    market_trend_pct REAL,
                    buy_threshold_used REAL,
                    recommended_action TEXT,
                    tech_score REAL,
                    news_sentiment REAL,
                    volume_trend REAL,
                    prediction_details TEXT,
                    model_used TEXT
                )
            """)
            
            for symbol, prediction in predictions.items():
                prediction_id = f"{symbol}_{prediction.timestamp.strftime('%Y%m%d_%H%M%S')}"
                details = prediction.supporting_features.get('prediction_details', {})
                
                cursor.execute("""
                    INSERT OR REPLACE INTO market_aware_predictions 
                    (prediction_id, symbol, timestamp, current_price, predicted_price,
                     price_change_pct, confidence, market_context, market_trend_pct,
                     buy_threshold_used, recommended_action, tech_score, news_sentiment,
                     volume_trend, prediction_details, model_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_id, symbol, prediction.timestamp, prediction.current_price,
                    prediction.predicted_price, prediction.price_change_pct, prediction.confidence,
                    details.get('market_context'), details.get('market_trend_pct'),
                    details.get('buy_threshold_used'), details.get('recommended_action'),
                    details.get('tech_score'), details.get('news_sentiment'),
                    details.get('volume_trend'), str(details), prediction.model_used
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Saved {len(predictions)} market-aware predictions to database")
            
        except Exception as e:
            logger.error(f"❌ Error saving predictions to database: {e}")

# Convenience functions for integration
def create_market_aware_predictor() -> MarketAwarePricePredictor:
    """Factory function to create market-aware predictor"""
    return MarketAwarePricePredictor()

def predict_with_market_context(symbol: str, current_price: float, features: Dict) -> PricePrediction:
    """Quick prediction with market context"""
    predictor = MarketAwarePricePredictor()
    return predictor.predict_price_with_market_context(symbol, current_price, features)
