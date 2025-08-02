#!/usr/bin/env python3
"""
Enhanced Confidence Calculation System
Replaces static 30%/80% confidence with dynamic quality-based confidence
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedConfidenceCalculator:
    """
    Calculate confidence based on multiple factors:
    1. News quality and volume
    2. Technical indicator strength
    3. Historical prediction accuracy
    4. Market volatility context
    """
    
    def __init__(self):
        self.base_confidence = 0.5
        self.max_confidence = 0.95
        self.min_confidence = 0.15
        
    def calculate_confidence(self, 
                           rsi: float, 
                           sentiment_data: Dict[str, Any],
                           symbol: str,
                           market_conditions: Optional[Dict] = None) -> float:
        """
        Calculate dynamic confidence score
        
        Args:
            rsi: RSI value (0-100)
            sentiment_data: News sentiment analysis results
            symbol: Stock symbol
            market_conditions: Market volatility, volume etc.
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            # 1. Technical Indicator Strength (25% weight)
            technical_confidence = self._calculate_technical_confidence(rsi)
            
            # 2. News Quality & Volume (35% weight)
            news_confidence = self._calculate_news_confidence(sentiment_data)
            
            # 3. Historical Accuracy (20% weight)
            historical_confidence = self._calculate_historical_confidence(symbol)
            
            # 4. Market Conditions (20% weight)
            market_confidence = self._calculate_market_confidence(market_conditions)
            
            # Weighted combination
            confidence = (
                technical_confidence * 0.25 +
                news_confidence * 0.35 +
                historical_confidence * 0.20 +
                market_confidence * 0.20
            )
            
            # Ensure within bounds
            confidence = max(self.min_confidence, min(self.max_confidence, confidence))
            
            logger.info(f"Confidence for {symbol}: {confidence:.3f} "
                       f"(tech:{technical_confidence:.2f}, news:{news_confidence:.2f}, "
                       f"hist:{historical_confidence:.2f}, market:{market_confidence:.2f})")
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence for {symbol}: {e}")
            return self.base_confidence
    
    def _calculate_technical_confidence(self, rsi: float) -> float:
        """
        Calculate confidence based on RSI strength
        Higher confidence for extreme RSI values (oversold/overbought)
        """
        if rsi is None:
            return 0.4
            
        # Distance from neutral (50)
        distance_from_neutral = abs(rsi - 50)
        
        # More confidence for extreme values
        if rsi < 20 or rsi > 80:  # Very extreme
            return 0.9
        elif rsi < 30 or rsi > 70:  # Extreme
            return 0.7
        elif rsi < 40 or rsi > 60:  # Moderate
            return 0.6
        else:  # Neutral
            return 0.4
    
    def _calculate_news_confidence(self, sentiment_data: Dict[str, Any]) -> float:
        """
        Calculate confidence based on news quality and volume
        """
        if not sentiment_data:
            return 0.3
            
        try:
            # News count factor
            news_count = sentiment_data.get('news_count', 0)
            count_factor = min(1.0, news_count / 10.0)  # Scale to 1.0 at 10+ articles
            
            # Quality factor from quality weighting system
            quality_factor = 0.5  # Default
            if 'quality_assessment' in sentiment_data:
                quality_grade = sentiment_data['quality_assessment'].get('overall_grade', 'C')
                quality_factor = {
                    'A': 0.9, 'B': 0.8, 'C': 0.6, 'D': 0.4, 'F': 0.2
                }.get(quality_grade, 0.5)
            
            # Sentiment consistency factor
            consistency_factor = 0.6  # Default
            method_breakdown = sentiment_data.get('method_breakdown', {})
            if method_breakdown:
                confidences = [m.get('confidence', 0.5) for m in method_breakdown.values()]
                if confidences:
                    consistency_factor = np.mean(confidences)
            
            # Combine factors
            news_confidence = (count_factor * 0.3 + quality_factor * 0.5 + consistency_factor * 0.2)
            
            return min(0.95, news_confidence)
            
        except Exception as e:
            logger.error(f"Error in news confidence calculation: {e}")
            return 0.4
    
    def _calculate_historical_confidence(self, symbol: str) -> float:
        """
        Calculate confidence based on historical prediction accuracy
        This would ideally query past prediction performance
        """
        # Placeholder - would implement database lookup of historical accuracy
        # For now, return base confidence with some symbol-specific variance
        base_accuracies = {
            'CBA.AX': 0.65, 'ANZ.AX': 0.62, 'WBC.AX': 0.60, 'NAB.AX': 0.58,
            'MQG.AX': 0.55, 'SUN.AX': 0.52, 'QBE.AX': 0.50
        }
        
        return base_accuracies.get(symbol, 0.55)
    
    def _calculate_market_confidence(self, market_conditions: Optional[Dict]) -> float:
        """
        Calculate confidence based on market volatility and conditions
        """
        if not market_conditions:
            return 0.6  # Neutral market assumption
            
        try:
            volatility = market_conditions.get('volatility', 0.5)
            volume = market_conditions.get('volume_ratio', 1.0)
            
            # Lower confidence in high volatility markets
            volatility_factor = max(0.3, 1.0 - volatility)
            
            # Higher confidence with higher volume
            volume_factor = min(1.0, volume)
            
            return (volatility_factor * 0.7 + volume_factor * 0.3)
            
        except Exception:
            return 0.6

# Integration function for dashboard
def get_enhanced_confidence(rsi: float, sentiment_data: Dict, symbol: str) -> float:
    """
    Drop-in replacement for the current dashboard confidence calculation
    """
    calculator = EnhancedConfidenceCalculator()
    return calculator.calculate_confidence(rsi, sentiment_data, symbol)

if __name__ == "__main__":
    # Test the enhanced confidence calculator
    calculator = EnhancedConfidenceCalculator()
    
    # Test cases
    test_cases = [
        {
            'rsi': 25, 
            'sentiment': {'news_count': 8, 'quality_assessment': {'overall_grade': 'A'}},
            'symbol': 'CBA.AX'
        },
        {
            'rsi': 55, 
            'sentiment': {'news_count': 2, 'quality_assessment': {'overall_grade': 'F'}},
            'symbol': 'NAB.AX'
        },
        {
            'rsi': 75, 
            'sentiment': {'news_count': 12, 'quality_assessment': {'overall_grade': 'B'}},
            'symbol': 'ANZ.AX'
        }
    ]
    
    print("🧮 Enhanced Confidence Calculator Test Results:")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        confidence = calculator.calculate_confidence(
            case['rsi'], case['sentiment'], case['symbol']
        )
        
        print(f"\n{i}. {case['symbol']}")
        print(f"   RSI: {case['rsi']}")
        print(f"   News: {case['sentiment']['news_count']} articles, Grade {case['sentiment']['quality_assessment']['overall_grade']}")
        print(f"   Confidence: {confidence:.1%}")
        
        # Compare with old static method
        old_confidence = 0.8 if case['rsi'] < 30 or case['rsi'] > 70 else 0.3
        print(f"   Old Static: {old_confidence:.1%}")
        print(f"   Improvement: {confidence - old_confidence:+.1%}")
