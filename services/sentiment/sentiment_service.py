"""
Sentiment Analysis Service - News and Market Sentiment

Purpose:
This service analyzes news sentiment and market sentiment for ASX stocks using
MarketAux API and advanced sentiment analysis. It provides sentiment scores,
confidence ratings, and sentiment-driven market insights.

Key Features:
- News sentiment analysis via MarketAux API
- Big 4 banks sentiment aggregation
- Market sentiment trending
- Sentiment caching to reduce API calls
- News volume and quality scoring
- Sentiment event publishing

Data Sources:
- MarketAux API for financial news
- News quality and source reliability scoring
- Sentiment analysis models

API Endpoints:
- analyze_sentiment(symbol) - Get sentiment for specific symbol
- get_big4_sentiment() - Get aggregated Big 4 banks sentiment
- get_market_sentiment() - Get overall market sentiment
- refresh_sentiment_cache() - Force refresh cached sentiment
- get_sentiment_trends(timeframe) - Get sentiment trends

Sentiment Scoring:
- Range: -1.0 (very negative) to +1.0 (very positive)
- Confidence: 0.0 to 1.0 based on news volume and quality
- News volume impact on reliability
- Source quality weighting

Integration:
- Used by Prediction Service for enhanced predictions
- Publishes sentiment updates via Redis events
- Caches results to minimize API usage

Dependencies:
- MarketAux API credentials
- News analyzer components
- Sentiment analysis models

Related Files:
- app/core/sentiment/marketaux_integration.py
- app/core/sentiment/news_analyzer.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Any
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Import news scraper and settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from app.config.settings import Settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    Settings = None

try:
    from services.core.news_scraper import AustralianFinancialNewsScraper
    NEWS_SCRAPER_AVAILABLE = True
except ImportError:
    NEWS_SCRAPER_AVAILABLE = False
    AustralianFinancialNewsScraper = None

class SentimentService(BaseService):
    """News and market sentiment analysis service"""
    
    def __init__(self, default_region: str = "asx"):
        super().__init__("sentiment")
        
        # Multi-region support
        self.config_manager = None
        self.current_region = default_region
        self.available_regions = ["asx", "usa"]
        
        # Initialize config manager
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app", "config", "regions"))
            from config_manager import ConfigManager
            self.config_manager = ConfigManager()
            self.logger.info(f"ConfigManager initialized, using region: {self.current_region}")
        except ImportError as e:
            self.logger.warning(f"ConfigManager not available: {e}")
            self.config_manager = None
        
        # Initialize sentiment components
        self.sentiment_cache = {}
        
        # Load regional configuration
        self._load_regional_config()
        
        # Load legacy configuration as fallback
        self._load_legacy_config()
        
        # Initialize RSS news scraper
        if NEWS_SCRAPER_AVAILABLE:
            self.news_scraper = None  # Will be initialized async
            self.news_scraper_enabled = True
            self.logger.info("RSS news scraper available - enhanced sentiment analysis enabled")
        else:
            self.news_scraper = None
            self.news_scraper_enabled = False
            self.logger.warning("RSS news scraper not available - fallback to API-only mode")
        
        # MarketAux API configuration (secondary source)
        self.marketaux_api_key = os.getenv("MARKETAUX_API_KEY", "")
        self.marketaux_base_url = "https://api.marketaux.com/v1/news/all"
        
        # Register enhanced methods
        self.register_handler("analyze_sentiment", self.analyze_sentiment)
        self.register_handler("get_big4_sentiment", self.get_big4_sentiment)
        self.register_handler("get_market_sentiment", self.get_market_sentiment)
        self.register_handler("refresh_sentiment_cache", self.refresh_sentiment_cache)
        self.register_handler("get_sentiment_trends", self.get_sentiment_trends)
        self.register_handler("get_news_volume", self.get_news_volume)
        self.register_handler("get_news_sources", self.get_news_sources)
        self.register_handler("analyze_news_sentiment", self.analyze_news_sentiment)
        
        # Multi-region specific handlers
        self.register_handler("switch_region", self.switch_region)
        self.register_handler("get_current_region", self.get_current_region)
        self.register_handler("get_available_regions", self.get_available_regions)
    
    def _load_regional_config(self):
        """Load configuration from ConfigManager for current region"""
        if not self.config_manager:
            return
            
        try:
            # Get regional configuration
            config = self.config_manager.get_config(self.current_region)
            
            # Extract news sources configuration
            news_config = config.get("news_sources", {})
            
            # Load news sources
            self.news_sources = news_config.get("rss_feeds", {})
            
            # Load keywords
            keywords = news_config.get("keywords", {})
            self.positive_keywords = self._extract_positive_keywords(keywords)
            self.negative_keywords = self._extract_negative_keywords(keywords)
            
            # Get primary symbols for sentiment analysis
            symbols_config = config.get("symbols", {})
            self.big4_symbols = symbols_config.get("primary", ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"])
            
            # Base configuration
            base_config = config.get("base_config", {})
            sentiment_config = base_config.get("sentiment_config", {})
            
            self.cache_ttl = sentiment_config.get("cache_ttl_minutes", 30) * 60
            self.sentiment_weights = sentiment_config.get("weights", {
                "news_sentiment": 0.4, 
                "technical_momentum": 0.3, 
                "market_sentiment": 0.2
            })
            self.time_decay = sentiment_config.get("time_decay", {})
            self.confidence_factors = sentiment_config.get("confidence_factors", {})
            self.alert_thresholds = sentiment_config.get("alert_thresholds", {
                "strong_positive": 80, 
                "positive": 60, 
                "neutral_high": 55
            })
            
            self.logger.info(f"Loaded regional sentiment configuration for {self.current_region}")
            
        except Exception as e:
            self.logger.error(f"Failed to load regional sentiment config: {e}")
            self._set_fallback_config()
    
    def _load_legacy_config(self):
    def _load_legacy_config(self):
        """Load legacy configuration from settings.py as fallback"""
        if SETTINGS_AVAILABLE:
            # Only load if not already set by regional config
            if not hasattr(self, 'cache_ttl'):
                self.cache_ttl = Settings.CACHE_SETTINGS.get('duration_minutes', 30) * 60
            
            if not hasattr(self, 'big4_symbols') or not self.big4_symbols:
                self.big4_symbols = Settings.BANK_SYMBOLS[:4]
            
            # Load sentiment configuration if not set
            if not hasattr(self, 'sentiment_weights'):
                sentiment_config = Settings.SENTIMENT_CONFIG
                self.sentiment_weights = sentiment_config.get('weights', {})
                self.time_decay = sentiment_config.get('time_decay', {})
                self.confidence_factors = sentiment_config.get('confidence_factors', {})
            
            # Alert thresholds from settings
            if not hasattr(self, 'alert_thresholds'):
                self.alert_thresholds = Settings.ALERT_THRESHOLDS.get('sentiment', {})
            
            # Enhanced sentiment keywords from settings.py
            if not hasattr(self, 'positive_keywords') and hasattr(Settings, 'NEWS_SOURCES'):
                keywords = Settings.NEWS_SOURCES.get('keywords', {})
                self.positive_keywords = self._extract_positive_keywords(keywords)
                self.negative_keywords = self._extract_negative_keywords(keywords)
            
            self.logger.info("Loaded legacy sentiment configuration from settings.py")
        else:
            self._set_fallback_config()
    
    def _set_fallback_config(self):
        """Set fallback configuration when no other config is available"""
        self.cache_ttl = 1800  # 30 minutes fallback
        self.big4_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]
        self.sentiment_weights = {"news_sentiment": 0.4, "technical_momentum": 0.3, "market_sentiment": 0.2}
        self.alert_thresholds = {"strong_positive": 80, "positive": 60, "neutral_high": 55}
        self.positive_keywords = [
            "growth", "profit", "increase", "strong", "positive", "good", "excellent",
            "outperform", "buy", "bullish", "upgrade", "beat", "exceed", "optimistic"
        ]
        self.negative_keywords = [
            "loss", "decline", "decrease", "weak", "negative", "poor", "bad",
            "underperform", "sell", "bearish", "downgrade", "miss", "below", "pessimistic"
        ]
        self.logger.warning("Using fallback sentiment configuration")
    
    # Multi-region support methods
    async def switch_region(self, region: str):
        """Switch to a different region configuration"""
        if region not in self.available_regions:
            return {"error": f"Region '{region}' not available. Available regions: {self.available_regions}"}
        
        if not self.config_manager:
            return {"error": "ConfigManager not available - cannot switch regions"}
        
        try:
            old_region = self.current_region
            self.current_region = region
            
            # Clear cache when switching regions
            self.sentiment_cache.clear()
            
            # Reload configuration for new region
            self._load_regional_config()
            
            self.logger.info(f"Switched sentiment service from {old_region} to {region}")
            return {
                "success": True,
                "previous_region": old_region,
                "current_region": region,
                "news_sources_count": len(getattr(self, 'news_sources', {}))
            }
        except Exception as e:
            # Rollback on error
            self.current_region = old_region if 'old_region' in locals() else "asx"
            self.logger.error(f"Failed to switch to region {region}: {e}")
            return {"error": f"Failed to switch region: {e}"}
    
    async def get_current_region(self):
        """Get current active region"""
        return {
            "current_region": self.current_region,
            "symbols": self.big4_symbols,
            "news_sources_count": len(getattr(self, 'news_sources', {})),
            "config_manager_available": self.config_manager is not None
        }
    
    async def get_available_regions(self):
        """Get list of available regions"""
        return {
            "available_regions": self.available_regions,
            "current_region": self.current_region,
            "config_manager_available": self.config_manager is not None
        }
    def _extract_positive_keywords(self, keywords_dict: Dict) -> List[str]:
        """Extract positive sentiment keywords from settings configuration"""
        positive_terms = [
            "growth", "profit", "increase", "strong", "positive", "good", "excellent",
            "outperform", "buy", "bullish", "upgrade", "beat", "exceed", "optimistic",
            "recovery", "expansion", "gain", "boost", "improve", "rise", "success"
        ]
        
        # Add context-specific positive terms from settings
        for category, terms in keywords_dict.items():
            for term in terms:
                if any(pos in term.lower() for pos in ["good", "strong", "growth", "profit"]):
                    positive_terms.append(term.lower())
        
        return list(set(positive_terms))  # Remove duplicates
    
    def _extract_negative_keywords(self, keywords_dict: Dict) -> List[str]:
        """Extract negative sentiment keywords from settings configuration"""
        negative_terms = [
            "loss", "decline", "decrease", "weak", "negative", "poor", "bad",
            "underperform", "sell", "bearish", "downgrade", "miss", "below", "pessimistic",
            "recession", "contraction", "fall", "drop", "concern", "risk", "worry"
        ]
        
        # Add context-specific negative terms from settings
        for category, terms in keywords_dict.items():
            for term in terms:
                if any(neg in term.lower() for neg in ["loss", "decline", "risk", "fall"]):
                    negative_terms.append(term.lower())
        
        return list(set(negative_terms))  # Remove duplicates
    
    async def _initialize_news_scraper(self):
        """Initialize news scraper asynchronously"""
        if self.news_scraper_enabled and not self.news_scraper:
            try:
                self.news_scraper = AustralianFinancialNewsScraper(
                    cache_duration=self.cache_ttl
                )
                await self.news_scraper.__aenter__()  # Initialize session
                self.logger.info("RSS news scraper initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize news scraper: {e}")
                self.news_scraper = None
                self.news_scraper_enabled = False
    async def analyze_sentiment(self, symbol: str, region: str = None):
        """Enhanced sentiment analysis using RSS feeds and API data, optionally switching regions"""
        # Handle region switching if requested
        original_region = None
        if region and region != self.current_region:
            if region not in self.available_regions:
                return {"error": f"Region '{region}' not available", "symbol": symbol}
            
            original_region = self.current_region
            switch_result = await self.switch_region(region)
            if "error" in switch_result:
                return {**switch_result, "symbol": symbol}
        
        try:
            # Input validation
            if not symbol or not isinstance(symbol, str):
                return {
                    "error": "Invalid symbol parameter",
                    "symbol": symbol,
                    "sentiment_score": 0.0,
                    "news_confidence": 0.0,
                    "region": self.current_region,
                    "fallback": True
                }
            
            # Sanitize symbol
            symbol = symbol.upper().strip()
            if not symbol.replace('.', '').replace('-', '').isalnum():
                return {
                    "error": "Invalid symbol format",
                    "symbol": symbol,
                    "sentiment_score": 0.0,
                    "news_confidence": 0.0,
                    "region": self.current_region,
                    "fallback": True
                }
            
            # Check cache first (include region in cache key)
            cache_key = f"sentiment:{symbol}:{self.current_region}"
            if cache_key in self.sentiment_cache:
                cached_data, timestamp = self.sentiment_cache[cache_key]
                cache_age = datetime.now().timestamp() - timestamp
                if cache_age < self.cache_ttl:
                    self.logger.info(f'"symbol": "{symbol}", "cache_age": {cache_age:.1f}, "action": "sentiment_cache_hit"')
                    return {**cached_data, "cached": True, "cache_age": cache_age}
            
            # Initialize news scraper if needed
            await self._initialize_news_scraper()
            
            # Fetch enhanced sentiment data using multiple sources
            try:
                sentiment_data = await asyncio.wait_for(
                    self._fetch_enhanced_sentiment(symbol), 
                    timeout=45.0  # Increased timeout for RSS processing
                )
            except asyncio.TimeoutError:
                self.logger.error(f'"symbol": "{symbol}", "error": "sentiment_fetch_timeout", "action": "fallback_to_neutral"')
                sentiment_data = self._get_neutral_sentiment(symbol, "Timeout during sentiment fetch")
            
            # Validate sentiment data structure
            if not isinstance(sentiment_data, dict):
                raise ValueError("Invalid sentiment data format")
            
            # Ensure required fields exist with valid values
            sentiment_data = self._validate_sentiment_data(sentiment_data, symbol)
            
            # Cache the result
            self.sentiment_cache[cache_key] = (sentiment_data, datetime.now().timestamp())
            
            # Publish sentiment update event with enhanced data
            self.publish_event("sentiment_updated", {
                "symbol": symbol,
                "sentiment_score": sentiment_data.get("sentiment_score", 0.0),
                "confidence": sentiment_data.get("news_confidence", 0.5),
                "source_mix": sentiment_data.get("source_mix", {}),
                "alert_level": self._determine_alert_level(sentiment_data.get("sentiment_score", 0.0)),
                "region": self.current_region
            })
            
            # Add region info to sentiment data
            sentiment_data["region"] = self.current_region
            
            self.logger.info(f'"symbol": "{symbol}", "sentiment": {sentiment_data.get("sentiment_score", 0.0)}, "confidence": {sentiment_data.get("news_confidence", 0.5)}, "sources": {sentiment_data.get("news_sources_count", 0)}, "region": "{self.current_region}", "action": "sentiment_analyzed"')
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "region": "{self.current_region}", "action": "sentiment_analysis_failed"')
            # Return neutral sentiment on error
            neutral_sentiment = self._get_neutral_sentiment(symbol, str(e))
            neutral_sentiment["region"] = self.current_region
            return neutral_sentiment
        finally:
            # Restore original region if it was temporarily changed
            if original_region and original_region != self.current_region:
                await self.switch_region(original_region)
    
    def _determine_alert_level(self, sentiment_score: float) -> str:
        """Determine alert level based on sentiment score and thresholds"""
        score_pct = sentiment_score * 100  # Convert to percentage
        
        if score_pct >= self.alert_thresholds.get('strong_positive', 80):
            return "STRONG_POSITIVE"
        elif score_pct >= self.alert_thresholds.get('positive', 60):
            return "POSITIVE"
        elif score_pct >= self.alert_thresholds.get('neutral_high', 55):
            return "NEUTRAL_HIGH"
        elif score_pct <= self.alert_thresholds.get('strong_negative', 20):
            return "STRONG_NEGATIVE"
        elif score_pct <= self.alert_thresholds.get('negative', 40):
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    async def _fetch_enhanced_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetch sentiment using multiple sources: RSS feeds + API"""
        sentiment_sources = {}
        
        # 1. RSS News Sentiment (Primary)
        rss_sentiment = await self._get_rss_sentiment(symbol)
        if rss_sentiment:
            sentiment_sources["rss_news"] = rss_sentiment
        
        # 2. MarketAux API Sentiment (Secondary)
        if self.marketaux_api_key:
            api_sentiment = await self._get_api_sentiment(symbol)
            if api_sentiment:
                sentiment_sources["marketaux_api"] = api_sentiment
        
        # 3. Combine sentiments with weighted approach
        combined_sentiment = self._combine_sentiment_sources(sentiment_sources, symbol)
        
        return combined_sentiment
    
    async def _get_rss_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from RSS news sources"""
        if not self.news_scraper_enabled or not self.news_scraper:
            return None
        
        try:
            # Get symbol-specific news
            symbol_news = await self.news_scraper.get_symbol_news(symbol, max_age_hours=24)
            
            if not symbol_news:
                return None
            
            # Analyze sentiment from RSS articles
            sentiment_scores = []
            quality_weights = []
            total_relevance = 0
            
            for article in symbol_news:
                # Calculate sentiment from article content
                article_sentiment = self._calculate_text_sentiment(
                    f"{article.title} {article.description} {article.content}"
                )
                
                sentiment_scores.append(article_sentiment)
                quality_weights.append(article.quality_score)
                total_relevance += article.relevance_score
            
            if sentiment_scores:
                # Weighted average sentiment
                weighted_sentiment = sum(s * w for s, w in zip(sentiment_scores, quality_weights)) / sum(quality_weights)
                
                # Calculate confidence based on article count, quality, and relevance
                article_count_factor = min(1.0, len(symbol_news) / self.confidence_factors.get('min_news_items', 3))
                avg_quality = sum(quality_weights) / len(quality_weights)
                avg_relevance = total_relevance / len(symbol_news)
                
                confidence = (article_count_factor * 0.4) + (avg_quality * 0.3) + (avg_relevance * 0.3)
                
                return {
                    "sentiment_score": weighted_sentiment,
                    "confidence": min(1.0, confidence),
                    "article_count": len(symbol_news),
                    "avg_quality": avg_quality,
                    "avg_relevance": avg_relevance,
                    "source": "rss_feeds"
                }
        
        except Exception as e:
            self.logger.error(f"RSS sentiment fetch failed for {symbol}: {e}")
        
        return None
    
    async def _get_api_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from MarketAux API (fallback/secondary)"""
        try:
            company_map = {
                "CBA.AX": "Commonwealth Bank",
                "ANZ.AX": "ANZ Bank", 
                "NAB.AX": "National Australia Bank",
                "WBC.AX": "Westpac",
                "MQG.AX": "Macquarie Bank",
                "COL.AX": "Coles",
                "BHP.AX": "BHP"
            }
            
            company_name = company_map.get(symbol, symbol.replace(".AX", ""))
            news_data = await self._fetch_marketaux_news(company_name)
            
            if news_data:
                analysis = self._analyze_news_sentiment(news_data, symbol)
                return {
                    **analysis,
                    "source": "marketaux_api"
                }
        
        except Exception as e:
            self.logger.error(f"API sentiment fetch failed for {symbol}: {e}")
        
        return None
    
    def _combine_sentiment_sources(self, sources: Dict[str, Dict], symbol: str) -> Dict[str, Any]:
        """Combine sentiment from multiple sources with intelligent weighting"""
        
        if not sources:
            return self._get_neutral_sentiment(symbol, "No sentiment sources available")
        
        # Weight preferences: RSS feeds > API > fallback
        source_weights = {
            "rss_news": 0.7,  # Primary weight for RSS feeds
            "marketaux_api": 0.3  # Secondary weight for API
        }
        
        weighted_sentiments = []
        total_weight = 0
        confidence_scores = []
        source_mix = {}
        
        for source_name, sentiment_data in sources.items():
            weight = source_weights.get(source_name, 0.1)
            sentiment_score = sentiment_data.get("sentiment_score", 0.0)
            confidence = sentiment_data.get("confidence", 0.5)
            
            weighted_sentiments.append(sentiment_score * weight)
            total_weight += weight
            confidence_scores.append(confidence * weight)
            
            source_mix[source_name] = {
                "sentiment": sentiment_score,
                "confidence": confidence,
                "weight": weight
            }
        
        # Calculate final scores
        if total_weight > 0:
            final_sentiment = sum(weighted_sentiments) / total_weight
            final_confidence = sum(confidence_scores) / total_weight
        else:
            final_sentiment = 0.0
            final_confidence = 0.5
        
        # Apply time decay factor from settings
        news_half_life = self.time_decay.get('news_half_life_hours', 24)
        time_factor = 1.0  # Could implement time decay based on article ages
        
        return {
            "symbol": symbol,
            "sentiment_score": final_sentiment * time_factor,
            "news_confidence": final_confidence,
            "news_quality_score": final_confidence,  # Use confidence as quality proxy
            "news_sources_count": len(sources),
            "source_mix": source_mix,
            "news_volume": sum(s.get("article_count", 1) for s in sources.values()),
            "sentiment_breakdown": self._calculate_sentiment_breakdown(sources),
            "enhanced_analysis": True,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
    
    def _calculate_sentiment_breakdown(self, sources: Dict[str, Dict]) -> Dict[str, int]:
        """Calculate sentiment breakdown across all sources"""
        positive = 0
        negative = 0
        neutral = 0
        
        for source_data in sources.values():
            sentiment = source_data.get("sentiment_score", 0.0)
            if sentiment > 0.1:
                positive += 1
            elif sentiment < -0.1:
                negative += 1
            else:
                neutral += 1
        
        return {"positive": positive, "neutral": neutral, "negative": negative}
    def _get_neutral_sentiment(self, symbol: str, error_msg: str = None) -> Dict[str, Any]:
        """Get neutral sentiment response for error cases"""
        return {
            "symbol": symbol,
            "sentiment_score": 0.0,
            "news_confidence": 0.5,
            "news_quality_score": 0.5,
            "news_volume": 0,
            "sentiment_breakdown": {"positive": 0, "neutral": 1, "negative": 0},
            "error": error_msg,
            "fallback": True,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
    
    def _validate_sentiment_data(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Validate and sanitize sentiment data structure"""
        validated = {
            "symbol": symbol,
            "sentiment_score": 0.0,
            "news_confidence": 0.5,
            "news_quality_score": 0.5,
            "news_volume": 0,
            "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
            "cached": False
        }
        
        # Validate sentiment_score
        if "sentiment_score" in data:
            try:
                score = float(data["sentiment_score"])
                validated["sentiment_score"] = max(-1.0, min(1.0, score))
            except (ValueError, TypeError):
                pass
        
        # Validate confidence scores
        for field in ["news_confidence", "news_quality_score"]:
            if field in data:
                try:
                    conf = float(data[field])
                    validated[field] = max(0.0, min(1.0, conf))
                except (ValueError, TypeError):
                    pass
        
        # Validate news_volume
        if "news_volume" in data:
            try:
                validated["news_volume"] = max(0, int(data["news_volume"]))
            except (ValueError, TypeError):
                pass
        
        # Validate sentiment_breakdown
        if "sentiment_breakdown" in data and isinstance(data["sentiment_breakdown"], dict):
            breakdown = data["sentiment_breakdown"]
            for sentiment_type in ["positive", "neutral", "negative"]:
                if sentiment_type in breakdown:
                    try:
                        validated["sentiment_breakdown"][sentiment_type] = max(0, int(breakdown[sentiment_type]))
                    except (ValueError, TypeError):
                        pass
        
        # Copy other safe fields
        safe_fields = ["company_name", "timestamp", "source", "raw_sentiments", "source_mix", "enhanced_analysis"]
        for field in safe_fields:
            if field in data:
                validated[field] = data[field]
        
        return validated
        """Fetch and analyze sentiment for a specific symbol"""
        try:
            # Extract company name from symbol for news search
            company_map = {
                "CBA.AX": "Commonwealth Bank",
                "ANZ.AX": "ANZ Bank",
                "NAB.AX": "National Australia Bank",
                "WBC.AX": "Westpac",
                "MQG.AX": "Macquarie Bank",
                "COL.AX": "Coles",
                "BHP.AX": "BHP"
            }
            
            company_name = company_map.get(symbol, symbol.replace(".AX", ""))
            
            # If MarketAux API key is available, use it
            if self.marketaux_api_key:
                news_data = await self._fetch_marketaux_news(company_name)
            else:
                # Fallback to simulated sentiment based on symbol characteristics
                news_data = self._generate_fallback_sentiment(symbol, company_name)
            
            # Analyze sentiment from news data
            sentiment_analysis = self._analyze_news_sentiment(news_data, symbol)
            
            return {
                "symbol": symbol,
                "company_name": company_name,
                **sentiment_analysis,
                "timestamp": datetime.now().isoformat(),
                "source": "marketaux" if self.marketaux_api_key else "fallback"
            }
            
        except Exception as e:
            raise Exception(f"Symbol sentiment fetch failed: {e}")
    
    async def _fetch_marketaux_news(self, company_name: str) -> List[Dict]:
        """Fetch news from MarketAux API with enhanced error handling"""
        # Input validation
        if not company_name or not isinstance(company_name, str):
            self.logger.error(f'"error": "invalid_company_name", "action": "marketaux_fetch_failed"')
            return []
        
        # Sanitize company name
        company_name = company_name.strip()
        if len(company_name) > 100:  # Reasonable limit
            company_name = company_name[:100]
        
        try:
            # Validate API key
            if not self.marketaux_api_key:
                self.logger.warning(f'"company": "{company_name}", "error": "no_api_key", "action": "marketaux_fetch_skipped"')
                return []
            
            params = {
                "api_token": self.marketaux_api_key,
                "symbols": company_name,
                "filter_entities": "true",
                "language": "en",
                "countries": "au",
                "limit": min(10, 50)  # Cap at reasonable limit
            }
            
            # Make request with timeout and error handling
            try:
                response = requests.get(
                    self.marketaux_base_url, 
                    params=params, 
                    timeout=15,
                    headers={'User-Agent': 'TradingService/1.0'}
                )
                response.raise_for_status()
            except requests.exceptions.Timeout:
                self.logger.error(f'"company": "{company_name}", "error": "request_timeout", "action": "marketaux_fetch_failed"')
                return []
            except requests.exceptions.RequestException as e:
                self.logger.error(f'"company": "{company_name}", "error": "{e}", "action": "marketaux_request_failed"')
                return []
            
            # Parse response safely
            try:
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON response format")
                
                news_articles = data.get("data", [])
                if not isinstance(news_articles, list):
                    self.logger.warning(f'"company": "{company_name}", "error": "invalid_data_format", "action": "returning_empty_list"')
                    return []
                
                # Validate and sanitize each article
                validated_articles = []
                for article in news_articles[:10]:  # Limit articles processed
                    if isinstance(article, dict):
                        validated_article = self._validate_news_article(article)
                        if validated_article:
                            validated_articles.append(validated_article)
                
                self.logger.info(f'"company": "{company_name}", "articles_found": {len(validated_articles)}, "action": "marketaux_fetch_success"')
                return validated_articles
                
            except (ValueError, KeyError) as e:
                self.logger.error(f'"company": "{company_name}", "error": "json_parse_failed", "details": "{e}", "action": "marketaux_fetch_failed"')
                return []
            
        except Exception as e:
            self.logger.error(f'"company": "{company_name}", "error": "{e}", "action": "marketaux_fetch_failed"')
            return []
    
    def _validate_news_article(self, article: Dict) -> Dict[str, Any]:
        """Validate and sanitize news article data"""
        try:
            validated = {}
            
            # Required fields with defaults
            validated["title"] = str(article.get("title", ""))[:500]  # Limit title length
            validated["description"] = str(article.get("description", ""))[:2000]  # Limit description
            validated["source"] = str(article.get("source", "unknown"))[:100]
            validated["published_at"] = article.get("published_at", datetime.now().isoformat())
            
            # Optional sentiment field
            if "sentiment" in article:
                try:
                    sentiment = float(article["sentiment"])
                    validated["sentiment"] = max(-1.0, min(1.0, sentiment))
                except (ValueError, TypeError):
                    pass
            
            # Validate that we have meaningful content
            if not validated["title"] and not validated["description"]:
                return None
            
            return validated
        except Exception as e:
            self.logger.warning(f'"error": "{e}", "action": "article_validation_failed"')
            return None
    
    def _generate_fallback_sentiment(self, symbol: str, company_name: str) -> List[Dict]:
        """Generate simulated sentiment when API is unavailable"""
        # Simplified sentiment based on historical bank performance patterns
        bank_sentiment_map = {
            "CBA.AX": {"base_sentiment": 0.05, "volatility": 0.1},  # Slightly positive
            "ANZ.AX": {"base_sentiment": -0.02, "volatility": 0.15}, # Slightly negative
            "NAB.AX": {"base_sentiment": 0.02, "volatility": 0.12},  # Neutral-positive
            "WBC.AX": {"base_sentiment": 0.01, "volatility": 0.1},   # Neutral
            "MQG.AX": {"base_sentiment": 0.08, "volatility": 0.2},   # More positive, higher volatility
        }
        
        sentiment_config = bank_sentiment_map.get(symbol, {"base_sentiment": 0.0, "volatility": 0.1})
        
        # Simulate some news articles with basic sentiment
        import random
        random.seed(int(datetime.now().timestamp()) % 1000)  # Consistent but changing
        
        simulated_news = []
        for i in range(3):  # 3 simulated articles
            sentiment_variation = random.uniform(-sentiment_config["volatility"], sentiment_config["volatility"])
            article_sentiment = sentiment_config["base_sentiment"] + sentiment_variation
            
            simulated_news.append({
                "title": f"{company_name} market update {i+1}",
                "description": f"Market analysis for {company_name}",
                "sentiment": max(-1, min(1, article_sentiment)),
                "published_at": datetime.now().isoformat(),
                "source": "simulated"
            })
        
        return simulated_news
    
    def _analyze_news_sentiment(self, news_data: List[Dict], symbol: str) -> Dict[str, Any]:
        """Analyze sentiment from news articles"""
        if not news_data:
            return {
                "sentiment_score": 0.0,
                "news_confidence": 0.2,  # Low confidence due to no news
                "news_quality_score": 0.3,
                "news_volume": 0,
                "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0}
            }
        
        sentiments = []
        quality_scores = []
        sentiment_breakdown = {"positive": 0, "neutral": 0, "negative": 0}
        
        for article in news_data:
            # Extract sentiment from article
            if "sentiment" in article:
                # Direct sentiment score from API
                sentiment = article["sentiment"]
            else:
                # Calculate sentiment from title and description
                sentiment = self._calculate_text_sentiment(
                    article.get("title", "") + " " + article.get("description", "")
                )
            
            sentiments.append(sentiment)
            
            # Calculate quality score (based on source, recency, etc.)
            quality = self._calculate_article_quality(article)
            quality_scores.append(quality)
            
            # Categorize sentiment
            if sentiment > 0.1:
                sentiment_breakdown["positive"] += 1
            elif sentiment < -0.1:
                sentiment_breakdown["negative"] += 1
            else:
                sentiment_breakdown["neutral"] += 1
        
        # Calculate weighted average sentiment
        if sentiments and quality_scores:
            weighted_sentiments = [s * q for s, q in zip(sentiments, quality_scores)]
            avg_sentiment = sum(weighted_sentiments) / sum(quality_scores)
            avg_quality = statistics.mean(quality_scores)
        else:
            avg_sentiment = 0.0
            avg_quality = 0.5
        
        # Calculate confidence based on news volume and quality
        news_volume = len(news_data)
        volume_factor = min(1.0, news_volume / 5)  # Full confidence at 5+ articles
        quality_factor = avg_quality
        
        news_confidence = (volume_factor * 0.6) + (quality_factor * 0.4)
        
        return {
            "sentiment_score": round(avg_sentiment, 3),
            "news_confidence": round(news_confidence, 3),
            "news_quality_score": round(avg_quality, 3),
            "news_volume": news_volume,
            "sentiment_breakdown": sentiment_breakdown,
            "raw_sentiments": [round(s, 3) for s in sentiments]
        }
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """Simple keyword-based sentiment analysis with enhanced validation"""
        # Input validation
        if not text or not isinstance(text, str):
            return 0.0
        
        # Sanitize and limit text length
        text = text.strip()[:10000]  # Reasonable text limit
        if not text:
            return 0.0
        
        try:
            text_lower = text.lower()
            words = text.split()
            total_words = len(words)
            
            if total_words == 0:
                return 0.0
            
            # Count positive and negative keywords
            positive_count = 0
            negative_count = 0
            
            for word in self.positive_keywords:
                if word in text_lower:
                    positive_count += text_lower.count(word)
            
            for word in self.negative_keywords:
                if word in text_lower:
                    negative_count += text_lower.count(word)
            
            # Calculate sentiment score with bounds checking
            positive_weight = min(positive_count / total_words * 10, 1.0)  # Cap at 1.0
            negative_weight = min(negative_count / total_words * 10, 1.0)  # Cap at 1.0
            
            sentiment = positive_weight - negative_weight
            
            # Ensure result is within bounds
            return max(-1.0, min(1.0, sentiment))
            
        except Exception as e:
            self.logger.warning(f'"error": "{e}", "action": "text_sentiment_calculation_failed"')
            return 0.0
    
    def _calculate_article_quality(self, article: Dict) -> float:
        """Calculate quality score for news article with enhanced validation"""
        try:
            if not isinstance(article, dict):
                return 0.5
            
            quality = 0.5  # Base quality
            
            # Source quality (if available)
            source = str(article.get("source", "")).lower().strip()
            high_quality_sources = [
                "reuters", "bloomberg", "financial review", "abc", "smh", 
                "afr", "australian financial review", "the australian",
                "wall street journal", "ft", "financial times"
            ]
            
            if source and any(hq_source in source for hq_source in high_quality_sources):
                quality += 0.3
            elif source and len(source) > 0:
                quality += 0.1  # Some credit for having a source
            
            # Recency bonus with proper date handling
            published_str = article.get("published_at", "")
            if published_str and isinstance(published_str, str):
                try:
                    # Handle various datetime formats
                    if published_str.endswith('Z'):
                        published_str = published_str[:-1] + '+00:00'
                    
                    published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    
                    # Calculate hours ago, handling timezone-aware datetimes
                    if published.tzinfo:
                        published = published.replace(tzinfo=None)
                    
                    hours_ago = (datetime.now() - published).total_seconds() / 3600
                    
                    if 0 <= hours_ago <= 24:
                        quality += 0.2  # Recent news is more relevant
                    elif 24 < hours_ago <= 168:  # 1 week
                        quality += 0.1  # Somewhat recent
                    # No bonus for older news
                        
                except (ValueError, AttributeError, OverflowError) as e:
                    self.logger.warning(f'"error": "{e}", "published_at": "{published_str}", "action": "date_parse_failed"')
            
            # Content length (longer articles often more comprehensive)
            try:
                title_length = len(str(article.get("title", "")))
                description_length = len(str(article.get("description", "")))
                
                total_content = title_length + description_length
                
                if total_content > 200:
                    quality += 0.2  # Substantial content
                elif total_content > 100:
                    quality += 0.1  # Reasonable content
                # No bonus for very short content
                
            except (TypeError, AttributeError):
                pass
            
            # Ensure quality stays within bounds
            return max(0.0, min(1.0, quality))
            
        except Exception as e:
            self.logger.warning(f'"error": "{e}", "action": "quality_calculation_failed"')
            return 0.5  # Default quality on error
    
    async def get_big4_sentiment(self, region: str = None):
        """Get aggregated sentiment for Big 4 banks with enhanced error handling"""
        # Store original region for restoration
        original_region = self.current_region if region and region != self.current_region else None
        
        try:
            # Switch to target region if specified
            if region and region != self.current_region:
                await self.switch_region(region)
            
            big4_sentiments = {}
            sentiment_scores = []
            confidence_scores = []
            error_count = 0
            
            # Get current region's big4 symbols
            big4_symbols = self.config.get("sentiment", {}).get("big4_symbols", self.big4_symbols)
            
            # Process each bank with error isolation
            for symbol in big4_symbols:
                try:
                    sentiment_data = await self.analyze_sentiment(symbol)
                    big4_sentiments[symbol] = sentiment_data
                    
                    if "error" not in sentiment_data or not sentiment_data.get("fallback", False):
                        sentiment_score = sentiment_data.get("sentiment_score", 0.0)
                        confidence = sentiment_data.get("news_confidence", 0.5)
                        
                        # Validate scores before adding
                        if isinstance(sentiment_score, (int, float)) and -1 <= sentiment_score <= 1:
                            sentiment_scores.append(float(sentiment_score))
                        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                            confidence_scores.append(float(confidence))
                    else:
                        error_count += 1
                        
                except Exception as e:
                    self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "big4_individual_sentiment_failed"')
                    big4_sentiments[symbol] = self._get_neutral_sentiment(symbol, str(e))
                    error_count += 1
            
            # Calculate aggregated metrics with proper validation
            if sentiment_scores and len(sentiment_scores) > 0:
                try:
                    avg_sentiment = statistics.mean(sentiment_scores)
                    sentiment_std = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
                    avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
                except (statistics.StatisticsError, ValueError) as e:
                    self.logger.error(f'"error": "{e}", "action": "big4_statistics_calculation_failed"')
                    avg_sentiment = 0.0
                    sentiment_std = 0.0
                    avg_confidence = 0.5
            else:
                avg_sentiment = 0.0
                sentiment_std = 0.0
                avg_confidence = 0.5
            
            # Additional insights
            positive_count = sum(1 for score in sentiment_scores if score > 0.1)
            negative_count = sum(1 for score in sentiment_scores if score < -0.1)
            neutral_count = len(sentiment_scores) - positive_count - negative_count
            
            return {
                "big4_average_sentiment": round(float(avg_sentiment), 3),
                "sentiment_volatility": round(float(sentiment_std), 3),
                "average_confidence": round(float(avg_confidence), 3),
                "individual_sentiments": big4_sentiments,
                "consensus": self._determine_sentiment_consensus(avg_sentiment),
                "sentiment_distribution": {
                    "positive": positive_count,
                    "neutral": neutral_count,
                    "negative": negative_count
                },
                "data_quality": {
                    "successful_fetches": len(sentiment_scores),
                    "total_symbols": len(big4_symbols),
                    "error_count": error_count,
                    "reliability": (len(sentiment_scores) / len(big4_symbols)) if big4_symbols else 0
                },
                "region": self.current_region,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "region": "{self.current_region}", "action": "big4_sentiment_failed"')
            return {
                "error": str(e),
                "big4_average_sentiment": 0.0,
                "sentiment_volatility": 0.0,
                "consensus": "NEUTRAL",
                "region": self.current_region,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            # Restore original region if it was temporarily changed
            if original_region and original_region != self.current_region:
                await self.switch_region(original_region)
    
    def _determine_sentiment_consensus(self, avg_sentiment: float) -> str:
        """Determine overall sentiment consensus"""
        if avg_sentiment > 0.1:
            return "POSITIVE"
        elif avg_sentiment < -0.1:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    async def get_market_sentiment(self, region: str = None):
        """Get overall market sentiment"""
        try:
            # Get Big 4 sentiment as market proxy
            big4_data = await self.get_big4_sentiment(region)
            
            if "error" in big4_data:
                return big4_data
            
            market_sentiment = {
                "overall_sentiment": big4_data.get("big4_average_sentiment", 0.0),
                "market_consensus": big4_data.get("consensus", "NEUTRAL"),
                "sentiment_volatility": big4_data.get("sentiment_volatility", 0.0),
                "based_on": "big4_banks",
                "region": big4_data.get("region", self.current_region),
                "timestamp": datetime.now().isoformat()
            }
            
            return market_sentiment
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "region": "{self.current_region}", "action": "market_sentiment_failed"')
            return {"error": str(e), "region": self.current_region}
    
    async def refresh_sentiment_cache(self, symbol: str = None, region: str = None):
        """Force refresh sentiment cache"""
        if symbol:
            # Include region in cache key if specified
            cache_region = region or self.current_region
            cache_key = f"sentiment:{symbol}:{cache_region}"
            if cache_key in self.sentiment_cache:
                del self.sentiment_cache[cache_key]
            return await self.analyze_sentiment(symbol, region)
        else:
            # Clear all cache or region-specific cache
            if region:
                # Clear cache for specific region
                region_keys = [key for key in self.sentiment_cache.keys() if key.endswith(f":{region}")]
                for key in region_keys:
                    del self.sentiment_cache[key]
                return {"cleared_entries": len(region_keys), "region": region}
            else:
                # Clear all cache
                cache_size = len(self.sentiment_cache)
                self.sentiment_cache.clear()
                return {"cleared_entries": cache_size}
    
    async def get_sentiment_trends(self, timeframe: str = "1d"):
        """Get sentiment trends over time"""
        # This would require historical data storage
        # For now, return current sentiment as trend baseline
        big4_sentiment = await self.get_big4_sentiment()
        
        return {
            "timeframe": timeframe,
            "current_sentiment": big4_sentiment.get("big4_average_sentiment", 0.0),
            "trend_direction": "stable",  # Would calculate from historical data
            "note": "Trending analysis requires historical data collection"
        }
    
    async def get_news_volume(self, symbol: str = None):
        """Get enhanced news volume metrics with RSS integration"""
        if symbol:
            sentiment_data = await self.analyze_sentiment(symbol)
            return {
                "symbol": symbol,
                "news_volume": sentiment_data.get("news_volume", 0),
                "news_quality": sentiment_data.get("news_quality_score", 0.5),
                "sources_count": sentiment_data.get("news_sources_count", 0),
                "enhanced_analysis": sentiment_data.get("enhanced_analysis", False)
            }
        else:
            # Get volume for all symbols
            volumes = {}
            for sym in self.big4_symbols:
                volumes[sym] = await self.get_news_volume(sym)
            return volumes
    
    async def get_news_sources(self):
        """Get information about configured news sources"""
        if SETTINGS_AVAILABLE and hasattr(Settings, 'NEWS_SOURCES'):
            news_sources = Settings.NEWS_SOURCES.get('rss_feeds', {})
            source_tiers = {
                'tier_1_government': ['rba', 'abs', 'treasury', 'apra'],
                'tier_2_financial_media': ['afr_companies', 'afr_markets', 'market_index', 'investing_au'],
                'tier_3_major_outlets': ['abc_business', 'smh_business', 'the_age_business', 'news_com_au'],
                'tier_4_specialized': ['motley_fool_au', 'investor_daily', 'aba_news', 'finsia']
            }
            
            return {
                "total_sources": len(news_sources),
                "source_tiers": source_tiers,
                "rss_scraper_enabled": self.news_scraper_enabled,
                "marketaux_api_enabled": bool(self.marketaux_api_key),
                "configured_sources": list(news_sources.keys()),
                "settings_loaded": True
            }
        else:
            return {
                "error": "Settings configuration not available",
                "rss_scraper_enabled": self.news_scraper_enabled,
                "marketaux_api_enabled": bool(self.marketaux_api_key),
                "settings_loaded": False
            }
    
    async def analyze_news_sentiment(self, symbol: str, max_age_hours: int = 24):
        """Analyze news sentiment for symbol using RSS feeds"""
        if not self.news_scraper_enabled:
            return {"error": "RSS news scraper not available"}
        
        await self._initialize_news_scraper()
        
        if not self.news_scraper:
            return {"error": "Failed to initialize news scraper"}
        
        try:
            # Get fresh news articles
            symbol_news = await self.news_scraper.get_symbol_news(symbol, max_age_hours)
            
            if not symbol_news:
                return {
                    "symbol": symbol,
                    "articles_found": 0,
                    "sentiment_score": 0.0,
                    "confidence": 0.2,
                    "message": "No recent news articles found"
                }
            
            # Analyze each article
            article_analyses = []
            for article in symbol_news:
                article_sentiment = self._calculate_text_sentiment(
                    f"{article.title} {article.description} {article.content}"
                )
                
                article_analyses.append({
                    "title": article.title[:100] + "..." if len(article.title) > 100 else article.title,
                    "source": article.source,
                    "published_at": article.published_at.isoformat(),
                    "sentiment_score": article_sentiment,
                    "quality_score": article.quality_score,
                    "relevance_score": article.relevance_score,
                    "financial_keywords": article.financial_keywords[:5],  # Top 5 keywords
                    "sentiment_keywords": article.sentiment_keywords[:5]
                })
            
            # Calculate overall sentiment
            sentiment_scores = [a["sentiment_score"] for a in article_analyses]
            quality_weights = [a["quality_score"] for a in article_analyses]
            
            if sentiment_scores and quality_weights:
                weighted_sentiment = sum(s * w for s, w in zip(sentiment_scores, quality_weights)) / sum(quality_weights)
                confidence = min(1.0, len(article_analyses) / 3) * (sum(quality_weights) / len(quality_weights))
            else:
                weighted_sentiment = 0.0
                confidence = 0.0
            
            return {
                "symbol": symbol,
                "articles_found": len(symbol_news),
                "sentiment_score": weighted_sentiment,
                "confidence": confidence,
                "analysis_timestamp": datetime.now().isoformat(),
                "article_analyses": article_analyses[:10],  # Return top 10 articles
                "source_breakdown": self._calculate_source_breakdown(symbol_news)
            }
            
        except Exception as e:
            self.logger.error(f"News sentiment analysis failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    def _calculate_source_breakdown(self, articles) -> Dict[str, int]:
        """Calculate breakdown of articles by source"""
        source_counts = {}
        for article in articles:
            source = article.source
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts
    
    async def health_check(self):
        """Enhanced health check with sentiment service and RSS scraper metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        sentiment_health = {
            **base_health,
            "cache_size": len(self.sentiment_cache),
            "marketaux_api_configured": bool(self.marketaux_api_key),
            "rss_scraper_enabled": self.news_scraper_enabled,
            "rss_scraper_initialized": self.news_scraper is not None,
            "supported_symbols": len(self.big4_symbols),
            "cache_ttl": self.cache_ttl,
            "settings_integration": SETTINGS_AVAILABLE,
            "news_scraper_integration": NEWS_SCRAPER_AVAILABLE
        }
        
        # Test RSS scraper if available
        if self.news_scraper_enabled:
            try:
                await self._initialize_news_scraper()
                if self.news_scraper:
                    cache_stats = self.news_scraper.get_cache_stats()
                    sentiment_health["rss_cache_stats"] = cache_stats
                    sentiment_health["rss_scraper_status"] = "operational"
                else:
                    sentiment_health["rss_scraper_status"] = "failed_to_initialize"
            except Exception as e:
                sentiment_health["rss_scraper_status"] = f"error: {str(e)}"
        else:
            sentiment_health["rss_scraper_status"] = "disabled"
        
        # Test MarketAux API connectivity if configured
        if self.marketaux_api_key:
            try:
                test_news = await self._fetch_marketaux_news("Commonwealth Bank")
                sentiment_health["marketaux_api_connectivity"] = "ok" if test_news else "no_data"
            except Exception as e:
                sentiment_health["marketaux_api_connectivity"] = f"failed: {str(e)}"
        else:
            sentiment_health["marketaux_api_connectivity"] = "not_configured"
        
        return sentiment_health

async def main():
    service = SentimentService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
