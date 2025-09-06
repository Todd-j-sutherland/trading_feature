"""
Shared data models for trading system services.

These models define the common data structures used across all services
to ensure consistency and type safety.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TradingSignal(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class MarketSentiment(Enum):
    """Market sentiment classifications."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class StockPrice:
    """Stock price data."""
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[int] = None
    change_percent: Optional[float] = None


@dataclass
class SentimentScore:
    """Sentiment analysis result."""
    symbol: str
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    source: str
    headline: Optional[str] = None


@dataclass
class TradingPosition:
    """Trading position information."""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    position_type: str  # "LONG" or "SHORT"
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None


@dataclass
class MLPrediction:
    """Machine learning prediction result."""
    symbol: str
    predicted_direction: TradingSignal
    confidence: float
    predicted_price_change: float
    features_used: Dict[str, Any]
    model_version: str
    timestamp: datetime


@dataclass
class ServiceHealthStatus:
    """Service health check status."""
    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    details: Dict[str, Any]
    response_time_ms: float


@dataclass
class NewsArticle:
    """News article data."""
    title: str
    content: str
    url: str
    published_at: datetime
    source: str
    symbols_mentioned: List[str]
    sentiment_score: Optional[float] = None