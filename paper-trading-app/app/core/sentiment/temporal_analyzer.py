#!/usr/bin/env python3
"""
Temporal Sentiment Analysis for Trading
Implements time-series analysis of sentiment evolution as suggested by Claude
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import sqlite3
import json
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class SentimentDataPoint:
    """Represents a single sentiment observation"""
    timestamp: datetime
    symbol: str
    sentiment_score: float
    confidence: float
    news_count: int
    relevance_score: float
    volume_impact: float = 0.0
    source_credibility: float = 0.8

class TemporalSentimentAnalyzer:
    """
    Analyzes sentiment evolution over time to detect trends and patterns
    Key features:
    - Sentiment velocity (rate of change)
    - Sentiment acceleration (trend changes)
    - Regime change detection
    - Time-decay weighting
    """
    
    def __init__(self, window_hours: int = 24, decay_factor: float = 0.95):
        self.window_hours = window_hours
        self.decay_factor = decay_factor
        self.sentiment_history = {}  # symbol -> deque of SentimentDataPoint
        self.regime_thresholds = {
            'bullish': 0.3,
            'bearish': -0.3,
            'volatile': 0.8  # sentiment volatility threshold
        }
        
    def add_sentiment_observation(self, data_point: SentimentDataPoint):
        """Add new sentiment observation to the temporal analysis"""
        symbol = data_point.symbol
        
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = deque(maxlen=200)  # Keep last 200 observations
        
        self.sentiment_history[symbol].append(data_point)
        self._cleanup_old_data(symbol)
    
    def analyze_sentiment_evolution(self, symbol: str) -> Dict:
        """
        Comprehensive temporal analysis of sentiment evolution
        Returns trend, velocity, acceleration, and regime information
        """
        if symbol not in self.sentiment_history:
            return self._empty_analysis()
        
        history = list(self.sentiment_history[symbol])
        if len(history) < 2:
            return self._empty_analysis()
        
        # Filter to time window
        cutoff_time = datetime.now() - timedelta(hours=self.window_hours)
        recent_history = [dp for dp in history if dp.timestamp >= cutoff_time]
        
        if len(recent_history) < 2:
            return self._empty_analysis()
        
        # Calculate temporal metrics
        sentiment_trend = self._calculate_sentiment_trend(recent_history)
        sentiment_velocity = self._calculate_sentiment_velocity(recent_history)
        sentiment_acceleration = self._calculate_sentiment_acceleration(recent_history)
        sentiment_volatility = self._calculate_sentiment_volatility(recent_history)
        
        # Regime detection
        current_regime = self._detect_sentiment_regime(recent_history)
        regime_stability = self._calculate_regime_stability(recent_history)
        
        # Time-weighted current sentiment
        weighted_sentiment = self._calculate_time_weighted_sentiment(recent_history)
        
        # Pattern recognition
        patterns = self._detect_sentiment_patterns(recent_history)
        
        # Prediction confidence based on temporal consistency
        temporal_confidence = self._calculate_temporal_confidence(
            sentiment_trend, sentiment_volatility, regime_stability
        )
        
        return {
            'symbol': symbol,
            'analysis_timestamp': datetime.now().isoformat(),
            'temporal_metrics': {
                'sentiment_trend': sentiment_trend,
                'sentiment_velocity': sentiment_velocity,
                'sentiment_acceleration': sentiment_acceleration,
                'sentiment_volatility': sentiment_volatility,
                'weighted_current_sentiment': weighted_sentiment
            },
            'regime_analysis': {
                'current_regime': current_regime,
                'regime_stability': regime_stability,
                'regime_duration_hours': self._calculate_regime_duration(recent_history)
            },
            'patterns': patterns,
            'temporal_confidence': temporal_confidence,
            'data_quality': {
                'observation_count': len(recent_history),
                'time_span_hours': self._calculate_time_span(recent_history),
                'avg_confidence': np.mean([dp.confidence for dp in recent_history]),
                'avg_relevance': np.mean([dp.relevance_score for dp in recent_history])
            },
            'trading_signals': self._generate_temporal_trading_signals(
                sentiment_trend, sentiment_velocity, sentiment_acceleration, current_regime
            )
        }
    
    def _calculate_sentiment_trend(self, history: List[SentimentDataPoint]) -> float:
        """Calculate linear trend of sentiment over time"""
        if len(history) < 2:
            return 0.0
        
        # Convert to time series
        timestamps = [(dp.timestamp - history[0].timestamp).total_seconds() / 3600 for dp in history]
        sentiments = [dp.sentiment_score for dp in history]
        
        # Linear regression
        if len(timestamps) > 1:
            coeffs = np.polyfit(timestamps, sentiments, 1)
            return float(coeffs[0])  # Slope represents trend
        return 0.0
    
    def _calculate_sentiment_velocity(self, history: List[SentimentDataPoint]) -> float:
        """Calculate rate of sentiment change (first derivative)"""
        if len(history) < 2:
            return 0.0
        
        # Calculate differences
        time_diffs = []
        sentiment_diffs = []
        
        for i in range(1, len(history)):
            time_diff = (history[i].timestamp - history[i-1].timestamp).total_seconds() / 3600
            sentiment_diff = history[i].sentiment_score - history[i-1].sentiment_score
            
            if time_diff > 0:
                time_diffs.append(time_diff)
                sentiment_diffs.append(sentiment_diff / time_diff)
        
        return np.mean(sentiment_diffs) if sentiment_diffs else 0.0
    
    def _calculate_sentiment_acceleration(self, history: List[SentimentDataPoint]) -> float:
        """Calculate sentiment acceleration (second derivative)"""
        if len(history) < 3:
            return 0.0
        
        # Calculate velocity at each point
        velocities = []
        velocity_times = []
        
        for i in range(1, len(history)):
            time_diff = (history[i].timestamp - history[i-1].timestamp).total_seconds() / 3600
            if time_diff > 0:
                velocity = (history[i].sentiment_score - history[i-1].sentiment_score) / time_diff
                velocities.append(velocity)
                velocity_times.append(history[i].timestamp)
        
        if len(velocities) < 2:
            return 0.0
        
        # Calculate acceleration
        accelerations = []
        for i in range(1, len(velocities)):
            time_diff = (velocity_times[i] - velocity_times[i-1]).total_seconds() / 3600
            if time_diff > 0:
                acceleration = (velocities[i] - velocities[i-1]) / time_diff
                accelerations.append(acceleration)
        
        return np.mean(accelerations) if accelerations else 0.0
    
    def _calculate_sentiment_volatility(self, history: List[SentimentDataPoint]) -> float:
        """Calculate sentiment volatility (standard deviation)"""
        if len(history) < 2:
            return 0.0
        
        sentiments = [dp.sentiment_score for dp in history]
        return float(np.std(sentiments))
    
    def _calculate_time_weighted_sentiment(self, history: List[SentimentDataPoint]) -> float:
        """Calculate sentiment with exponential time decay weighting"""
        if not history:
            return 0.0
        
        now = datetime.now()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for dp in history:
            # Calculate time decay weight
            hours_ago = (now - dp.timestamp).total_seconds() / 3600
            time_weight = self.decay_factor ** hours_ago
            
            # Combine with confidence and relevance weights
            total_weight = time_weight * dp.confidence * dp.relevance_score
            
            weighted_sum += dp.sentiment_score * total_weight
            weight_sum += total_weight
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def _detect_sentiment_regime(self, history: List[SentimentDataPoint]) -> str:
        """Detect current sentiment regime (bullish, bearish, neutral, volatile)"""
        if len(history) < 3:
            return 'insufficient_data'
        
        recent_sentiments = [dp.sentiment_score for dp in history[-5:]]  # Last 5 observations
        avg_sentiment = np.mean(recent_sentiments)
        volatility = np.std(recent_sentiments)
        
        if volatility > self.regime_thresholds['volatile']:
            return 'volatile'
        elif avg_sentiment > self.regime_thresholds['bullish']:
            return 'bullish'
        elif avg_sentiment < self.regime_thresholds['bearish']:
            return 'bearish'
        else:
            return 'neutral'
    
    def _calculate_regime_stability(self, history: List[SentimentDataPoint]) -> float:
        """Calculate how stable the current sentiment regime is"""
        if len(history) < 5:
            return 0.5
        
        # Look at regime over sliding windows
        window_size = 5
        regimes = []
        
        for i in range(len(history) - window_size + 1):
            window = history[i:i + window_size]
            regime = self._detect_sentiment_regime(window)
            regimes.append(regime)
        
        if not regimes:
            return 0.5
        
        # Calculate stability as consistency of regimes
        current_regime = regimes[-1]
        stability = sum(1 for r in regimes[-3:] if r == current_regime) / min(3, len(regimes))
        
        return stability
    
    def _calculate_regime_duration(self, history: List[SentimentDataPoint]) -> float:
        """Calculate how long the current regime has been in place"""
        if len(history) < 2:
            return 0.0
        
        current_regime = self._detect_sentiment_regime(history)
        
        # Go backwards to find regime start
        duration_hours = 0
        for i in range(len(history) - 1, 0, -1):
            window = history[max(0, i-4):i+1]
            if self._detect_sentiment_regime(window) != current_regime:
                break
            duration_hours = (history[-1].timestamp - history[i].timestamp).total_seconds() / 3600
        
        return duration_hours
    
    def _detect_sentiment_patterns(self, history: List[SentimentDataPoint]) -> Dict:
        """Detect common sentiment patterns"""
        if len(history) < 5:
            return {'patterns': [], 'confidence': 0.0}
        
        sentiments = [dp.sentiment_score for dp in history]
        patterns = []
        
        # Pattern 1: Momentum (consistent direction)
        recent_trend = self._calculate_sentiment_trend(history[-5:])
        if abs(recent_trend) > 0.1:
            direction = 'upward' if recent_trend > 0 else 'downward'
            patterns.append({
                'type': 'momentum',
                'direction': direction,
                'strength': abs(recent_trend),
                'confidence': min(1.0, abs(recent_trend) * 5)
            })
        
        # Pattern 2: Reversal (change in direction)
        if len(history) >= 10:
            early_trend = self._calculate_sentiment_trend(history[:5])
            late_trend = self._calculate_sentiment_trend(history[-5:])
            
            if early_trend * late_trend < 0 and abs(early_trend - late_trend) > 0.2:
                patterns.append({
                    'type': 'reversal',
                    'from': 'positive' if early_trend > 0 else 'negative',
                    'to': 'positive' if late_trend > 0 else 'negative',
                    'strength': abs(early_trend - late_trend),
                    'confidence': min(1.0, abs(early_trend - late_trend) * 2)
                })
        
        # Pattern 3: Volatility spike
        current_volatility = self._calculate_sentiment_volatility(history[-5:])
        baseline_volatility = self._calculate_sentiment_volatility(history[:-5]) if len(history) > 10 else 0
        
        if current_volatility > baseline_volatility * 2 and current_volatility > 0.3:
            patterns.append({
                'type': 'volatility_spike',
                'current_volatility': current_volatility,
                'baseline_volatility': baseline_volatility,
                'confidence': min(1.0, current_volatility / 0.5)
            })
        
        return {
            'patterns': patterns,
            'pattern_count': len(patterns),
            'overall_confidence': np.mean([p['confidence'] for p in patterns]) if patterns else 0.0
        }
    
    def _calculate_temporal_confidence(self, trend: float, volatility: float, regime_stability: float) -> float:
        """Calculate confidence in temporal analysis predictions"""
        # Base confidence
        confidence = 0.5
        
        # Strong trend increases confidence
        if abs(trend) > 0.2:
            confidence += 0.2
        elif abs(trend) > 0.1:
            confidence += 0.1
        
        # Low volatility increases confidence
        if volatility < 0.2:
            confidence += 0.15
        elif volatility < 0.4:
            confidence += 0.1
        else:
            confidence -= 0.1  # High volatility reduces confidence
        
        # Regime stability increases confidence
        confidence += regime_stability * 0.25
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_temporal_trading_signals(self, trend: float, velocity: float, 
                                         acceleration: float, regime: str) -> Dict:
        """Generate trading signals based on temporal analysis"""
        signals = {
            'momentum_signal': 'HOLD',
            'reversal_signal': 'HOLD',
            'regime_signal': 'HOLD',
            'overall_signal': 'HOLD',
            'confidence': 0.0,
            'reasoning': []
        }
        
        reasoning = []
        signal_strength = 0
        
        # Momentum signals
        if trend > 0.15 and velocity > 0.1:
            signals['momentum_signal'] = 'BUY'
            signal_strength += 1
            reasoning.append(f"Strong positive momentum (trend: {trend:.3f}, velocity: {velocity:.3f})")
        elif trend < -0.15 and velocity < -0.1:
            signals['momentum_signal'] = 'SELL'
            signal_strength += 1
            reasoning.append(f"Strong negative momentum (trend: {trend:.3f}, velocity: {velocity:.3f})")
        
        # Reversal signals
        if acceleration > 0.2 and trend < 0:
            signals['reversal_signal'] = 'BUY'
            signal_strength += 1
            reasoning.append(f"Potential reversal to upside (acceleration: {acceleration:.3f})")
        elif acceleration < -0.2 and trend > 0:
            signals['reversal_signal'] = 'SELL'
            signal_strength += 1
            reasoning.append(f"Potential reversal to downside (acceleration: {acceleration:.3f})")
        
        # Regime signals
        if regime == 'bullish':
            signals['regime_signal'] = 'BUY'
            signal_strength += 0.5
            reasoning.append("Bullish sentiment regime")
        elif regime == 'bearish':
            signals['regime_signal'] = 'SELL'
            signal_strength += 0.5
            reasoning.append("Bearish sentiment regime")
        elif regime == 'volatile':
            reasoning.append("Volatile regime - proceed with caution")
        
        # Overall signal
        buy_signals = sum(1 for s in [signals['momentum_signal'], signals['reversal_signal'], signals['regime_signal']] if s == 'BUY')
        sell_signals = sum(1 for s in [signals['momentum_signal'], signals['reversal_signal'], signals['regime_signal']] if s == 'SELL')
        
        if buy_signals > sell_signals and signal_strength >= 1.5:
            signals['overall_signal'] = 'BUY'
        elif sell_signals > buy_signals and signal_strength >= 1.5:
            signals['overall_signal'] = 'SELL'
        
        signals['confidence'] = min(1.0, signal_strength / 3.0)
        signals['reasoning'] = reasoning
        
        return signals
    
    def _cleanup_old_data(self, symbol: str):
        """Remove old data points outside the analysis window"""
        if symbol not in self.sentiment_history:
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.window_hours * 2)  # Keep 2x window for calculations
        history = self.sentiment_history[symbol]
        
        # Remove old data points
        while history and history[0].timestamp < cutoff_time:
            history.popleft()
    
    def _calculate_time_span(self, history: List[SentimentDataPoint]) -> float:
        """Calculate time span of the data in hours"""
        if len(history) < 2:
            return 0.0
        
        return (history[-1].timestamp - history[0].timestamp).total_seconds() / 3600
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure when insufficient data"""
        return {
            'temporal_metrics': {
                'sentiment_trend': 0.0,
                'sentiment_velocity': 0.0,
                'sentiment_acceleration': 0.0,
                'sentiment_volatility': 0.0,
                'weighted_current_sentiment': 0.0
            },
            'regime_analysis': {
                'current_regime': 'insufficient_data',
                'regime_stability': 0.0,
                'regime_duration_hours': 0.0
            },
            'patterns': {'patterns': [], 'confidence': 0.0},
            'temporal_confidence': 0.0,
            'trading_signals': {
                'momentum_signal': 'HOLD',
                'reversal_signal': 'HOLD',
                'regime_signal': 'HOLD',
                'overall_signal': 'HOLD',
                'confidence': 0.0,
                'reasoning': ['Insufficient historical data']
            }
        }
    
    def get_summary_stats(self, symbol: str) -> Dict:
        """Get summary statistics for temporal analysis"""
        if symbol not in self.sentiment_history:
            return {'error': 'No data for symbol'}
        
        history = list(self.sentiment_history[symbol])
        if not history:
            return {'error': 'No historical data'}
        
        sentiments = [dp.sentiment_score for dp in history]
        confidences = [dp.confidence for dp in history]
        
        return {
            'symbol': symbol,
            'total_observations': len(history),
            'time_span_hours': self._calculate_time_span(history),
            'sentiment_stats': {
                'mean': np.mean(sentiments),
                'std': np.std(sentiments),
                'min': np.min(sentiments),
                'max': np.max(sentiments),
                'current': sentiments[-1] if sentiments else 0
            },
            'confidence_stats': {
                'mean': np.mean(confidences),
                'std': np.std(confidences),
                'current': confidences[-1] if confidences else 0
            },
            'data_freshness': {
                'latest_observation': history[-1].timestamp.isoformat(),
                'hours_since_latest': (datetime.now() - history[-1].timestamp).total_seconds() / 3600
            }
        }
