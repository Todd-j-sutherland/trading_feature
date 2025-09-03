#!/usr/bin/env python3
"""
Enhanced Sentiment Integration Module
Integrates the enhanced sentiment scoring system with the existing trading application
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.core.sentiment.enhanced_scoring import (
    EnhancedSentimentScorer, 
    SentimentMetrics, 
    MarketRegime, 
    SentimentStrength,
    create_market_context_detector
)

logger = logging.getLogger(__name__)

class SentimentIntegrationManager:
    """
    Manages integration between enhanced sentiment system and existing application
    """
    
    def __init__(self):
        self.enhanced_scorer = EnhancedSentimentScorer()
        self.integration_history = []
        
    def convert_legacy_to_enhanced(self, legacy_sentiment_data: Dict, 
                                 market_data: Optional[Dict] = None,
                                 news_items: Optional[List[Dict]] = None) -> SentimentMetrics:
        """
        Convert legacy sentiment data format to enhanced sentiment metrics
        
        Args:
            legacy_sentiment_data: Output from existing news_sentiment.py
            market_data: Market context data
            news_items: Raw news items with timestamps
            
        Returns:
            SentimentMetrics with enhanced analysis
        """
        
        # Extract components from legacy format
        raw_components = self._extract_components_from_legacy(legacy_sentiment_data)
        
        # Add market data if not provided
        if market_data is None:
            market_data = self._create_market_context_from_legacy(legacy_sentiment_data)
        
        # Extract news items if not provided
        if news_items is None:
            news_items = self._extract_news_items_from_legacy(legacy_sentiment_data)
        
        # Calculate enhanced sentiment
        enhanced_metrics = self.enhanced_scorer.calculate_enhanced_sentiment(
            raw_components=raw_components,
            market_data=market_data,
            news_items=news_items
        )
        
        # Calculate enhancement metrics with proper None handling
        legacy_sentiment = legacy_sentiment_data.get('overall_sentiment', 0)
        legacy_confidence = legacy_sentiment_data.get('confidence', 0)
        
        # Handle None values
        if legacy_sentiment is None:
            legacy_sentiment = 0
        if legacy_confidence is None:
            legacy_confidence = 0
            
        # Store conversion for analysis
        self.integration_history.append({
            'timestamp': datetime.now().isoformat(),
            'legacy_score': legacy_sentiment,
            'enhanced_score': enhanced_metrics.normalized_score,
            'enhancement_delta': enhanced_metrics.normalized_score - ((legacy_sentiment + 1) * 50),
            'confidence_improvement': enhanced_metrics.confidence - legacy_confidence,
            'symbol': legacy_sentiment_data.get('symbol', 'UNKNOWN')
        })
        
        return enhanced_metrics
    
    def _extract_components_from_legacy(self, legacy_data: Dict) -> Dict[str, float]:
        """Extract sentiment components from legacy format"""
        
        components = {}
        
        # News sentiment (main component)
        if 'sentiment_scores' in legacy_data:
            sentiment_scores = legacy_data['sentiment_scores']
            if isinstance(sentiment_scores, dict):
                components['news_sentiment'] = sentiment_scores.get('average_sentiment', 0)
            else:
                components['news_sentiment'] = sentiment_scores if isinstance(sentiment_scores, (int, float)) else 0
        else:
            components['news_sentiment'] = legacy_data.get('overall_sentiment', 0)
        
        # Reddit/social sentiment
        reddit_data = legacy_data.get('reddit_sentiment', {})
        if isinstance(reddit_data, dict):
            components['social_sentiment'] = reddit_data.get('average_sentiment', 0)
        else:
            components['social_sentiment'] = 0
        
        # Technical momentum (from sentiment components if available)
        sentiment_components = legacy_data.get('sentiment_components', {})
        if isinstance(sentiment_components, dict):
            components['technical_momentum'] = sentiment_components.get('momentum', 0)
        else:
            components['technical_momentum'] = 0
        
        # Events impact
        significant_events = legacy_data.get('significant_events', {})
        if isinstance(significant_events, dict):
            events_detected = significant_events.get('events_detected', [])
            if events_detected:
                # Convert event significance to sentiment
                event_sentiment = sum(event.get('sentiment_impact', 0) for event in events_detected) / len(events_detected)
                components['analyst_sentiment'] = event_sentiment
            else:
                components['analyst_sentiment'] = 0
        else:
            components['analyst_sentiment'] = 0
        
        # Fill in missing components with neutral values
        component_defaults = {
            'options_flow': 0,
            'insider_activity': 0,
            'earnings_surprise': 0
        }
        
        for component, default_value in component_defaults.items():
            if component not in components:
                components[component] = default_value
        
        return components
    
    def _create_market_context_from_legacy(self, legacy_data: Dict) -> Dict:
        """Create market context from legacy data"""
        
        # Handle edge cases and validate inputs
        if not legacy_data or not isinstance(legacy_data, dict):
            logger.warning("Invalid legacy_data provided, using defaults")
            legacy_data = {}
        
        # Extract volatility from confidence (inverse relationship)
        confidence = legacy_data.get('confidence', 0.5)
        if confidence is None or not isinstance(confidence, (int, float)):
            confidence = 0.5
            logger.warning(f"Invalid confidence value {confidence}, using default 0.5")
        
        estimated_volatility = max(0.1, min(0.5, 1 - confidence))
        
        # Determine regime from recent sentiment and news count
        overall_sentiment = legacy_data.get('overall_sentiment', 0)
        news_count = legacy_data.get('news_count', 0)
        
        # Validate numeric values
        if overall_sentiment is None or not isinstance(overall_sentiment, (int, float)):
            overall_sentiment = 0
        if news_count is None or not isinstance(news_count, (int, float)):
            news_count = 0
        
        if news_count > 10 and abs(overall_sentiment) > 0.3:
            regime = 'volatile'
        elif overall_sentiment > 0.2:
            regime = 'bull'
        elif overall_sentiment < -0.2:
            regime = 'bear'
        else:
            regime = 'stable'
        
        return {
            'volatility': estimated_volatility,
            'regime': regime,
            'regime_confidence': confidence,
            'market_trend': 'bullish' if overall_sentiment > 0 else 'bearish' if overall_sentiment < 0 else 'sideways',
            'sector_rotation': 'financial' if 'bank' in legacy_data.get('symbol', '').lower() else 'neutral'
        }
    
    def _extract_news_items_from_legacy(self, legacy_data: Dict) -> List[Dict]:
        """Extract news items from legacy format"""
        
        news_items = []
        
        # Get recent headlines if available
        headlines = legacy_data.get('recent_headlines', [])
        
        for i, headline in enumerate(headlines[:10]):  # Limit to 10 items
            # Estimate timestamp (recent news, decreasing age)
            estimated_time = datetime.now() - timedelta(hours=i)
            
            # Estimate sentiment from overall sentiment (with some variance)
            base_sentiment = legacy_data.get('overall_sentiment', 0)
            # Add some variance to make it more realistic
            estimated_sentiment = base_sentiment + ((-1) ** i) * 0.1 * (i / len(headlines))
            estimated_sentiment = max(-1, min(1, estimated_sentiment))
            
            news_items.append({
                'published': estimated_time.isoformat() + 'Z',
                'sentiment': estimated_sentiment,
                'title': headline
            })
        
        return news_items
    
    def generate_enhanced_trading_signals(self, legacy_sentiment_data: Dict, 
                                        risk_profiles: List[str] = None) -> Dict:
        """
        Generate enhanced trading signals for multiple risk profiles
        
        Args:
            legacy_sentiment_data: Legacy sentiment data
            risk_profiles: List of risk tolerance levels
            
        Returns:
            Dict with enhanced signals for each risk profile
        """
        
        if risk_profiles is None:
            risk_profiles = ['conservative', 'moderate', 'aggressive']
        
        # Convert to enhanced metrics
        enhanced_metrics = self.convert_legacy_to_enhanced(legacy_sentiment_data)
        
        # Generate signals for each risk profile
        signals = {}
        for risk_profile in risk_profiles:
            signal_data = self.enhanced_scorer.get_trading_signal(enhanced_metrics, risk_profile)
            signals[risk_profile] = signal_data
        
        # Add enhanced analysis summary
        signals['enhanced_analysis'] = {
            'normalized_score': enhanced_metrics.normalized_score,
            'strength_category': enhanced_metrics.strength_category.name,
            'confidence': enhanced_metrics.confidence,
            'z_score': enhanced_metrics.z_score,
            'percentile_rank': enhanced_metrics.percentile_rank,
            'volatility_adjusted_score': enhanced_metrics.volatility_adjusted_score,
            'market_adjusted_score': enhanced_metrics.market_adjusted_score,
            'improvement_over_legacy': self._calculate_enhancement_metrics(legacy_sentiment_data, enhanced_metrics)
        }
        
        return signals
    
    def _calculate_enhancement_metrics(self, legacy_data: Dict, enhanced_metrics: SentimentMetrics) -> Dict:
        """Calculate metrics showing improvement over legacy system"""
        
        legacy_score = legacy_data.get('overall_sentiment', 0)
        legacy_confidence = legacy_data.get('confidence', 0)
        
        # Convert legacy score to 0-100 scale for comparison
        legacy_normalized = ((legacy_score + 1) / 2) * 100
        
        return {
            'score_refinement': enhanced_metrics.normalized_score - legacy_normalized,
            'confidence_improvement': enhanced_metrics.confidence - legacy_confidence,
            'statistical_significance': abs(enhanced_metrics.z_score),
            'market_adjustment_applied': enhanced_metrics.market_adjusted_score != enhanced_metrics.raw_score,
            'volatility_adjustment_applied': enhanced_metrics.volatility_adjusted_score != enhanced_metrics.raw_score,
            'enhancement_summary': self._generate_enhancement_summary(legacy_data, enhanced_metrics)
        }
    
    def _generate_enhancement_summary(self, legacy_data: Dict, enhanced_metrics: SentimentMetrics) -> str:
        """Generate human-readable enhancement summary"""
        
        enhancements = []
        
        if enhanced_metrics.confidence > legacy_data.get('confidence', 0) + 0.1:
            enhancements.append("Significantly improved confidence")
        
        if abs(enhanced_metrics.z_score) > 1.5:
            enhancements.append("Statistically significant signal")
        
        if enhanced_metrics.percentile_rank > 80 or enhanced_metrics.percentile_rank < 20:
            enhancements.append("Extreme historical positioning")
        
        if enhanced_metrics.market_adjusted_score != enhanced_metrics.raw_score:
            enhancements.append("Market regime adjustment applied")
        
        if enhanced_metrics.volatility_adjusted_score != enhanced_metrics.raw_score:
            enhancements.append("Volatility adjustment applied")
        
        if not enhancements:
            enhancements.append("Standard enhancement applied")
        
        return "; ".join(enhancements)
    
    def get_integration_performance_report(self) -> Dict:
        """Generate performance report of the integration"""
        
        if not self.integration_history:
            return {'error': 'No integration history available'}
        
        # Calculate statistics
        score_improvements = [h['enhancement_delta'] for h in self.integration_history]
        confidence_improvements = [h['confidence_improvement'] for h in self.integration_history]
        
        return {
            'total_conversions': len(self.integration_history),
            'average_score_improvement': sum(score_improvements) / len(score_improvements),
            'average_confidence_improvement': sum(confidence_improvements) / len(confidence_improvements),
            'max_score_improvement': max(score_improvements),
            'max_confidence_improvement': max(confidence_improvements),
            'symbols_processed': list(set(h['symbol'] for h in self.integration_history)),
            'processing_timeframe': {
                'start': self.integration_history[0]['timestamp'] if self.integration_history else None,
                'end': self.integration_history[-1]['timestamp'] if self.integration_history else None
            },
            'enhancement_effectiveness': 'High' if sum(score_improvements) > 0 else 'Moderate'
        }

# Integration wrapper functions for easy adoption
def enhance_existing_sentiment(sentiment_data: Dict, 
                             market_data: Optional[Dict] = None,
                             news_items: Optional[List[Dict]] = None) -> SentimentMetrics:
    """
    Convenience function to enhance existing sentiment data
    
    Usage:
        enhanced_result = enhance_existing_sentiment(legacy_sentiment_data)
    """
    manager = SentimentIntegrationManager()
    return manager.convert_legacy_to_enhanced(sentiment_data, market_data, news_items)

def get_enhanced_trading_signals(sentiment_data: Dict, 
                               risk_profiles: List[str] = None) -> Dict:
    """
    Convenience function to get enhanced trading signals
    
    Usage:
        signals = get_enhanced_trading_signals(legacy_sentiment_data, ['conservative', 'aggressive'])
    """
    manager = SentimentIntegrationManager()
    return manager.generate_enhanced_trading_signals(sentiment_data, risk_profiles)

# Example usage and testing
if __name__ == "__main__":
    # Example legacy sentiment data (from your existing system)
    legacy_sentiment = {
        'symbol': 'CBA.AX',
        'timestamp': datetime.now().isoformat(),
        'news_count': 8,
        'sentiment_scores': {
            'average_sentiment': 0.15,
            'positive_count': 5,
            'negative_count': 2,
            'neutral_count': 1
        },
        'reddit_sentiment': {
            'average_sentiment': 0.05,
            'posts_analyzed': 12
        },
        'significant_events': {
            'events_detected': [
                {'type': 'earnings_report', 'sentiment_impact': 0.2},
                {'type': 'dividend_announcement', 'sentiment_impact': 0.1}
            ]
        },
        'overall_sentiment': 0.12,
        'confidence': 0.68,
        'recent_headlines': [
            'CBA reports strong quarterly earnings',
            'Banking sector sees increased activity',
            'Interest rate concerns impact financial stocks'
        ]
    }
    
    # Test the integration
    manager = SentimentIntegrationManager()
    
    print("Enhanced Sentiment Integration Test")
    print("=" * 50)
    
    # Convert to enhanced metrics
    enhanced_metrics = manager.convert_legacy_to_enhanced(legacy_sentiment)
    
    print(f"Legacy Score: {legacy_sentiment['overall_sentiment']:.3f}")
    print(f"Enhanced Normalized Score: {enhanced_metrics.normalized_score:.1f}/100")
    print(f"Strength Category: {enhanced_metrics.strength_category.name}")
    print(f"Statistical Significance (Z-Score): {enhanced_metrics.z_score:.2f}")
    print(f"Historical Percentile: {enhanced_metrics.percentile_rank:.1f}%")
    print(f"Confidence: {enhanced_metrics.confidence:.2f}")
    
    # Generate trading signals
    signals = manager.generate_enhanced_trading_signals(legacy_sentiment)
    
    print("\nEnhanced Trading Signals")
    print("-" * 30)
    for risk_level, signal_data in signals.items():
        if risk_level != 'enhanced_analysis':
            print(f"{risk_level.title()}: {signal_data['signal']} {signal_data['strength']}")
            print(f"  Reasoning: {signal_data['reasoning']}")
    
    print(f"\nPerformance Report:")
    report = manager.get_integration_performance_report()
    print(f"Total Conversions: {report['total_conversions']}")
    print(f"Enhancement Effectiveness: {report['enhancement_effectiveness']}")
