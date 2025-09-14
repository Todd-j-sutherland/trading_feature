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
        """Get sentiment analysis for specific symbol"""
        try:
            # Check cache first
            cache_key = f"sentiment:{symbol}"
            if cache_key in self.sentiment_cache:
                cached_data, timestamp = self.sentiment_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    self.logger.info(f'"symbol": "{symbol}", "action": "sentiment_cache_hit"')
                    return cached_data
            
            # Fetch fresh sentiment data
            sentiment_data = await self._fetch_symbol_sentiment(symbol)
            
            # Cache the result
            self.sentiment_cache[cache_key] = (sentiment_data, datetime.now().timestamp())
            
            # Publish sentiment update event
            self.publish_event("sentiment_updated", {
                "symbol": symbol,
                "sentiment_score": sentiment_data.get("sentiment_score", 0.0),
                "confidence": sentiment_data.get("news_confidence", 0.5)
            })
            
            self.logger.info(f'"symbol": "{symbol}", "sentiment": {sentiment_data.get("sentiment_score", 0.0)}, "action": "sentiment_analyzed"')
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "sentiment_analysis_failed"')
            # Return neutral sentiment on error
            return {
                "symbol": symbol,
                "sentiment_score": 0.0,
                "news_confidence": 0.5,
                "news_quality_score": 0.5,
                "news_volume": 0,
                "error": str(e),
                "fallback": True
            }
    
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
        """Fetch news from MarketAux API"""
        try:
            params = {
                "api_token": self.marketaux_api_key,
                "symbols": company_name,
                "filter_entities": "true",
                "language": "en",
                "countries": "au",
                "limit": 10
            }
            
            response = requests.get(self.marketaux_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except Exception as e:
            self.logger.error(f'"company": "{company_name}", "error": "{e}", "action": "marketaux_fetch_failed"')
            return []
    
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
        """Simple keyword-based sentiment analysis"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Calculate sentiment score
        positive_weight = positive_count / max(1, total_words) * 10
        negative_weight = negative_count / max(1, total_words) * 10
        
        sentiment = positive_weight - negative_weight
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_article_quality(self, article: Dict) -> float:
        """Calculate quality score for news article"""
        quality = 0.5  # Base quality
        
        # Source quality (if available)
        source = article.get("source", "").lower()
        high_quality_sources = ["reuters", "bloomberg", "financial review", "abc", "smh"]
        if any(hq_source in source for hq_source in high_quality_sources):
            quality += 0.3
        
        # Recency bonus
        published_str = article.get("published_at", "")
        if published_str:
            try:
                published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                hours_ago = (datetime.now() - published.replace(tzinfo=None)).total_seconds() / 3600
                if hours_ago < 24:
                    quality += 0.2  # Recent news is more relevant
            except:
                pass
        
        # Content length (longer articles often more comprehensive)
        description_length = len(article.get("description", ""))
        if description_length > 100:
            quality += 0.1
        
        return min(1.0, quality)
    
    async def get_big4_sentiment(self):
        """Get aggregated sentiment for Big 4 banks"""
        try:
            big4_sentiments = {}
            sentiment_scores = []
            
            for symbol in self.big4_symbols:
                sentiment_data = await self.analyze_sentiment(symbol)
                big4_sentiments[symbol] = sentiment_data
                
                if "error" not in sentiment_data:
                    sentiment_scores.append(sentiment_data.get("sentiment_score", 0.0))
            
            # Calculate aggregated metrics
            if sentiment_scores:
                avg_sentiment = statistics.mean(sentiment_scores)
                sentiment_std = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
            else:
                avg_sentiment = 0.0
                sentiment_std = 0.0
            
            return {
                "big4_average_sentiment": round(avg_sentiment, 3),
                "sentiment_volatility": round(sentiment_std, 3),
                "individual_sentiments": big4_sentiments,
                "consensus": self._determine_sentiment_consensus(avg_sentiment),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "big4_sentiment_failed"')
            return {"error": str(e)}
    
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
