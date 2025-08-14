"""
Real-Time Anomaly Detection System
Detects unusual market conditions, breaking news impacts, and trading anomalies
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import json
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    VOLUME_SPIKE = "volume_spike"
    PRICE_DIVERGENCE = "price_divergence"
    SENTIMENT_SHOCK = "sentiment_shock"
    NEWS_IMPACT = "news_impact"
    TECHNICAL_BREAKDOWN = "technical_breakdown"
    CORRELATION_BREAK = "correlation_break"

class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Anomaly:
    """
    Data class for anomaly detection results
    """
    type: AnomalyType
    severity: AnomalySeverity
    symbol: str
    timestamp: datetime
    description: str
    confidence: float
    data: Dict
    impact_score: float

class AnomalyDetector:
    """
    Advanced anomaly detection system for market conditions and trading signals
    """
    
    def __init__(self, database_path: str = "morning_analysis.db"):
        self.database_path = database_path
        self.lookback_days = 30  # Days for baseline calculation
        
        # Anomaly thresholds
        self.thresholds = {
            'sentiment_z_score': 2.5,      # Standard deviations from mean
            'price_change_z_score': 2.0,
            'volume_multiplier': 3.0,       # X times normal volume
            'news_count_multiplier': 2.5,   # X times normal news volume
            'correlation_break': 0.3,       # Correlation drop threshold
            'technical_divergence': 0.8     # Technical vs price divergence
        }
        
        # Impact scoring weights
        self.impact_weights = {
            'magnitude': 0.3,
            'rarity': 0.2,
            'market_cap_effect': 0.2,
            'timing': 0.15,
            'persistence': 0.15
        }
    
    def get_baseline_statistics(self, symbol: str, days: int = None) -> Dict:
        """
        Calculate baseline statistics for anomaly detection
        """
        if days is None:
            days = self.lookback_days
            
        try:
            conn = sqlite3.connect(self.database_path)
            
            # Get historical data for baseline
            query = """
            SELECT 
                ef.symbol,
                ef.sentiment_score,
                ef.technical_score,
                ef.confidence,
                ef.news_count,
                ef.timestamp,
                eo.actual_price_change,
                eo.volume_change_percent
            FROM enhanced_features ef
            LEFT JOIN enhanced_outcomes eo ON ef.symbol = eo.symbol 
                AND date(ef.timestamp) = date(eo.timestamp)
            WHERE ef.symbol = ? 
                AND ef.timestamp > datetime('now', '-{} days')
            ORDER BY ef.timestamp DESC
            """.format(days)
            
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return {'data_available': False}
            
            # Calculate baseline statistics
            baseline = {
                'data_available': True,
                'sample_size': len(df),
                'sentiment': {
                    'mean': df['sentiment_score'].mean(),
                    'std': df['sentiment_score'].std(),
                    'min': df['sentiment_score'].min(),
                    'max': df['sentiment_score'].max()
                },
                'technical': {
                    'mean': df['technical_score'].mean(),
                    'std': df['technical_score'].std(),
                    'min': df['technical_score'].min(),
                    'max': df['technical_score'].max()
                },
                'news_count': {
                    'mean': df['news_count'].mean(),
                    'std': df['news_count'].std(),
                    'max': df['news_count'].max()
                },
                'confidence': {
                    'mean': df['confidence'].mean(),
                    'std': df['confidence'].std()
                }
            }
            
            # Price and volume statistics (if available)
            if 'actual_price_change' in df.columns and not df['actual_price_change'].isna().all():
                price_data = df['actual_price_change'].dropna()
                baseline['price_change'] = {
                    'mean': price_data.mean(),
                    'std': price_data.std(),
                    'min': price_data.min(),
                    'max': price_data.max()
                }
            
            if 'volume_change_percent' in df.columns and not df['volume_change_percent'].isna().all():
                volume_data = df['volume_change_percent'].dropna()
                baseline['volume'] = {
                    'mean': volume_data.mean(),
                    'std': volume_data.std(),
                    'max': volume_data.max()
                }
            
            return baseline
            
        except Exception as e:
            logger.error(f"Error calculating baseline statistics: {e}")
            return {'data_available': False, 'error': str(e)}
    
    def detect_sentiment_anomalies(self, symbol: str, current_sentiment: float) -> List[Anomaly]:
        """
        Detect sentiment-based anomalies
        """
        anomalies = []
        baseline = self.get_baseline_statistics(symbol)
        
        if not baseline.get('data_available', False):
            return anomalies
        
        try:
            # Calculate z-score for current sentiment
            sentiment_mean = baseline['sentiment']['mean']
            sentiment_std = baseline['sentiment']['std']
            
            if sentiment_std > 0:
                z_score = (current_sentiment - sentiment_mean) / sentiment_std
                
                if abs(z_score) > self.thresholds['sentiment_z_score']:
                    severity = AnomalySeverity.CRITICAL if abs(z_score) > 4 else \
                              AnomalySeverity.HIGH if abs(z_score) > 3 else \
                              AnomalySeverity.MEDIUM
                    
                    direction = "extremely positive" if z_score > 0 else "extremely negative"
                    impact_score = min(abs(z_score) / 5.0, 1.0)  # Normalize to 0-1
                    
                    anomaly = Anomaly(
                        type=AnomalyType.SENTIMENT_SHOCK,
                        severity=severity,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        description=f"Sentiment anomaly detected: {direction} sentiment (z-score: {z_score:.2f})",
                        confidence=min(abs(z_score) / 5.0, 1.0),
                        data={
                            'current_sentiment': current_sentiment,
                            'baseline_mean': sentiment_mean,
                            'baseline_std': sentiment_std,
                            'z_score': z_score
                        },
                        impact_score=impact_score
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting sentiment anomalies: {e}")
            return anomalies
    
    def detect_news_volume_anomalies(self, symbol: str, current_news_count: int) -> List[Anomaly]:
        """
        Detect news volume anomalies
        """
        anomalies = []
        baseline = self.get_baseline_statistics(symbol)
        
        if not baseline.get('data_available', False):
            return anomalies
        
        try:
            baseline_mean = baseline['news_count']['mean']
            
            if baseline_mean > 0:
                multiplier = current_news_count / baseline_mean
                
                if multiplier > self.thresholds['news_count_multiplier']:
                    severity = AnomalySeverity.CRITICAL if multiplier > 5 else \
                              AnomalySeverity.HIGH if multiplier > 4 else \
                              AnomalySeverity.MEDIUM
                    
                    impact_score = min(multiplier / 5.0, 1.0)
                    
                    anomaly = Anomaly(
                        type=AnomalyType.NEWS_IMPACT,
                        severity=severity,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        description=f"News volume spike: {multiplier:.1f}x normal volume ({current_news_count} vs {baseline_mean:.1f})",
                        confidence=min(multiplier / 5.0, 1.0),
                        data={
                            'current_news_count': current_news_count,
                            'baseline_mean': baseline_mean,
                            'multiplier': multiplier
                        },
                        impact_score=impact_score
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting news volume anomalies: {e}")
            return anomalies
    
    def detect_technical_divergence(self, symbol: str, 
                                  technical_score: float, 
                                  sentiment_score: float) -> List[Anomaly]:
        """
        Detect divergence between technical and sentiment signals
        """
        anomalies = []
        
        try:
            # Calculate signal divergence
            # If both signals point in same direction, no divergence
            # If they point in opposite directions, check magnitude
            
            sentiment_direction = 1 if sentiment_score > 0 else -1 if sentiment_score < 0 else 0
            technical_direction = 1 if technical_score > 0 else -1 if technical_score < 0 else 0
            
            if sentiment_direction * technical_direction < 0:  # Opposite directions
                # Calculate divergence strength
                divergence_magnitude = abs(sentiment_score) + abs(technical_score)
                
                if divergence_magnitude > self.thresholds['technical_divergence']:
                    severity = AnomalySeverity.HIGH if divergence_magnitude > 1.0 else \
                              AnomalySeverity.MEDIUM
                    
                    sentiment_signal = "BULLISH" if sentiment_score > 0 else "BEARISH"
                    technical_signal = "BULLISH" if technical_score > 0 else "BEARISH"
                    
                    impact_score = min(divergence_magnitude / 1.5, 1.0)
                    
                    anomaly = Anomaly(
                        type=AnomalyType.PRICE_DIVERGENCE,
                        severity=severity,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        description=f"Signal divergence: Sentiment={sentiment_signal} vs Technical={technical_signal}",
                        confidence=min(divergence_magnitude / 1.5, 1.0),
                        data={
                            'sentiment_score': sentiment_score,
                            'technical_score': technical_score,
                            'divergence_magnitude': divergence_magnitude,
                            'sentiment_signal': sentiment_signal,
                            'technical_signal': technical_signal
                        },
                        impact_score=impact_score
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting technical divergence: {e}")
            return anomalies
    
    def detect_correlation_breaks(self, symbols: List[str]) -> List[Anomaly]:
        """
        Detect breaks in normal correlation patterns between bank stocks
        """
        anomalies = []
        
        try:
            # Get recent data for all symbols
            conn = sqlite3.connect(self.database_path)
            
            # Calculate correlation matrix for recent period
            query = """
            SELECT symbol, sentiment_score, timestamp
            FROM enhanced_features 
            WHERE symbol IN ({}) 
                AND timestamp > datetime('now', '-7 days')
            ORDER BY timestamp DESC
            """.format(','.join(['?' for _ in symbols]))
            
            df = pd.read_sql_query(query, conn, params=symbols)
            conn.close()
            
            if len(df) < 10:  # Need sufficient data
                return anomalies
            
            # Pivot to get correlation matrix
            pivot_df = df.pivot(index='timestamp', columns='symbol', values='sentiment_score')
            correlation_matrix = pivot_df.corr()
            
            # Check for unusually low correlations (normally banks are correlated)
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols[i+1:], i+1):
                    if symbol1 in correlation_matrix.index and symbol2 in correlation_matrix.columns:
                        correlation = correlation_matrix.loc[symbol1, symbol2]
                        
                        if not pd.isna(correlation) and correlation < self.thresholds['correlation_break']:
                            severity = AnomalySeverity.HIGH if correlation < 0 else AnomalySeverity.MEDIUM
                            
                            impact_score = max(0, (0.8 - correlation) / 0.8)
                            
                            anomaly = Anomaly(
                                type=AnomalyType.CORRELATION_BREAK,
                                severity=severity,
                                symbol=f"{symbol1}-{symbol2}",
                                timestamp=datetime.now(),
                                description=f"Correlation breakdown between {symbol1} and {symbol2}: {correlation:.3f}",
                                confidence=impact_score,
                                data={
                                    'symbol1': symbol1,
                                    'symbol2': symbol2,
                                    'correlation': correlation,
                                    'expected_correlation': 0.7  # Normal bank correlation
                                },
                                impact_score=impact_score
                            )
                            
                            anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting correlation breaks: {e}")
            return anomalies
    
    def run_comprehensive_detection(self, current_data: Dict) -> Dict:
        """
        Run comprehensive anomaly detection across all systems
        """
        all_anomalies = []
        
        try:
            symbol = current_data.get('symbol', 'UNKNOWN')
            sentiment_score = current_data.get('sentiment_score', 0.0)
            technical_score = current_data.get('technical_score', 0.0)
            news_count = current_data.get('news_count', 0)
            
            # Detect sentiment anomalies
            sentiment_anomalies = self.detect_sentiment_anomalies(symbol, sentiment_score)
            all_anomalies.extend(sentiment_anomalies)
            
            # Detect news volume anomalies
            news_anomalies = self.detect_news_volume_anomalies(symbol, news_count)
            all_anomalies.extend(news_anomalies)
            
            # Detect technical divergence
            divergence_anomalies = self.detect_technical_divergence(symbol, technical_score, sentiment_score)
            all_anomalies.extend(divergence_anomalies)
            
            # Detect correlation breaks (for bank stocks)
            if symbol in ['CBA', 'WBC', 'ANZ', 'NAB']:
                correlation_anomalies = self.detect_correlation_breaks(['CBA', 'WBC', 'ANZ', 'NAB'])
                all_anomalies.extend(correlation_anomalies)
            
            # Sort by impact score
            all_anomalies.sort(key=lambda x: x.impact_score, reverse=True)
            
            # Calculate overall risk level
            if all_anomalies:
                max_impact = max(a.impact_score for a in all_anomalies)
                critical_count = len([a for a in all_anomalies if a.severity == AnomalySeverity.CRITICAL])
                high_count = len([a for a in all_anomalies if a.severity == AnomalySeverity.HIGH])
                
                if critical_count > 0 or max_impact > 0.8:
                    risk_level = "CRITICAL"
                elif high_count > 1 or max_impact > 0.6:
                    risk_level = "HIGH"
                elif len(all_anomalies) > 2:
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
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive anomaly detection: {e}")
            return {
                'anomalies': [],
                'total_anomalies': 0,
                'risk_level': "ERROR",
                'error': str(e),
                'detection_timestamp': datetime.now().isoformat()
            }

def test_anomaly_detection():
    """
    Test the anomaly detection system
    """
    print("⚡ Testing Anomaly Detection System")
    print("=" * 50)
    
    detector = AnomalyDetector()
    
    # Test cases simulating various market conditions
    test_cases = [
        {
            'name': 'Normal Market Conditions',
            'data': {
                'symbol': 'CBA',
                'sentiment_score': 0.15,
                'technical_score': 0.10,
                'news_count': 8
            }
        },
        {
            'name': 'Extreme Positive Sentiment',
            'data': {
                'symbol': 'WBC',
                'sentiment_score': 0.85,  # Very high
                'technical_score': 0.20,
                'news_count': 25  # High news volume
            }
        },
        {
            'name': 'Signal Divergence',
            'data': {
                'symbol': 'ANZ',
                'sentiment_score': 0.60,   # Bullish sentiment
                'technical_score': -0.50,  # Bearish technical
                'news_count': 5
            }
        },
        {
            'name': 'Market Shock Event',
            'data': {
                'symbol': 'NAB',
                'sentiment_score': -0.75,  # Very negative
                'technical_score': -0.40,
                'news_count': 40  # News explosion
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print(f"Data: {test_case['data']}")
        
        results = detector.run_comprehensive_detection(test_case['data'])
        
        print(f"Risk Level: {results['risk_level']}")
        print(f"Total Anomalies: {results['total_anomalies']}")
        print(f"Max Impact Score: {results['max_impact_score']:.3f}")
        
        if results['anomalies']:
            print("\nDetected Anomalies:")
            for anomaly in results['anomalies'][:3]:  # Show top 3
                print(f"  • {anomaly.type.value.upper()} ({anomaly.severity.value}): {anomaly.description}")
                print(f"    Impact: {anomaly.impact_score:.3f}, Confidence: {anomaly.confidence:.3f}")
        else:
            print("No anomalies detected")
    
    print("\n✅ Anomaly Detection Test Complete!")

if __name__ == "__main__":
    test_anomaly_detection()
