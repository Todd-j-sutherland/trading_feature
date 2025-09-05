"""
AI-Enhanced Smart Position Sizing System
Integrates sentiment analysis, pattern recognition, and volatility forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings

from ..sentiment.enhanced_scoring import EnhancedSentimentScorer
from ..analysis.pattern_ai import AIPatternDetector
from ..monitoring.anomaly_ai import AnomalyDetector
from .risk_management import PositionRiskAssessor
from ...config.settings import Settings

logger = logging.getLogger(__name__)

class SmartPositionSizer:
    """
    AI-powered position sizing with sentiment-technical fusion
    Optimizes position sizes based on market conditions, sentiment, and risk
    """
    
    def __init__(self, sentiment_scorer=None, pattern_detector=None, anomaly_detector=None):
        # Initialize AI components
        self.sentiment_scorer = sentiment_scorer or EnhancedSentimentScorer()
        self.pattern_detector = pattern_detector or AIPatternDetector()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.risk_assessor = PositionRiskAssessor()
        
        # Position sizing models
        self.volatility_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.return_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.risk_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Scalers
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        
        # Training status
        self.is_trained = False
        
        # Base settings
        self.base_position_size = 0.02  # 2% of portfolio
        self.max_position_size = 0.10   # 10% max
        self.min_position_size = 0.005  # 0.5% min
        
        # Risk adjustment factors
        self.sentiment_multipliers = {
            'very_bullish': 1.5,     # Strong positive sentiment
            'bullish': 1.2,          # Moderate positive sentiment
            'neutral': 1.0,          # Neutral sentiment
            'bearish': 0.8,          # Moderate negative sentiment  
            'very_bearish': 0.5      # Strong negative sentiment
        }
        
        self.pattern_multipliers = {
            'strong_bullish': 1.4,   # Strong bullish patterns
            'bullish': 1.2,          # Bullish patterns
            'neutral': 1.0,          # No clear pattern
            'bearish': 0.8,          # Bearish patterns
            'strong_bearish': 0.6    # Strong bearish patterns
        }
        
        self.volatility_adjustments = {
            'very_low': 1.3,         # Low volatility = larger positions
            'low': 1.1,              # Moderately low volatility
            'normal': 1.0,           # Normal volatility
            'high': 0.8,             # High volatility = smaller positions
            'very_high': 0.5         # Very high volatility
        }
    
    def calculate_optimal_position_size(self, 
                                      symbol: str,
                                      current_price: float,
                                      portfolio_value: float,
                                      historical_data: pd.DataFrame,
                                      news_data: List[Dict] = None,
                                      max_risk_pct: float = 0.02) -> Dict[str, Any]:
        """
        Calculate optimal position size using AI-driven analysis
        
        Args:
            symbol: Trading symbol
            current_price: Current asset price
            portfolio_value: Total portfolio value
            historical_data: Historical price/volume data
            news_data: Recent news for sentiment analysis
            max_risk_pct: Maximum risk percentage (default 2%)
            
        Returns:
            Dictionary with position sizing recommendations
        """
        try:
            # 1. Sentiment Analysis
            sentiment_analysis = self._analyze_market_sentiment(symbol, news_data, historical_data)
            
            # 2. Pattern Recognition
            pattern_analysis = self._analyze_chart_patterns(historical_data, symbol)
            
            # 3. Anomaly Detection
            current_data = {
                'price': current_price,
                'volume': historical_data['Volume'].iloc[-1] if len(historical_data) > 0 else 0,
                'sentiment_score': sentiment_analysis['sentiment_score']
            }
            anomaly_analysis = self.anomaly_detector.detect_anomalies(symbol, current_data, historical_data)
            
            # 4. Volatility Forecast
            volatility_forecast = self._forecast_volatility(historical_data)
            
            # 5. Risk Assessment
            risk_assessment = self._assess_position_risk(historical_data, current_price)
            
            # 6. Calculate base position size
            base_size = self.base_position_size * portfolio_value / current_price
            
            # 7. Apply AI-driven adjustments
            adjustments = self._calculate_ai_adjustments(
                sentiment_analysis, pattern_analysis, anomaly_analysis, 
                volatility_forecast, risk_assessment
            )
            
            # 8. Calculate final position size
            adjusted_size = base_size * adjustments['total_multiplier']
            
            # 9. Apply risk constraints
            final_size = self._apply_risk_constraints(
                adjusted_size, portfolio_value, current_price, max_risk_pct
            )
            
            # 10. Generate recommendations
            recommendation = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'recommended_shares': int(final_size),
                'recommended_value': final_size * current_price,
                'position_pct': (final_size * current_price) / portfolio_value * 100,
                'confidence': adjustments['confidence'],
                
                # AI Analysis Components
                'sentiment_analysis': sentiment_analysis,
                'pattern_analysis': pattern_analysis,
                'anomaly_analysis': anomaly_analysis,
                'volatility_forecast': volatility_forecast,
                'risk_assessment': risk_assessment,
                
                # Adjustment Factors
                'adjustments': adjustments,
                
                # Risk Management
                'stop_loss_price': self._calculate_stop_loss(current_price, adjustments),
                'take_profit_price': self._calculate_take_profit(current_price, adjustments),
                'max_loss_amount': final_size * current_price * max_risk_pct,
                
                # Monitoring
                'monitoring_alerts': self._generate_monitoring_alerts(adjustments, anomaly_analysis)
            }
            
            logger.info(f"Position sizing calculated for {symbol}: "
                       f"{final_size:.0f} shares ({recommendation['position_pct']:.2f}%)")
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return self._fallback_position_size(symbol, current_price, portfolio_value, max_risk_pct)
    
    def _analyze_market_sentiment(self, symbol: str, news_data: List[Dict], 
                                 historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market sentiment using AI"""
        try:
            sentiment_score = 0.0
            sentiment_confidence = 0.0
            sentiment_category = 'neutral'
            
            if news_data and len(news_data) > 0:
                # Use enhanced sentiment scorer
                sentiment_results = []
                for news_item in news_data[-10:]:  # Last 10 news items
                    if 'title' in news_item or 'content' in news_item:
                        text = news_item.get('title', '') + ' ' + news_item.get('content', '')
                        result = self.sentiment_scorer.analyze_sentiment(text, symbol)
                        sentiment_results.append(result)
                
                if sentiment_results:
                    scores = [r.get('overall_sentiment', 0) for r in sentiment_results]
                    confidences = [r.get('confidence', 0) for r in sentiment_results]
                    
                    sentiment_score = np.mean(scores)
                    sentiment_confidence = np.mean(confidences)
            
            # Classify sentiment
            if sentiment_score > 0.6:
                sentiment_category = 'very_bullish'
            elif sentiment_score > 0.2:
                sentiment_category = 'bullish'
            elif sentiment_score > -0.2:
                sentiment_category = 'neutral'
            elif sentiment_score > -0.6:
                sentiment_category = 'bearish'
            else:
                sentiment_category = 'very_bearish'
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_category': sentiment_category,
                'sentiment_confidence': sentiment_confidence,
                'news_count': len(news_data) if news_data else 0
            }
            
        except Exception as e:
            logger.warning(f"Error in sentiment analysis: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_category': 'neutral',
                'sentiment_confidence': 0.0,
                'news_count': 0
            }
    
    def _analyze_chart_patterns(self, historical_data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Analyze chart patterns using AI"""
        try:
            if len(historical_data) < 20:
                return {
                    'pattern_strength': 0.0,
                    'pattern_category': 'neutral',
                    'pattern_confidence': 0.0,
                    'signals': []
                }
            
            # Use pattern detector
            pattern_result = self.pattern_detector.detect_patterns(historical_data, symbol)
            
            # Extract pattern signals
            signals = pattern_result.get('signals', [])
            bullish_signals = [s for s in signals if s.get('direction') == 'bullish']
            bearish_signals = [s for s in signals if s.get('direction') == 'bearish']
            
            # Calculate pattern strength
            bullish_strength = sum([s.get('strength', 0) for s in bullish_signals])
            bearish_strength = sum([s.get('strength', 0) for s in bearish_signals])
            net_strength = bullish_strength - bearish_strength
            
            # Categorize pattern
            if net_strength > 0.6:
                pattern_category = 'strong_bullish'
            elif net_strength > 0.2:
                pattern_category = 'bullish'
            elif net_strength > -0.2:
                pattern_category = 'neutral'
            elif net_strength > -0.6:
                pattern_category = 'bearish'
            else:
                pattern_category = 'strong_bearish'
            
            return {
                'pattern_strength': net_strength,
                'pattern_category': pattern_category,
                'pattern_confidence': pattern_result.get('confidence', 0.0),
                'signals': signals,
                'bullish_count': len(bullish_signals),
                'bearish_count': len(bearish_signals)
            }
            
        except Exception as e:
            logger.warning(f"Error in pattern analysis: {e}")
            return {
                'pattern_strength': 0.0,
                'pattern_category': 'neutral',
                'pattern_confidence': 0.0,
                'signals': []
            }
    
    def _forecast_volatility(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Forecast volatility using historical data"""
        try:
            if len(historical_data) < 20:
                return {
                    'predicted_volatility': 0.02,
                    'volatility_category': 'normal',
                    'volatility_trend': 'stable'
                }
            
            # Calculate returns
            returns = historical_data['Close'].pct_change().dropna()
            
            # Current volatility (20-day)
            current_vol = returns.tail(20).std()
            
            # Volatility trend (comparing recent vs longer-term)
            recent_vol = returns.tail(10).std()
            longer_vol = returns.tail(30).std() if len(returns) >= 30 else current_vol
            
            volatility_trend = 'increasing' if recent_vol > longer_vol * 1.1 else \
                              'decreasing' if recent_vol < longer_vol * 0.9 else 'stable'
            
            # Categorize volatility
            if current_vol < 0.01:
                volatility_category = 'very_low'
            elif current_vol < 0.02:
                volatility_category = 'low'
            elif current_vol < 0.04:
                volatility_category = 'normal'
            elif current_vol < 0.06:
                volatility_category = 'high'
            else:
                volatility_category = 'very_high'
            
            return {
                'predicted_volatility': current_vol,
                'volatility_category': volatility_category,
                'volatility_trend': volatility_trend,
                'recent_vs_longer': recent_vol / longer_vol if longer_vol > 0 else 1.0
            }
            
        except Exception as e:
            logger.warning(f"Error in volatility forecast: {e}")
            return {
                'predicted_volatility': 0.02,
                'volatility_category': 'normal',
                'volatility_trend': 'stable'
            }
    
    def _assess_position_risk(self, historical_data: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Assess position risk factors"""
        try:
            if len(historical_data) < 10:
                return {
                    'risk_score': 0.5,
                    'risk_category': 'medium',
                    'drawdown_risk': 0.1
                }
            
            # Calculate maximum drawdown
            prices = historical_data['Close']
            rolling_max = prices.expanding().max()
            drawdowns = (prices - rolling_max) / rolling_max
            max_drawdown = abs(drawdowns.min())
            
            # Calculate price position relative to recent range
            recent_high = prices.tail(20).max()
            recent_low = prices.tail(20).min()
            price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5
            
            # Risk scoring
            drawdown_risk = min(max_drawdown * 2, 1.0)  # Scale to 0-1
            position_risk = 1 - price_position  # Higher risk if near recent lows
            
            overall_risk = (drawdown_risk + position_risk) / 2
            
            # Categorize risk
            if overall_risk < 0.3:
                risk_category = 'low'
            elif overall_risk < 0.6:
                risk_category = 'medium'
            else:
                risk_category = 'high'
            
            return {
                'risk_score': overall_risk,
                'risk_category': risk_category,
                'drawdown_risk': max_drawdown,
                'price_position': price_position
            }
            
        except Exception as e:
            logger.warning(f"Error in risk assessment: {e}")
            return {
                'risk_score': 0.5,
                'risk_category': 'medium',
                'drawdown_risk': 0.1
            }
    
    def _calculate_ai_adjustments(self, sentiment: Dict, patterns: Dict, 
                                 anomalies: Dict, volatility: Dict, risk: Dict) -> Dict[str, Any]:
        """Calculate AI-driven position size adjustments"""
        
        # Individual multipliers
        sentiment_mult = self.sentiment_multipliers.get(sentiment['sentiment_category'], 1.0)
        pattern_mult = self.pattern_multipliers.get(patterns['pattern_category'], 1.0)
        volatility_mult = self.volatility_adjustments.get(volatility['volatility_category'], 1.0)
        
        # Risk adjustment
        risk_mult = 1.2 if risk['risk_category'] == 'low' else \
                   1.0 if risk['risk_category'] == 'medium' else 0.7
        
        # Anomaly adjustment
        anomaly_mult = 0.5 if anomalies['severity'] == 'severe' else \
                      0.8 if anomalies['severity'] == 'moderate' else 1.0
        
        # Calculate total multiplier
        total_multiplier = sentiment_mult * pattern_mult * volatility_mult * risk_mult * anomaly_mult
        
        # Confidence calculation
        confidence_factors = [
            sentiment['sentiment_confidence'],
            patterns['pattern_confidence'],
            1.0 - risk['risk_score'],  # Lower risk = higher confidence
            anomalies['confidence']
        ]
        overall_confidence = np.mean([f for f in confidence_factors if f > 0])
        
        return {
            'sentiment_multiplier': sentiment_mult,
            'pattern_multiplier': pattern_mult,
            'volatility_multiplier': volatility_mult,
            'risk_multiplier': risk_mult,
            'anomaly_multiplier': anomaly_mult,
            'total_multiplier': total_multiplier,
            'confidence': overall_confidence,
            'adjustment_reasoning': self._generate_adjustment_reasoning(
                sentiment_mult, pattern_mult, volatility_mult, risk_mult, anomaly_mult
            )
        }
    
    def _apply_risk_constraints(self, position_size: float, portfolio_value: float, 
                               current_price: float, max_risk_pct: float) -> float:
        """Apply risk management constraints"""
        
        # Position value constraints
        position_value = position_size * current_price
        max_position_value = portfolio_value * self.max_position_size
        min_position_value = portfolio_value * self.min_position_size
        
        # Risk-based constraints
        max_risk_value = portfolio_value * max_risk_pct
        max_shares_by_risk = max_risk_value / current_price
        
        # Apply all constraints
        constrained_size = min(
            position_size,
            max_position_value / current_price,
            max_shares_by_risk
        )
        
        constrained_size = max(constrained_size, min_position_value / current_price)
        
        return constrained_size
    
    def _calculate_stop_loss(self, current_price: float, adjustments: Dict) -> float:
        """Calculate dynamic stop loss based on AI analysis"""
        
        # Base stop loss (2% below entry)
        base_stop_pct = 0.02
        
        # Adjust based on volatility and confidence
        confidence = adjustments.get('confidence', 0.5)
        volatility_mult = adjustments.get('volatility_multiplier', 1.0)
        
        # Higher confidence = tighter stop, higher volatility = wider stop
        adjusted_stop_pct = base_stop_pct * (2 - confidence) * volatility_mult
        
        return current_price * (1 - adjusted_stop_pct)
    
    def _calculate_take_profit(self, current_price: float, adjustments: Dict) -> float:
        """Calculate dynamic take profit based on AI analysis"""
        
        # Base take profit (6% above entry)
        base_profit_pct = 0.06
        
        # Adjust based on sentiment and patterns
        sentiment_mult = adjustments.get('sentiment_multiplier', 1.0)
        pattern_mult = adjustments.get('pattern_multiplier', 1.0)
        
        # More bullish signals = higher profit target
        adjusted_profit_pct = base_profit_pct * sentiment_mult * pattern_mult
        
        return current_price * (1 + adjusted_profit_pct)
    
    def _generate_monitoring_alerts(self, adjustments: Dict, anomalies: Dict) -> List[str]:
        """Generate monitoring alerts based on AI analysis"""
        alerts = []
        
        if anomalies['severity'] in ['moderate', 'severe']:
            alerts.append(f"Market anomaly detected: {anomalies['severity']}")
        
        if adjustments['total_multiplier'] > 1.5:
            alerts.append("High conviction trade - increased position size")
        elif adjustments['total_multiplier'] < 0.7:
            alerts.append("Low conviction trade - reduced position size")
        
        if adjustments['confidence'] < 0.3:
            alerts.append("Low confidence - consider waiting for better setup")
        
        return alerts
    
    def _generate_adjustment_reasoning(self, sentiment_mult: float, pattern_mult: float,
                                     volatility_mult: float, risk_mult: float, 
                                     anomaly_mult: float) -> str:
        """Generate human-readable reasoning for adjustments"""
        
        reasons = []
        
        if sentiment_mult > 1.1:
            reasons.append("Positive sentiment increases position")
        elif sentiment_mult < 0.9:
            reasons.append("Negative sentiment reduces position")
        
        if pattern_mult > 1.1:
            reasons.append("Bullish patterns support larger position")
        elif pattern_mult < 0.9:
            reasons.append("Bearish patterns suggest smaller position")
        
        if volatility_mult < 0.9:
            reasons.append("High volatility reduces position size")
        elif volatility_mult > 1.1:
            reasons.append("Low volatility allows larger position")
        
        if risk_mult < 0.9:
            reasons.append("High risk environment reduces position")
        elif risk_mult > 1.1:
            reasons.append("Low risk environment increases position")
        
        if anomaly_mult < 0.9:
            reasons.append("Market anomalies suggest caution")
        
        return "; ".join(reasons) if reasons else "Standard position sizing applied"
    
    def _fallback_position_size(self, symbol: str, current_price: float, 
                               portfolio_value: float, max_risk_pct: float) -> Dict[str, Any]:
        """Fallback position sizing for error cases"""
        
        base_shares = (portfolio_value * self.base_position_size) / current_price
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'recommended_shares': int(base_shares),
            'recommended_value': base_shares * current_price,
            'position_pct': self.base_position_size * 100,
            'confidence': 0.5,
            'stop_loss_price': current_price * 0.98,
            'take_profit_price': current_price * 1.06,
            'max_loss_amount': base_shares * current_price * max_risk_pct,
            'error': 'Using fallback position sizing due to analysis error'
        }
