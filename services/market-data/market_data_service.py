"""
Market Data Service - ASX Data Collection and Distribution

Purpose:
This service is responsible for collecting, processing, and distributing market data
for Australian Securities Exchange (ASX) stocks, particularly the Big 4 banks and 
major financial institutions.

Key Responsibilities:
- Fetch real-time and historical price data
- Calculate technical indicators (RSI, moving averages, etc.)
- Provide volume analysis and market context
- Cache frequently requested data
- Monitor ASX market hours and conditions
- Publish market data updates via Redis events

Data Sources:
- Alpha Vantage API for price data
- yfinance for backup data
- ASX market status and context

API Endpoints (via Unix socket):
- get_market_data(symbol) - Get comprehensive market data for a symbol
- get_asx_context() - Get overall ASX market conditions
- get_technical_indicators(symbol) - Get technical analysis data
- refresh_cache(symbol) - Force refresh cached data
- health() - Service health check

Dependencies:
- Base service framework
- Alpha Vantage API credentials
- Redis for event publishing

Related Files:
- app/core/data/price_fetcher.py
- app/core/analysis/technical_analyzer.py
- app/config/alpha_vantage_config.py

Configuration:
- ALPHA_VANTAGE_API_KEY environment variable
- Market hours: 10:00-16:00 AEST
- Cache TTL: 5 minutes for real-time data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

class MarketDataService(BaseService):
    """Market data collection and distribution service"""
    
    def __init__(self):
        super().__init__("market-data")
        
        # Initialize market data components
        self.data_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.asx_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        
        # ASX market hours (AEST)
        self.market_hours = {
            "open": "10:00",
            "close": "16:00",
            "timezone": "Australia/Sydney"
        }
        
        # Register API methods
        self.register_handler("get_market_data", self.get_market_data)
        self.register_handler("get_asx_context", self.get_asx_context)
        self.register_handler("get_technical_indicators", self.get_technical_indicators)
        self.register_handler("refresh_cache", self.refresh_cache)
        self.register_handler("get_multiple_symbols", self.get_multiple_symbols)
    
    async def get_market_data(self, symbol: str):
        """Get comprehensive market data for a symbol"""
        try:
            # Check cache first
            cache_key = f"market_data:{symbol}"
            if cache_key in self.data_cache:
                cached_data, timestamp = self.data_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    self.logger.info(f'"symbol": "{symbol}", "action": "cache_hit"')
                    return cached_data
            
            # Fetch fresh data
            ticker = yf.Ticker(symbol)
            
            # Get current data
            info = ticker.info
            hist = ticker.history(period="5d")
            
            if hist.empty:
                raise Exception(f"No data available for {symbol}")
            
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            # Calculate technical indicators
            technical_data = await self._calculate_technical_indicators(hist)
            
            # Prepare comprehensive market data
            market_data = {
                "symbol": symbol,
                "current_price": float(current_price),
                "previous_close": float(previous_close),
                "change": float(current_price - previous_close),
                "change_percent": float((current_price - previous_close) / previous_close * 100),
                "volume": int(hist['Volume'].iloc[-1]),
                "technical": technical_data,
                "market_cap": info.get("marketCap", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "yfinance"
            }
            
            # Cache the result
            self.data_cache[cache_key] = (market_data, datetime.now().timestamp())
            
            # Publish market data update event
            self.publish_event("market_data_updated", {
                "symbol": symbol,
                "price": current_price,
                "change_percent": market_data["change_percent"]
            })
            
            self.logger.info(f'"symbol": "{symbol}", "price": {current_price}, "action": "data_fetched"')
            return market_data
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "data_fetch_failed"')
            return {"error": str(e), "symbol": symbol}
    
    async def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical analysis indicators"""
        try:
            close_prices = hist['Close']
            volumes = hist['Volume']
            
            # RSI calculation
            rsi = self._calculate_rsi(close_prices)
            
            # Moving averages
            ma_10 = close_prices.rolling(window=10).mean().iloc[-1] if len(close_prices) >= 10 else close_prices.iloc[-1]
            ma_20 = close_prices.rolling(window=20).mean().iloc[-1] if len(close_prices) >= 20 else close_prices.iloc[-1]
            
            # Volume analysis
            avg_volume = volumes.rolling(window=10).mean().iloc[-1] if len(volumes) >= 10 else volumes.iloc[-1]
            volume_ratio = volumes.iloc[-1] / avg_volume if avg_volume > 0 else 1.0
            
            # Volatility (standard deviation of returns)
            returns = close_prices.pct_change().dropna()
            volatility = returns.std() if len(returns) > 1 else 0.0
            
            # Momentum (3-day price change)
            momentum = (close_prices.iloc[-1] / close_prices.iloc[-4] - 1) * 100 if len(close_prices) >= 4 else 0.0
            
            # Technical score calculation
            tech_score = self._calculate_technical_score(rsi, ma_10, ma_20, close_prices.iloc[-1])
            
            return {
                "rsi": float(rsi),
                "ma_10": float(ma_10),
                "ma_20": float(ma_20),
                "volume_ratio": float(volume_ratio),
                "volatility": float(volatility),
                "momentum": float(momentum),
                "tech_score": float(tech_score),
                "current_price": float(close_prices.iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "technical_calculation_failed"')
            return {"error": str(e)}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not rsi.empty else 50.0
        except:
            return 50.0  # Neutral RSI if calculation fails
    
    def _calculate_technical_score(self, rsi: float, ma_10: float, ma_20: float, current_price: float) -> float:
        """Calculate overall technical analysis score (0-100)"""
        score = 50.0  # Start with neutral
        
        # RSI component (0-30 points)
        if 30 <= rsi <= 70:
            score += 10  # Neutral RSI is good
        elif rsi < 30:
            score += 15  # Oversold - potential buy
        elif rsi > 70:
            score -= 10  # Overbought - potential sell
        
        # Moving average component (0-20 points)
        if current_price > ma_10 > ma_20:
            score += 20  # Strong uptrend
        elif current_price > ma_10:
            score += 10  # Moderate uptrend
        elif current_price < ma_10 < ma_20:
            score -= 15  # Downtrend
        
        return max(0, min(100, score))
    
    async def get_asx_context(self):
        """Get overall ASX market conditions"""
        try:
            # Get ASX 200 index data
            asx200 = yf.Ticker("^AXJO")
            asx_hist = asx200.history(period="5d")
            
            if not asx_hist.empty:
                current_level = asx_hist['Close'].iloc[-1]
                previous_close = asx_hist['Close'].iloc[-2] if len(asx_hist) > 1 else current_level
                
                market_change = (current_level - previous_close) / previous_close * 100
                
                # Determine market context
                if market_change > 1:
                    context = "BULLISH"
                    buy_threshold = 0.65  # Lower threshold in bull market
                elif market_change < -1:
                    context = "BEARISH" 
                    buy_threshold = 0.80  # Higher threshold in bear market
                else:
                    context = "NEUTRAL"
                    buy_threshold = 0.70  # Standard threshold
                
                return {
                    "context": context,
                    "asx200_level": float(current_level),
                    "market_change": float(market_change),
                    "buy_threshold": buy_threshold,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "context": "NEUTRAL",
                    "buy_threshold": 0.70,
                    "error": "No ASX 200 data available"
                }
                
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "asx_context_failed"')
            return {
                "context": "NEUTRAL",
                "buy_threshold": 0.70,
                "error": str(e)
            }
    
    async def get_technical_indicators(self, symbol: str):
        """Get technical analysis data only"""
        market_data = await self.get_market_data(symbol)
        if "error" in market_data:
            return market_data
        
        return market_data.get("technical", {})
    
    async def refresh_cache(self, symbol: str = None):
        """Force refresh cached data"""
        if symbol:
            cache_key = f"market_data:{symbol}"
            if cache_key in self.data_cache:
                del self.data_cache[cache_key]
            return await self.get_market_data(symbol)
        else:
            # Clear all cache
            cache_size = len(self.data_cache)
            self.data_cache.clear()
            return {"cleared_entries": cache_size}
    
    async def get_multiple_symbols(self, symbols: List[str] = None):
        """Get market data for multiple symbols efficiently"""
        if not symbols:
            symbols = self.asx_symbols
        
        results = {}
        for symbol in symbols:
            results[symbol] = await self.get_market_data(symbol)
        
        return {
            "symbols": results,
            "summary": {
                "total_symbols": len(symbols),
                "successful": len([r for r in results.values() if "error" not in r]),
                "failed": len([r for r in results.values() if "error" in r])
            }
        }
    
    async def health_check(self):
        """Enhanced health check with market data metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        market_health = {
            **base_health,
            "cache_size": len(self.data_cache),
            "supported_symbols": len(self.asx_symbols),
            "cache_ttl": self.cache_ttl,
            "market_hours": self.market_hours
        }
        
        # Test data connectivity
        try:
            test_symbol = "CBA.AX"
            test_data = await self.get_market_data(test_symbol)
            market_health["data_connectivity"] = "ok" if "error" not in test_data else "failed"
        except:
            market_health["data_connectivity"] = "failed"
        
        return market_health

async def main():
    service = MarketDataService()
    
    # Setup event subscriptions if needed
    # Could subscribe to external market events here
    
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
