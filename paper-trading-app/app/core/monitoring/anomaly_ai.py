"""
Real-time Anomaly Detection for Trading Analysis
Detects unusual market behavior and sentiment patterns
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings

from ..sentiment.enhanced_scoring import EnhancedSentimentScorer
from ..analysis.technical import TechnicalAnalyzer
from ...config.settings import Settings

logger = logging.getLogger(__name__)

class AnomalyType:
    """Anomaly type classifications"""
    PRICE_ANOMALY = "price_anomaly"
    VOLUME_ANOMALY = "volume_anomaly" 
    SENTIMENT_ANOMALY = "sentiment_anomaly"
    VOLATILITY_ANOMALY = "volatility_anomaly"
    CORRELATION_ANOMALY = "correlation_anomaly"
    NEWS_FLOW_ANOMALY = "news_flow_anomaly"

class AnomalyDetector:
    """
    ML-powered anomaly detection system
    Integrates with your existing sentiment and technical analysis
    """
    
    def __init__(self):
        # Initialize models
        self.price_detector = IsolationForest(contamination=0.1, random_state=42)
        self.volume_detector = IsolationForest(contamination=0.1, random_state=42)
        self.sentiment_detector = IsolationForest(contamination=0.1, random_state=42)
        self.volatility_detector = IsolationForest(contamination=0.1, random_state=42)
        
        # Clustering for pattern anomalies
        self.pattern_clusterer = DBSCAN(eps=0.5, min_samples=5)
        
        # Scalers for normalization
        self.price_scaler = StandardScaler()
        self.volume_scaler = StandardScaler()
        self.sentiment_scaler = StandardScaler()
        self.volatility_scaler = StandardScaler()
        
        # Training status
        self.is_trained = False
        self.baseline_period_days = 30
        
        # Thresholds
        self.anomaly_thresholds = {
            'severe': -0.6,      # Very unusual
            'moderate': -0.4,    # Moderately unusual
            'mild': -0.2         # Slightly unusual
        }
        
        # Alert settings
        self.alert_settings = {
            'price_change_threshold': 0.05,    # 5% price change
            'volume_multiplier': 3.0,          # 3x average volume
            'sentiment_deviation': 2.0,        # 2 std deviations
            'volatility_multiplier': 2.5       # 2.5x normal volatility
        }
    
    def detect_anomalies(self, 
                        symbol: str,
                        current_data: Dict[str, Any],
                        historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive anomaly detection across multiple dimensions
        """
        try:
            # Train baseline models if needed
            if not self.is_trained:
                self._train_baseline_models(historical_data)
            
            # Extract current features
            current_features = self._extract_anomaly_features(current_data, historical_data)
            
            # Detect anomalies across different dimensions
            anomalies = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'overall_anomaly_score': 0.0,
                'anomalies_detected': [],
                'severity': 'normal',
                'recommended_actions': [],
                'confidence': 0.0
            }
            
            # Price anomaly detection
            price_anomaly = self._detect_price_anomaly(current_features)
            if price_anomaly['is_anomaly']:
                anomalies['anomalies_detected'].append(price_anomaly)
            
            # Volume anomaly detection
            volume_anomaly = self._detect_volume_anomaly(current_features)
            if volume_anomaly['is_anomaly']:
                anomalies['anomalies_detected'].append(volume_anomaly)
            
            # Sentiment anomaly detection
            sentiment_anomaly = self._detect_sentiment_anomaly(current_features)
            if sentiment_anomaly['is_anomaly']:
                anomalies['anomalies_detected'].append(sentiment_anomaly)
            
            # Volatility anomaly detection
            volatility_anomaly = self._detect_volatility_anomaly(current_features)
            if volatility_anomaly['is_anomaly']:
                anomalies['anomalies_detected'].append(volatility_anomaly)
            
            # Cross-dimensional correlation anomalies
            correlation_anomaly = self._detect_correlation_anomaly(current_features, historical_data)
            if correlation_anomaly['is_anomaly']:
                anomalies['anomalies_detected'].append(correlation_anomaly)
            
            # Calculate overall anomaly score
            anomalies['overall_anomaly_score'] = self._calculate_overall_score(anomalies['anomalies_detected'])
            anomalies['severity'] = self._categorize_severity(anomalies['overall_anomaly_score'])
            anomalies['confidence'] = self._calculate_confidence(anomalies['anomalies_detected'])
            
            # Generate recommendations
            anomalies['recommended_actions'] = self._generate_recommendations(anomalies)
            
            # Log significant anomalies
            if anomalies['severity'] in ['moderate', 'severe']:
                logger.warning(f"Anomaly detected for {symbol}: {anomalies['severity']} "
                             f"(score: {anomalies['overall_anomaly_score']:.3f})")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {symbol}: {e}")
            return self._empty_anomaly_result(symbol)
    
    def _extract_anomaly_features(self, current_data: Dict, historical_data: pd.DataFrame) -> Dict:
        """Extract features for anomaly detection"""
        features = {}
        
        # Current market data
        current_price = current_data.get('price', 0)
        current_volume = current_data.get('volume', 0)
        current_sentiment = current_data.get('sentiment_score', 0)
        
        # Historical context (last 20 periods)
        recent_data = historical_data.tail(20) if len(historical_data) > 20 else historical_data
        
        if len(recent_data) > 0:
            # Price features
            avg_price = recent_data['Close'].mean()
            price_std = recent_data['Close'].std()
            price_change_rate = (current_price / avg_price - 1) if avg_price > 0 else 0
            
            # Volume features
            avg_volume = recent_data['Volume'].mean()
            volume_std = recent_data['Volume'].std()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volatility features
            returns = recent_data['Close'].pct_change().dropna()
            current_volatility = returns.std()
            historical_volatility = returns.rolling(10).std().mean()
            volatility_ratio = current_volatility / historical_volatility if historical_volatility > 0 else 1
            
            # Trend features
            trend = np.polyfit(range(len(recent_data)), recent_data['Close'], 1)[0]
            
            features = {
                'price_z_score': (current_price - avg_price) / price_std if price_std > 0 else 0,
                'price_change_rate': price_change_rate,
                'volume_ratio': volume_ratio,
                'volume_z_score': (current_volume - avg_volume) / volume_std if volume_std > 0 else 0,
                'volatility_ratio': volatility_ratio,
                'sentiment_score': current_sentiment,
                'trend_strength': abs(trend),
                'price_momentum': recent_data['Close'].pct_change().tail(3).mean()
            }
        else:
            # Default values if insufficient data
            features = {
                'price_z_score': 0, 'price_change_rate': 0, 'volume_ratio': 1,
                'volume_z_score': 0, 'volatility_ratio': 1, 'sentiment_score': 0,
                'trend_strength': 0, 'price_momentum': 0
            }
        
        return features
    
    def _train_baseline_models(self, historical_data: pd.DataFrame):
        """Train baseline models using historical data"""
        try:
            if len(historical_data) < self.baseline_period_days:
                logger.warning("Insufficient historical data for anomaly detection training")
                return
            
            # Prepare training features
            training_features = []
            
            for i in range(20, len(historical_data)):  # Need lookback window
                window_data = historical_data.iloc[i-20:i]
                current_row = historical_data.iloc[i]
                
                mock_current = {
                    'price': current_row['Close'],
                    'volume': current_row['Volume'],
                    'sentiment_score': np.random.normal(0, 0.3)  # Mock sentiment for training
                }
                
                features = self._extract_anomaly_features(mock_current, window_data)
                training_features.append(list(features.values()))
            
            if len(training_features) < 10:
                logger.warning("Insufficient training samples for anomaly detection")
                return
            
            training_array = np.array(training_features)
            
            # Train individual detectors
            price_features = training_array[:, [0, 1]].reshape(-1, 1)  # price_z_score, price_change_rate
            volume_features = training_array[:, [2, 3]].reshape(-1, 1)  # volume ratios
            volatility_features = training_array[:, [4]].reshape(-1, 1)  # volatility_ratio
            sentiment_features = training_array[:, [5]].reshape(-1, 1)  # sentiment_score
            
            # Fit models
            if len(price_features) > 5:
                self.price_detector.fit(price_features)
                self.price_scaler.fit(price_features)
            
            if len(volume_features) > 5:
                self.volume_detector.fit(volume_features)
                self.volume_scaler.fit(volume_features)
            
            if len(volatility_features) > 5:
                self.volatility_detector.fit(volatility_features)
                self.volatility_scaler.fit(volatility_features)
            
            if len(sentiment_features) > 5:
                self.sentiment_detector.fit(sentiment_features)
                self.sentiment_scaler.fit(sentiment_features)
            
            self.is_trained = True
            logger.info("Anomaly detection models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training anomaly detection models: {e}")
    
    def _detect_price_anomaly(self, features: Dict) -> Dict:
        """Detect price-related anomalies"""
        try:
            price_data = np.array([[features['price_z_score'], features['price_change_rate']]])
            scaled_data = self.price_scaler.transform(price_data)
            
            anomaly_score = self.price_detector.decision_function(scaled_data)[0]
            is_anomaly = self.price_detector.predict(scaled_data)[0] == -1
            
            return {
                'type': AnomalyType.PRICE_ANOMALY,
                'is_anomaly': is_anomaly,
                'score': anomaly_score,
                'severity': self._score_to_severity(anomaly_score),
                'details': {
                    'price_z_score': features['price_z_score'],
                    'price_change_rate': features['price_change_rate']
                },
                'description': f"Price Z-score: {features['price_z_score']:.2f}, "
                             f"Change rate: {features['price_change_rate']:.1%}"
            }
        except Exception as e:
            return {'type': AnomalyType.PRICE_ANOMALY, 'is_anomaly': False, 'score': 0, 'error': str(e)}
    
    def _detect_volume_anomaly(self, features: Dict) -> Dict:
        """Detect volume-related anomalies"""
        try:
            volume_data = np.array([[features['volume_ratio'], features['volume_z_score']]])
            scaled_data = self.volume_scaler.transform(volume_data)
            
            anomaly_score = self.volume_detector.decision_function(scaled_data)[0]
            is_anomaly = self.volume_detector.predict(scaled_data)[0] == -1
            
            # Additional volume checks
            unusual_volume = features['volume_ratio'] > self.alert_settings['volume_multiplier']
            
            return {
                'type': AnomalyType.VOLUME_ANOMALY,
                'is_anomaly': is_anomaly or unusual_volume,
                'score': anomaly_score,
                'severity': self._score_to_severity(anomaly_score),
                'details': {
                    'volume_ratio': features['volume_ratio'],
                    'volume_z_score': features['volume_z_score'],
                    'unusual_volume': unusual_volume
                },
                'description': f"Volume ratio: {features['volume_ratio']:.1f}x, "
                             f"Z-score: {features['volume_z_score']:.2f}"
            }
        except Exception as e:
            return {'type': AnomalyType.VOLUME_ANOMALY, 'is_anomaly': False, 'score': 0, 'error': str(e)}
    
    def _detect_sentiment_anomaly(self, features: Dict) -> Dict:
        """Detect sentiment-related anomalies"""
        try:
            sentiment_data = np.array([[features['sentiment_score']]])
            scaled_data = self.sentiment_scaler.transform(sentiment_data)
            
            anomaly_score = self.sentiment_detector.decision_function(scaled_data)[0]
            is_anomaly = self.sentiment_detector.predict(scaled_data)[0] == -1
            
            # Check for extreme sentiment
            extreme_sentiment = abs(features['sentiment_score']) > 0.8
            
            return {
                'type': AnomalyType.SENTIMENT_ANOMALY,
                'is_anomaly': is_anomaly or extreme_sentiment,
                'score': anomaly_score,
                'severity': self._score_to_severity(anomaly_score),
                'details': {
                    'sentiment_score': features['sentiment_score'],
                    'extreme_sentiment': extreme_sentiment
                },
                'description': f"Sentiment score: {features['sentiment_score']:.3f}"
            }
        except Exception as e:
            return {'type': AnomalyType.SENTIMENT_ANOMALY, 'is_anomaly': False, 'score': 0, 'error': str(e)}
    
    def _detect_volatility_anomaly(self, features: Dict) -> Dict:
        """Detect volatility-related anomalies"""
        try:
            volatility_data = np.array([[features['volatility_ratio']]])
            scaled_data = self.volatility_scaler.transform(volatility_data)
            
            anomaly_score = self.volatility_detector.decision_function(scaled_data)[0]
            is_anomaly = self.volatility_detector.predict(scaled_data)[0] == -1
            
            # Check for extreme volatility
            extreme_volatility = features['volatility_ratio'] > self.alert_settings['volatility_multiplier']
            
            return {
                'type': AnomalyType.VOLATILITY_ANOMALY,
                'is_anomaly': is_anomaly or extreme_volatility,
                'score': anomaly_score,
                'severity': self._score_to_severity(anomaly_score),
                'details': {
                    'volatility_ratio': features['volatility_ratio'],
                    'extreme_volatility': extreme_volatility
                },
                'description': f"Volatility ratio: {features['volatility_ratio']:.2f}x"
            }
        except Exception as e:
            return {'type': AnomalyType.VOLATILITY_ANOMALY, 'is_anomaly': False, 'score': 0, 'error': str(e)}
    
    def _detect_correlation_anomaly(self, features: Dict, historical_data: pd.DataFrame) -> Dict:
        """Detect correlation anomalies between price and volume"""
        try:
            if len(historical_data) < 20:
                return {'type': AnomalyType.CORRELATION_ANOMALY, 'is_anomaly': False, 'score': 0}
            
            recent_data = historical_data.tail(20)
            
            # Calculate price-volume correlation
            price_changes = recent_data['Close'].pct_change().dropna()
            volume_changes = recent_data['Volume'].pct_change().dropna()
            
            if len(price_changes) > 5 and len(volume_changes) > 5:
                correlation = price_changes.corr(volume_changes)
                
                # Typical price-volume correlation should be positive
                # Negative correlation might indicate unusual behavior
                unusual_correlation = correlation < -0.3 or correlation > 0.8
                
                anomaly_score = -abs(correlation) if unusual_correlation else 0
                
                return {
                    'type': AnomalyType.CORRELATION_ANOMALY,
                    'is_anomaly': unusual_correlation,
                    'score': anomaly_score,
                    'severity': self._score_to_severity(anomaly_score),
                    'details': {
                        'price_volume_correlation': correlation,
                        'unusual_correlation': unusual_correlation
                    },
                    'description': f"Price-Volume correlation: {correlation:.3f}"
                }
            
            return {'type': AnomalyType.CORRELATION_ANOMALY, 'is_anomaly': False, 'score': 0}
            
        except Exception as e:
            return {'type': AnomalyType.CORRELATION_ANOMALY, 'is_anomaly': False, 'score': 0, 'error': str(e)}
    
    def _calculate_overall_score(self, anomalies: List[Dict]) -> float:
        """Calculate overall anomaly score"""
        if not anomalies:
            return 0.0
        
        # Weight different anomaly types
        weights = {
            AnomalyType.PRICE_ANOMALY: 0.3,
            AnomalyType.VOLUME_ANOMALY: 0.2,
            AnomalyType.SENTIMENT_ANOMALY: 0.2,
            AnomalyType.VOLATILITY_ANOMALY: 0.2,
            AnomalyType.CORRELATION_ANOMALY: 0.1
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for anomaly in anomalies:
            if anomaly.get('is_anomaly', False):
                weight = weights.get(anomaly['type'], 0.1)
                weighted_score += anomaly.get('score', 0) * weight
                total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _categorize_severity(self, score: float) -> str:
        """Categorize anomaly severity based on score"""
        if score <= self.anomaly_thresholds['severe']:
            return 'severe'
        elif score <= self.anomaly_thresholds['moderate']:
            return 'moderate'
        elif score <= self.anomaly_thresholds['mild']:
            return 'mild'
        else:
            return 'normal'
    
    def _score_to_severity(self, score: float) -> str:
        """Convert anomaly score to severity level"""
        return self._categorize_severity(score)
    
    def _calculate_confidence(self, anomalies: List[Dict]) -> float:
        """Calculate confidence in anomaly detection"""
        if not anomalies:
            return 0.0
        
        # Confidence based on number of anomalies and their scores
        anomaly_count = len([a for a in anomalies if a.get('is_anomaly', False)])
        avg_score = np.mean([abs(a.get('score', 0)) for a in anomalies])
        
        # More anomalies + stronger scores = higher confidence
        confidence = min((anomaly_count * 0.2) + (avg_score * 0.5), 1.0)
        return max(confidence, 0.0)
    
    def _generate_recommendations(self, anomaly_result: Dict) -> List[str]:
        """Generate recommended actions based on anomalies"""
        recommendations = []
        
        severity = anomaly_result.get('severity', 'normal')
        anomalies = anomaly_result.get('anomalies_detected', [])
        
        if severity == 'severe':
            recommendations.append("IMMEDIATE ATTENTION: Severe market anomaly detected")
            recommendations.append("Consider reducing position sizes")
            recommendations.append("Monitor closely for next 1-2 hours")
        
        elif severity == 'moderate':
            recommendations.append("Moderate anomaly detected - exercise caution")
            recommendations.append("Review position risk management")
        
        # Specific recommendations based on anomaly types
        for anomaly in anomalies:
            if anomaly['type'] == AnomalyType.VOLUME_ANOMALY and anomaly.get('is_anomaly'):
                recommendations.append("Unusual volume detected - possible news or institutional activity")
            
            elif anomaly['type'] == AnomalyType.PRICE_ANOMALY and anomaly.get('is_anomaly'):
                recommendations.append("Significant price movement - verify against news/events")
            
            elif anomaly['type'] == AnomalyType.SENTIMENT_ANOMALY and anomaly.get('is_anomaly'):
                recommendations.append("Extreme sentiment detected - contrarian opportunity possible")
        
        return recommendations
    
    def _empty_anomaly_result(self, symbol: str) -> Dict:
        """Return empty result for error cases"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'overall_anomaly_score': 0.0,
            'anomalies_detected': [],
            'severity': 'normal',
            'recommended_actions': [],
            'confidence': 0.0,
            'error': 'Insufficient data for anomaly detection'
        }
