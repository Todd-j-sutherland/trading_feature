"""
Simplified Anomaly Detection System
Works with the current sentiment_scores database structure
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    SENTIMENT_EXTREME = "sentiment_extreme"
    CONFIDENCE_ANOMALY = "confidence_anomaly"
    SIGNAL_DIVERGENCE = "signal_divergence"
    NEWS_SPIKE = "news_spike"
    TECHNICAL_EXTREME = "technical_extreme"

class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SimpleAnomaly:
    """Data class for anomaly detection results"""
    type: AnomalyType
    severity: AnomalySeverity
    symbol: str
    timestamp: datetime
    description: str
    confidence: float
    data: Dict
    impact_score: float

class SimpleAnomalyDetector:
    """
    Simplified anomaly detection for available sentiment data
    """
    
    def __init__(self, database_path: str = "morning_analysis.db"):
        self.database_path = database_path
        
        # Anomaly thresholds (more conservative for limited data)
        self.thresholds = {
            'sentiment_z_score': 2.0,       # Standard deviations from mean
            'confidence_threshold': 0.9,    # Very high confidence anomaly
            'news_spike_multiplier': 5.0,   # Unusual news volume
            'technical_extreme': 0.3,       # Extreme technical score
            'signal_conflict': True          # Check for signal conflicts
        }
    
    def get_baseline_stats(self) -> Dict:
        """Get baseline statistics from available data"""
        try:
            conn = sqlite3.connect(self.database_path)
            df = pd.read_sql_query("SELECT * FROM sentiment_scores ORDER BY timestamp DESC", conn)
            conn.close()
            
            if df.empty:
                return {'data_available': False}
            
            stats = {
                'data_available': True,
                'total_records': len(df),
                'sentiment': {
                    'mean': df['sentiment_score'].mean(),
                    'std': df['sentiment_score'].std(),
                    'min': df['sentiment_score'].min(),
                    'max': df['sentiment_score'].max()
                },
                'confidence': {
                    'mean': df['confidence'].mean(),
                    'std': df['confidence'].std(),
                    'min': df['confidence'].min(),
                    'max': df['confidence'].max()
                },
                'technical': {
                    'mean': df['technical_score'].mean(),
                    'std': df['technical_score'].std(),
                    'min': df['technical_score'].min(),
                    'max': df['technical_score'].max()
                },
                'news': {
                    'mean': df['news_count'].mean(),
                    'max': df['news_count'].max(),
                    'std': df['news_count'].std()
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting baseline stats: {e}")
            return {'data_available': False, 'error': str(e)}
    
    def detect_sentiment_anomalies(self, symbol: str, sentiment_score: float, baseline: Dict) -> List[SimpleAnomaly]:
        """Detect sentiment-based anomalies"""
        anomalies = []
        
        if not baseline.get('data_available', False):
            return anomalies
        
        try:
            sentiment_mean = baseline['sentiment']['mean']
            sentiment_std = baseline['sentiment']['std']
            
            if sentiment_std > 0:
                z_score = (sentiment_score - sentiment_mean) / sentiment_std
                
                if abs(z_score) > self.thresholds['sentiment_z_score']:
                    # Determine severity
                    if abs(z_score) > 3.0:
                        severity = AnomalySeverity.CRITICAL
                    elif abs(z_score) > 2.5:
                        severity = AnomalySeverity.HIGH
                    else:
                        severity = AnomalySeverity.MEDIUM
                    
                    direction = "extremely positive" if z_score > 0 else "extremely negative"
                    impact_score = min(abs(z_score) / 4.0, 1.0)
                    
                    anomaly = SimpleAnomaly(
                        type=AnomalyType.SENTIMENT_EXTREME,
                        severity=severity,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        description=f"Extreme sentiment detected: {direction} ({z_score:.2f}σ from mean)",
                        confidence=min(abs(z_score) / 4.0, 1.0),
                        data={
                            'current_sentiment': sentiment_score,
                            'baseline_mean': sentiment_mean,
                            'z_score': z_score,
                            'direction': direction
                        },
                        impact_score=impact_score
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting sentiment anomalies: {e}")
            return []
    
    def detect_confidence_anomalies(self, symbol: str, confidence: float, baseline: Dict) -> List[SimpleAnomaly]:
        """Detect confidence-based anomalies"""
        anomalies = []
        
        if not baseline.get('data_available', False):
            return anomalies
        
        try:
            # Very high confidence could be suspicious
            if confidence > self.thresholds['confidence_threshold']:
                severity = AnomalySeverity.HIGH if confidence > 0.95 else AnomalySeverity.MEDIUM
                
                anomaly = SimpleAnomaly(
                    type=AnomalyType.CONFIDENCE_ANOMALY,
                    severity=severity,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    description=f"Unusually high confidence detected: {confidence:.1%}",
                    confidence=confidence,
                    data={
                        'current_confidence': confidence,
                        'baseline_mean': baseline['confidence']['mean'],
                        'baseline_max': baseline['confidence']['max']
                    },
                    impact_score=min((confidence - 0.9) / 0.1, 1.0)
                )
                
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting confidence anomalies: {e}")
            return []
    
    def detect_news_anomalies(self, symbol: str, news_count: int, baseline: Dict) -> List[SimpleAnomaly]:
        """Detect news volume anomalies"""
        anomalies = []
        
        if not baseline.get('data_available', False):
            return anomalies
        
        try:
            baseline_mean = baseline['news']['mean']
            
            if baseline_mean > 0 and news_count > baseline_mean * self.thresholds['news_spike_multiplier']:
                severity = AnomalySeverity.CRITICAL if news_count > baseline_mean * 10 else AnomalySeverity.HIGH
                
                anomaly = SimpleAnomaly(
                    type=AnomalyType.NEWS_SPIKE,
                    severity=severity,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    description=f"News volume spike: {news_count} articles (avg: {baseline_mean:.1f})",
                    confidence=min(news_count / (baseline_mean * 10), 1.0),
                    data={
                        'current_news_count': news_count,
                        'baseline_mean': baseline_mean,
                        'multiplier': news_count / baseline_mean if baseline_mean > 0 else 0
                    },
                    impact_score=min(news_count / (baseline_mean * 10), 1.0)
                )
                
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting news anomalies: {e}")
            return []
    
    def detect_technical_anomalies(self, symbol: str, technical_score: float, baseline: Dict) -> List[SimpleAnomaly]:
        """Detect technical indicator anomalies"""
        anomalies = []
        
        if not baseline.get('data_available', False):
            return anomalies
        
        try:
            if abs(technical_score) > self.thresholds['technical_extreme']:
                severity = AnomalySeverity.HIGH if abs(technical_score) > 0.5 else AnomalySeverity.MEDIUM
                
                direction = "extremely bullish" if technical_score > 0 else "extremely bearish"
                
                anomaly = SimpleAnomaly(
                    type=AnomalyType.TECHNICAL_EXTREME,
                    severity=severity,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    description=f"Extreme technical signal: {direction} ({technical_score:.3f})",
                    confidence=min(abs(technical_score) / 0.5, 1.0),
                    data={
                        'current_technical': technical_score,
                        'baseline_mean': baseline['technical']['mean'],
                        'direction': direction
                    },
                    impact_score=min(abs(technical_score) / 0.5, 1.0)
                )
                
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting technical anomalies: {e}")
            return []
    
    def detect_signal_divergence(self, symbol: str, sentiment_score: float, technical_score: float) -> List[SimpleAnomaly]:
        """Detect divergence between sentiment and technical signals"""
        anomalies = []
        
        try:
            # Check if signals point in opposite directions with significant magnitude
            sentiment_direction = 1 if sentiment_score > 0.05 else -1 if sentiment_score < -0.05 else 0
            technical_direction = 1 if technical_score > 0.05 else -1 if technical_score < -0.05 else 0
            
            if sentiment_direction != 0 and technical_direction != 0 and sentiment_direction != technical_direction:
                # Signals diverge
                divergence_strength = abs(sentiment_score) + abs(technical_score)
                
                if divergence_strength > 0.2:  # Significant divergence
                    severity = AnomalySeverity.HIGH if divergence_strength > 0.4 else AnomalySeverity.MEDIUM
                    
                    sentiment_signal = "BULLISH" if sentiment_score > 0 else "BEARISH"
                    technical_signal = "BULLISH" if technical_score > 0 else "BEARISH"
                    
                    anomaly = SimpleAnomaly(
                        type=AnomalyType.SIGNAL_DIVERGENCE,
                        severity=severity,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        description=f"Signal conflict: Sentiment={sentiment_signal} vs Technical={technical_signal}",
                        confidence=min(divergence_strength / 0.5, 1.0),
                        data={
                            'sentiment_score': sentiment_score,
                            'technical_score': technical_score,
                            'sentiment_signal': sentiment_signal,
                            'technical_signal': technical_signal,
                            'divergence_strength': divergence_strength
                        },
                        impact_score=min(divergence_strength / 0.5, 1.0)
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting signal divergence: {e}")
            return []
    
    def run_detection(self, current_data: Dict) -> Dict:
        """Run comprehensive anomaly detection"""
        try:
            symbol = current_data.get('symbol', 'UNKNOWN')
            sentiment_score = current_data.get('sentiment_score', 0.0)
            technical_score = current_data.get('technical_score', 0.0)
            confidence = current_data.get('confidence', 0.0)
            news_count = current_data.get('news_count', 0)
            
            # Get baseline statistics
            baseline = self.get_baseline_stats()
            
            all_anomalies = []
            
            # Run all detection methods
            all_anomalies.extend(self.detect_sentiment_anomalies(symbol, sentiment_score, baseline))
            all_anomalies.extend(self.detect_confidence_anomalies(symbol, confidence, baseline))
            all_anomalies.extend(self.detect_news_anomalies(symbol, news_count, baseline))
            all_anomalies.extend(self.detect_technical_anomalies(symbol, technical_score, baseline))
            all_anomalies.extend(self.detect_signal_divergence(symbol, sentiment_score, technical_score))
            
            # Sort by impact score
            all_anomalies.sort(key=lambda x: x.impact_score, reverse=True)
            
            # Calculate risk level
            if all_anomalies:
                max_impact = max(a.impact_score for a in all_anomalies)
                critical_count = len([a for a in all_anomalies if a.severity == AnomalySeverity.CRITICAL])
                high_count = len([a for a in all_anomalies if a.severity == AnomalySeverity.HIGH])
                
                if critical_count > 0:
                    risk_level = "CRITICAL"
                elif high_count > 0:
                    risk_level = "HIGH"
                elif len(all_anomalies) > 1:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
            else:
                risk_level = "NORMAL"
            
            return {
                'anomalies': all_anomalies,
                'total_anomalies': len(all_anomalies),
                'risk_level': risk_level,
                'max_impact_score': max(a.impact_score for a in all_anomalies) if all_anomalies else 0.0,
                'severity_counts': {
                    'critical': len([a for a in all_anomalies if a.severity == AnomalySeverity.CRITICAL]),
                    'high': len([a for a in all_anomalies if a.severity == AnomalySeverity.HIGH]),
                    'medium': len([a for a in all_anomalies if a.severity == AnomalySeverity.MEDIUM]),
                    'low': len([a for a in all_anomalies if a.severity == AnomalySeverity.LOW])
                },
                'detection_timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'baseline': baseline
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {
                'anomalies': [],
                'total_anomalies': 0,
                'risk_level': "ERROR",
                'error': str(e),
                'detection_timestamp': datetime.now().isoformat()
            }

def test_simple_anomaly_detection():
    """Test the simplified anomaly detection system"""
    print("⚡ Testing Simplified Anomaly Detection System")
    print("=" * 60)
    
    detector = SimpleAnomalyDetector()
    
    # Get baseline stats
    baseline = detector.get_baseline_stats()
    if baseline.get('data_available', False):
        print("📊 Baseline Statistics:")
        print(f"  Records: {baseline['total_records']}")
        print(f"  Avg Sentiment: {baseline['sentiment']['mean']:.3f} (±{baseline['sentiment']['std']:.3f})")
        print(f"  Avg Confidence: {baseline['confidence']['mean']:.3f}")
        print(f"  Avg Technical: {baseline['technical']['mean']:.3f}")
    else:
        print("⚠️ No baseline data available")
    
    # Test cases
    test_cases = [
        {
            'name': 'Normal Conditions',
            'data': {
                'symbol': 'CBA.AX',
                'sentiment_score': 0.10,
                'technical_score': 0.05,
                'confidence': 0.75,
                'news_count': 2
            }
        },
        {
            'name': 'Extreme Positive Sentiment',
            'data': {
                'symbol': 'WBC.AX',
                'sentiment_score': 0.45,  # Very high
                'technical_score': 0.20,
                'confidence': 0.85,
                'news_count': 15  # High news
            }
        },
        {
            'name': 'Signal Divergence',
            'data': {
                'symbol': 'ANZ.AX',
                'sentiment_score': 0.30,   # Bullish
                'technical_score': -0.25,  # Bearish
                'confidence': 0.80,
                'news_count': 5
            }
        },
        {
            'name': 'High Confidence Anomaly',
            'data': {
                'symbol': 'NAB.AX',
                'sentiment_score': 0.15,
                'technical_score': 0.10,
                'confidence': 0.95,  # Very high confidence
                'news_count': 3
            }
        }
    ]
    
    print(f"\n🧪 Anomaly Detection Tests:")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  {i}. {test_case['name']}")
        results = detector.run_detection(test_case['data'])
        
        print(f"     Risk Level: {results['risk_level']}")
        print(f"     Anomalies: {results['total_anomalies']}")
        
        if results['anomalies']:
            for anomaly in results['anomalies'][:2]:  # Show first 2
                print(f"     • {anomaly.type.value.upper()} ({anomaly.severity.value}): {anomaly.description}")
        else:
            print("     • No anomalies detected")
    
    print("\n✅ Simplified Anomaly Detection Test Complete!")

if __name__ == "__main__":
    test_simple_anomaly_detection()
