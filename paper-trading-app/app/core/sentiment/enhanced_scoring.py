#!/usr/bin/env python3
"""
Enhanced Dynamic Sentiment Scoring System
Industry-standard approach with adaptive scoring, volatility adjustment, and market context
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime classification"""
    BULL_MARKET = "bull"
    BEAR_MARKET = "bear"
    VOLATILE = "volatile"
    STABLE = "stable"
    CRISIS = "crisis"

class SentimentStrength(Enum):
    """Standardized sentiment strength levels"""
    VERY_STRONG_POSITIVE = 5
    STRONG_POSITIVE = 4
    MODERATE_POSITIVE = 3
    NEUTRAL = 2
    MODERATE_NEGATIVE = 1
    STRONG_NEGATIVE = 0
    VERY_STRONG_NEGATIVE = -1

@dataclass
class SentimentMetrics:
    """Standardized sentiment metrics container"""
    raw_score: float  # -1 to 1
    normalized_score: float  # 0 to 100
    strength_category: SentimentStrength
    confidence: float  # 0 to 1
    volatility_adjusted_score: float
    market_adjusted_score: float
    z_score: float  # Statistical significance
    percentile_rank: float  # 0 to 100

class EnhancedSentimentScorer:
    """
    Industry-standard dynamic sentiment scoring system
    
    Features:
    - Multiple scoring methodologies
    - Volatility adjustment (VIX-style)
    - Market regime adaptation
    - Statistical normalization
    - Time-decay weighting
    - Uncertainty quantification
    """
    
    def __init__(self, lookback_days: int = 252, min_samples: int = 30):
        self.lookback_days = lookback_days  # 1 year trading days
        self.min_samples = min_samples
        self.sentiment_history = []
        self.volatility_window = 20  # Rolling volatility window
        
        # Industry-standard scoring parameters
        self.scoring_config = {
            'base_weights': {
                'news_sentiment': 0.30,
                'social_sentiment': 0.15,
                'technical_momentum': 0.20,
                'options_flow': 0.10,
                'insider_activity': 0.10,
                'analyst_sentiment': 0.10,
                'earnings_surprise': 0.05
            },
            'volatility_adjustment': {
                'low_vol_threshold': 0.15,   # Below 15% annualized
                'high_vol_threshold': 0.35,  # Above 35% annualized
                'vol_multiplier_range': (0.7, 1.5)
            },
            'market_regime_adjustments': {
                MarketRegime.BULL_MARKET: 1.1,
                MarketRegime.BEAR_MARKET: 0.9,
                MarketRegime.VOLATILE: 0.8,
                MarketRegime.STABLE: 1.0,
                MarketRegime.CRISIS: 0.6
            },
            'time_decay_half_life': 5.0  # Days for news to lose half impact
        }
    
    def calculate_enhanced_sentiment(self, 
                                   raw_components: Dict[str, float],
                                   market_data: Optional[Dict] = None,
                                   news_items: Optional[List[Dict]] = None) -> SentimentMetrics:
        """
        Calculate enhanced sentiment score using industry standards
        
        Args:
            raw_components: Dict of component scores (news, social, technical, etc.)
            market_data: Market context data (volatility, regime, etc.)
            news_items: List of news items with timestamps for time decay
            
        Returns:
            SentimentMetrics object with comprehensive scoring
        """
        
        # 1. Calculate base weighted score
        base_score = self._calculate_weighted_base_score(raw_components)
        
        # 2. Apply time decay to news components
        time_adjusted_score = self._apply_time_decay(base_score, news_items)
        
        # 3. Calculate volatility adjustment
        volatility_adjusted_score = self._apply_volatility_adjustment(
            time_adjusted_score, market_data
        )
        
        # 4. Apply market regime adjustment
        market_adjusted_score = self._apply_market_regime_adjustment(
            volatility_adjusted_score, market_data
        )
        
        # 5. Calculate statistical metrics
        z_score, percentile_rank = self._calculate_statistical_metrics(market_adjusted_score)
        
        # 6. Normalize to 0-100 scale (industry standard)
        normalized_score = self._normalize_score(market_adjusted_score)
        
        # 7. Determine strength category
        strength_category = self._categorize_strength(normalized_score, z_score)
        
        # 8. Calculate confidence
        confidence = self._calculate_confidence(raw_components, market_data)
        
        # Store for historical analysis
        self._update_history(market_adjusted_score)
        
        return SentimentMetrics(
            raw_score=base_score,
            normalized_score=normalized_score,
            strength_category=strength_category,
            confidence=confidence,
            volatility_adjusted_score=volatility_adjusted_score,
            market_adjusted_score=market_adjusted_score,
            z_score=z_score,
            percentile_rank=percentile_rank
        )
    
    def _calculate_weighted_base_score(self, components: Dict[str, float]) -> float:
        """Calculate base weighted sentiment score with robust error handling"""
        weights = self.scoring_config['base_weights']
        total_weight = 0
        weighted_sum = 0
        
        for component, score in components.items():
            if component in weights and score is not None:
                try:
                    # Convert to float and validate
                    score_float = float(score)
                    
                    # Check for invalid values
                    if np.isnan(score_float) or np.isinf(score_float):
                        logger.warning(f"Invalid score value for {component}: {score}")
                        continue
                    
                    # Clip score to valid range
                    score_float = np.clip(score_float, -1, 1)
                    
                    weight = weights[component]
                    weighted_sum += score_float * weight
                    total_weight += weight
                    
                except (ValueError, TypeError):
                    logger.warning(f"Cannot convert score to float for {component}: {score}")
                    continue
        
        # Normalize by actual weights used (handles missing components)
        base_score = weighted_sum / total_weight if total_weight > 0 else 0
        return np.clip(base_score, -1, 1)
    
    def _apply_time_decay(self, base_score: float, news_items: Optional[List[Dict]]) -> float:
        """Apply exponential time decay to news components"""
        if not news_items:
            return base_score
        
        half_life = self.scoring_config['time_decay_half_life']
        current_time = datetime.now()
        
        weighted_sentiment = 0
        total_weight = 0
        
        for item in news_items:
            try:
                # Parse news timestamp
                published_str = item.get('published', '')
                if not published_str:
                    continue
                    
                news_time = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                if news_time.tzinfo:
                    news_time = news_time.replace(tzinfo=None)
                
                # Calculate time decay
                hours_old = (current_time - news_time).total_seconds() / 3600
                days_old = hours_old / 24
                
                # Exponential decay: weight = 0.5^(days_old / half_life)
                weight = 0.5 ** (days_old / half_life)
                
                # Get news sentiment with validation
                news_sentiment = item.get('sentiment', 0)
                try:
                    news_sentiment = float(news_sentiment)
                    if np.isnan(news_sentiment) or np.isinf(news_sentiment):
                        continue
                    news_sentiment = np.clip(news_sentiment, -1, 1)
                except (ValueError, TypeError):
                    continue
                
                weighted_sentiment += news_sentiment * weight
                total_weight += weight
                
            except Exception as e:
                logger.warning(f"Error processing news time decay: {e}")
                continue
        
        if total_weight > 0:
            # Blend time-decayed news with base score
            news_contribution = weighted_sentiment / total_weight
            news_weight = self.scoring_config['base_weights'].get('news_sentiment', 0.3)
            
            # Replace news component with time-decayed version
            adjusted_score = base_score + (news_contribution - base_score) * news_weight
            return np.clip(adjusted_score, -1, 1)
        
        return base_score
    
    def _apply_volatility_adjustment(self, score: float, market_data: Optional[Dict]) -> float:
        """Apply volatility-based adjustment (similar to VIX impact) with error handling"""
        if not market_data or 'volatility' not in market_data:
            return score
        
        try:
            volatility = float(market_data['volatility'])
            
            # Validate volatility value
            if np.isnan(volatility) or np.isinf(volatility) or volatility < 0:
                logger.warning(f"Invalid volatility value: {volatility}")
                return score
            
            config = self.scoring_config['volatility_adjustment']
            
            # Calculate volatility multiplier
            if volatility < config['low_vol_threshold']:
                # Low volatility - sentiment matters more (trending markets)
                multiplier = config['vol_multiplier_range'][1]  # 1.5
            elif volatility > config['high_vol_threshold']:
                # High volatility - sentiment matters less (noise dominates)
                multiplier = config['vol_multiplier_range'][0]  # 0.7
            else:
                # Linear interpolation between thresholds
                vol_range = config['high_vol_threshold'] - config['low_vol_threshold']
                vol_position = (volatility - config['low_vol_threshold']) / vol_range
                mult_range = config['vol_multiplier_range'][1] - config['vol_multiplier_range'][0]
                multiplier = config['vol_multiplier_range'][1] - (vol_position * mult_range)
        
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Error in volatility adjustment: {e}")
            return score
        
        adjusted_score = score * multiplier
        return np.clip(adjusted_score, -1, 1)
    
    def _apply_market_regime_adjustment(self, score: float, market_data: Optional[Dict]) -> float:
        """Apply market regime-based adjustment"""
        if not market_data or 'regime' not in market_data:
            return score
        
        try:
            regime = MarketRegime(market_data['regime'])
            multiplier = self.scoring_config['market_regime_adjustments'][regime]
            
            adjusted_score = score * multiplier
            return np.clip(adjusted_score, -1, 1)
            
        except (ValueError, KeyError):
            logger.warning(f"Unknown market regime: {market_data.get('regime')}")
            return score
    
    def _calculate_statistical_metrics(self, score: float) -> Tuple[float, float]:
        """Calculate z-score and percentile rank against historical distribution"""
        if len(self.sentiment_history) < self.min_samples:
            return 0.0, 50.0  # Default to neutral if insufficient history
        
        history_array = np.array(self.sentiment_history[-self.lookback_days:])
        
        # Calculate z-score
        mean_score = np.mean(history_array)
        std_score = np.std(history_array)
        
        if std_score > 0:
            z_score = (score - mean_score) / std_score
        else:
            z_score = 0.0
        
        # Calculate percentile rank
        percentile_rank = (np.sum(history_array < score) / len(history_array)) * 100
        
        return z_score, percentile_rank
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-100 scale (industry standard)"""
        # Convert from -1,1 to 0,100
        normalized = ((score + 1) / 2) * 100
        return np.clip(normalized, 0, 100)
    
    def _categorize_strength(self, normalized_score: float, z_score: float) -> SentimentStrength:
        """Categorize sentiment strength using both absolute and relative measures"""
        # Use z-score for relative strength, normalized score for absolute
        if normalized_score >= 85 and z_score >= 2.0:
            return SentimentStrength.VERY_STRONG_POSITIVE
        elif normalized_score >= 70 and z_score >= 1.0:
            return SentimentStrength.STRONG_POSITIVE
        elif normalized_score >= 60:
            return SentimentStrength.MODERATE_POSITIVE
        elif normalized_score <= 15 and z_score <= -2.0:
            return SentimentStrength.VERY_STRONG_NEGATIVE
        elif normalized_score <= 30 and z_score <= -1.0:
            return SentimentStrength.STRONG_NEGATIVE
        elif normalized_score <= 40:
            return SentimentStrength.MODERATE_NEGATIVE
        else:
            return SentimentStrength.NEUTRAL
    
    def _calculate_confidence(self, components: Dict[str, float], 
                            market_data: Optional[Dict]) -> float:
        """Calculate confidence in the sentiment score"""
        confidence_factors = []
        
        # 1. Data availability confidence (more valid components = higher confidence)
        valid_components = 0
        for v in components.values():
            if v is not None:
                try:
                    val = float(v)
                    if not (np.isnan(val) or np.isinf(val)):
                        valid_components += 1
                except (ValueError, TypeError):
                    continue
        
        total_components = len(self.scoring_config['base_weights'])
        data_confidence = valid_components / total_components
        confidence_factors.append(data_confidence * 0.3)
        
        # 2. Consensus confidence (agreement between components)
        non_null_values = []
        for v in components.values():
            if v is not None:
                try:
                    val = float(v)
                    if not (np.isnan(val) or np.isinf(val)):
                        non_null_values.append(val)
                except (ValueError, TypeError):
                    continue
        
        if len(non_null_values) > 1:
            # Calculate standard deviation of components
            std_dev = np.std(non_null_values)
            # Lower std dev = higher confidence (more agreement)
            consensus_confidence = max(0, 1 - (std_dev / 0.5))  # Normalize by max expected std
            confidence_factors.append(consensus_confidence * 0.25)
        
        # 3. Historical stability confidence
        if len(self.sentiment_history) >= 5:
            recent_volatility = np.std(self.sentiment_history[-5:])
            stability_confidence = max(0, 1 - (recent_volatility / 0.3))
            confidence_factors.append(stability_confidence * 0.2)
        
        # 4. Market regime confidence
        if market_data and 'regime_confidence' in market_data:
            regime_confidence = market_data['regime_confidence']
            confidence_factors.append(regime_confidence * 0.15)
        
        # 5. Sample size confidence
        sample_confidence = min(1.0, len(self.sentiment_history) / self.min_samples)
        confidence_factors.append(sample_confidence * 0.1)
        
        total_confidence = sum(confidence_factors)
        return np.clip(total_confidence, 0, 1)
    
    def _update_history(self, score: float):
        """Update sentiment history for statistical analysis"""
        self.sentiment_history.append(score)
        
        # Keep only recent history
        if len(self.sentiment_history) > self.lookback_days:
            self.sentiment_history = self.sentiment_history[-self.lookback_days:]
    
    def get_trading_signal(self, sentiment_metrics: SentimentMetrics, 
                          risk_tolerance: str = 'moderate') -> Dict[str, any]:
        """
        Generate trading signal based on sentiment metrics
        
        Args:
            sentiment_metrics: SentimentMetrics object
            risk_tolerance: 'conservative', 'moderate', 'aggressive'
            
        Returns:
            Dict with trading signal and parameters
        """
        
        # Risk tolerance thresholds
        thresholds = {
            'conservative': {'buy': 75, 'sell': 25, 'z_buy': 1.5, 'z_sell': -1.5, 'min_confidence': 0.8},
            'moderate': {'buy': 65, 'sell': 35, 'z_buy': 1.0, 'z_sell': -1.0, 'min_confidence': 0.6},
            'aggressive': {'buy': 60, 'sell': 40, 'z_buy': 0.5, 'z_sell': -0.5, 'min_confidence': 0.4}
        }
        
        config = thresholds.get(risk_tolerance, thresholds['moderate'])
        
        # Determine signal
        signal = 'HOLD'
        strength = 'WEAK'
        
        if (sentiment_metrics.normalized_score >= config['buy'] and 
            sentiment_metrics.z_score >= config['z_buy'] and 
            sentiment_metrics.confidence >= config['min_confidence']):
            
            signal = 'BUY'
            if sentiment_metrics.strength_category in [SentimentStrength.VERY_STRONG_POSITIVE, 
                                                     SentimentStrength.STRONG_POSITIVE]:
                strength = 'STRONG'
            elif sentiment_metrics.strength_category == SentimentStrength.MODERATE_POSITIVE:
                strength = 'MODERATE'
                
        elif (sentiment_metrics.normalized_score <= config['sell'] and 
              sentiment_metrics.z_score <= config['z_sell'] and 
              sentiment_metrics.confidence >= config['min_confidence']):
            
            signal = 'SELL'
            if sentiment_metrics.strength_category in [SentimentStrength.VERY_STRONG_NEGATIVE, 
                                                     SentimentStrength.STRONG_NEGATIVE]:
                strength = 'STRONG'
            elif sentiment_metrics.strength_category == SentimentStrength.MODERATE_NEGATIVE:
                strength = 'MODERATE'
        
        return {
            'signal': signal,
            'strength': strength,
            'confidence': sentiment_metrics.confidence,
            'normalized_score': sentiment_metrics.normalized_score,
            'percentile_rank': sentiment_metrics.percentile_rank,
            'z_score': sentiment_metrics.z_score,
            'regime_adjusted': sentiment_metrics.market_adjusted_score,
            'reasoning': self._generate_signal_reasoning(sentiment_metrics, signal, strength)
        }
    
    def _generate_signal_reasoning(self, metrics: SentimentMetrics, 
                                 signal: str, strength: str) -> str:
        """Generate human-readable reasoning for the trading signal"""
        
        percentile = metrics.percentile_rank
        z_score = metrics.z_score
        confidence = metrics.confidence
        
        reasoning_parts = []
        
        # Percentile reasoning
        if percentile >= 90:
            reasoning_parts.append(f"Score in top 10% historically ({percentile:.1f}th percentile)")
        elif percentile <= 10:
            reasoning_parts.append(f"Score in bottom 10% historically ({percentile:.1f}th percentile)")
        else:
            reasoning_parts.append(f"Score at {percentile:.1f}th percentile")
        
        # Z-score reasoning
        if abs(z_score) >= 2:
            reasoning_parts.append(f"Statistically extreme (z-score: {z_score:.2f})")
        elif abs(z_score) >= 1:
            reasoning_parts.append(f"Statistically significant (z-score: {z_score:.2f})")
        
        # Confidence reasoning
        if confidence >= 0.8:
            reasoning_parts.append("High confidence in analysis")
        elif confidence >= 0.6:
            reasoning_parts.append("Moderate confidence in analysis")
        else:
            reasoning_parts.append("Low confidence - proceed with caution")
        
        return f"{signal} {strength}: " + "; ".join(reasoning_parts)

def create_market_context_detector() -> Dict[str, any]:
    """
    Create market context for sentiment adjustment
    This would typically connect to market data APIs
    """
    # Example market context - replace with real data
    return {
        'volatility': 0.25,  # 25% annualized volatility
        'regime': 'volatile',
        'regime_confidence': 0.7,
        'market_trend': 'sideways',
        'sector_rotation': 'defensive'
    }

# Example usage and testing
if __name__ == "__main__":
    # Initialize enhanced scorer
    scorer = EnhancedSentimentScorer()
    
    # Example raw sentiment components (from your existing system)
    raw_components = {
        'news_sentiment': 0.25,      # From news analysis
        'social_sentiment': 0.15,    # From Reddit/Twitter
        'technical_momentum': -0.1,  # From technical analysis
        'options_flow': 0.05,        # From options data
        'insider_activity': 0.0,     # Neutral insider activity
        'analyst_sentiment': 0.1,    # Analyst upgrades/downgrades
        'earnings_surprise': 0.2     # Recent earnings beat
    }
    
    # Market context
    market_data = create_market_context_detector()
    
    # Example news items with timestamps
    news_items = [
        {
            'published': '2024-01-15T10:30:00Z',
            'sentiment': 0.3,
            'title': 'Bank reports strong quarterly results'
        },
        {
            'published': '2024-01-14T15:45:00Z',
            'sentiment': -0.1,
            'title': 'Regulatory concerns raised'
        }
    ]
    
    # Calculate enhanced sentiment
    sentiment_metrics = scorer.calculate_enhanced_sentiment(
        raw_components=raw_components,
        market_data=market_data,
        news_items=news_items
    )
    
    # Generate trading signals for different risk tolerances
    conservative_signal = scorer.get_trading_signal(sentiment_metrics, 'conservative')
    moderate_signal = scorer.get_trading_signal(sentiment_metrics, 'moderate')
    aggressive_signal = scorer.get_trading_signal(sentiment_metrics, 'aggressive')
    
    # Display results
    print("Enhanced Sentiment Analysis Results")
    print("=" * 50)
    print(f"Raw Score: {sentiment_metrics.raw_score:.3f}")
    print(f"Normalized Score: {sentiment_metrics.normalized_score:.1f}/100")
    print(f"Strength Category: {sentiment_metrics.strength_category.name}")
    print(f"Confidence: {sentiment_metrics.confidence:.2f}")
    print(f"Z-Score: {sentiment_metrics.z_score:.2f}")
    print(f"Percentile Rank: {sentiment_metrics.percentile_rank:.1f}%")
    print(f"Volatility Adjusted: {sentiment_metrics.volatility_adjusted_score:.3f}")
    print(f"Market Adjusted: {sentiment_metrics.market_adjusted_score:.3f}")
    
    print("\nTrading Signals by Risk Tolerance")
    print("-" * 50)
    for risk_level, signal_data in [
        ('Conservative', conservative_signal),
        ('Moderate', moderate_signal), 
        ('Aggressive', aggressive_signal)
    ]:
        print(f"{risk_level}: {signal_data['signal']} {signal_data['strength']}")
        print(f"  Reasoning: {signal_data['reasoning']}")
        print()
