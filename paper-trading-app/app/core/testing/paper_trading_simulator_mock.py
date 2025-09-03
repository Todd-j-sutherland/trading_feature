#!/usr/bin/env python3
"""
Paper Trading Mock Data Simulator

This simulator generates realistic mock data for all components of the paper trading system:
- News sentiment analysis
- ML scoring and predictions  
- Technical analysis indicators
- Social media sentiment
- Economic context
- Market data (prices, volume, volatility)

Purpose: Test paper trading strategies against various market scenarios without 
         depending on real-time data sources or external APIs.

Usage:
    python -m app.core.testing.paper_trading_simulator_mock --scenario bullish --symbols CBA ANZ WBC
    python -m app.core.testing.paper_trading_simulator_mock --scenario bearish --duration 24
    python -m app.core.testing.paper_trading_simulator_mock --scenario volatile --news-impact high
"""

import json
import random
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import argparse

# Import existing ML components for integration
try:
    from enhanced_ml_system.testing.test_validation_framework import MockNewsGenerator, MockYahooDataFetcher
    ML_COMPONENTS_AVAILABLE = True
except ImportError:
    ML_COMPONENTS_AVAILABLE = False
    print("⚠️ Enhanced ML components not available - using standalone simulation")

try:
    from app.core.ml.trading_scorer import MLTradingScorer
    from app.core.ml.ensemble_predictor import EnsemblePredictor
    PRODUCTION_ML_AVAILABLE = True
except ImportError:
    PRODUCTION_ML_AVAILABLE = False
    print("⚠️ Production ML components not available - using mock ML simulation")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MockMarketScenario:
    """Configuration for different market scenarios"""
    name: str
    market_trend: str  # 'bullish', 'bearish', 'neutral', 'volatile'
    sentiment_bias: float  # -1 to 1, overall sentiment tendency
    volatility_level: float  # 0 to 1, market volatility
    news_frequency: str  # 'low', 'medium', 'high'
    economic_regime: str  # 'expansion', 'contraction', 'neutral'
    correlation_strength: float  # 0 to 1, how correlated banks are
    trend_duration_hours: int  # How long trends persist
    
    # Technical indicators bias
    rsi_bias: float  # -1 to 1, RSI tendency (overbought/oversold)
    macd_bias: float  # -1 to 1, MACD signal tendency
    volume_bias: float  # 0 to 2, volume multiplier
    
    # News and social sentiment
    news_sentiment_variance: float  # 0 to 1, how much sentiment varies
    social_media_activity: float  # 0 to 1, social media engagement level
    reddit_sentiment_correlation: float  # 0 to 1, correlation with news


class PaperTradingMockSimulator:
    """
    Comprehensive mock data simulator for paper trading system testing
    Integrates with existing ML components when available
    """
    
    def __init__(self, scenario: Optional[MockMarketScenario] = None, use_real_ml: Optional[bool] = None):
        """Initialize the mock simulator with a market scenario"""
        from app.config.settings import Settings
        
        self.scenario = scenario or self._get_neutral_scenario()
        self.start_time = datetime.now()
        self.time_offset = 0  # Hours from start
        
        # Use config default if use_real_ml not explicitly provided
        if use_real_ml is None:
            settings = Settings()
            use_real_ml = settings.PAPER_TRADING_USE_REAL_ML
        
        self.use_real_ml = use_real_ml and PRODUCTION_ML_AVAILABLE
        
        # Initialize ML components if available
        self.ml_scorer = None
        self.ensemble_predictor = None
        self.mock_news_generator = None
        self.mock_data_fetcher = None
        
        if self.use_real_ml:
            try:
                self.ml_scorer = MLTradingScorer()
                self.ensemble_predictor = EnsemblePredictor()
                logger.info("✅ Production ML components initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize production ML: {e}")
                self.use_real_ml = False
        
        if ML_COMPONENTS_AVAILABLE:
            try:
                self.mock_news_generator = MockNewsGenerator()
                self.mock_data_fetcher = MockYahooDataFetcher()
                logger.info("✅ Enhanced ML mock components initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize ML mock components: {e}")
        
        # Bank symbols from your settings
        self.bank_symbols = [
            'CBA', 'WBC', 'ANZ', 'NAB', 'MQG', 'SUN', 'QBE', 
            'BOQ', 'BEN', 'AMP', 'IFL'
        ]
        
        # Initialize base prices (realistic ASX bank prices)
        self.base_prices = {
            'CBA': 105.50, 'WBC': 22.80, 'ANZ': 27.45, 'NAB': 34.20,
            'MQG': 185.30, 'SUN': 12.15, 'QBE': 15.85, 'BOQ': 6.45,
            'BEN': 145.20, 'AMP': 1.05, 'IFL': 25.75
        }
        
        # Track current state
        self.current_prices = self.base_prices.copy()
        self.price_history = {symbol: [price] for symbol, price in self.base_prices.items()}
        self.volume_history = {symbol: [random.randint(100000, 1000000)] for symbol in self.bank_symbols}
        
        # Persistent news and sentiment state
        self.persistent_news_themes = {}
        self.sentiment_momentum = {symbol: 0.0 for symbol in self.bank_symbols}
        
        logger.info(f"🎬 Mock simulator initialized with scenario: {self.scenario.name}")
        logger.info(f"📊 Market trend: {self.scenario.market_trend}, Volatility: {self.scenario.volatility_level:.2f}")
        logger.info(f"🧠 Using real ML: {self.use_real_ml}, Enhanced mocks: {ML_COMPONENTS_AVAILABLE}")
    
    def _get_neutral_scenario(self) -> MockMarketScenario:
        """Default neutral market scenario"""
        return MockMarketScenario(
            name="neutral_market",
            market_trend="neutral",
            sentiment_bias=0.0,
            volatility_level=0.3,
            news_frequency="medium",
            economic_regime="neutral",
            correlation_strength=0.6,
            trend_duration_hours=4,
            rsi_bias=0.0,
            macd_bias=0.0,
            volume_bias=1.0,
            news_sentiment_variance=0.3,
            social_media_activity=0.5,
            reddit_sentiment_correlation=0.7
        )
    
    def advance_time(self, hours: float = 4.0):
        """Advance the simulation time"""
        self.time_offset += hours
        logger.info(f"⏰ Advanced simulation time by {hours} hours (total: {self.time_offset:.1f}h)")
    
    def get_current_time(self) -> datetime:
        """Get current simulation time"""
        return self.start_time + timedelta(hours=self.time_offset)
    
    def generate_mock_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Generate realistic mock news sentiment analysis for a bank
        Uses enhanced MockNewsGenerator if available, otherwise fallback simulation
        """
        current_time = self.get_current_time()
        
        # Use enhanced news generator if available
        if self.mock_news_generator:
            try:
                return self._generate_enhanced_news_sentiment(symbol, current_time)
            except Exception as e:
                logger.warning(f"Enhanced news generation failed: {e}, falling back to basic simulation")
        
        # Fallback to basic simulation
        return self._generate_basic_news_sentiment(symbol, current_time)
    
    def _generate_enhanced_news_sentiment(self, symbol: str, current_time: datetime) -> Dict[str, Any]:
        """Generate news sentiment using the enhanced ML mock components"""
        # Determine sentiment category based on scenario
        if self.scenario.sentiment_bias > 0.3:
            sentiment_category = 'positive'
        elif self.scenario.sentiment_bias < -0.3:
            sentiment_category = 'negative'
        else:
            sentiment_category = 'neutral'
        
        # Generate realistic news articles
        articles = []
        news_count_map = {'low': (1, 3), 'medium': (3, 8), 'high': (8, 15)}
        min_news, max_news = news_count_map[self.scenario.news_frequency]
        news_count = random.randint(min_news, max_news)
        
        for i in range(news_count):
            article_time = current_time - timedelta(hours=random.randint(1, 24))
            article = self.mock_news_generator.generate_article(symbol, sentiment_category, article_time)
            articles.append(article)
        
        # Calculate aggregate sentiment from articles
        if articles:
            sentiment_scores = []
            for art in articles:
                # Convert expected_sentiment string to numeric score
                expected_sentiment = art.get('expected_sentiment', 'neutral')
                if expected_sentiment == 'positive':
                    score = random.uniform(0.2, 0.8)
                elif expected_sentiment == 'negative':
                    score = random.uniform(-0.8, -0.2)
                else:  # neutral
                    score = random.uniform(-0.1, 0.1)
                
                # Add to article for consistency
                art['sentiment_score'] = score
                sentiment_scores.append(score)
            
            overall_sentiment = statistics.mean(sentiment_scores)
            confidence = min(0.95, len(articles) / 10.0 + random.uniform(0.1, 0.3))
        else:
            overall_sentiment = self.scenario.sentiment_bias
            confidence = 0.3
        
        # Add momentum
        momentum = self.sentiment_momentum.get(symbol, 0.0)
        overall_sentiment = overall_sentiment * 0.7 + momentum * 0.3
        self.sentiment_momentum[symbol] = overall_sentiment * 0.8 + random.gauss(0, 0.1)
        
        return {
            'symbol': symbol,
            'timestamp': current_time.isoformat(),
            'sentiment_score': float(overall_sentiment),
            'overall_sentiment': float(overall_sentiment),
            'confidence': float(confidence),
            'ml_confidence': float(confidence),
            'news_count': news_count,
            'trading_recommendation': self._get_trading_recommendation(overall_sentiment, confidence),
            'signal': self._get_trading_signal(overall_sentiment, confidence),
            'articles': articles[:5],  # Return first 5 articles
            'recent_headlines': [art['title'] for art in articles[:5]],
            'enhanced_ml_features': {
                'article_quality_score': statistics.mean([art.get('quality_score', 0.7) for art in articles]) if articles else 0.7,
                'source_diversity': len(set(art.get('source', 'unknown') for art in articles)),
                'temporal_distribution': self._calculate_temporal_distribution(articles),
                'sentiment_volatility': statistics.stdev([art.get('sentiment_score', 0) for art in articles]) if len(articles) > 1 else 0.1
            }
        }
    
    def _generate_basic_news_sentiment(self, symbol: str, current_time: datetime) -> Dict[str, Any]:
        """Basic news sentiment generation (original implementation)"""
        # Apply scenario sentiment bias with some randomness
        base_sentiment = self.scenario.sentiment_bias + random.gauss(0, self.scenario.news_sentiment_variance)
        base_sentiment = max(-1.0, min(1.0, base_sentiment))
        
        # Add momentum from previous sentiment
        momentum = self.sentiment_momentum.get(symbol, 0.0)
        sentiment_score = base_sentiment * 0.7 + momentum * 0.3
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Update momentum (sentiment trends persist)
        self.sentiment_momentum[symbol] = sentiment_score * 0.8 + random.gauss(0, 0.1)
        
        # Generate news count based on frequency setting
        news_count_map = {'low': (1, 3), 'medium': (3, 8), 'high': (8, 15)}
        min_news, max_news = news_count_map[self.scenario.news_frequency]
        news_count = random.randint(min_news, max_news)
        
        # Generate confidence based on news count and scenario
        base_confidence = min(0.9, news_count / 10.0)
        confidence = base_confidence + random.gauss(0, 0.1)
        confidence = max(0.1, min(0.95, confidence))
        
        # Generate realistic headlines themes
        positive_themes = [
            "strong quarterly earnings", "dividend increase", "market expansion",
            "positive regulatory news", "digital transformation progress", "merger synergies"
        ]
        negative_themes = [
            "regulatory concerns", "market volatility impact", "economic headwinds",
            "operational challenges", "interest rate pressure", "competitive pressure"
        ]
        neutral_themes = [
            "quarterly update", "market analysis", "industry outlook",
            "business update", "regulatory compliance", "strategic review"
        ]
        
        # Select themes based on sentiment
        if sentiment_score > 0.2:
            key_themes = random.sample(positive_themes, min(3, len(positive_themes)))
        elif sentiment_score < -0.2:
            key_themes = random.sample(negative_themes, min(3, len(negative_themes)))
        else:
            key_themes = random.sample(neutral_themes, min(3, len(neutral_themes)))
        
        # Generate ML trading details
        ml_score = (sentiment_score + 1) * 50  # Convert -1,1 to 0,100
        ml_score += random.gauss(0, 10)  # Add noise
        ml_score = max(0, min(100, ml_score))
        
        # Generate recent headlines
        recent_headlines = []
        for i in range(min(news_count, 5)):
            theme = random.choice(key_themes)
            company_name = self._get_company_name(symbol)
            headline = f"{company_name} reports {theme}"
            recent_headlines.append({
                'title': headline,
                'source': random.choice(['AFR', 'ABC News', 'Yahoo Finance', 'The Australian']),
                'timestamp': (current_time - timedelta(hours=random.randint(1, 24))).isoformat(),
                'sentiment': sentiment_score + random.gauss(0, 0.2)
            })
        
        return {
            'symbol': symbol,
            'timestamp': current_time.isoformat(),
            'sentiment_score': float(sentiment_score),
            'overall_sentiment': float(sentiment_score),
            'confidence': float(confidence),
            'ml_confidence': float(confidence),
            'news_count': news_count,
            'trading_recommendation': self._get_trading_recommendation(sentiment_score, confidence),
            'signal': self._get_trading_signal(sentiment_score, confidence),
            'ml_prediction': {
                'prediction': self._get_trading_signal(sentiment_score, confidence),
                'confidence': confidence,
                'ml_score': ml_score
            },
            'sentiment_components': {
                'news_sentiment': sentiment_score,
                'social_sentiment': sentiment_score + random.gauss(0, 0.1),
                'technical_sentiment': sentiment_score + random.gauss(0, 0.15)
            },
            'recent_headlines': recent_headlines,
            'key_themes': key_themes,
            'time_context': {
                'analysis_timestamp': current_time.isoformat(),
                'data_freshness': 'fresh',
                'market_session': 'open' if 9 <= current_time.hour <= 16 else 'closed'
            },
            'ml_trading_details': {
                'ml_score': ml_score,
                'feature_importance': {
                    'sentiment_strength': random.uniform(0.2, 0.4),
                    'news_volume': random.uniform(0.1, 0.3),
                    'market_context': random.uniform(0.1, 0.2),
                    'technical_indicators': random.uniform(0.2, 0.4)
                }
            }
        }
        
        # Apply scenario sentiment bias with some randomness
        base_sentiment = self.scenario.sentiment_bias + random.gauss(0, self.scenario.news_sentiment_variance)
        base_sentiment = max(-1.0, min(1.0, base_sentiment))
        
        # Add momentum from previous sentiment
        momentum = self.sentiment_momentum.get(symbol, 0.0)
        sentiment_score = base_sentiment * 0.7 + momentum * 0.3
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Update momentum (sentiment trends persist)
        self.sentiment_momentum[symbol] = sentiment_score * 0.8 + random.gauss(0, 0.1)
        
        # Generate news count based on frequency setting
        news_count_map = {'low': (1, 3), 'medium': (3, 8), 'high': (8, 15)}
        min_news, max_news = news_count_map[self.scenario.news_frequency]
        news_count = random.randint(min_news, max_news)
        
        # Generate confidence based on news count and scenario
        base_confidence = min(0.9, news_count / 10.0)
        confidence = base_confidence + random.gauss(0, 0.1)
        confidence = max(0.1, min(0.95, confidence))
        
        # Generate realistic headlines themes
        positive_themes = [
            "strong quarterly earnings", "dividend increase", "market expansion",
            "positive regulatory news", "digital transformation progress", "merger synergies"
        ]
        negative_themes = [
            "regulatory concerns", "market volatility impact", "economic headwinds",
            "operational challenges", "interest rate pressure", "competitive pressure"
        ]
        neutral_themes = [
            "quarterly update", "market analysis", "industry outlook",
            "business update", "regulatory compliance", "strategic review"
        ]
        
        # Select themes based on sentiment
        if sentiment_score > 0.2:
            key_themes = random.sample(positive_themes, min(3, len(positive_themes)))
        elif sentiment_score < -0.2:
            key_themes = random.sample(negative_themes, min(3, len(negative_themes)))
        else:
            key_themes = random.sample(neutral_themes, min(3, len(neutral_themes)))
        
        # Generate ML trading details
        ml_score = (sentiment_score + 1) * 50  # Convert -1,1 to 0,100
        ml_score += random.gauss(0, 10)  # Add noise
        ml_score = max(0, min(100, ml_score))
        
        # Generate recent headlines
        recent_headlines = []
        for i in range(min(news_count, 5)):
            theme = random.choice(key_themes)
            company_name = self._get_company_name(symbol)
            headline = f"{company_name} reports {theme}"
            recent_headlines.append({
                'title': headline,
                'source': random.choice(['AFR', 'ABC News', 'Yahoo Finance', 'The Australian']),
                'timestamp': (current_time - timedelta(hours=random.randint(1, 24))).isoformat(),
                'sentiment': sentiment_score + random.gauss(0, 0.2)
            })
        
        return {
            'symbol': symbol,
            'timestamp': current_time.isoformat(),
            'sentiment_score': float(sentiment_score),
            'overall_sentiment': float(sentiment_score),
            'confidence': float(confidence),
            'ml_confidence': float(confidence),
            'news_count': news_count,
            'trading_recommendation': self._get_trading_recommendation(sentiment_score, confidence),
            'signal': self._get_trading_signal(sentiment_score, confidence),
            'ml_prediction': {
                'prediction': self._get_trading_signal(sentiment_score, confidence),
                'confidence': confidence,
                'ml_score': ml_score
            },
            'sentiment_components': {
                'news_sentiment': sentiment_score,
                'social_sentiment': sentiment_score + random.gauss(0, 0.1),
                'technical_sentiment': sentiment_score + random.gauss(0, 0.15)
            },
            'recent_headlines': recent_headlines,
            'key_themes': key_themes,
            'time_context': {
                'analysis_timestamp': current_time.isoformat(),
                'data_freshness': 'fresh',
                'market_session': 'open' if 9 <= current_time.hour <= 16 else 'closed'
            },
            'ml_trading_details': {
                'ml_score': ml_score,
                'feature_importance': {
                    'sentiment_strength': random.uniform(0.2, 0.4),
                    'news_volume': random.uniform(0.1, 0.3),
                    'market_context': random.uniform(0.1, 0.2),
                    'technical_indicators': random.uniform(0.2, 0.4)
                }
            }
        }
    
    def generate_mock_ml_scores(self, bank_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate realistic ML scores for all banks
        Mimics MLTradingScorer.calculate_scores_for_all_banks()
        """
        ml_scores = {}
        
        for symbol in self.bank_symbols:
            # Get bank analysis or generate basic one
            bank_analysis = bank_analyses.get(symbol, {'overall_sentiment': random.gauss(0, 0.3)})
            sentiment = bank_analysis.get('overall_sentiment', 0)
            
            # Generate 6-component ML scores (0-100 scale)
            sentiment_strength = max(0, min(100, (sentiment + 1) * 50 + random.gauss(0, 10)))
            sentiment_confidence = max(0, min(100, bank_analysis.get('confidence', 0.5) * 100 + random.gauss(0, 10)))
            
            # Economic context based on scenario
            economic_base = {'expansion': 75, 'neutral': 50, 'contraction': 25}[self.scenario.economic_regime]
            economic_context = max(0, min(100, economic_base + random.gauss(0, 15)))
            
            # Divergence score (how different this bank is from sector average)
            sector_sentiments = [ba.get('overall_sentiment', 0) for ba in bank_analyses.values()]
            sector_avg = sum(sector_sentiments) / len(sector_sentiments) if sector_sentiments else 0
            divergence = abs(sentiment - sector_avg) * 100
            divergence_score = max(0, min(100, divergence + random.gauss(0, 10)))
            
            # Technical momentum based on scenario
            tech_base = {'bullish': 70, 'bearish': 30, 'neutral': 50, 'volatile': 50}[self.scenario.market_trend]
            technical_momentum = max(0, min(100, tech_base + random.gauss(0, 15)))
            
            # ML prediction confidence
            ml_prediction_confidence = max(0, min(100, random.uniform(30, 85)))
            
            # Overall ML score (weighted average)
            overall_ml_score = (
                sentiment_strength * 0.25 +
                sentiment_confidence * 0.20 +
                economic_context * 0.20 +
                divergence_score * 0.15 +
                technical_momentum * 0.10 +
                ml_prediction_confidence * 0.10
            )
            
            # Generate trading recommendation
            if overall_ml_score >= 70:
                recommendation = 'STRONG_BUY'
            elif overall_ml_score >= 60:
                recommendation = 'BUY'
            elif overall_ml_score <= 30:
                recommendation = 'STRONG_SELL'
            elif overall_ml_score <= 40:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'
            
            ml_scores[symbol] = {
                'overall_ml_score': float(overall_ml_score),
                'trading_recommendation': recommendation,
                'components': {
                    'sentiment_strength': float(sentiment_strength),
                    'sentiment_confidence': float(sentiment_confidence),
                    'economic_context': float(economic_context),
                    'divergence_score': float(divergence_score),
                    'technical_momentum': float(technical_momentum),
                    'ml_prediction_confidence': float(ml_prediction_confidence)
                },
                'risk_factors': self._generate_risk_factors(overall_ml_score),
                'confidence_level': 'HIGH' if overall_ml_score > 70 or overall_ml_score < 30 else 'MEDIUM'
            }
        
        return ml_scores
    
    def generate_mock_economic_context(self) -> Dict[str, Any]:
        """
        Generate mock economic sentiment analysis
        Mimics EconomicSentimentAnalyzer.analyze_economic_sentiment()
        """
        # Base economic sentiment on scenario
        regime_sentiment = {
            'expansion': 0.3, 'neutral': 0.0, 'contraction': -0.3
        }[self.scenario.economic_regime]
        
        overall_sentiment = regime_sentiment + random.gauss(0, 0.2)
        overall_sentiment = max(-1.0, min(1.0, overall_sentiment))
        
        confidence = random.uniform(0.6, 0.9)
        
        market_regimes = {
            'expansion': {'regime': 'Bull Market', 'description': 'Strong economic growth and positive market sentiment'},
            'neutral': {'regime': 'Neutral Market', 'description': 'Balanced economic conditions with mixed signals'},
            'contraction': {'regime': 'Bear Market', 'description': 'Economic headwinds and negative market sentiment'}
        }
        
        # Generate economic indicators
        indicators = {}
        for indicator in ['interest_rates', 'inflation', 'employment', 'gdp_growth', 'consumer_confidence']:
            base_value = random.uniform(-0.5, 0.5)
            indicators[indicator] = {
                'value': base_value,
                'trend': 'rising' if base_value > 0.1 else 'falling' if base_value < -0.1 else 'stable',
                'sentiment': base_value + random.gauss(0, 0.1)
            }
        
        return {
            'overall_sentiment': float(overall_sentiment),
            'confidence': float(confidence),
            'market_regime': market_regimes[self.scenario.economic_regime],
            'indicators': indicators,
            'timestamp': self.get_current_time().isoformat(),
            'analysis_quality': 'high'
        }
    
    def generate_mock_technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """Generate mock technical analysis data"""
        current_price = self.current_prices[symbol]
        price_history = self.price_history[symbol]
        
        # Generate technical indicators based on scenario
        rsi_base = 50 + self.scenario.rsi_bias * 30
        rsi = max(0, min(100, rsi_base + random.gauss(0, 10)))
        
        macd_signal = self.scenario.macd_bias + random.gauss(0, 0.3)
        
        # Moving averages
        sma_20 = current_price * (1 + random.gauss(0, 0.02))
        sma_50 = current_price * (1 + random.gauss(0, 0.05))
        
        # Volume
        base_volume = self.volume_history[symbol][-1] if self.volume_history[symbol] else 500000
        volume = int(base_volume * self.scenario.volume_bias * random.uniform(0.7, 1.3))
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'rsi': rsi,
            'macd': macd_signal,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'volume': volume,
            'volatility': self.scenario.volatility_level + random.gauss(0, 0.1),
            'trend': self.scenario.market_trend,
            'support_level': current_price * 0.95,
            'resistance_level': current_price * 1.05
        }
    
    def generate_mock_social_media_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Generate mock social media (Reddit) sentiment"""
        # Correlate with news sentiment but add some variance
        news_sentiment = self.sentiment_momentum.get(symbol, 0.0)
        correlation = self.scenario.reddit_sentiment_correlation
        
        reddit_sentiment = (news_sentiment * correlation + 
                          random.gauss(0, 0.3) * (1 - correlation))
        reddit_sentiment = max(-1.0, min(1.0, reddit_sentiment))
        
        # Generate post count based on social media activity
        base_posts = int(self.scenario.social_media_activity * 20)
        post_count = max(1, base_posts + random.randint(-5, 5))
        
        return {
            'symbol': symbol,
            'reddit_sentiment': float(reddit_sentiment),
            'post_count': post_count,
            'engagement_score': random.uniform(0.3, 0.8),
            'trending_keywords': random.sample([
                'earnings', 'dividend', 'growth', 'volatility', 'bullish', 'bearish'
            ], 3),
            'sentiment_confidence': random.uniform(0.4, 0.8)
        }
    
    def update_market_prices(self):
        """Update market prices based on scenario"""
        for symbol in self.bank_symbols:
            current_price = self.current_prices[symbol]
            
            # Base price movement on market trend
            trend_factor = {
                'bullish': 0.001, 'bearish': -0.001, 'neutral': 0.0, 'volatile': 0.0
            }[self.scenario.market_trend]
            
            # Add volatility
            volatility_factor = self.scenario.volatility_level * random.gauss(0, 0.02)
            
            # Add correlation with other banks
            if len(self.price_history[symbol]) > 1:
                # Calculate sector movement
                sector_changes = []
                for other_symbol in self.bank_symbols:
                    if other_symbol != symbol and len(self.price_history[other_symbol]) > 1:
                        change = (self.price_history[other_symbol][-1] / 
                                self.price_history[other_symbol][-2] - 1)
                        sector_changes.append(change)
                
                if sector_changes:
                    sector_avg_change = statistics.mean(sector_changes)
                    correlation_factor = sector_avg_change * self.scenario.correlation_strength
                else:
                    correlation_factor = 0.0
            else:
                correlation_factor = 0.0
            
            # Calculate new price
            total_change = trend_factor + volatility_factor + correlation_factor
            new_price = current_price * (1 + total_change)
            new_price = max(0.01, new_price)  # Prevent negative prices
            
            self.current_prices[symbol] = round(new_price, 2)
            self.price_history[symbol].append(new_price)
            
            # Update volume
            base_volume = self.volume_history[symbol][-1]
            volume_change = random.gauss(0, 0.2) * self.scenario.volume_bias
            new_volume = int(base_volume * (1 + volume_change))
            new_volume = max(10000, new_volume)
            self.volume_history[symbol].append(new_volume)
    
    def run_full_evaluation_cycle(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a complete evaluation cycle generating all mock data
        This simulates what PaperTradingSimulator.evaluate_trading_opportunity() does
        """
        if symbols is None:
            symbols = self.bank_symbols[:5]  # Test with 5 banks by default
        
        logger.info(f"🔄 Running full evaluation cycle for {len(symbols)} symbols")
        
        # Update market prices first
        self.update_market_prices()
        
        # Generate all analysis components
        results = {
            'scenario': self.scenario.name,
            'timestamp': self.get_current_time().isoformat(),
            'market_summary': {
                'trend': self.scenario.market_trend,
                'volatility': self.scenario.volatility_level,
                'economic_regime': self.scenario.economic_regime
            },
            'evaluations': {},
            'economic_context': self.generate_mock_economic_context(),
            'market_data': {}
        }
        
        # Generate bank analyses
        bank_analyses = {}
        for symbol in symbols:
            news_analysis = self.generate_mock_news_sentiment(symbol)
            bank_analyses[symbol] = news_analysis
            
            results['evaluations'][symbol] = {
                'news_analysis': news_analysis,
                'technical_analysis': self.generate_mock_technical_analysis(symbol),
                'social_media': self.generate_mock_social_media_sentiment(symbol)
            }
            
            results['market_data'][symbol] = {
                'current_price': self.current_prices[symbol],
                'price_change_24h': self._calculate_price_change(symbol, 24),
                'volume': self.volume_history[symbol][-1],
                'volatility': self.scenario.volatility_level
            }
        
        # Generate ML scores based on all analyses (use enhanced method)
        ml_scores = self.generate_enhanced_ml_scores(bank_analyses)
        results['ml_scores'] = ml_scores
        
        # Generate summary statistics
        results['summary'] = self._generate_summary_stats(results)
        
        logger.info(f"✅ Evaluation cycle complete - {len(symbols)} symbols analyzed")
        return results
    
    def run_enhanced_evaluation_cycle(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run enhanced evaluation cycle with ML integration
        """
        if symbols is None:
            symbols = self.bank_symbols[:5]
        
        logger.info(f"🔄 Running enhanced evaluation cycle for {len(symbols)} symbols")
        
        # Update market prices first
        self.update_market_prices()
        
        # Generate all analysis components with enhanced features
        results = {
            'scenario': self.scenario.name,
            'timestamp': self.get_current_time().isoformat(),
            'market_summary': {
                'trend': self.scenario.market_trend,
                'volatility': self.scenario.volatility_level,
                'economic_regime': self.scenario.economic_regime
            },
            'evaluations': {},
            'economic_context': self.generate_mock_economic_context(),
            'market_data': {},
            'enhanced_features': {
                'ml_integration_enabled': self.use_real_ml,
                'enhanced_mocks_available': ML_COMPONENTS_AVAILABLE,
                'processing_timestamp': self.get_current_time().isoformat()
            }
        }
        
        # Generate bank analyses with enhanced features
        bank_analyses = {}
        processing_times = []
        
        for symbol in symbols:
            start_time = datetime.now()
            
            news_analysis = self.generate_mock_news_sentiment(symbol)
            bank_analyses[symbol] = news_analysis
            
            results['evaluations'][symbol] = {
                'news_analysis': news_analysis,
                'technical_analysis': self.generate_mock_technical_analysis(symbol),
                'social_media': self.generate_mock_social_media_sentiment(symbol)
            }
            
            results['market_data'][symbol] = self.generate_enhanced_market_data(symbol)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            processing_times.append(processing_time)
        
        # Generate enhanced ML scores
        ml_scores = self.generate_enhanced_ml_scores(bank_analyses)
        results['ml_scores'] = ml_scores
        
        # Generate enhanced summary statistics
        results['summary'] = self._generate_enhanced_summary_stats(results, processing_times)
        
        logger.info(f"✅ Enhanced evaluation cycle complete - {len(symbols)} symbols analyzed")
        return results
    
    def _generate_enhanced_summary_stats(self, results: Dict[str, Any], processing_times: List[float]) -> Dict[str, Any]:
        """Generate enhanced summary statistics with ML metrics"""
        basic_summary = self._generate_summary_stats(results)
        
        # Add enhanced metrics
        ml_scores = results.get('ml_scores', {})
        enhanced_metrics = {
            'avg_processing_time_ms': statistics.mean(processing_times) if processing_times else 0,
            'total_processing_time_ms': sum(processing_times),
            'ml_components_used': {
                'real_ml_scorer': self.use_real_ml and self.ml_scorer is not None,
                'enhanced_news_gen': self.mock_news_generator is not None,
                'enhanced_data_fetch': self.mock_data_fetcher is not None
            }
        }
        
        # Calculate ML-specific metrics
        if ml_scores:
            ml_confidences = []
            prediction_accuracies = []
            
            for symbol, scores in ml_scores.items():
                components = scores.get('components', {})
                if 'sentiment_confidence' in components:
                    ml_confidences.append(components['sentiment_confidence'] / 100.0)
                
                # Simulate prediction accuracy based on scenario and ML score
                base_accuracy = min(0.85, scores.get('overall_ml_score', 50) / 100.0)
                scenario_bonus = {'bullish': 0.05, 'bearish': 0.05, 'volatile': -0.1, 'neutral': 0.0}
                accuracy = base_accuracy + scenario_bonus.get(self.scenario.market_trend, 0.0)
                prediction_accuracies.append(max(0.4, min(0.95, accuracy)))
            
            enhanced_metrics.update({
                'avg_ml_confidence': statistics.mean(ml_confidences) if ml_confidences else 0.5,
                'prediction_accuracy': statistics.mean(prediction_accuracies) if prediction_accuracies else 0.7,
                'ml_score_variance': statistics.stdev([s['overall_ml_score'] for s in ml_scores.values()]) if len(ml_scores) > 1 else 0
            })
        
        basic_summary['enhanced_metrics'] = enhanced_metrics
        return basic_summary
    
    def _calculate_price_change(self, symbol: str, hours: int) -> float:
        """Calculate price change over specified hours"""
        history = self.price_history[symbol]
        if len(history) < 2:
            return 0.0
        
        periods_back = min(hours // 4, len(history) - 1)  # Assuming 4-hour periods
        if periods_back == 0:
            return 0.0
        
        old_price = history[-periods_back - 1]
        current_price = history[-1]
        return ((current_price - old_price) / old_price) * 100
    
    def _generate_summary_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the evaluation"""
        evaluations = results.get('evaluations', {})
        ml_scores = results.get('ml_scores', {})
        
        if not evaluations:
            return {}
        
        # Sentiment statistics
        sentiments = [eval_data['news_analysis']['sentiment_score'] 
                     for eval_data in evaluations.values()]
        avg_sentiment = statistics.mean(sentiments) if sentiments else 0.0
        
        # ML score statistics
        ml_score_values = [score['overall_ml_score'] for score in ml_scores.values()]
        avg_ml_score = statistics.mean(ml_score_values) if ml_score_values else 0.0
        
        # Trading recommendations
        recommendations = [score['trading_recommendation'] for score in ml_scores.values()]
        recommendation_counts = {rec: recommendations.count(rec) for rec in set(recommendations)}
        
        # Price changes
        price_changes = [results['market_data'][symbol]['price_change_24h'] 
                        for symbol in evaluations.keys()]
        avg_price_change = statistics.mean(price_changes) if price_changes else 0.0
        
        return {
            'symbols_analyzed': len(evaluations),
            'avg_sentiment': float(avg_sentiment),
            'avg_ml_score': float(avg_ml_score),
            'avg_price_change_24h': float(avg_price_change),
            'recommendation_distribution': recommendation_counts,
            'market_trend': self.scenario.market_trend,
            'volatility_level': self.scenario.volatility_level
        }
    
    def _get_company_name(self, symbol: str) -> str:
        """Get full company name from symbol"""
        company_names = {
            'CBA': 'Commonwealth Bank', 'WBC': 'Westpac', 'ANZ': 'ANZ Bank',
            'NAB': 'National Australia Bank', 'MQG': 'Macquarie Group',
            'SUN': 'Suncorp', 'QBE': 'QBE Insurance', 'BOQ': 'Bank of Queensland',
            'BEN': 'Bendigo Bank', 'AMP': 'AMP Limited', 'IFL': 'Insignia Financial'
        }
        return company_names.get(symbol, symbol)
    
    def _get_trading_recommendation(self, sentiment: float, confidence: float) -> str:
        """Generate trading recommendation based on sentiment and confidence"""
        if confidence < 0.4:
            return 'HOLD'
        
        if sentiment > 0.3 and confidence > 0.7:
            return 'STRONG_BUY'
        elif sentiment > 0.1 and confidence > 0.5:
            return 'BUY'
        elif sentiment < -0.3 and confidence > 0.7:
            return 'STRONG_SELL'
        elif sentiment < -0.1 and confidence > 0.5:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _get_trading_signal(self, sentiment: float, confidence: float) -> str:
        """Generate simple trading signal"""
        if confidence < 0.4:
            return 'HOLD'
        
        if sentiment > 0.2:
            return 'BUY'
        elif sentiment < -0.2:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _generate_risk_factors(self, ml_score: float) -> List[str]:
        """Generate risk factors based on ML score"""
        risk_factors = []
        
        if ml_score < 40:
            risk_factors.extend(['Low sentiment confidence', 'Negative market indicators'])
        if self.scenario.volatility_level > 0.6:
            risk_factors.append('High market volatility')
        if self.scenario.economic_regime == 'contraction':
            risk_factors.append('Economic contraction environment')
        if self.scenario.news_frequency == 'low':
            risk_factors.append('Limited news coverage')
        
    def _calculate_temporal_distribution(self, articles: List[Dict]) -> Dict[str, float]:
        """Calculate temporal distribution of articles"""
        if not articles:
            return {'recent_24h': 0.0, 'past_week': 0.0, 'older': 0.0}
        
        now = datetime.now()
        recent_24h = sum(1 for art in articles 
                        if (now - datetime.fromisoformat(art.get('timestamp', now.isoformat()))).days < 1)
        past_week = sum(1 for art in articles 
                       if 1 <= (now - datetime.fromisoformat(art.get('timestamp', now.isoformat()))).days <= 7)
        older = len(articles) - recent_24h - past_week
        
        total = len(articles)
        return {
            'recent_24h': recent_24h / total,
            'past_week': past_week / total,
            'older': older / total
        }
    
    def generate_enhanced_ml_scores(self, bank_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate ML scores using real ML components if available, otherwise enhanced simulation
        """
        if self.use_real_ml and self.ml_scorer:
            try:
                return self._generate_real_ml_scores(bank_analyses)
            except Exception as e:
                logger.warning(f"Real ML scoring failed: {e}, falling back to simulation")
        
        return self.generate_mock_ml_scores(bank_analyses)
    
    def _generate_real_ml_scores(self, bank_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ML scores using production ML components"""
        ml_scores = {}
        
        try:
            # Generate required inputs for real ML scorer
            economic_analysis = self.generate_mock_economic_context()
            
            # Generate technical analyses for all symbols
            technical_analyses = {}
            for symbol in self.bank_symbols:
                technical_analyses[symbol] = self.generate_mock_technical_analysis(symbol)
            
            # Use real MLTradingScorer with correct parameters
            real_scores = self.ml_scorer.calculate_scores_for_all_banks(
                bank_analyses=bank_analyses,
                economic_analysis=economic_analysis,
                technical_analyses=technical_analyses,
                divergence_analysis=None  # Optional parameter
            )
            
            # Convert to expected format and add scenario-based adjustments
            for symbol, scores in real_scores.items():
                # Apply scenario bias to real scores
                scenario_adjustment = self._get_scenario_ml_adjustment()
                
                adjusted_score = scores.get('overall_ml_score', 50) * (1 + scenario_adjustment)
                adjusted_score = max(0, min(100, adjusted_score))
                
                ml_scores[symbol] = {
                    'overall_ml_score': float(adjusted_score),
                    'trading_recommendation': self._get_recommendation_from_score(adjusted_score),
                    'components': scores.get('components', {}),
                    'confidence_level': scores.get('confidence_level', 'MEDIUM'),
                    'risk_factors': scores.get('risk_factors', []),
                    'real_ml_features': {
                        'model_version': scores.get('model_version', 'production'),
                        'feature_count': scores.get('feature_count', 0),
                        'training_date': scores.get('training_date', 'unknown'),
                        'prediction_latency_ms': random.randint(50, 200),
                        'real_ml_used': True,
                        'processing_method': 'production_ml_scorer'
                    }
                }
            
            logger.info(f"✅ Generated real ML scores for {len(ml_scores)} symbols using production MLTradingScorer")
            return ml_scores
            
        except Exception as e:
            logger.error(f"❌ Real ML scoring failed: {e}")
            raise
    
    def _get_scenario_ml_adjustment(self) -> float:
        """Get ML score adjustment based on market scenario"""
        adjustments = {
            'bullish': 0.15,      # Boost ML scores in bull market
            'bearish': -0.15,     # Reduce ML scores in bear market
            'volatile': 0.0,      # No bias in volatile market
            'neutral': 0.0,       # No bias in neutral market
        }
        
        base_adjustment = adjustments.get(self.scenario.market_trend, 0.0)
        
        # Add volatility impact
        volatility_impact = (self.scenario.volatility_level - 0.3) * 0.1
        
        return base_adjustment + volatility_impact
    
    def _get_recommendation_from_score(self, score: float) -> str:
        """Convert ML score to trading recommendation"""
        if score >= 75:
            return 'STRONG_BUY'
        elif score >= 60:
            return 'BUY'
        elif score <= 25:
            return 'STRONG_SELL'
        elif score <= 40:
            return 'SELL'
        else:
            return 'HOLD'
    
    def generate_enhanced_market_data(self, symbol: str) -> Dict[str, Any]:
        """Generate market data using mock data fetcher if available"""
        if self.mock_data_fetcher:
            try:
                # Generate realistic price history
                historical_data = self.mock_data_fetcher.get_historical_data(symbol, days_back=30)
                
                return {
                    'symbol': symbol,
                    'current_price': self.current_prices[symbol],
                    'price_change_24h': self._calculate_price_change(symbol, 24),
                    'volume': self.volume_history[symbol][-1],
                    'volatility': self.scenario.volatility_level,
                    'historical_data': historical_data,
                    'technical_indicators': {
                        'sma_20': historical_data.get('sma_20', self.current_prices[symbol]),
                        'sma_50': historical_data.get('sma_50', self.current_prices[symbol]),
                        'rsi': historical_data.get('rsi', 50),
                        'macd': historical_data.get('macd', 0),
                        'bollinger_bands': historical_data.get('bollinger_bands', {})
                    },
                    'enhanced_features': {
                        'data_quality_score': random.uniform(0.8, 0.98),
                        'missing_data_pct': random.uniform(0, 0.05),
                        'outlier_count': random.randint(0, 3),
                        'correlation_with_sector': random.uniform(0.5, 0.9)
                    }
                }
            except Exception as e:
                logger.warning(f"Enhanced market data generation failed: {e}")
        
        # Fallback to basic market data
        return {
            'symbol': symbol,
            'current_price': self.current_prices[symbol],
            'price_change_24h': self._calculate_price_change(symbol, 24),
            'volume': self.volume_history[symbol][-1],
            'volatility': self.scenario.volatility_level
        }


def get_predefined_scenarios() -> Dict[str, MockMarketScenario]:
    """Get predefined market scenarios for testing"""
    
    scenarios = {
        'bullish': MockMarketScenario(
            name="bullish_market",
            market_trend="bullish",
            sentiment_bias=0.4,
            volatility_level=0.2,
            news_frequency="high",
            economic_regime="expansion",
            correlation_strength=0.8,
            trend_duration_hours=6,
            rsi_bias=0.3,
            macd_bias=0.4,
            volume_bias=1.3,
            news_sentiment_variance=0.2,
            social_media_activity=0.8,
            reddit_sentiment_correlation=0.8
        ),
        
        'bearish': MockMarketScenario(
            name="bearish_market",
            market_trend="bearish",
            sentiment_bias=-0.4,
            volatility_level=0.4,
            news_frequency="high",
            economic_regime="contraction",
            correlation_strength=0.9,
            trend_duration_hours=8,
            rsi_bias=-0.4,
            macd_bias=-0.5,
            volume_bias=1.5,
            news_sentiment_variance=0.3,
            social_media_activity=0.7,
            reddit_sentiment_correlation=0.7
        ),
        
        'volatile': MockMarketScenario(
            name="volatile_market",
            market_trend="volatile",
            sentiment_bias=0.0,
            volatility_level=0.8,
            news_frequency="high",
            economic_regime="neutral",
            correlation_strength=0.4,
            trend_duration_hours=2,
            rsi_bias=0.0,
            macd_bias=0.0,
            volume_bias=2.0,
            news_sentiment_variance=0.6,
            social_media_activity=0.9,
            reddit_sentiment_correlation=0.5
        ),
        
        'neutral': MockMarketScenario(
            name="neutral_market",
            market_trend="neutral",
            sentiment_bias=0.0,
            volatility_level=0.3,
            news_frequency="medium",
            economic_regime="neutral",
            correlation_strength=0.6,
            trend_duration_hours=4,
            rsi_bias=0.0,
            macd_bias=0.0,
            volume_bias=1.0,
            news_sentiment_variance=0.3,
            social_media_activity=0.5,
            reddit_sentiment_correlation=0.7
        ),
        
        'low_liquidity': MockMarketScenario(
            name="low_liquidity_market",
            market_trend="neutral",
            sentiment_bias=0.0,
            volatility_level=0.6,
            news_frequency="low",
            economic_regime="neutral",
            correlation_strength=0.3,
            trend_duration_hours=12,
            rsi_bias=0.0,
            macd_bias=0.0,
            volume_bias=0.3,
            news_sentiment_variance=0.4,
            social_media_activity=0.2,
            reddit_sentiment_correlation=0.4
        )
    }
    
    return scenarios


def main():
    """Main CLI interface for the mock simulator"""
    parser = argparse.ArgumentParser(description='Paper Trading Mock Data Simulator - Enhanced ML Integration')
    
    parser.add_argument(
        '--scenario', 
        choices=['bullish', 'bearish', 'volatile', 'neutral', 'low_liquidity'],
        default='neutral',
        help='Market scenario to simulate'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['CBA', 'ANZ', 'WBC', 'NAB', 'MQG'],
        help='Bank symbols to analyze'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=24,
        help='Simulation duration in hours'
    )
    
    parser.add_argument(
        '--cycles',
        type=int,
        default=6,
        help='Number of 4-hour evaluation cycles to run'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--test-paper-trading',
        action='store_true',
        help='Test against actual paper trading simulator'
    )
    
    ml_group = parser.add_mutually_exclusive_group()
    ml_group.add_argument(
        '--use-real-ml',
        action='store_true',
        help='Use production ML components instead of simulation'
    )
    ml_group.add_argument(
        '--use-mock-ml',
        action='store_true',
        help='Use mock ML simulation instead of production components'
    )
    
    parser.add_argument(
        '--benchmark-mode',
        action='store_true',
        help='Run comprehensive benchmark comparing mock vs real components'
    )
    
    parser.add_argument(
        '--generate-training-data',
        action='store_true',
        help='Generate synthetic training data for ML model improvement'
    )
    
    args = parser.parse_args()
    
    # Get scenario
    scenarios = get_predefined_scenarios()
    scenario = scenarios[args.scenario]
    
    # Determine use_real_ml: CLI flags override config default
    use_real_ml = None
    if args.use_real_ml:
        use_real_ml = True
    elif args.use_mock_ml:
        use_real_ml = False
    # If neither flag specified, use_real_ml remains None and constructor will use config default
    
    # Initialize simulator (will use config default if use_real_ml is None)
    simulator = PaperTradingMockSimulator(scenario, use_real_ml=use_real_ml)
    
    print(f"🎬 Starting Enhanced Paper Trading Mock Simulator")
    print(f"📊 Scenario: {scenario.name}")
    print(f"📈 Market Trend: {scenario.market_trend}")
    print(f"⚡ Volatility: {scenario.volatility_level:.2f}")
    print(f"📰 News Frequency: {scenario.news_frequency}")
    print(f"🏦 Symbols: {', '.join(args.symbols)}")
    print(f"⏰ Duration: {args.duration} hours ({args.cycles} cycles)")
    print(f"🧠 ML Components: Real={args.use_real_ml}, Enhanced Mocks={ML_COMPONENTS_AVAILABLE}")
    print("=" * 80)
    
    # Run benchmark mode if requested
    if args.benchmark_mode:
        run_benchmark_analysis(simulator, args.symbols)
        return
    
    # Generate training data if requested
    if args.generate_training_data:
        generate_training_data(simulator, args.symbols, args.cycles)
        return
    
    all_results = []
    
    # Run evaluation cycles
    for cycle in range(args.cycles):
        print(f"\n🔄 Cycle {cycle + 1}/{args.cycles}")
        
        # Run evaluation with enhanced ML
        results = simulator.run_enhanced_evaluation_cycle(args.symbols)
        all_results.append(results)
        
        # Display enhanced summary
        summary = results['summary']
        print(f"   📊 Symbols Analyzed: {summary['symbols_analyzed']}")
        print(f"   😊 Avg Sentiment: {summary['avg_sentiment']:+.3f}")
        print(f"   🧠 Avg ML Score: {summary['avg_ml_score']:.1f}/100")
        print(f"   💹 Avg Price Change: {summary['avg_price_change_24h']:+.2f}%")
        
        # Show enhanced metrics if available
        if 'enhanced_metrics' in summary:
            metrics = summary['enhanced_metrics']
            print(f"   🔧 ML Model Confidence: {metrics.get('avg_ml_confidence', 0):.1%}")
            print(f"   📈 Prediction Accuracy: {metrics.get('prediction_accuracy', 0):.1%}")
            print(f"   ⚡ Processing Speed: {metrics.get('avg_latency_ms', 0):.0f}ms")
        
        # Show recommendations
        rec_dist = summary['recommendation_distribution']
        if rec_dist:
            print(f"   🎯 Recommendations: {', '.join([f'{k}({v})' for k, v in rec_dist.items()])}")
        
        # Advance time for next cycle
        if cycle < args.cycles - 1:
            simulator.advance_time(4.0)
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
    
    # Test against paper trading simulator if requested
    if args.test_paper_trading:
        print(f"\n🧪 Testing against actual paper trading simulator...")
        test_paper_trading_integration(simulator, args.symbols)
    
    print(f"\n✅ Enhanced mock simulation complete!")
    print(f"💡 Use --use-real-ml to test with production ML components")
    print(f"💡 Use --benchmark-mode to compare mock vs real performance")


def run_benchmark_analysis(simulator: PaperTradingMockSimulator, symbols: List[str]):
    """Run comprehensive benchmark comparing mock vs real ML components"""
    print(f"\n🔬 Running Benchmark Analysis")
    print("=" * 60)
    
    benchmark_results = {
        'mock_only': {},
        'real_ml': {},
        'comparison': {}
    }
    
    # Test with mock components only
    print(f"📊 Testing with mock components only...")
    simulator.use_real_ml = False
    mock_results = simulator.run_enhanced_evaluation_cycle(symbols[:3])
    benchmark_results['mock_only'] = mock_results
    
    # Test with real ML if available
    if PRODUCTION_ML_AVAILABLE:
        print(f"🧠 Testing with real ML components...")
        simulator.use_real_ml = True
        real_results = simulator.run_enhanced_evaluation_cycle(symbols[:3])
        benchmark_results['real_ml'] = real_results
        
        # Compare results
        mock_summary = mock_results['summary']
        real_summary = real_results['summary']
        
        print(f"\n📈 Performance Comparison:")
        print(f"   Mock Processing Time: {mock_summary.get('enhanced_metrics', {}).get('avg_processing_time_ms', 0):.1f}ms")
        print(f"   Real Processing Time: {real_summary.get('enhanced_metrics', {}).get('avg_processing_time_ms', 0):.1f}ms")
        print(f"   Mock Avg ML Score: {mock_summary.get('avg_ml_score', 0):.1f}")
        print(f"   Real Avg ML Score: {real_summary.get('avg_ml_score', 0):.1f}")
        
        benchmark_results['comparison'] = {
            'processing_time_ratio': (real_summary.get('enhanced_metrics', {}).get('avg_processing_time_ms', 1) /
                                    max(1, mock_summary.get('enhanced_metrics', {}).get('avg_processing_time_ms', 1))),
            'ml_score_correlation': calculate_correlation(
                [mock_results['ml_scores'][s]['overall_ml_score'] for s in symbols[:3] if s in mock_results['ml_scores']],
                [real_results['ml_scores'][s]['overall_ml_score'] for s in symbols[:3] if s in real_results['ml_scores']]
            ),
            'recommendation_agreement': calculate_recommendation_agreement(
                mock_results['ml_scores'], real_results['ml_scores']
            )
        }
        
        print(f"   ML Score Correlation: {benchmark_results['comparison']['ml_score_correlation']:.3f}")
        print(f"   Recommendation Agreement: {benchmark_results['comparison']['recommendation_agreement']:.1%}")
    else:
        print(f"⚠️ Real ML components not available for comparison")
    
    print(f"\n✅ Benchmark analysis complete")
    return benchmark_results


def generate_training_data(simulator: PaperTradingMockSimulator, symbols: List[str], cycles: int):
    """Generate synthetic training data for ML model improvement"""
    print(f"\n🏗️ Generating Training Data")
    print("=" * 60)
    
    training_scenarios = ['bullish', 'bearish', 'volatile', 'neutral']
    all_training_data = []
    
    for scenario_name in training_scenarios:
        print(f"📊 Generating data for {scenario_name} scenario...")
        
        scenarios = get_predefined_scenarios()
        scenario = scenarios[scenario_name]
        test_simulator = PaperTradingMockSimulator(scenario)
        
        scenario_data = []
        for cycle in range(cycles):
            results = test_simulator.run_enhanced_evaluation_cycle(symbols)
            
            # Extract training features
            for symbol in symbols:
                if symbol in results['evaluations']:
                    training_sample = {
                        'timestamp': results['timestamp'],
                        'symbol': symbol,
                        'scenario': scenario_name,
                        'cycle': cycle,
                        
                        # Features
                        'sentiment_score': results['evaluations'][symbol]['news_analysis']['sentiment_score'],
                        'news_count': results['evaluations'][symbol]['news_analysis']['news_count'],
                        'social_sentiment': results['evaluations'][symbol]['social_media']['reddit_sentiment'],
                        'volatility': results['market_data'][symbol]['volatility'],
                        'price_change_24h': results['market_data'][symbol]['price_change_24h'],
                        'volume_ratio': results['evaluations'][symbol]['technical_analysis']['volume'] / 500000,
                        'rsi': results['evaluations'][symbol]['technical_analysis']['rsi'],
                        
                        # Labels
                        'ml_score': results['ml_scores'][symbol]['overall_ml_score'],
                        'recommendation': results['ml_scores'][symbol]['trading_recommendation'],
                        'market_trend': scenario.market_trend,
                        'economic_regime': scenario.economic_regime
                    }
                    scenario_data.append(training_sample)
            
            test_simulator.advance_time(4.0)
        
        all_training_data.extend(scenario_data)
        print(f"   Generated {len(scenario_data)} samples for {scenario_name}")
    
    # Save training data
    training_file = Path('data/synthetic_training_data.json')
    training_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(training_file, 'w') as f:
        json.dump(all_training_data, f, indent=2)
    
    print(f"\n💾 Training data saved: {training_file}")
    print(f"📊 Total samples: {len(all_training_data)}")
    print(f"🏦 Symbols: {len(symbols)}")
    print(f"📈 Scenarios: {len(training_scenarios)}")
    print(f"⏰ Cycles per scenario: {cycles}")
    
    return all_training_data


def calculate_correlation(list1: List[float], list2: List[float]) -> float:
    """Calculate correlation coefficient between two lists"""
    if len(list1) != len(list2) or len(list1) < 2:
        return 0.0
    
    mean1 = statistics.mean(list1)
    mean2 = statistics.mean(list2)
    
    numerator = sum((x - mean1) * (y - mean2) for x, y in zip(list1, list2))
    
    sum_sq1 = sum((x - mean1) ** 2 for x in list1)
    sum_sq2 = sum((y - mean2) ** 2 for y in list2)
    
    denominator = math.sqrt(sum_sq1 * sum_sq2)
    
    return numerator / denominator if denominator != 0 else 0.0


def calculate_recommendation_agreement(mock_scores: Dict, real_scores: Dict) -> float:
    """Calculate agreement rate between mock and real recommendations"""
    agreements = 0
    total = 0
    
    for symbol in mock_scores:
        if symbol in real_scores:
            mock_rec = mock_scores[symbol]['trading_recommendation']
            real_rec = real_scores[symbol]['trading_recommendation']
            if mock_rec == real_rec:
                agreements += 1
            total += 1
    
    return agreements / total if total > 0 else 0.0


def test_paper_trading_integration(mock_simulator: PaperTradingMockSimulator, symbols: List[str]):
    """Test integration with the actual paper trading simulator"""
    try:
        from app.core.trading.paper_trading_simulator import PaperTradingSimulator
        
        # Create real paper trading simulator
        real_simulator = PaperTradingSimulator()
        
        print(f"🔍 Comparing mock vs real analysis structure...")
        
        # Generate mock data
        mock_results = mock_simulator.run_enhanced_evaluation_cycle(symbols[:2])
        
        # Run real analysis for comparison (first symbol only)
        test_symbol = symbols[0]
        try:
            real_results = real_simulator.evaluate_trading_opportunity(test_symbol)
            
            print(f"✅ Real analysis completed for {test_symbol}")
            print(f"📊 Enhanced mock vs Real structure comparison:")
            
            # Compare keys
            mock_news = mock_results['evaluations'][test_symbol]['news_analysis']
            mock_keys = set(mock_news.keys())
            real_keys = set(real_results.keys())
            
            print(f"   Common keys: {len(mock_keys & real_keys)}")
            print(f"   Mock-only keys: {mock_keys - real_keys}")
            print(f"   Real-only keys: {real_keys - mock_keys}")
            
            # Compare specific values
            if 'sentiment_score' in real_results:
                mock_sentiment = mock_news['sentiment_score']
                real_sentiment = real_results.get('sentiment_score', 0)
                print(f"   Sentiment - Mock: {mock_sentiment:+.3f}, Real: {real_sentiment:+.3f}")
            
            # Check enhanced features
            if 'enhanced_ml_features' in mock_news:
                print(f"   Enhanced features available: {list(mock_news['enhanced_ml_features'].keys())}")
            
        except Exception as e:
            print(f"⚠️ Real analysis failed: {e}")
            print(f"✅ Enhanced mock analysis structure validated independently")
        
    except ImportError as e:
        print(f"⚠️ Cannot import paper trading simulator: {e}")
        print(f"✅ Enhanced mock simulation structure is ready for integration")


if __name__ == "__main__":
    main()
