"""
Trading signal generation module
Generates buy/sell/hold signals based on enhanced sentiment and technical analysis
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum

from ..sentiment.enhanced_scoring import EnhancedSentimentScorer, SentimentMetrics
from ..analysis.technical import TechnicalAnalyzer
from ...config.settings import Settings

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    """Signal strength enumeration"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY" 
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class TradingSignal:
    """Represents a trading signal"""
    
    def __init__(
        self,
        symbol: str,
        signal: SignalStrength,
        confidence: float,
        timestamp: datetime,
        reasoning: str,
        supporting_data: Optional[Dict] = None
    ):
        self.symbol = symbol
        self.signal = signal
        self.confidence = confidence
        self.timestamp = timestamp
        self.reasoning = reasoning
        self.supporting_data = supporting_data or {}

class TradingSignalGenerator:
    """
    Generates trading signals by combining sentiment analysis with technical indicators
    """
    
    def __init__(self):
        self.sentiment_scorer = EnhancedSentimentScorer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.signal_history = []
        
    def generate_signal(
        self,
        symbol: str,
        sentiment_data: Dict,
        market_data: Optional[Dict] = None,
        technical_data: Optional[Dict] = None
    ) -> TradingSignal:
        """
        Generate a trading signal for a given symbol
        
        Args:
            symbol: Stock symbol
            sentiment_data: Sentiment analysis data
            market_data: Market context data
            technical_data: Technical analysis data
            
        Returns:
            TradingSignal object
        """
        try:
            # Get enhanced sentiment metrics
            sentiment_metrics = self.sentiment_scorer.calculate_enhanced_sentiment(
                news_sentiment=sentiment_data.get('news_sentiment', 0.5),
                social_sentiment=sentiment_data.get('social_sentiment', 0.5),
                technical_momentum=sentiment_data.get('technical_momentum', 0.5),
                market_data=market_data
            )
            
            # Calculate technical score if data available
            technical_score = self._calculate_technical_score(technical_data) if technical_data else 50
            
            # Combine scores with weights
            weights = Settings.SENTIMENT_CONFIG['weights']
            combined_score = (
                sentiment_metrics.normalized_score * weights['news_sentiment'] +
                technical_score * weights['technical_momentum'] +
                50 * weights['market_sentiment']  # Neutral market assumption
            )
            
            # Generate signal based on combined score
            signal_strength, confidence = self._score_to_signal(
                combined_score, 
                sentiment_metrics.confidence
            )
            
            # Create reasoning
            reasoning = self._generate_reasoning(
                signal_strength, 
                sentiment_metrics, 
                technical_score, 
                combined_score
            )
            
            # Create trading signal
            trading_signal = TradingSignal(
                symbol=symbol,
                signal=signal_strength,
                confidence=confidence,
                timestamp=datetime.now(),
                reasoning=reasoning,
                supporting_data={
                    'sentiment_score': sentiment_metrics.normalized_score,
                    'sentiment_confidence': sentiment_metrics.confidence,
                    'technical_score': technical_score,
                    'combined_score': combined_score,
                    'sentiment_strength': sentiment_metrics.strength_category.value
                }
            )
            
            # Store in history
            self.signal_history.append(trading_signal)
            
            logger.info(f"Generated {signal_strength.value} signal for {symbol} "
                       f"(confidence: {confidence:.2f})")
            
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            # Return neutral signal on error
            return TradingSignal(
                symbol=symbol,
                signal=SignalStrength.HOLD,
                confidence=0.5,
                timestamp=datetime.now(),
                reasoning=f"Error in signal generation: {str(e)}",
                supporting_data={'error': str(e)}
            )
    
    def _calculate_technical_score(self, technical_data: Dict) -> float:
        """Calculate technical analysis score from 0-100"""
        if not technical_data:
            return 50.0
        
        # Simple technical scoring based on common indicators
        score = 50.0
        
        # RSI scoring
        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            score += 20  # Oversold - bullish
        elif rsi > 70:
            score -= 20  # Overbought - bearish
        
        # MACD scoring
        macd_signal = technical_data.get('macd_signal', 0)
        if macd_signal > 0:
            score += 15
        elif macd_signal < 0:
            score -= 15
        
        # Volume scoring
        volume_ratio = technical_data.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            score += 10  # High volume confirms move
        
        # Moving average scoring
        price = technical_data.get('price', 0)
        sma_20 = technical_data.get('sma_20', price)
        sma_50 = technical_data.get('sma_50', price)
        
        if price > sma_20 > sma_50:
            score += 15  # Bullish trend
        elif price < sma_20 < sma_50:
            score -= 15  # Bearish trend
        
        return max(0, min(100, score))
    
    def _score_to_signal(self, score: float, sentiment_confidence: float) -> Tuple[SignalStrength, float]:
        """Convert combined score to signal strength and confidence"""
        
        # Adjust confidence based on sentiment confidence
        confidence = (sentiment_confidence + 0.5) / 1.5  # Normalize to 0.33-1.0 range
        
        # Determine signal strength based on score thresholds
        thresholds = Settings.ALERT_THRESHOLDS['technical']
        
        if score >= thresholds['strong_buy']:
            return SignalStrength.STRONG_BUY, confidence
        elif score >= thresholds['buy']:
            return SignalStrength.BUY, confidence * 0.9
        elif score >= thresholds['hold_high']:
            return SignalStrength.HOLD, confidence * 0.8
        elif score >= thresholds['sell']:
            return SignalStrength.HOLD, confidence * 0.8
        elif score >= thresholds['strong_sell']:
            return SignalStrength.SELL, confidence * 0.9
        else:
            return SignalStrength.STRONG_SELL, confidence
    
    def _generate_reasoning(
        self,
        signal: SignalStrength,
        sentiment_metrics: SentimentMetrics,
        technical_score: float,
        combined_score: float
    ) -> str:
        """Generate human-readable reasoning for the signal"""
        
        reasoning_parts = []
        
        # Signal summary
        reasoning_parts.append(f"{signal.value} signal generated")
        
        # Sentiment contribution
        sentiment_desc = "positive" if sentiment_metrics.normalized_score > 55 else \
                        "negative" if sentiment_metrics.normalized_score < 45 else "neutral"
        reasoning_parts.append(f"Sentiment: {sentiment_desc} ({sentiment_metrics.normalized_score:.1f}/100)")
        
        # Technical contribution
        technical_desc = "bullish" if technical_score > 55 else \
                        "bearish" if technical_score < 45 else "neutral"
        reasoning_parts.append(f"Technical: {technical_desc} ({technical_score:.1f}/100)")
        
        # Confidence note
        if sentiment_metrics.confidence > 0.7:
            reasoning_parts.append("High confidence in sentiment analysis")
        elif sentiment_metrics.confidence < 0.5:
            reasoning_parts.append("Low confidence - proceed with caution")
        
        return "; ".join(reasoning_parts)
    
    def generate_portfolio_signals(self, symbols: List[str]) -> Dict[str, TradingSignal]:
        """Generate signals for multiple symbols"""
        signals = {}
        
        for symbol in symbols:
            try:
                # This would normally fetch real data - using placeholder for now
                sentiment_data = {
                    'news_sentiment': 0.5,
                    'social_sentiment': 0.5,
                    'technical_momentum': 0.5
                }
                
                signal = self.generate_signal(symbol, sentiment_data)
                signals[symbol] = signal
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    def get_signal_summary(self, signals: Dict[str, TradingSignal]) -> Dict:
        """Generate summary of multiple signals"""
        if not signals:
            return {}
        
        signal_counts = {}
        total_confidence = 0
        
        for symbol, signal in signals.items():
            signal_type = signal.signal.value
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            total_confidence += signal.confidence
        
        return {
            'total_signals': len(signals),
            'signal_distribution': signal_counts,
            'average_confidence': total_confidence / len(signals),
            'dominant_signal': max(signal_counts.items(), key=lambda x: x[1])[0] if signal_counts else None
        }
