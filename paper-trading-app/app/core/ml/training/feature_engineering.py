#!/usr/bin/env python3
"""
Advanced Financial Feature Engineering
Implements Claude's suggestions for financial microstructure and alternative data features
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import requests
import json
import time
from dataclasses import dataclass
from collections import defaultdict
import warnings

logger = logging.getLogger(__name__)

@dataclass
class MarketMicrostructureFeatures:
    """Market microstructure features for trading"""
    bid_ask_spread_trend: float
    order_flow_imbalance: float
    volume_profile_score: float
    tick_size_impact: float
    market_depth_ratio: float
    price_impact_estimate: float

@dataclass
class CrossAssetFeatures:
    """Cross-asset correlation features"""
    aud_usd_correlation: float
    bond_yield_impact: float
    sector_rotation_signal: float
    commodity_correlation: float
    global_risk_sentiment: float

@dataclass
class AlternativeDataFeatures:
    """Alternative data features"""
    google_trends_score: float
    social_media_velocity: float
    news_clustering_score: float
    narrative_shift_indicator: float
    market_attention_score: float

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering for financial sentiment analysis
    Implements Claude's suggestions for microstructure and alternative data
    """
    
    def __init__(self):
        self.feature_cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=30)  # Cache features for 30 minutes
        
        # API configurations (would need actual API keys)
        self.api_configs = {
            'google_trends': {'enabled': False},  # Requires pytrends
            'social_media': {'enabled': False},   # Requires Twitter API
            'alternative_data': {'enabled': False}  # Requires specialized data providers
        }
        
        # Feature weights for different market conditions
        self.feature_weights = {
            'high_volatility': {
                'microstructure': 0.4,
                'cross_asset': 0.3,
                'alternative': 0.3
            },
            'normal': {
                'microstructure': 0.3,
                'cross_asset': 0.4,
                'alternative': 0.3
            },
            'low_volatility': {
                'microstructure': 0.2,
                'cross_asset': 0.5,
                'alternative': 0.3
            }
        }
    
    def engineer_comprehensive_features(self, symbol: str, sentiment_data: Dict, 
                                      news_data: List[Dict] = None) -> Dict:
        """
        Generate comprehensive feature set including all advanced features
        """
        try:
            # Base sentiment features
            base_features = self._extract_base_sentiment_features(sentiment_data)
            
            # Market microstructure features
            microstructure_features = self._engineer_microstructure_features(symbol)
            
            # Cross-asset features
            cross_asset_features = self._engineer_cross_asset_features(symbol)
            
            # Alternative data features
            alternative_features = self._engineer_alternative_data_features(symbol, news_data)
            
            # Temporal features
            temporal_features = self._engineer_temporal_features(sentiment_data)
            
            # News-specific features
            news_features = self._engineer_news_features(news_data) if news_data else {}
            
            # Market regime features
            regime_features = self._engineer_market_regime_features(symbol)
            
            # Combine all features
            comprehensive_features = {
                **base_features,
                **microstructure_features,
                **cross_asset_features,
                **alternative_features,
                **temporal_features,
                **news_features,
                **regime_features
            }
            
            # Add feature interactions
            interaction_features = self._engineer_feature_interactions(comprehensive_features)
            comprehensive_features.update(interaction_features)
            
            # Add feature quality metrics
            feature_quality = self._assess_feature_quality(comprehensive_features)
            
            return {
                'features': comprehensive_features,
                'feature_quality': feature_quality,
                'feature_count': len(comprehensive_features),
                'generation_timestamp': datetime.now().isoformat(),
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Comprehensive feature engineering failed: {e}")
            return {'features': {}, 'error': str(e)}
    
    def _extract_base_sentiment_features(self, sentiment_data: Dict) -> Dict:
        """Extract base sentiment features"""
        return {
            'sentiment_score': sentiment_data.get('overall_sentiment', 0),
            'sentiment_confidence': sentiment_data.get('confidence', 0.5),
            'news_count': sentiment_data.get('news_count', 0),
            'reddit_sentiment': sentiment_data.get('reddit_sentiment', 0),
            'event_score': sentiment_data.get('event_score', 0),
            'sentiment_volatility': sentiment_data.get('sentiment_volatility', 0),
        }
    
    def _engineer_microstructure_features(self, symbol: str) -> Dict:
        """
        Engineer market microstructure features
        These would require real market data feeds in production
        """
        cache_key = f"microstructure_{symbol}"
        
        if self._is_cached(cache_key):
            return self.feature_cache[cache_key]
        
        try:
            # Simulate microstructure features (in production, use real market data)
            features = {
                'bid_ask_spread_trend': self._calculate_spread_trend(symbol),
                'order_flow_imbalance': self._calculate_order_flow_imbalance(symbol),
                'volume_profile_score': self._calculate_volume_profile(symbol),
                'tick_size_impact': self._calculate_tick_impact(symbol),
                'market_depth_ratio': self._calculate_market_depth(symbol),
                'price_impact_estimate': self._estimate_price_impact(symbol),
                'liquidity_score': self._calculate_liquidity_score(symbol),
                'microstructure_quality': self._assess_microstructure_quality(symbol)
            }
            
            self._cache_features(cache_key, features)
            return features
            
        except Exception as e:
            logger.warning(f"Microstructure feature engineering failed: {e}")
            return self._get_default_microstructure_features()
    
    def _engineer_cross_asset_features(self, symbol: str) -> Dict:
        """Engineer cross-asset correlation features"""
        cache_key = f"cross_asset_{symbol}"
        
        if self._is_cached(cache_key):
            return self.feature_cache[cache_key]
        
        try:
            features = {
                'aud_usd_correlation': self._calculate_aud_correlation(symbol),
                'bond_yield_impact': self._calculate_bond_yield_impact(symbol),
                'sector_rotation_signal': self._calculate_sector_rotation(symbol),
                'commodity_correlation': self._calculate_commodity_correlation(symbol),
                'global_risk_sentiment': self._calculate_global_risk_sentiment(),
                'vix_correlation': self._calculate_vix_correlation(symbol),
                'interest_rate_sensitivity': self._calculate_rate_sensitivity(symbol),
                'cross_asset_momentum': self._calculate_cross_asset_momentum(symbol)
            }
            
            self._cache_features(cache_key, features)
            return features
            
        except Exception as e:
            logger.warning(f"Cross-asset feature engineering failed: {e}")
            return self._get_default_cross_asset_features()
    
    def _engineer_alternative_data_features(self, symbol: str, news_data: List[Dict] = None) -> Dict:
        """Engineer alternative data features"""
        cache_key = f"alternative_{symbol}"
        
        if self._is_cached(cache_key):
            return self.feature_cache[cache_key]
        
        try:
            features = {
                'google_trends_score': self._get_google_trends_score(symbol),
                'social_media_velocity': self._calculate_social_media_velocity(symbol),
                'news_clustering_score': self._calculate_news_clustering(news_data),
                'narrative_shift_indicator': self._detect_narrative_shift(news_data),
                'market_attention_score': self._calculate_attention_score(symbol),
                'search_volume_trend': self._get_search_volume_trend(symbol),
                'media_sentiment_divergence': self._calculate_media_divergence(symbol),
                'insider_activity_proxy': self._get_insider_activity_proxy(symbol)
            }
            
            self._cache_features(cache_key, features)
            return features
            
        except Exception as e:
            logger.warning(f"Alternative data feature engineering failed: {e}")
            return self._get_default_alternative_features()
    
    def _engineer_temporal_features(self, sentiment_data: Dict) -> Dict:
        """Engineer temporal features"""
        now = datetime.now()
        
        return {
            'hour_of_day': now.hour,
            'day_of_week': now.weekday(),
            'is_market_hours': 1 if 9 <= now.hour <= 16 else 0,
            'is_weekend': 1 if now.weekday() >= 5 else 0,
            'time_since_market_open': self._calculate_time_since_open(now),
            'time_until_market_close': self._calculate_time_until_close(now),
            'is_earnings_season': self._is_earnings_season(now),
            'is_end_of_quarter': self._is_end_of_quarter(now),
            'trading_session_type': self._get_trading_session_type(now)
        }
    
    def _engineer_news_features(self, news_data: List[Dict]) -> Dict:
        """Engineer news-specific features"""
        if not news_data:
            return {'news_feature_count': 0}
        
        try:
            # News velocity and timing
            news_timestamps = [self._parse_timestamp(n.get('timestamp', '')) for n in news_data]
            news_timestamps = [ts for ts in news_timestamps if ts is not None]
            
            # News content features
            headlines = [n.get('title', '') for n in news_data]
            all_text = ' '.join(headlines)
            
            features = {
                'news_velocity_1h': self._calculate_news_velocity(news_timestamps, hours=1),
                'news_velocity_4h': self._calculate_news_velocity(news_timestamps, hours=4),
                'news_velocity_24h': self._calculate_news_velocity(news_timestamps, hours=24),
                'avg_headline_length': np.mean([len(h) for h in headlines]) if headlines else 0,
                'headline_complexity': self._calculate_text_complexity(all_text),
                'financial_keyword_density': self._calculate_financial_keyword_density(all_text),
                'urgency_indicator': self._calculate_urgency_indicator(headlines),
                'source_diversity': len(set(n.get('source', '') for n in news_data)),
                'news_recency_score': self._calculate_news_recency_score(news_timestamps)
            }
            
            return features
            
        except Exception as e:
            logger.warning(f"News feature engineering failed: {e}")
            return {'news_feature_count': 0, 'error': str(e)}
    
    def _engineer_market_regime_features(self, symbol: str) -> Dict:
        """Engineer market regime features"""
        try:
            # These would use real market data in production
            features = {
                'market_regime': self._detect_market_regime(),
                'volatility_regime': self._detect_volatility_regime(),
                'trend_strength': self._calculate_trend_strength(symbol),
                'mean_reversion_indicator': self._calculate_mean_reversion(symbol),
                'momentum_regime': self._detect_momentum_regime(symbol),
                'market_stress_indicator': self._calculate_market_stress(),
                'sector_relative_strength': self._calculate_sector_strength(symbol),
                'market_breadth_indicator': self._calculate_market_breadth()
            }
            
            return features
            
        except Exception as e:
            logger.warning(f"Market regime feature engineering failed: {e}")
            return {'market_regime': 0, 'volatility_regime': 0}
    
    def _engineer_feature_interactions(self, features: Dict) -> Dict:
        """Engineer feature interactions"""
        try:
            interactions = {}
            
            # Sentiment-confidence interaction
            sentiment = features.get('sentiment_score', 0)
            confidence = features.get('sentiment_confidence', 0.5)
            interactions['sentiment_confidence_interaction'] = sentiment * confidence
            
            # News velocity and sentiment interaction
            news_velocity = features.get('news_velocity_1h', 0)
            interactions['news_velocity_sentiment_interaction'] = news_velocity * sentiment
            
            # Market hours and sentiment interaction
            market_hours = features.get('is_market_hours', 0)
            interactions['market_hours_sentiment'] = market_hours * sentiment
            
            # Cross-asset correlation and sentiment
            aud_correlation = features.get('aud_usd_correlation', 0)
            interactions['aud_sentiment_interaction'] = aud_correlation * sentiment
            
            # Volatility regime and confidence
            vol_regime = features.get('volatility_regime', 0)
            interactions['volatility_confidence_interaction'] = vol_regime * confidence
            
            # Alternative data and traditional sentiment
            google_trends = features.get('google_trends_score', 0)
            interactions['trends_sentiment_interaction'] = google_trends * sentiment
            
            return interactions
            
        except Exception as e:
            logger.warning(f"Feature interaction engineering failed: {e}")
            return {}
    
    # Microstructure feature calculation methods
    def _calculate_spread_trend(self, symbol: str) -> float:
        """Calculate bid-ask spread trend (simulated)"""
        # In production, this would use real market data
        return np.random.normal(0, 0.1)  # Simulated spread trend
    
    def _calculate_order_flow_imbalance(self, symbol: str) -> float:
        """Calculate order flow imbalance (simulated)"""
        return np.random.normal(0, 0.2)  # Simulated order flow
    
    def _calculate_volume_profile(self, symbol: str) -> float:
        """Calculate volume profile score (simulated)"""
        return np.random.uniform(-1, 1)  # Simulated volume profile
    
    def _calculate_tick_impact(self, symbol: str) -> float:
        """Calculate tick size impact (simulated)"""
        return np.random.normal(0, 0.05)
    
    def _calculate_market_depth(self, symbol: str) -> float:
        """Calculate market depth ratio (simulated)"""
        return np.random.uniform(0.5, 2.0)
    
    def _estimate_price_impact(self, symbol: str) -> float:
        """Estimate price impact (simulated)"""
        return np.random.exponential(0.1)
    
    def _calculate_liquidity_score(self, symbol: str) -> float:
        """Calculate liquidity score (simulated)"""
        return np.random.uniform(0, 1)
    
    def _assess_microstructure_quality(self, symbol: str) -> float:
        """Assess microstructure data quality (simulated)"""
        return np.random.uniform(0.7, 1.0)
    
    # Cross-asset feature calculation methods
    def _calculate_aud_correlation(self, symbol: str) -> float:
        """Calculate AUD/USD correlation impact (simulated)"""
        # In production, calculate rolling correlation with AUD/USD
        return np.random.normal(0, 0.3)
    
    def _calculate_bond_yield_impact(self, symbol: str) -> float:
        """Calculate bond yield impact on banks (simulated)"""
        # Banks are sensitive to interest rate changes
        return np.random.normal(0, 0.2)
    
    def _calculate_sector_rotation(self, symbol: str) -> float:
        """Calculate sector rotation signal (simulated)"""
        return np.random.normal(0, 0.15)
    
    def _calculate_commodity_correlation(self, symbol: str) -> float:
        """Calculate commodity correlation (simulated)"""
        return np.random.normal(0, 0.1)
    
    def _calculate_global_risk_sentiment(self) -> float:
        """Calculate global risk sentiment (simulated)"""
        return np.random.normal(0, 0.25)
    
    def _calculate_vix_correlation(self, symbol: str) -> float:
        """Calculate VIX correlation (simulated)"""
        return np.random.normal(-0.2, 0.2)  # Banks often negatively correlated with VIX
    
    def _calculate_rate_sensitivity(self, symbol: str) -> float:
        """Calculate interest rate sensitivity (simulated)"""
        return np.random.uniform(0.3, 0.8)  # Banks are typically rate-sensitive
    
    def _calculate_cross_asset_momentum(self, symbol: str) -> float:
        """Calculate cross-asset momentum (simulated)"""
        return np.random.normal(0, 0.2)
    
    # Alternative data feature calculation methods
    def _get_google_trends_score(self, symbol: str) -> float:
        """Get Google Trends score (simulated - would use pytrends in production)"""
        if not self.api_configs['google_trends']['enabled']:
            return np.random.uniform(0, 1)  # Simulated
        
        # In production, use pytrends to get actual search volume
        try:
            # from pytrends.request import TrendReq
            # pytrends = TrendReq(hl='en-US', tz=360)
            # pytrends.build_payload([bank_name], cat=0, timeframe='now 7-d', geo='AU')
            # data = pytrends.interest_over_time()
            # return normalize_trend_score(data)
            pass
        except:
            pass
        
        return np.random.uniform(0, 1)
    
    def _calculate_social_media_velocity(self, symbol: str) -> float:
        """Calculate social media mention velocity (simulated)"""
        return np.random.exponential(0.5)
    
    def _calculate_news_clustering(self, news_data: List[Dict]) -> float:
        """Calculate news clustering score to detect narrative shifts"""
        if not news_data or len(news_data) < 2:
            return 0.0
        
        # Simple clustering based on keyword similarity
        headlines = [n.get('title', '') for n in news_data]
        keywords = []
        
        for headline in headlines:
            words = headline.lower().split()
            keywords.extend([w for w in words if len(w) > 4])  # Only longer words
        
        # Calculate keyword diversity
        unique_keywords = len(set(keywords))
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 0.0
        
        # Lower diversity indicates clustering (similar topics)
        clustering_score = 1 - (unique_keywords / total_keywords)
        return min(1.0, max(0.0, clustering_score))
    
    def _detect_narrative_shift(self, news_data: List[Dict]) -> float:
        """Detect narrative shifts in news (simulated)"""
        if not news_data:
            return 0.0
        
        # Simple implementation: check for significant changes in sentiment
        sentiments = [n.get('sentiment', 0) for n in news_data if 'sentiment' in n]
        
        if len(sentiments) < 4:
            return 0.0
        
        # Compare recent vs older sentiment
        recent_sentiment = np.mean(sentiments[-2:])
        older_sentiment = np.mean(sentiments[:-2])
        
        shift_magnitude = abs(recent_sentiment - older_sentiment)
        return min(1.0, shift_magnitude * 2)  # Scale to 0-1
    
    def _calculate_attention_score(self, symbol: str) -> float:
        """Calculate market attention score (simulated)"""
        return np.random.uniform(0, 1)
    
    def _get_search_volume_trend(self, symbol: str) -> float:
        """Get search volume trend (simulated)"""
        return np.random.normal(0, 0.3)
    
    def _calculate_media_divergence(self, symbol: str) -> float:
        """Calculate divergence between different media sources (simulated)"""
        return np.random.uniform(0, 0.5)
    
    def _get_insider_activity_proxy(self, symbol: str) -> float:
        """Get insider activity proxy (simulated)"""
        return np.random.normal(0, 0.1)
    
    # Temporal feature calculation methods
    def _calculate_time_since_open(self, now: datetime) -> float:
        """Calculate time since market open in hours"""
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        if now < market_open:
            return 0
        return (now - market_open).total_seconds() / 3600
    
    def _calculate_time_until_close(self, now: datetime) -> float:
        """Calculate time until market close in hours"""
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        if now > market_close:
            return 0
        return (market_close - now).total_seconds() / 3600
    
    def _is_earnings_season(self, now: datetime) -> int:
        """Check if it's earnings season (simulated)"""
        # Earnings typically in Feb, May, Aug, Nov
        earnings_months = [2, 5, 8, 11]
        return 1 if now.month in earnings_months else 0
    
    def _is_end_of_quarter(self, now: datetime) -> int:
        """Check if it's end of quarter"""
        end_of_quarter_months = [3, 6, 9, 12]
        return 1 if now.month in end_of_quarter_months and now.day > 25 else 0
    
    def _get_trading_session_type(self, now: datetime) -> int:
        """Get trading session type (0=pre-market, 1=regular, 2=after-hours)"""
        hour = now.hour
        if hour < 9:
            return 0  # Pre-market
        elif 9 <= hour <= 16:
            return 1  # Regular hours
        else:
            return 2  # After-hours
    
    # News feature calculation methods
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        try:
            if isinstance(timestamp_str, str):
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return None
        except:
            return None
    
    def _calculate_news_velocity(self, timestamps: List[datetime], hours: int) -> float:
        """Calculate news velocity over specified hours"""
        if not timestamps:
            return 0.0
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_news = [ts for ts in timestamps if ts >= cutoff]
        
        return len(recent_news) / hours  # News per hour
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity (simulated)"""
        if not text:
            return 0.0
        
        # Simple complexity based on word length and sentence length
        words = text.split()
        avg_word_length = np.mean([len(w) for w in words]) if words else 0
        sentences = text.split('.')
        avg_sentence_length = np.mean([len(s.split()) for s in sentences]) if sentences else 0
        
        complexity = (avg_word_length + avg_sentence_length / 10) / 10
        return min(1.0, complexity)
    
    def _calculate_financial_keyword_density(self, text: str) -> float:
        """Calculate density of financial keywords"""
        financial_keywords = [
            'profit', 'revenue', 'earnings', 'dividend', 'loss', 'growth',
            'investment', 'loan', 'credit', 'debt', 'capital', 'rate',
            'market', 'stock', 'share', 'price', 'volume', 'trading'
        ]
        
        words = text.lower().split()
        if not words:
            return 0.0
        
        keyword_count = sum(1 for word in words if any(kw in word for kw in financial_keywords))
        return keyword_count / len(words)
    
    def _calculate_urgency_indicator(self, headlines: List[str]) -> float:
        """Calculate urgency indicator from headlines"""
        urgency_words = ['breaking', 'urgent', 'alert', 'immediate', 'now', 'today']
        
        urgency_count = 0
        total_headlines = len(headlines)
        
        for headline in headlines:
            headline_lower = headline.lower()
            if any(word in headline_lower for word in urgency_words):
                urgency_count += 1
        
        return urgency_count / total_headlines if total_headlines > 0 else 0.0
    
    def _calculate_news_recency_score(self, timestamps: List[datetime]) -> float:
        """Calculate news recency score"""
        if not timestamps:
            return 0.0
        
        now = datetime.now()
        hours_ago = [(now - ts).total_seconds() / 3600 for ts in timestamps]
        
        # Exponential decay weight
        weights = [np.exp(-h / 24) for h in hours_ago]  # 24-hour half-life
        return np.mean(weights)
    
    # Market regime calculation methods
    def _detect_market_regime(self) -> int:
        """Detect current market regime (simulated)"""
        # 0=bear, 1=neutral, 2=bull
        return np.random.choice([0, 1, 2], p=[0.2, 0.6, 0.2])
    
    def _detect_volatility_regime(self) -> int:
        """Detect volatility regime (simulated)"""
        # 0=low, 1=normal, 2=high
        return np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
    
    def _calculate_trend_strength(self, symbol: str) -> float:
        """Calculate trend strength (simulated)"""
        return np.random.uniform(0, 1)
    
    def _calculate_mean_reversion(self, symbol: str) -> float:
        """Calculate mean reversion indicator (simulated)"""
        return np.random.normal(0, 0.2)
    
    def _detect_momentum_regime(self, symbol: str) -> int:
        """Detect momentum regime (simulated)"""
        return np.random.choice([0, 1, 2])  # 0=weak, 1=moderate, 2=strong
    
    def _calculate_market_stress(self) -> float:
        """Calculate market stress indicator (simulated)"""
        return np.random.uniform(0, 1)
    
    def _calculate_sector_strength(self, symbol: str) -> float:
        """Calculate sector relative strength (simulated)"""
        return np.random.normal(0, 0.3)
    
    def _calculate_market_breadth(self) -> float:
        """Calculate market breadth indicator (simulated)"""
        return np.random.uniform(-1, 1)
    
    # Utility methods
    def _assess_feature_quality(self, features: Dict) -> Dict:
        """Assess quality of generated features"""
        total_features = len(features)
        missing_features = sum(1 for v in features.values() if v is None or (isinstance(v, float) and np.isnan(v)))
        extreme_features = sum(1 for v in features.values() if isinstance(v, (int, float)) and abs(v) > 10)
        
        quality_score = 1.0 - (missing_features + extreme_features) / total_features
        
        return {
            'quality_score': max(0.0, quality_score),
            'total_features': total_features,
            'missing_features': missing_features,
            'extreme_features': extreme_features,
            'completeness': 1.0 - missing_features / total_features if total_features > 0 else 0.0
        }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if features are cached and still valid"""
        if cache_key not in self.feature_cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[cache_key]
    
    def _cache_features(self, cache_key: str, features: Dict):
        """Cache features with expiry"""
        self.feature_cache[cache_key] = features
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
    
    def _get_default_microstructure_features(self) -> Dict:
        """Get default microstructure features when calculation fails"""
        return {
            'bid_ask_spread_trend': 0.0,
            'order_flow_imbalance': 0.0,
            'volume_profile_score': 0.0,
            'tick_size_impact': 0.0,
            'market_depth_ratio': 1.0,
            'price_impact_estimate': 0.0,
            'liquidity_score': 0.5,
            'microstructure_quality': 0.5
        }
    
    def _get_default_cross_asset_features(self) -> Dict:
        """Get default cross-asset features when calculation fails"""
        return {
            'aud_usd_correlation': 0.0,
            'bond_yield_impact': 0.0,
            'sector_rotation_signal': 0.0,
            'commodity_correlation': 0.0,
            'global_risk_sentiment': 0.0,
            'vix_correlation': 0.0,
            'interest_rate_sensitivity': 0.5,
            'cross_asset_momentum': 0.0
        }
    
    def _get_default_alternative_features(self) -> Dict:
        """Get default alternative data features when calculation fails"""
        return {
            'google_trends_score': 0.5,
            'social_media_velocity': 0.0,
            'news_clustering_score': 0.0,
            'narrative_shift_indicator': 0.0,
            'market_attention_score': 0.5,
            'search_volume_trend': 0.0,
            'media_sentiment_divergence': 0.0,
            'insider_activity_proxy': 0.0
        }
    
    def get_feature_importance(self, features: Dict, target_correlation: Dict = None) -> Dict:
        """Calculate feature importance based on various metrics"""
        try:
            importance_scores = {}
            
            for feature_name, feature_value in features.items():
                if not isinstance(feature_value, (int, float)):
                    continue
                
                # Base importance on feature variance and magnitude
                magnitude_score = min(1.0, abs(feature_value))
                
                # Feature category importance
                category_importance = 1.0
                if 'microstructure' in feature_name:
                    category_importance = 0.8
                elif 'cross_asset' in feature_name:
                    category_importance = 0.9
                elif 'alternative' in feature_name:
                    category_importance = 0.7
                elif 'sentiment' in feature_name:
                    category_importance = 1.0
                
                # Combined importance
                importance_scores[feature_name] = magnitude_score * category_importance
            
            # Normalize importance scores
            max_importance = max(importance_scores.values()) if importance_scores else 1.0
            normalized_scores = {k: v/max_importance for k, v in importance_scores.items()}
            
            return {
                'feature_importance': normalized_scores,
                'top_features': sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"Feature importance calculation failed: {e}")
            return {'feature_importance': {}, 'top_features': []}
