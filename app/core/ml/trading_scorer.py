"""
ML Trading Score System

Provides comprehensive ML-based trading scores for each bank, combining:
- Sentiment analysis confidence
- Technical indicators
- Market regime context
- Historical performance
- Risk assessment
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MLTradingScorer:
    """
    Calculates comprehensive ML trading scores for banks.
    """
    
    def __init__(self):
        """Initialize the ML Trading Scorer."""
        self.weights = {
            'sentiment_strength': 0.25,
            'sentiment_confidence': 0.20,
            'economic_context': 0.15,
            'divergence_score': 0.20,
            'technical_momentum': 0.15,
            'ml_prediction_confidence': 0.05
        }
        logger.info("MLTradingScorer initialized")
    
    def calculate_ml_trading_score(self, 
                                 bank_analysis: Dict,
                                 economic_analysis: Dict,
                                 divergence_data: Dict = None,
                                 technical_data: Dict = None,
                                 ml_prediction: Dict = None) -> Dict[str, Any]:
        """
        Calculate comprehensive ML trading score for a bank.
        
        Args:
            bank_analysis: Individual bank sentiment analysis
            economic_analysis: Economic context analysis
            divergence_data: Divergence analysis data (optional)
            technical_data: Technical analysis data (optional)
            ml_prediction: ML model prediction (optional)
            
        Returns:
            Dictionary with ML trading score and breakdown
        """
        logger.info("Calculating ML trading score...")
        
        # Component scores (0-100 scale)
        component_scores = {}
        
        # 1. Sentiment Strength Score - validate sentiment data
        sentiment = bank_analysis.get('overall_sentiment')
        if sentiment is None or sentiment == 0:
            logger.warning(f"Invalid sentiment data for bank analysis - skipping ML scoring")
            return {
                'overall_score': 50,  # Neutral score when sentiment unavailable
                'recommendation': 'HOLD',
                'risk_level': 'MEDIUM',
                'component_scores': {'sentiment_strength': 0, 'error': 'Missing sentiment data'},
                'confidence_factors': ['Technical analysis only'],
                'risk_factors': ['No sentiment data available'],
                'explanation': 'Sentiment analysis unavailable - using technical signals only'
            }
            
        component_scores['sentiment_strength'] = self._score_sentiment_strength(sentiment)
        
        # 2. Sentiment Confidence Score
        confidence = bank_analysis.get('confidence', 0)
        component_scores['sentiment_confidence'] = confidence * 100
        
        # 3. Economic Context Score
        component_scores['economic_context'] = self._score_economic_context(
            sentiment, economic_analysis
        )
        
        # 4. Divergence Score
        component_scores['divergence_score'] = self._score_divergence(divergence_data)
        
        # 5. Technical Momentum Score
        component_scores['technical_momentum'] = self._score_technical_momentum(technical_data)
        
        # 6. ML Prediction Confidence Score
        component_scores['ml_prediction_confidence'] = self._score_ml_prediction(ml_prediction)
        
        # Calculate weighted overall score
        overall_score = sum(
            component_scores[component] * self.weights[component]
            for component in self.weights.keys()
        )
        
        # Determine trading recommendation
        recommendation = self._get_trading_recommendation(overall_score, sentiment)
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(component_scores, bank_analysis)
        
        # Position sizing recommendation
        position_size = self._recommend_position_size(overall_score, risk_level)
        
        result = {
            'overall_ml_score': round(overall_score, 2),
            'component_scores': {k: round(v, 2) for k, v in component_scores.items()},
            'weights_used': self.weights,
            'trading_recommendation': recommendation,
            'risk_level': risk_level,
            'position_size_pct': position_size,
            'score_interpretation': self._interpret_score(overall_score),
            'confidence_factors': self._identify_confidence_factors(component_scores),
            'risk_factors': self._identify_risk_factors(component_scores, bank_analysis),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"ML trading score calculated: {overall_score:.2f}/100")
        return result
    
    def _score_sentiment_strength(self, sentiment: float) -> float:
        """Score sentiment strength (0-100)."""
        # Convert sentiment (-1 to 1) to 0-100 scale
        # Strong positive/negative sentiments score higher
        abs_sentiment = abs(sentiment)
        return min(abs_sentiment * 100, 100)
    
    def _score_economic_context(self, sentiment: float, economic_analysis: Dict) -> float:
        """Score how well sentiment aligns with economic context."""
        economic_sentiment = economic_analysis.get('overall_sentiment', 0)
        regime = economic_analysis.get('market_regime', {}).get('regime', 'Neutral')
        
        # Check alignment between bank sentiment and economic context
        alignment = 1 - abs(sentiment - economic_sentiment)
        alignment_score = max(0, alignment) * 100
        
        # Adjust for market regime
        regime_multipliers = {
            'Expansion': 1.2,
            'Neutral': 1.0,
            'Tightening': 0.9,
            'Contraction': 0.8,
            'Easing': 1.1
        }
        
        multiplier = regime_multipliers.get(regime, 1.0)
        return min(alignment_score * multiplier, 100)
    
    def _score_divergence(self, divergence_data: Dict = None) -> float:
        """Score divergence significance."""
        if not divergence_data:
            return 50  # Neutral score if no divergence data
        
        divergence_score = divergence_data.get('divergence_score', 0)
        significance = divergence_data.get('significance', 1)
        
        # Higher significance and absolute divergence score higher
        score = min(abs(divergence_score) * significance * 50, 100)
        return score
    
    def _score_technical_momentum(self, technical_data: Dict = None) -> float:
        """Score technical momentum indicators."""
        if not technical_data:
            return 50  # Neutral score if no technical data
        
        # Combine multiple technical indicators
        indicators = {
            'rsi': technical_data.get('rsi', 50),
            'macd': technical_data.get('macd', 0),
            'trend_strength': technical_data.get('trend_strength', 0.5),
            'volume_confirmation': technical_data.get('volume_confirmation', 0.5)
        }
        
        # Score RSI (oversold/overbought conditions)
        rsi = indicators['rsi']
        if rsi < 30:  # Oversold - potential buy
            rsi_score = (30 - rsi) * 2
        elif rsi > 70:  # Overbought - potential sell
            rsi_score = (rsi - 70) * 2
        else:
            rsi_score = 0
        
        # Score MACD
        macd_score = min(abs(indicators['macd']) * 50, 50)
        
        # Score trend strength
        trend_score = indicators['trend_strength'] * 50
        
        # Score volume confirmation
        volume_score = indicators['volume_confirmation'] * 25
        
        total_score = min(rsi_score + macd_score + trend_score + volume_score, 100)
        return total_score
    
    def _score_ml_prediction(self, ml_prediction: Dict = None) -> float:
        """Score ML model prediction confidence."""
        if not ml_prediction or 'error' in ml_prediction:
            return 25  # Low score if no ML prediction
        
        ensemble_confidence = ml_prediction.get('ensemble_confidence', 0)
        feature_count = ml_prediction.get('feature_count', 0)
        
        # Base score from confidence
        confidence_score = ensemble_confidence * 80
        
        # Bonus for having sufficient features
        feature_bonus = min(feature_count / 20 * 20, 20)
        
        return min(confidence_score + feature_bonus, 100)
    
    def _get_trading_recommendation(self, overall_score: float, sentiment: float) -> str:
        """Get trading recommendation based on score and sentiment."""
        if overall_score >= 75:
            return "STRONG_BUY" if sentiment > 0 else "STRONG_SELL"
        elif overall_score >= 60:
            return "BUY" if sentiment > 0 else "SELL"
        elif overall_score >= 40:
            return "WEAK_BUY" if sentiment > 0.1 else "WEAK_SELL" if sentiment < -0.1 else "HOLD"
        else:
            return "HOLD"
    
    def _calculate_risk_level(self, component_scores: Dict, bank_analysis: Dict) -> str:
        """Calculate risk level based on component scores and analysis."""
        # Low confidence in any component increases risk
        low_confidence_components = sum(1 for score in component_scores.values() if score < 40)
        
        # High divergence increases risk
        divergence_risk = component_scores.get('divergence_score', 50) > 80
        
        # Low news count increases risk
        news_count = bank_analysis.get('news_count', 0)
        news_risk = news_count < 5
        
        risk_factors = low_confidence_components + int(divergence_risk) + int(news_risk)
        
        if risk_factors >= 3:
            return "HIGH"
        elif risk_factors >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _recommend_position_size(self, overall_score: float, risk_level: str) -> float:
        """Recommend position size as percentage of portfolio."""
        base_size = overall_score / 100 * 0.15  # Base: up to 15% for perfect score
        
        # Adjust for risk
        risk_multipliers = {"LOW": 1.0, "MEDIUM": 0.7, "HIGH": 0.4}
        multiplier = risk_multipliers.get(risk_level, 0.5)
        
        recommended_size = base_size * multiplier
        return min(max(recommended_size, 0.01), 0.20)  # Between 1% and 20%
    
    def _interpret_score(self, score: float) -> str:
        """Provide interpretation of the ML trading score."""
        if score >= 80:
            return "Excellent trading opportunity with high confidence"
        elif score >= 70:
            return "Strong trading opportunity with good confidence"
        elif score >= 60:
            return "Moderate trading opportunity with reasonable confidence"
        elif score >= 40:
            return "Weak trading opportunity with low confidence"
        else:
            return "Poor trading opportunity - consider avoiding"
    
    def _identify_confidence_factors(self, component_scores: Dict) -> List[str]:
        """Identify factors that increase confidence."""
        factors = []
        
        if component_scores.get('sentiment_confidence', 0) >= 70:
            factors.append("High sentiment analysis confidence")
        
        if component_scores.get('economic_context', 0) >= 70:
            factors.append("Strong economic context alignment")
        
        if component_scores.get('divergence_score', 0) >= 70:
            factors.append("Significant sector divergence detected")
        
        if component_scores.get('technical_momentum', 0) >= 70:
            factors.append("Positive technical momentum indicators")
        
        if component_scores.get('ml_prediction_confidence', 0) >= 70:
            factors.append("High ML model prediction confidence")
        
        return factors
    
    def _identify_risk_factors(self, component_scores: Dict, bank_analysis: Dict) -> List[str]:
        """Identify factors that increase risk."""
        factors = []
        
        if component_scores.get('sentiment_confidence', 0) < 50:
            factors.append("Low sentiment analysis confidence")
        
        if component_scores.get('economic_context', 0) < 40:
            factors.append("Poor economic context alignment")
        
        if bank_analysis.get('news_count', 0) < 5:
            factors.append("Limited news coverage")
        
        if component_scores.get('technical_momentum', 0) < 30:
            factors.append("Weak technical indicators")
        
        if component_scores.get('ml_prediction_confidence', 0) < 30:
            factors.append("Low ML model confidence")
        
        return factors
    
    def calculate_scores_for_all_banks(self, 
                                     bank_analyses: Dict,
                                     economic_analysis: Dict,
                                     divergence_analysis: Dict = None,
                                     technical_analyses: Dict = None,
                                     ml_predictions: Dict = None) -> Dict[str, Dict]:
        """
        Calculate ML trading scores for all banks.
        
        Args:
            bank_analyses: Dictionary of bank analyses {symbol: analysis}
            economic_analysis: Economic context analysis
            divergence_analysis: Divergence analysis results
            technical_analyses: Technical analyses {symbol: analysis}
            ml_predictions: ML predictions {symbol: prediction}
            
        Returns:
            Dictionary of ML trading scores {symbol: score_data}
        """
        logger.info("Calculating ML trading scores for all banks...")
        
        ml_scores = {}
        divergent_banks = divergence_analysis.get('divergent_banks', {}) if divergence_analysis else {}
        
        for symbol, bank_analysis in bank_analyses.items():
            try:
                # Get relevant data for this bank
                divergence_data = divergent_banks.get(symbol)
                technical_data = technical_analyses.get(symbol) if technical_analyses else None
                ml_prediction = ml_predictions.get(symbol) if ml_predictions else None
                
                # Calculate ML trading score
                ml_score = self.calculate_ml_trading_score(
                    bank_analysis=bank_analysis,
                    economic_analysis=economic_analysis,
                    divergence_data=divergence_data,
                    technical_data=technical_data,
                    ml_prediction=ml_prediction
                )
                
                ml_scores[symbol] = ml_score
                logger.info(f"ML score for {symbol}: {ml_score['overall_ml_score']:.2f}")
                
            except Exception as e:
                logger.error(f"Error calculating ML score for {symbol}: {e}")
                ml_scores[symbol] = {
                    'overall_ml_score': 0,
                    'error': str(e),
                    'trading_recommendation': 'HOLD'
                }
        
        # Add summary statistics
        valid_scores = [
            data['overall_ml_score'] for data in ml_scores.values() 
            if 'error' not in data
        ]
        
        if valid_scores:
            ml_scores['_summary'] = {
                'average_score': round(np.mean(valid_scores), 2),
                'highest_score': max(valid_scores),
                'lowest_score': min(valid_scores),
                'banks_analyzed': len(valid_scores),
                'strong_buy_count': sum(1 for data in ml_scores.values() 
                                      if data.get('trading_recommendation') == 'STRONG_BUY'),
                'buy_count': sum(1 for data in ml_scores.values() 
                               if data.get('trading_recommendation') in ['BUY', 'WEAK_BUY'])
            }
        
        logger.info(f"ML trading scores calculated for {len(ml_scores)} banks")
        return ml_scores

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    scorer = MLTradingScorer()
    
    # Mock data
    bank_analysis = {
        'overall_sentiment': 0.3,
        'confidence': 0.8,
        'news_count': 12,
        'signal': 'BUY'
    }
    
    economic_analysis = {
        'overall_sentiment': 0.2,
        'confidence': 0.85,
        'market_regime': {'regime': 'Expansion'}
    }
    
    divergence_data = {
        'divergence_score': 0.25,
        'significance': 1.8,
        'opportunity': 'outperformer'
    }
    
    ml_prediction = {
        'ensemble_confidence': 0.75,
        'feature_count': 18,
        'ensemble_prediction': 'profitable'
    }
    
    score_result = scorer.calculate_ml_trading_score(
        bank_analysis, economic_analysis, divergence_data, None, ml_prediction
    )
    
    print(json.dumps(score_result, indent=2))
