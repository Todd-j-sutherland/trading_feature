"""
Sentiment Analyzer - Analyzes sentiment of news articles.
"""

from typing import Dict, Any, List
import re
from datetime import datetime

from shared.models import SentimentScore, NewsArticle


class SentimentAnalyzer:
    """Analyzes sentiment of text content."""
    
    def __init__(self):
        # Simple keyword-based sentiment analysis
        # In production, this would use transformer models like FinBERT
        self.positive_keywords = {
            'profit', 'growth', 'increase', 'gain', 'rise', 'surge', 'bull', 'bullish',
            'strong', 'outperform', 'beat', 'exceed', 'positive', 'upgrade', 'buy',
            'recommend', 'optimistic', 'confidence', 'rally', 'upward', 'boom'
        }
        
        self.negative_keywords = {
            'loss', 'decline', 'decrease', 'fall', 'drop', 'crash', 'bear', 'bearish',
            'weak', 'underperform', 'miss', 'below', 'negative', 'downgrade', 'sell',
            'concern', 'pessimistic', 'worry', 'plunge', 'downward', 'slump'
        }
        
        self.neutral_keywords = {
            'stable', 'unchanged', 'flat', 'sideways', 'hold', 'maintain', 'steady'
        }
    
    def analyze_article(self, article: NewsArticle) -> SentimentScore:
        """Analyze sentiment of a single article."""
        # Combine title and content for analysis
        text = f"{article.title} {article.content}".lower()
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Count keyword matches
        positive_count = sum(1 for word in words if word in self.positive_keywords)
        negative_count = sum(1 for word in words if word in self.negative_keywords)
        neutral_count = sum(1 for word in words if word in self.neutral_keywords)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        # Calculate sentiment score
        if total_sentiment_words == 0:
            score = 0.0
            confidence = 0.1  # Low confidence when no sentiment words found
        else:
            # Score between -1 and 1
            score = (positive_count - negative_count) / max(1, len(words) / 10)
            score = max(-1.0, min(1.0, score))
            
            # Confidence based on number of sentiment words relative to text length
            confidence = min(1.0, total_sentiment_words / max(1, len(words) / 20))
            confidence = max(0.1, confidence)  # Minimum confidence
        
        return SentimentScore(
            symbol=article.symbols_mentioned[0] if article.symbols_mentioned else "UNKNOWN",
            score=score,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            source=f"sentiment-analyzer-{article.source}",
            headline=article.title
        )
    
    def analyze_text(self, text: str, symbol: str = "UNKNOWN") -> SentimentScore:
        """Analyze sentiment of raw text."""
        # Create a temporary article object
        article = NewsArticle(
            title=text[:100] + "..." if len(text) > 100 else text,
            content=text,
            url="",
            published_at=datetime.utcnow(),
            source="text-input",
            symbols_mentioned=[symbol]
        )
        
        return self.analyze_article(article)
    
    def bulk_analyze(self, articles: List[NewsArticle]) -> List[SentimentScore]:
        """Analyze sentiment for multiple articles."""
        return [self.analyze_article(article) for article in articles]
    
    def get_aggregate_sentiment(self, articles: List[NewsArticle], symbol: str) -> SentimentScore:
        """Get aggregated sentiment for articles about a symbol."""
        relevant_articles = [
            article for article in articles 
            if symbol in article.symbols_mentioned
        ]
        
        if not relevant_articles:
            return SentimentScore(
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                timestamp=datetime.utcnow(),
                source="sentiment-analyzer-aggregate",
                headline="No relevant articles found"
            )
        
        # Analyze each article
        sentiment_scores = self.bulk_analyze(relevant_articles)
        
        # Calculate weighted average (more recent articles have higher weight)
        now = datetime.utcnow()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for article, score in zip(relevant_articles, sentiment_scores):
            # Weight based on recency (newer = higher weight)
            age_hours = (now - article.published_at).total_seconds() / 3600
            weight = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours
            
            weighted_sum += score.score * weight * score.confidence
            weight_sum += weight * score.confidence
        
        final_score = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        avg_confidence = sum(s.confidence for s in sentiment_scores) / len(sentiment_scores)
        
        return SentimentScore(
            symbol=symbol,
            score=final_score,
            confidence=avg_confidence,
            timestamp=datetime.utcnow(),
            source="sentiment-analyzer-aggregate",
            headline=f"Aggregate of {len(relevant_articles)} articles"
        )
    
    def add_keywords(self, positive: List[str] = None, negative: List[str] = None, neutral: List[str] = None):
        """Add custom keywords to the analyzer."""
        if positive:
            self.positive_keywords.update(positive)
        if negative:
            self.negative_keywords.update(negative)
        if neutral:
            self.neutral_keywords.update(neutral)
    
    def get_keyword_stats(self) -> Dict[str, int]:
        """Get statistics about loaded keywords."""
        return {
            "positive_keywords": len(self.positive_keywords),
            "negative_keywords": len(self.negative_keywords),
            "neutral_keywords": len(self.neutral_keywords),
            "total_keywords": len(self.positive_keywords) + len(self.negative_keywords) + len(self.neutral_keywords)
        }