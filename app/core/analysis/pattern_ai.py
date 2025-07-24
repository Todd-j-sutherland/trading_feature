"""
AI-Powered Pattern Recognition for Trading Analysis
Extends existing technical analysis with ML pattern detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.signal import find_peaks, find_peaks_cwt
# import talib
import pandas_ta as ta

from ..analysis.technical import TechnicalAnalyzer
from ...config.settings import Settings

logger = logging.getLogger(__name__)

class AIPatternDetector:
    """
    ML-powered chart pattern detection system
    Integrates with your existing TechnicalAnalyzer
    """
    
    def __init__(self):
        self.pattern_classifier = KMeans(n_clusters=8, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Pattern mappings
        self.pattern_names = {
            0: "Bullish Breakout",
            1: "Bearish Breakdown", 
            2: "Consolidation",
            3: "Head & Shoulders",
            4: "Inverse H&S",
            5: "Triangle",
            6: "Flag/Pennant",
            7: "Double Top/Bottom"
        }
        
        # Confidence thresholds
        self.confidence_levels = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    def detect_patterns(self, price_data: pd.DataFrame, symbol: str) -> Dict:
        """
        Detect chart patterns using ML
        Integrates with your existing sentiment scoring
        """
        try:
            if len(price_data) < 50:
                return self._empty_pattern_result(symbol)
            
            # Extract pattern features
            features = self._extract_pattern_features(price_data)
            
            # Train classifier if not done
            if not self.is_trained:
                self._train_pattern_classifier(features)
            
            # Detect current pattern
            current_features = features[-1:].reshape(1, -1)
            scaled_features = self.scaler.transform(current_features)
            
            pattern_id = self.pattern_classifier.predict(scaled_features)[0]
            pattern_name = self.pattern_names[pattern_id]
            
            # Calculate pattern strength and confidence
            strength = self._calculate_pattern_strength(features, pattern_id)
            confidence = self._calculate_pattern_confidence(scaled_features, pattern_id)
            
            # Generate target price based on pattern
            target_price = self._predict_target_price(price_data, pattern_id, strength)
            
            # Generate trading signal
            signal = self._generate_pattern_signal(pattern_id, strength, confidence)
            
            return {
                'symbol': symbol,
                'pattern_detected': pattern_name,
                'pattern_id': pattern_id,
                'strength': strength,
                'confidence': confidence,
                'target_price': target_price,
                'current_price': price_data['Close'].iloc[-1],
                'signal': signal,
                'breakout_probability': self._calculate_breakout_probability(features),
                'time_horizon_days': self._estimate_time_horizon(pattern_id),
                'support_level': self._find_support_level(price_data),
                'resistance_level': self._find_resistance_level(price_data)
            }
            
        except Exception as e:
            logger.error(f"Error detecting patterns for {symbol}: {e}")
            return self._empty_pattern_result(symbol)
    
    def _extract_pattern_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract features for pattern recognition"""
        features = []
        
        # Rolling window analysis
        window_sizes = [10, 20, 50]
        
        for window in window_sizes:
            if len(data) >= window:
                window_data = data.tail(window)
                
                # Price features
                price_change = (window_data['Close'].iloc[-1] / window_data['Close'].iloc[0] - 1)
                volatility = window_data['Close'].pct_change().std()
                
                # Volume features  
                avg_volume = window_data['Volume'].mean()
                volume_trend = np.polyfit(range(len(window_data)), window_data['Volume'], 1)[0]
                
                # Technical indicators using your existing setup
                rsi = ta.rsi(window_data["Close"], length=14).iloc[-1] if len(window_data) >= 14 else 50
                
                # Peak/trough analysis
                peaks, _ = find_peaks(window_data['Close'].values, distance=5)
                troughs, _ = find_peaks(-window_data['Close'].values, distance=5)
                
                # Trend analysis
                trend_slope = np.polyfit(range(len(window_data)), window_data['Close'], 1)[0]
                
                features.extend([
                    price_change,
                    volatility, 
                    avg_volume,
                    volume_trend,
                    rsi,
                    len(peaks),
                    len(troughs),
                    trend_slope
                ])
        
        return np.array(features).reshape(1, -1)
    
    def _train_pattern_classifier(self, features: np.ndarray):
        """Train the pattern classifier with synthetic data"""
        # For now, create synthetic training data
        # In production, you'd use historical labeled patterns
        synthetic_features = self._generate_synthetic_training_data()
        
        # Scale features
        self.scaler.fit(synthetic_features)
        scaled_features = self.scaler.transform(synthetic_features)
        
        # Train classifier
        self.pattern_classifier.fit(scaled_features)
        self.is_trained = True
        
        logger.info("Pattern classifier trained successfully")
    
    def _generate_synthetic_training_data(self) -> np.ndarray:
        """Generate synthetic training data for pattern classification"""
        np.random.seed(42)
        n_samples = 1000
        n_features = 24  # 8 features * 3 windows
        
        # Create different pattern types with characteristic features
        training_data = []
        
        for _ in range(n_samples):
            # Random pattern with some structure
            features = np.random.normal(0, 1, n_features)
            
            # Add some pattern-specific modifications
            pattern_type = np.random.randint(0, 8)
            if pattern_type == 0:  # Bullish breakout
                features[0] = abs(features[0]) + 0.5  # Positive price change
                features[16] = abs(features[16]) + 0.5  # Strong trend
            elif pattern_type == 1:  # Bearish breakdown
                features[0] = -abs(features[0]) - 0.5  # Negative price change
                features[16] = -abs(features[16]) - 0.5  # Negative trend
            
            training_data.append(features)
        
        return np.array(training_data)
    
    def _calculate_pattern_strength(self, features: np.ndarray, pattern_id: int) -> float:
        """Calculate pattern strength (0-1)"""
        # Simplified strength calculation
        # In practice, this would use more sophisticated metrics
        trend_strength = abs(features[0, -1])  # Last trend slope
        volume_confirmation = min(abs(features[0, -3]), 2.0) / 2.0  # Volume trend
        
        return min((trend_strength + volume_confirmation) / 2, 1.0)
    
    def _calculate_pattern_confidence(self, scaled_features: np.ndarray, pattern_id: int) -> float:
        """Calculate confidence in pattern detection"""
        # Distance to cluster center as confidence measure
        cluster_centers = self.pattern_classifier.cluster_centers_
        distance = np.linalg.norm(scaled_features[0] - cluster_centers[pattern_id])
        
        # Convert distance to confidence (closer = higher confidence)
        confidence = max(0, 1 - distance / 5.0)  # Normalize by expected max distance
        return min(confidence, 1.0)
    
    def _predict_target_price(self, data: pd.DataFrame, pattern_id: int, strength: float) -> float:
        """Predict target price based on pattern"""
        current_price = data['Close'].iloc[-1]
        volatility = data['Close'].pct_change().std()
        
        # Pattern-specific target calculations
        if pattern_id in [0, 4]:  # Bullish patterns
            target_multiplier = 1 + (strength * volatility * 2)
        elif pattern_id in [1, 3]:  # Bearish patterns  
            target_multiplier = 1 - (strength * volatility * 2)
        else:  # Neutral patterns
            target_multiplier = 1 + (strength * volatility * 0.5 * np.random.choice([-1, 1]))
        
        return current_price * target_multiplier
    
    def _generate_pattern_signal(self, pattern_id: int, strength: float, confidence: float) -> str:
        """Generate trading signal based on pattern"""
        if confidence < self.confidence_levels['low']:
            return "HOLD"
        
        if pattern_id in [0, 4] and strength > 0.6:  # Strong bullish
            return "BUY"
        elif pattern_id in [1, 3] and strength > 0.6:  # Strong bearish
            return "SELL"
        elif strength > 0.8:  # Very strong pattern
            return "STRONG_BUY" if pattern_id in [0, 4] else "STRONG_SELL"
        else:
            return "HOLD"
    
    def _calculate_breakout_probability(self, features: np.ndarray) -> float:
        """Calculate probability of pattern breakout"""
        volatility = features[0, 1]  # Use volatility as proxy
        volume_trend = features[0, 3]  # Volume trend
        
        # Simple heuristic - high volume + moderate volatility = higher breakout probability
        breakout_prob = min((abs(volume_trend) + volatility) / 2, 1.0)
        return breakout_prob
    
    def _estimate_time_horizon(self, pattern_id: int) -> int:
        """Estimate time horizon for pattern completion"""
        time_horizons = {
            0: 5,   # Bullish breakout - quick
            1: 5,   # Bearish breakdown - quick  
            2: 15,  # Consolidation - longer
            3: 10,  # Head & Shoulders - medium
            4: 10,  # Inverse H&S - medium
            5: 8,   # Triangle - medium-quick
            6: 3,   # Flag/Pennant - very quick
            7: 12   # Double Top/Bottom - longer
        }
        return time_horizons.get(pattern_id, 7)
    
    def _find_support_level(self, data: pd.DataFrame) -> float:
        """Find nearest support level"""
        recent_data = data.tail(50) if len(data) > 50 else data
        lows = recent_data['Low'].values
        
        # Find recent significant lows
        troughs, _ = find_peaks(-lows, distance=5, prominence=lows.std())
        
        if len(troughs) > 0:
            support_levels = lows[troughs]
            # Return most recent significant support
            return support_levels[-1] if len(support_levels) > 0 else recent_data['Low'].min()
        
        return recent_data['Low'].min()
    
    def _find_resistance_level(self, data: pd.DataFrame) -> float:
        """Find nearest resistance level"""
        recent_data = data.tail(50) if len(data) > 50 else data
        highs = recent_data['High'].values
        
        # Find recent significant highs  
        peaks, _ = find_peaks(highs, distance=5, prominence=highs.std())
        
        if len(peaks) > 0:
            resistance_levels = highs[peaks]
            # Return most recent significant resistance
            return resistance_levels[-1] if len(resistance_levels) > 0 else recent_data['High'].max()
        
        return recent_data['High'].max()
    
    def _empty_pattern_result(self, symbol: str) -> Dict:
        """Return empty result for error cases"""
        return {
            'symbol': symbol,
            'pattern_detected': "Insufficient Data",
            'pattern_id': -1,
            'strength': 0.0,
            'confidence': 0.0,
            'target_price': 0.0,
            'current_price': 0.0,
            'signal': "HOLD",
            'breakout_probability': 0.0,
            'time_horizon_days': 0,
            'support_level': 0.0,
            'resistance_level': 0.0
        }
