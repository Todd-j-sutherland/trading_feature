"""
Market Sentiment Analyzer - Analyzes overall market sentiment.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from shared.models import MarketSentiment


class MarketSentimentAnalyzer:
    """Analyzes overall market sentiment trends."""
    
    def __init__(self):
        self.market_symbols = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX"]
        self.sentiment_history = defaultdict(list)
    
    def analyze_market_sentiment(self) -> Dict[str, Any]:
        """Analyze overall market sentiment."""
        # This is a simplified implementation
        # In production, this would aggregate sentiment from multiple sources
        
        current_time = datetime.utcnow()
        
        # Simulated market sentiment analysis
        # In real implementation, this would:
        # 1. Collect sentiment scores for all major stocks
        # 2. Weight by market cap
        # 3. Analyze trends over time
        # 4. Consider economic indicators
        
        market_sentiment_score = self._calculate_market_score()
        trend = self._calculate_trend()
        volatility = self._calculate_volatility()
        
        # Determine overall sentiment
        if market_sentiment_score > 0.2:
            overall_sentiment = MarketSentiment.BULLISH
        elif market_sentiment_score < -0.2:
            overall_sentiment = MarketSentiment.BEARISH
        else:
            overall_sentiment = MarketSentiment.NEUTRAL
        
        return {
            "overall_sentiment": overall_sentiment.value,
            "sentiment_score": market_sentiment_score,
            "trend": trend,
            "volatility": volatility,
            "confidence": abs(market_sentiment_score),
            "analysis_time": current_time.isoformat(),
            "components": {
                "banking_sector": self._analyze_banking_sector(),
                "economic_indicators": self._analyze_economic_indicators(),
                "news_sentiment": self._analyze_news_sentiment()
            },
            "recommendations": self._get_market_recommendations(overall_sentiment, volatility)
        }
    
    def _calculate_market_score(self) -> float:
        """Calculate overall market sentiment score."""
        # Simplified calculation
        # In reality, this would aggregate multiple data sources
        import random
        return random.uniform(-0.5, 0.5)  # Placeholder
    
    def _calculate_trend(self) -> str:
        """Calculate market trend direction."""
        # Simplified trend analysis
        # In reality, this would analyze historical data
        trends = ["IMPROVING", "DETERIORATING", "STABLE"]
        import random
        return random.choice(trends)
    
    def _calculate_volatility(self) -> str:
        """Calculate market volatility level."""
        volatility_levels = ["LOW", "MEDIUM", "HIGH"]
        import random
        return random.choice(volatility_levels)
    
    def _analyze_banking_sector(self) -> Dict[str, Any]:
        """Analyze banking sector sentiment."""
        return {
            "sector_sentiment": 0.1,
            "top_performers": ["CBA.AX"],
            "concerns": ["regulatory pressure"],
            "outlook": "POSITIVE"
        }
    
    def _analyze_economic_indicators(self) -> Dict[str, Any]:
        """Analyze economic indicators impact."""
        return {
            "interest_rates": "STABLE",
            "inflation": "MODERATE",
            "employment": "STRONG",
            "gdp_growth": "POSITIVE",
            "overall_impact": "NEUTRAL"
        }
    
    def _analyze_news_sentiment(self) -> Dict[str, Any]:
        """Analyze news sentiment trends."""
        return {
            "positive_news_ratio": 0.6,
            "negative_news_ratio": 0.3,
            "neutral_news_ratio": 0.1,
            "major_themes": ["earnings", "regulatory", "economic"],
            "sentiment_strength": "MODERATE"
        }
    
    def _get_market_recommendations(self, sentiment: MarketSentiment, volatility: str) -> List[str]:
        """Get market-based recommendations."""
        recommendations = []
        
        if sentiment == MarketSentiment.BULLISH:
            recommendations.append("Consider increasing exposure to growth stocks")
            if volatility == "LOW":
                recommendations.append("Good time for moderate position increases")
        elif sentiment == MarketSentiment.BEARISH:
            recommendations.append("Consider defensive positioning")
            recommendations.append("Review stop-loss levels")
        else:  # NEUTRAL
            recommendations.append("Maintain current positioning")
            recommendations.append("Look for selective opportunities")
        
        if volatility == "HIGH":
            recommendations.append("Reduce position sizes due to high volatility")
            recommendations.append("Consider shorter holding periods")
        
        return recommendations
    
    def update_sentiment_history(self, symbol: str, score: float):
        """Update historical sentiment data."""
        self.sentiment_history[symbol].append({
            "score": score,
            "timestamp": datetime.utcnow()
        })
        
        # Keep only last 100 data points
        if len(self.sentiment_history[symbol]) > 100:
            self.sentiment_history[symbol] = self.sentiment_history[symbol][-100:]
    
    def get_sentiment_trend(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """Get sentiment trend for a symbol over specified days."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        recent_data = [
            entry for entry in self.sentiment_history[symbol]
            if entry["timestamp"] >= cutoff_time
        ]
        
        if len(recent_data) < 2:
            return {
                "trend": "INSUFFICIENT_DATA",
                "change": 0.0,
                "confidence": 0.0
            }
        
        # Calculate trend
        scores = [entry["score"] for entry in recent_data]
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        change = avg_second - avg_first
        
        if change > 0.1:
            trend = "IMPROVING"
        elif change < -0.1:
            trend = "DETERIORATING"
        else:
            trend = "STABLE"
        
        return {
            "trend": trend,
            "change": change,
            "confidence": min(1.0, len(recent_data) / 20),  # More data = higher confidence
            "data_points": len(recent_data)
        }