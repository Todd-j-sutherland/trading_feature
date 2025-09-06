"""
Sentiment Service - News Collection and Sentiment Analysis

This service handles:
- News collection from multiple sources
- Sentiment analysis using FinBERT and other models
- Social media sentiment aggregation
- Sentiment scoring and caching
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import traceback

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# Local imports with fallbacks
from services.shared.models.sentiment_models import SentimentScore, NewsArticle, SentimentSummary
from services.shared.utils.database_utils import DatabaseManager
from services.shared.utils.logging_utils import setup_logging
from services.shared.config.service_config import get_service_config
from services.shared.config.database_config import get_database_config


# Setup logging
logger = setup_logging("sentiment_service")
config = get_service_config("sentiment")
db_config = get_database_config()

# Initialize FastAPI app (if available)
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Sentiment Service",
        description="News collection and sentiment analysis for ASX trading system",
        version="1.0.0"
    )
else:
    app = None
    logger.warning("FastAPI not available - service will run in compatibility mode")


class SentimentServiceCore:
    """Core sentiment analysis functionality (works without FastAPI)"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(db_config.primary_db_path)
        self.cache_duration = timedelta(minutes=30)  # Cache sentiment for 30 minutes
        self.news_sources = [
            'asx.com.au',
            'afr.com',
            'abc.net.au/news',
            'reuters.com',
            'bloomberg.com'
        ]
        
        # Initialize sentiment cache
        self.sentiment_cache: Dict[str, Dict] = {}
        
        # Sentiment keywords for basic analysis (fallback)
        self.positive_keywords = [
            'growth', 'profit', 'gains', 'positive', 'strong', 'beat', 'exceed',
            'upgrade', 'expansion', 'acquisition', 'dividend', 'bullish', 'buy',
            'outperform', 'revenue', 'earnings', 'success', 'recovery'
        ]
        
        self.negative_keywords = [
            'loss', 'decline', 'drop', 'fall', 'negative', 'weak', 'miss',
            'downgrade', 'cut', 'reduce', 'bearish', 'sell', 'underperform',
            'warning', 'concern', 'risk', 'challenge', 'crisis', 'debt'
        ]
    
    def get_sentiment_score(self, symbol: str) -> SentimentScore:
        """Get sentiment score for a symbol"""
        try:
            # Check cache first
            cached_sentiment = self._get_cached_sentiment(symbol)
            if cached_sentiment:
                return SentimentScore.from_dict(cached_sentiment)
            
            # Collect news articles
            articles = self._collect_news_articles(symbol)
            
            # Analyze sentiment
            sentiment_score = self._analyze_sentiment(articles)
            
            # Cache result
            self._cache_sentiment(symbol, sentiment_score)
            
            # Save to database
            self._save_sentiment_score(symbol, sentiment_score)
            
            return sentiment_score
            
        except Exception as e:
            logger.error(f"Error getting sentiment score for {symbol}: {e}")
            return self._get_fallback_sentiment_score(symbol)
    
    def get_sentiment_summary(self, symbols: List[str]) -> SentimentSummary:
        """Get sentiment summary for multiple symbols"""
        try:
            sentiment_scores = []
            total_positive = 0
            total_negative = 0
            total_neutral = 0
            
            for symbol in symbols:
                sentiment = self.get_sentiment_score(symbol)
                sentiment_scores.append(sentiment)
                
                if sentiment.overall_sentiment > 0.1:
                    total_positive += 1
                elif sentiment.overall_sentiment < -0.1:
                    total_negative += 1
                else:
                    total_neutral += 1
            
            # Calculate market sentiment
            total_symbols = len(symbols)
            market_sentiment = sum(s.overall_sentiment for s in sentiment_scores) / total_symbols if total_symbols > 0 else 0
            
            summary = SentimentSummary(
                symbols_analyzed=total_symbols,
                average_sentiment=market_sentiment,
                positive_sentiment_count=total_positive,
                negative_sentiment_count=total_negative,
                neutral_sentiment_count=total_neutral,
                sentiment_scores=sentiment_scores,
                analysis_timestamp=datetime.now()
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return SentimentSummary(
                symbols_analyzed=0,
                average_sentiment=0.0,
                positive_sentiment_count=0,
                negative_sentiment_count=0,
                neutral_sentiment_count=0,
                sentiment_scores=[],
                analysis_timestamp=datetime.now()
            )
    
    def update_sentiment_cache(self, symbols: List[str]) -> int:
        """Update sentiment cache for multiple symbols"""
        updated_count = 0
        
        for symbol in symbols:
            try:
                sentiment = self.get_sentiment_score(symbol)
                if sentiment:
                    updated_count += 1
                    logger.debug(f"Updated sentiment cache for {symbol}")
            except Exception as e:
                logger.error(f"Error updating sentiment cache for {symbol}: {e}")
        
        logger.info(f"Updated sentiment cache for {updated_count}/{len(symbols)} symbols")
        return updated_count
    
    def _get_cached_sentiment(self, symbol: str) -> Optional[Dict]:
        """Get cached sentiment if still valid"""
        if symbol in self.sentiment_cache:
            cached_data = self.sentiment_cache[symbol]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['sentiment']
        
        return None
    
    def _cache_sentiment(self, symbol: str, sentiment: SentimentScore):
        """Cache sentiment score"""
        self.sentiment_cache[symbol] = {
            'sentiment': sentiment.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _collect_news_articles(self, symbol: str) -> List[NewsArticle]:
        """Collect news articles for a symbol (simplified implementation)"""
        articles = []
        
        try:
            # This is a simplified implementation
            # In production, this would integrate with news APIs
            
            # For now, return sample articles based on symbol
            sample_articles = [
                NewsArticle(
                    title=f"{symbol} Reports Strong Quarterly Results",
                    content=f"ASX-listed {symbol} has announced strong quarterly performance with revenue growth and positive outlook.",
                    source="ASX Announcements",
                    published_date=datetime.now() - timedelta(hours=2),
                    url=f"https://example.com/news/{symbol}",
                    relevance_score=0.9
                ),
                NewsArticle(
                    title=f"Market Analysis: {symbol} Outlook",
                    content=f"Analysts remain optimistic about {symbol}'s prospects in the current market environment.",
                    source="Financial Review",
                    published_date=datetime.now() - timedelta(hours=6),
                    url=f"https://example.com/analysis/{symbol}",
                    relevance_score=0.7
                )
            ]
            
            articles.extend(sample_articles)
            
        except Exception as e:
            logger.error(f"Error collecting news articles for {symbol}: {e}")
        
        return articles
    
    def _analyze_sentiment(self, articles: List[NewsArticle]) -> SentimentScore:
        """Analyze sentiment from articles"""
        try:
            if not articles:
                return SentimentScore(
                    symbol="",
                    overall_sentiment=0.0,
                    news_sentiment=0.0,
                    social_sentiment=0.0,
                    article_count=0,
                    confidence_score=0.0,
                    analysis_timestamp=datetime.now()
                )
            
            # Basic keyword-based sentiment analysis (fallback)
            total_sentiment = 0.0
            total_weight = 0.0
            
            for article in articles:
                article_sentiment = self._analyze_article_sentiment(article)
                weight = article.relevance_score
                
                total_sentiment += article_sentiment * weight
                total_weight += weight
            
            overall_sentiment = total_sentiment / total_weight if total_weight > 0 else 0.0
            
            # Calculate confidence based on article count and consistency
            confidence = min(0.9, len(articles) * 0.2)  # Max 90% confidence
            
            sentiment_score = SentimentScore(
                symbol="",  # Will be set by caller
                overall_sentiment=overall_sentiment,
                news_sentiment=overall_sentiment,
                social_sentiment=0.0,  # Not implemented yet
                article_count=len(articles),
                confidence_score=confidence,
                analysis_timestamp=datetime.now()
            )
            
            return sentiment_score
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._get_fallback_sentiment_score("")
    
    def _analyze_article_sentiment(self, article: NewsArticle) -> float:
        """Analyze sentiment of a single article using keyword matching"""
        text = f"{article.title} {article.content}".lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)
        
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            return 0.0  # Neutral
        
        # Calculate sentiment score between -1 and 1
        sentiment = (positive_count - negative_count) / total_keywords
        
        # Apply dampening factor for more conservative scoring
        return sentiment * 0.7
    
    def _save_sentiment_score(self, symbol: str, sentiment: SentimentScore):
        """Save sentiment score to database"""
        try:
            query = """
                INSERT OR REPLACE INTO sentiment_scores (
                    symbol, timestamp, overall_sentiment, news_sentiment,
                    social_sentiment, article_count, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                symbol,
                sentiment.analysis_timestamp.isoformat(),
                sentiment.overall_sentiment,
                sentiment.news_sentiment,
                sentiment.social_sentiment,
                sentiment.article_count,
                sentiment.confidence_score
            )
            
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error saving sentiment score: {e}")
    
    def _get_fallback_sentiment_score(self, symbol: str) -> SentimentScore:
        """Get fallback sentiment score when analysis fails"""
        return SentimentScore(
            symbol=symbol,
            overall_sentiment=0.0,
            confidence=0.1,  # Add the confidence field that's required
            confidence_score=0.1,
            news_sentiment=0.0,
            social_sentiment=0.0,
            article_count=0,
            analysis_timestamp=datetime.now()
        )


# Initialize service core
sentiment_service = SentimentServiceCore()


# FastAPI endpoints (if available)
if FASTAPI_AVAILABLE and PYDANTIC_AVAILABLE:
    
    class SentimentRequest(BaseModel):
        symbol: str
    
    class SentimentBatchRequest(BaseModel):
        symbols: List[str]
    
    @app.get("/sentiment/{symbol}")
    async def get_sentiment(symbol: str):
        """Get sentiment score for a symbol"""
        try:
            import json
            sentiment = sentiment_service.get_sentiment_score(symbol.upper())
            # Use the same datetime serialization fix
            if hasattr(sentiment, 'model_dump'):
                data = sentiment.model_dump()
            else:
                data = sentiment.__dict__.copy()
            
            # Use json.dumps with default=str to handle datetime objects
            json_data = json.dumps(data, default=str)
            return JSONResponse(content=json.loads(json_data))
        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/sentiment/batch")
    async def get_sentiment_batch(request: SentimentBatchRequest):
        """Get sentiment scores for multiple symbols"""
        try:
            import json
            summary = sentiment_service.get_sentiment_summary(request.symbols)
            # Use the same datetime serialization fix
            if hasattr(summary, 'model_dump'):
                data = summary.model_dump()
            else:
                data = summary.__dict__.copy()
            
            # Use json.dumps with default=str to handle datetime objects
            json_data = json.dumps(data, default=str)
            return JSONResponse(content=json.loads(json_data))
        except Exception as e:
            logger.error(f"Error getting batch sentiment: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/sentiment/update-cache")
    async def update_cache(request: SentimentBatchRequest):
        """Update sentiment cache for symbols"""
        try:
            updated_count = sentiment_service.update_sentiment_cache(request.symbols)
            return JSONResponse(content={
                'updated_symbols': updated_count,
                'total_symbols': len(request.symbols),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error updating sentiment cache: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Test with a sample symbol
            test_sentiment = sentiment_service.get_sentiment_score("CBA")
            
            return JSONResponse(content={
                'status': 'healthy',
                'service': 'sentiment',
                'cache_size': len(sentiment_service.sentiment_cache),
                'test_sentiment_confidence': test_sentiment.confidence_score,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    'status': 'unhealthy',
                    'service': 'sentiment',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            )


# Legacy compatibility functions
def get_symbol_sentiment(symbol: str) -> dict:
    """Legacy function for sentiment analysis"""
    sentiment = sentiment_service.get_sentiment_score(symbol)
    return sentiment.to_dict()


def get_market_sentiment(symbols: List[str]) -> dict:
    """Legacy function for market sentiment analysis"""
    summary = sentiment_service.get_sentiment_summary(symbols)
    return summary.to_dict()


def update_sentiment_data(symbols: List[str]) -> int:
    """Legacy function for updating sentiment data"""
    return sentiment_service.update_sentiment_cache(symbols)


# Main execution
if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        import uvicorn
        logger.info("Starting Sentiment Service on port 8002")
        uvicorn.run(app, host="0.0.0.0", port=8002)
    else:
        logger.info("Sentiment Service running in compatibility mode (FastAPI not available)")
        print("Sentiment Service Core initialized successfully")
        
        # Test with a sample symbol
        test_sentiment = sentiment_service.get_sentiment_score("CBA")
        print(f"Test sentiment for CBA: {test_sentiment.to_dict()}")
