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

class SentimentService(BaseService):
    """News and market sentiment analysis service"""
    
    def __init__(self):
        super().__init__("sentiment")
        
        # Initialize sentiment components
        self.sentiment_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        
        # MarketAux API configuration
        self.marketaux_api_key = os.getenv("MARKETAUX_API_KEY", "")
        self.marketaux_base_url = "https://api.marketaux.com/v1/news/all"
        
        # Big 4 banks for aggregated sentiment
        self.big4_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]
        
        # Sentiment keywords and scoring
        self.positive_keywords = [
            "growth", "profit", "increase", "strong", "positive", "good", "excellent",
            "outperform", "buy", "bullish", "upgrade", "beat", "exceed", "optimistic"
        ]
        
        self.negative_keywords = [
            "loss", "decline", "decrease", "weak", "negative", "poor", "bad",
            "underperform", "sell", "bearish", "downgrade", "miss", "below", "pessimistic"
        ]
        
        # Register methods
        self.register_handler("analyze_sentiment", self.analyze_sentiment)
        self.register_handler("get_big4_sentiment", self.get_big4_sentiment)
        self.register_handler("get_market_sentiment", self.get_market_sentiment)
        self.register_handler("refresh_sentiment_cache", self.refresh_sentiment_cache)
        self.register_handler("get_sentiment_trends", self.get_sentiment_trends)
        self.register_handler("get_news_volume", self.get_news_volume)
    
    async def analyze_sentiment(self, symbol: str):
        """Get sentiment analysis for specific symbol with validation"""
        # Input validation
        if not symbol or not isinstance(symbol, str):
            return {
                "error": "Invalid symbol parameter",
                "symbol": symbol,
                "sentiment_score": 0.0,
                "news_confidence": 0.0,
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
                "fallback": True
            }
        
        try:
            # Check cache first
            cache_key = f"sentiment:{symbol}"
            if cache_key in self.sentiment_cache:
                cached_data, timestamp = self.sentiment_cache[cache_key]
                cache_age = datetime.now().timestamp() - timestamp
                if cache_age < self.cache_ttl:
                    self.logger.info(f'"symbol": "{symbol}", "cache_age": {cache_age:.1f}, "action": "sentiment_cache_hit"')
                    return {**cached_data, "cached": True, "cache_age": cache_age}
            
            # Fetch fresh sentiment data with timeout protection
            try:
                sentiment_data = await asyncio.wait_for(
                    self._fetch_symbol_sentiment(symbol), 
                    timeout=30.0
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
            
            # Publish sentiment update event
            self.publish_event("sentiment_updated", {
                "symbol": symbol,
                "sentiment_score": sentiment_data.get("sentiment_score", 0.0),
                "confidence": sentiment_data.get("news_confidence", 0.5)
            })
            
            self.logger.info(f'"symbol": "{symbol}", "sentiment": {sentiment_data.get("sentiment_score", 0.0)}, "confidence": {sentiment_data.get("news_confidence", 0.5)}, "action": "sentiment_analyzed"')
        return sentiment_data
    
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
        safe_fields = ["company_name", "timestamp", "source", "raw_sentiments"]
        for field in safe_fields:
            if field in data:
                validated[field] = data[field]
        
        return validated
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "sentiment_analysis_failed"')
            # Return neutral sentiment on error
            return self._get_neutral_sentiment(symbol, str(e))
    
    async def _fetch_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
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
    
    async def get_big4_sentiment(self):
        """Get aggregated sentiment for Big 4 banks with enhanced error handling"""
        try:
            big4_sentiments = {}
            sentiment_scores = []
            confidence_scores = []
            error_count = 0
            
            # Process each bank with error isolation
            for symbol in self.big4_symbols:
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
                    "total_symbols": len(self.big4_symbols),
                    "error_count": error_count,
                    "reliability": (len(sentiment_scores) / len(self.big4_symbols)) if self.big4_symbols else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "big4_sentiment_failed"')
            return {
                "error": str(e),
                "big4_average_sentiment": 0.0,
                "sentiment_volatility": 0.0,
                "consensus": "NEUTRAL",
                "timestamp": datetime.now().isoformat()
            }
    
    def _determine_sentiment_consensus(self, avg_sentiment: float) -> str:
        """Determine overall sentiment consensus"""
        if avg_sentiment > 0.1:
            return "POSITIVE"
        elif avg_sentiment < -0.1:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    async def get_market_sentiment(self):
        """Get overall market sentiment"""
        try:
            # Get Big 4 sentiment as market proxy
            big4_data = await self.get_big4_sentiment()
            
            if "error" in big4_data:
                return big4_data
            
            market_sentiment = {
                "overall_sentiment": big4_data.get("big4_average_sentiment", 0.0),
                "market_consensus": big4_data.get("consensus", "NEUTRAL"),
                "sentiment_volatility": big4_data.get("sentiment_volatility", 0.0),
                "based_on": "big4_banks",
                "timestamp": datetime.now().isoformat()
            }
            
            return market_sentiment
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "market_sentiment_failed"')
            return {"error": str(e)}
    
    async def refresh_sentiment_cache(self, symbol: str = None):
        """Force refresh sentiment cache"""
        if symbol:
            cache_key = f"sentiment:{symbol}"
            if cache_key in self.sentiment_cache:
                del self.sentiment_cache[cache_key]
            return await self.analyze_sentiment(symbol)
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
        """Get news volume metrics"""
        if symbol:
            sentiment_data = await self.analyze_sentiment(symbol)
            return {
                "symbol": symbol,
                "news_volume": sentiment_data.get("news_volume", 0),
                "news_quality": sentiment_data.get("news_quality_score", 0.5)
            }
        else:
            # Get volume for all symbols
            volumes = {}
            for sym in self.big4_symbols:
                volumes[sym] = await self.get_news_volume(sym)
            return volumes
    
    async def health_check(self):
        """Enhanced health check with sentiment service metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        sentiment_health = {
            **base_health,
            "cache_size": len(self.sentiment_cache),
            "marketaux_api_configured": bool(self.marketaux_api_key),
            "supported_symbols": len(self.big4_symbols),
            "cache_ttl": self.cache_ttl
        }
        
        # Test API connectivity if configured
        if self.marketaux_api_key:
            try:
                test_news = await self._fetch_marketaux_news("Commonwealth Bank")
                sentiment_health["api_connectivity"] = "ok" if test_news else "no_data"
            except:
                sentiment_health["api_connectivity"] = "failed"
        else:
            sentiment_health["api_connectivity"] = "not_configured"
        
        return sentiment_health

async def main():
    service = SentimentService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
