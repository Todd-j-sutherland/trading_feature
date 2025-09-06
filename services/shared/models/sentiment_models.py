"""Sentiment analysis data models for service communication"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    # Fallback for environments without pydantic
    BaseModel = object
    def Field(*args, **kwargs):
        return None
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class SentimentPolarity(str, Enum):
    """Sentiment polarity types"""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class NewsSource(str, Enum):
    """News source types"""
    ABC_NEWS = "ABC_NEWS"
    SMH = "SMH"
    FINANCIAL_REVIEW = "FINANCIAL_REVIEW"
    REDDIT = "REDDIT"
    MARKETAUX = "MARKETAUX"
    OTHER = "OTHER"


class NewsArticle(BaseModel):
    """News article model"""
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    source: str = Field(..., description="News source")
    published_date: datetime = Field(..., description="Publication date")
    url: str = Field(..., description="Article URL")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance to symbol")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return self.model_dump() if hasattr(self, 'model_dump') else self.__dict__
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsArticle':
        """Create from dictionary for backwards compatibility"""
        return cls(**data)


class SentimentScore(BaseModel):
    """Sentiment analysis result"""
    symbol: str = Field(..., description="Stock symbol analyzed")
    overall_sentiment: float = Field(..., ge=-1.0, le=1.0, description="Overall sentiment score -1 to +1")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in sentiment analysis")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score (alias for confidence)")
    
    # Detailed scores
    news_sentiment: Optional[float] = Field(None, description="News-based sentiment")
    social_sentiment: Optional[float] = Field(None, description="Social media sentiment")
    
    # Volume metrics
    news_count: int = Field(0, description="Number of news articles analyzed")
    social_mentions: int = Field(0, description="Number of social media mentions")
    article_count: int = Field(0, description="Number of articles analyzed (alias for news_count)")
    
    # Timing
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    # Sentiment components
    positive_score: float = Field(0.0, description="Positive sentiment component")
    negative_score: float = Field(0.0, description="Negative sentiment component")
    neutral_score: float = Field(0.0, description="Neutral sentiment component")
    
    # Temporal analysis
    sentiment_trend: Optional[float] = Field(None, description="Sentiment trend over time")
    volatility: Optional[float] = Field(None, description="Sentiment volatility")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    analysis_period: Optional[str] = Field(None, description="Time period analyzed")
    sources_used: List[NewsSource] = Field(default=[], description="News sources analyzed")

    @validator('overall_sentiment')
    def validate_sentiment(cls, v):
        if v < -1.0 or v > 1.0:
            raise ValueError('Sentiment must be between -1.0 and 1.0')
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return self.model_dump() if hasattr(self, 'model_dump') else self.__dict__
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentScore':
        """Create from dictionary for backwards compatibility"""
        return cls(**data)


class NewsItem(BaseModel):
    """Individual news item"""
    title: str = Field(..., description="News article title")
    content: Optional[str] = Field(None, description="Article content")
    url: Optional[str] = Field(None, description="Article URL")
    
    # Source information
    source: NewsSource = Field(..., description="News source")
    author: Optional[str] = Field(None, description="Article author")
    
    # Timing
    published_date: datetime = Field(..., description="Publication date")
    analyzed_date: datetime = Field(default_factory=datetime.now, description="Analysis date")
    
    # Sentiment analysis
    sentiment_score: Optional[float] = Field(None, description="Sentiment score for this article")
    confidence: Optional[float] = Field(None, description="Confidence in sentiment")
    polarity: Optional[SentimentPolarity] = Field(None, description="Sentiment polarity")
    
    # Keywords and relevance
    keywords: List[str] = Field(default=[], description="Extracted keywords")
    relevance_score: Optional[float] = Field(None, description="Relevance to target symbol")
    symbols_mentioned: List[str] = Field(default=[], description="Stock symbols mentioned")


class SentimentRequest(BaseModel):
    """Request for sentiment analysis"""
    symbol: str = Field(..., description="Stock symbol to analyze")
    
    # Analysis options
    include_news: bool = Field(True, description="Include news analysis")
    include_social: bool = Field(True, description="Include social media analysis")
    
    # Time constraints
    hours_back: int = Field(24, description="Hours back to analyze")
    max_articles: Optional[int] = Field(None, description="Maximum articles to analyze")
    
    # Data sources
    preferred_sources: List[NewsSource] = Field(default=[], description="Preferred news sources")
    exclude_sources: List[NewsSource] = Field(default=[], description="Sources to exclude")
    
    # Options
    force_refresh: bool = Field(False, description="Force refresh of cached data")
    cache_duration: int = Field(3600, description="Cache duration in seconds")
    
    # Metadata
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class SentimentAnalysis(BaseModel):
    """Complete sentiment analysis result"""
    request: SentimentRequest = Field(..., description="Original request")
    sentiment_score: SentimentScore = Field(..., description="Aggregated sentiment score")
    
    # Detailed results
    news_items: List[NewsItem] = Field(default=[], description="Individual news items analyzed")
    
    # Processing statistics
    total_articles_found: int = Field(0, description="Total articles found")
    articles_analyzed: int = Field(0, description="Articles successfully analyzed")
    processing_time_ms: float = Field(0.0, description="Processing time in milliseconds")
    
    # Quality metrics
    data_quality_score: float = Field(1.0, description="Data quality assessment")
    reliability_score: float = Field(1.0, description="Analysis reliability score")
    
    # Warnings and errors
    warnings: List[str] = Field(default=[], description="Analysis warnings")
    errors: List[str] = Field(default=[], description="Processing errors")


class SentimentTrend(BaseModel):
    """Sentiment trend over time"""
    symbol: str = Field(..., description="Stock symbol")
    
    # Time series data
    timestamps: List[datetime] = Field(..., description="Time points")
    sentiment_scores: List[float] = Field(..., description="Sentiment scores over time")
    
    # Trend analysis
    trend_direction: str = Field(..., description="Overall trend direction")
    trend_strength: float = Field(..., description="Trend strength")
    volatility: float = Field(..., description="Sentiment volatility")
    
    # Statistics
    mean_sentiment: float = Field(..., description="Mean sentiment over period")
    min_sentiment: float = Field(..., description="Minimum sentiment")
    max_sentiment: float = Field(..., description="Maximum sentiment")
    
    # Metadata
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    data_points: int = Field(..., description="Number of data points")


class SentimentSummary(BaseModel):
    """Sentiment summary for multiple symbols"""
    symbols_analyzed: int = Field(default=0, description="Number of symbols analyzed")
    average_sentiment: float = Field(default=0.0, description="Average sentiment across all symbols")
    positive_sentiment_count: int = Field(default=0, description="Number of symbols with positive sentiment")
    negative_sentiment_count: int = Field(default=0, description="Number of symbols with negative sentiment")
    neutral_sentiment_count: int = Field(default=0, description="Number of symbols with neutral sentiment")
    sentiment_scores: List[SentimentScore] = Field(default=[], description="Individual sentiment scores")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return self.model_dump() if hasattr(self, 'model_dump') else self.__dict__
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentSummary':
        """Create from dictionary for backwards compatibility"""
        return cls(**data)
