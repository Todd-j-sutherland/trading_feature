"""Market and price data models for service communication"""

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


class MarketTrend(str, Enum):
    """Market trend types"""
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    BULLISH = "BULLISH"


class TradingSession(str, Enum):
    """Trading session types"""
    PRE_MARKET = "PRE_MARKET"
    MARKET_HOURS = "MARKET_HOURS"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"


class PriceData(BaseModel):
    """Stock price data"""
    symbol: str = Field(..., description="Stock symbol")
    
    # OHLCV data
    open_price: float = Field(..., description="Opening price")
    high_price: float = Field(..., description="High price")
    low_price: float = Field(..., description="Low price")
    close_price: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    
    # Price changes
    price_change: float = Field(..., description="Price change from previous close")
    price_change_pct: float = Field(..., description="Percentage price change")
    
    # Intraday metrics
    daily_range: float = Field(..., description="High - Low range")
    average_price: float = Field(..., description="Volume weighted average price")
    
    # Timestamps
    timestamp: datetime = Field(..., description="Price data timestamp")
    market_date: str = Field(..., description="Market date (YYYY-MM-DD)")
    
    # Market context
    trading_session: TradingSession = Field(..., description="Current trading session")
    is_real_time: bool = Field(True, description="Whether price is real-time")


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators"""
    symbol: str = Field(..., description="Stock symbol")
    
    # Momentum indicators
    rsi_14: Optional[float] = Field(None, description="14-day RSI")
    rsi_50: Optional[float] = Field(None, description="50-day RSI")
    
    # Moving averages
    sma_10: Optional[float] = Field(None, description="10-day SMA")
    sma_20: Optional[float] = Field(None, description="20-day SMA")
    sma_50: Optional[float] = Field(None, description="50-day SMA")
    sma_200: Optional[float] = Field(None, description="200-day SMA")
    
    # Exponential moving averages
    ema_12: Optional[float] = Field(None, description="12-day EMA")
    ema_26: Optional[float] = Field(None, description="26-day EMA")
    
    # MACD indicators
    macd_line: Optional[float] = Field(None, description="MACD line")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    macd_histogram: Optional[float] = Field(None, description="MACD histogram")
    
    # Bollinger Bands
    bollinger_upper: Optional[float] = Field(None, description="Upper Bollinger Band")
    bollinger_lower: Optional[float] = Field(None, description="Lower Bollinger Band")
    bollinger_width: Optional[float] = Field(None, description="Bollinger Band width")
    
    # Volume indicators
    volume_sma20: Optional[float] = Field(None, description="20-day volume SMA")
    volume_ratio: Optional[float] = Field(None, description="Current volume / average volume")
    on_balance_volume: Optional[float] = Field(None, description="On-balance volume")
    
    # Volatility indicators
    atr_14: Optional[float] = Field(None, description="14-day Average True Range")
    volatility_20d: Optional[float] = Field(None, description="20-day volatility")
    
    # Custom indicators
    momentum_score: Optional[float] = Field(None, description="Custom momentum score")
    trend_strength: Optional[float] = Field(None, description="Trend strength indicator")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")
    data_period: str = Field("1D", description="Data period used for calculations")


class MarketContext(BaseModel):
    """Market context and conditions"""
    # ASX 200 context
    asx200_level: float = Field(..., description="Current ASX 200 level")
    asx200_change: float = Field(..., description="ASX 200 change from previous close")
    asx200_change_pct: float = Field(..., description="ASX 200 percentage change")
    
    # Market trend analysis
    market_trend: MarketTrend = Field(..., description="Current market trend")
    trend_strength: float = Field(..., description="Market trend strength")
    
    # Volatility measures
    vix_level: Optional[float] = Field(None, description="VIX volatility index")
    market_volatility: float = Field(..., description="Market volatility measure")
    
    # Currency impact
    aud_usd_rate: Optional[float] = Field(None, description="AUD/USD exchange rate")
    currency_impact: Optional[float] = Field(None, description="Currency impact on ASX")
    
    # Market breadth
    advancing_stocks: Optional[int] = Field(None, description="Number of advancing stocks")
    declining_stocks: Optional[int] = Field(None, description="Number of declining stocks")
    market_breadth: Optional[float] = Field(None, description="Market breadth ratio")
    
    # Sector performance
    financial_sector_change: Optional[float] = Field(None, description="Financial sector performance")
    sector_correlation: Optional[float] = Field(None, description="Sector correlation with market")
    
    # Trading context
    confidence_multiplier: float = Field(1.0, description="Context-based confidence multiplier")
    buy_threshold: float = Field(70.0, description="Dynamic buy threshold percentage")
    
    # Market timing
    market_session: TradingSession = Field(..., description="Current market session")
    time_to_close: Optional[int] = Field(None, description="Minutes until market close")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Context timestamp")
    data_quality: float = Field(1.0, description="Data quality score")


class MarketSnapshot(BaseModel):
    """Complete market snapshot"""
    # Market overview
    market_context: MarketContext = Field(..., description="Market context")
    
    # Individual stock data
    stock_prices: Dict[str, PriceData] = Field(default={}, description="Stock price data")
    technical_indicators: Dict[str, TechnicalIndicators] = Field(default={}, description="Technical indicators")
    
    # Market statistics
    total_volume: int = Field(0, description="Total market volume")
    total_value: float = Field(0.0, description="Total market value traded")
    
    # Performance metrics
    top_gainers: List[str] = Field(default=[], description="Top gaining stocks")
    top_losers: List[str] = Field(default=[], description="Top losing stocks")
    most_active: List[str] = Field(default=[], description="Most active stocks by volume")
    
    # Snapshot metadata
    snapshot_time: datetime = Field(default_factory=datetime.now, description="Snapshot timestamp")
    data_sources: List[str] = Field(default=[], description="Data sources used")
    coverage: float = Field(1.0, description="Data coverage percentage")
