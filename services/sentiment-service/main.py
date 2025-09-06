"""
Sentiment Service - News sentiment analysis and scoring.

This service handles:
- News collection from multiple sources
- Sentiment analysis using various models
- Real-time sentiment scoring for stocks
- Market sentiment aggregation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime, timedelta
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from shared.models import SentimentScore, NewsArticle, MarketSentiment
from shared.utils import setup_service_logging, health_check_endpoint, validate_symbol
from core.news_collector import NewsCollector
from core.sentiment_analyzer import SentimentAnalyzer
from core.market_sentiment import MarketSentimentAnalyzer


class SentimentService:
    """Main sentiment analysis service."""
    
    def __init__(self):
        self.logger = setup_service_logging("sentiment-service")
        self.news_collector = NewsCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.market_analyzer = MarketSentimentAnalyzer()
        self.logger.info("Sentiment service initialized")
    
    def get_sentiment_score(self, symbol: str) -> SentimentScore:
        """Get current sentiment score for a symbol."""
        symbol = validate_symbol(symbol)
        
        # Get recent news for the symbol
        news_articles = self.news_collector.get_recent_news(symbol, hours=24)
        
        if not news_articles:
            # Return neutral sentiment if no news
            return SentimentScore(
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                timestamp=datetime.utcnow(),
                source="sentiment-service",
                headline="No recent news available"
            )
        
        # Analyze sentiment of all articles
        sentiment_scores = []
        for article in news_articles:
            score = self.sentiment_analyzer.analyze_article(article)
            sentiment_scores.append(score)
        
        # Aggregate scores
        avg_score = sum(s.score for s in sentiment_scores) / len(sentiment_scores)
        avg_confidence = sum(s.confidence for s in sentiment_scores) / len(sentiment_scores)
        
        # Weight by recency (more recent articles have higher weight)
        weighted_score = self._calculate_weighted_sentiment(sentiment_scores)
        
        return SentimentScore(
            symbol=symbol,
            score=weighted_score,
            confidence=avg_confidence,
            timestamp=datetime.utcnow(),
            source="sentiment-service",
            headline=f"Based on {len(news_articles)} articles"
        )
    
    def get_recent_news(self, symbol: str, hours: int = 24) -> List[NewsArticle]:
        """Get recent news articles for a symbol."""
        symbol = validate_symbol(symbol)
        return self.news_collector.get_recent_news(symbol, hours)
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment analysis."""
        return self.market_analyzer.analyze_market_sentiment()
    
    def analyze_bulk_sentiment(self, symbols: List[str]) -> Dict[str, SentimentScore]:
        """Analyze sentiment for multiple symbols."""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_sentiment_score(symbol)
            except Exception as e:
                self.logger.error(f"Error analyzing sentiment for {symbol}: {e}")
                # Continue with other symbols
        return results
    
    def _calculate_weighted_sentiment(self, sentiment_scores: List[SentimentScore]) -> float:
        """Calculate time-weighted sentiment score."""
        if not sentiment_scores:
            return 0.0
        
        now = datetime.utcnow()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for score in sentiment_scores:
            # Calculate age in hours
            age_hours = (now - score.timestamp).total_seconds() / 3600
            
            # Weight function: more recent = higher weight
            weight = max(0.1, 1.0 - (age_hours / 24))  # Linear decay over 24 hours
            
            weighted_sum += score.score * weight * score.confidence
            weight_sum += weight * score.confidence
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0


# FastAPI app
app = FastAPI(title="Sentiment Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instance
sentiment_service = SentimentService()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Service health check."""
    health_check_func = health_check_endpoint("sentiment-service", "1.0.0")
    return health_check_func()

@app.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Get sentiment score for a symbol."""
    try:
        sentiment_score = sentiment_service.get_sentiment_score(symbol)
        return {
            "symbol": sentiment_score.symbol,
            "score": sentiment_score.score,
            "confidence": sentiment_score.confidence,
            "timestamp": sentiment_score.timestamp.isoformat(),
            "source": sentiment_score.source,
            "headline": sentiment_score.headline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/{symbol}")
async def get_news(symbol: str, hours: int = 24):
    """Get recent news for a symbol."""
    try:
        news_articles = sentiment_service.get_recent_news(symbol, hours)
        return {
            "symbol": symbol,
            "articles": [
                {
                    "title": article.title,
                    "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                    "url": article.url,
                    "published_at": article.published_at.isoformat(),
                    "source": article.source,
                    "sentiment_score": article.sentiment_score
                }
                for article in news_articles
            ],
            "count": len(news_articles)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-sentiment")
async def get_market_sentiment():
    """Get overall market sentiment."""
    try:
        return sentiment_service.get_market_sentiment()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sentiment/bulk")
async def analyze_bulk_sentiment(symbols: List[str]):
    """Analyze sentiment for multiple symbols."""
    try:
        results = sentiment_service.analyze_bulk_sentiment(symbols)
        return {
            "results": {
                symbol: {
                    "score": score.score,
                    "confidence": score.confidence,
                    "timestamp": score.timestamp.isoformat()
                }
                for symbol, score in results.items()
            },
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)