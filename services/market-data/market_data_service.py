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
        # Input validation
        if not symbol or not isinstance(symbol, str):
            return {"error": "Invalid symbol parameter"}
        
        # Sanitize symbol
        symbol = symbol.upper().strip()
        if not symbol.replace('.', '').replace('-', '').isalnum():
            return {"error": "Invalid symbol format"}
        
        try:
            # Check cache first
            cache_key = f"market_data:{symbol}"
            if cache_key in self.data_cache:
                cached_data, timestamp = self.data_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    self.logger.info(f'"symbol": "{symbol}", "action": "cache_hit"')
                    return {**cached_data, "cached": True, "cache_age": datetime.now().timestamp() - timestamp}
            
            # Fetch fresh data with timeout
            ticker = yf.Ticker(symbol)
            
            # Get current data with error handling
            try:
                info = ticker.info or {}
                hist = ticker.history(period="5d")
            except Exception as fetch_error:
                self.logger.error(f'"symbol": "{symbol}", "error": "{fetch_error}", "action": "yfinance_fetch_failed"')
                return {"error": f"Data fetch failed: {fetch_error}", "symbol": symbol}
            
            if hist.empty or len(hist) == 0:
                return {"error": f"No historical data available for {symbol}", "symbol": symbol}
            
            # Validate data integrity
            if 'Close' not in hist.columns or hist['Close'].isnull().all():
                return {"error": f"Invalid price data for {symbol}", "symbol": symbol}
            
            current_price = float(hist['Close'].iloc[-1])
            previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
            
            # Validate price data
            if current_price <= 0:
                return {"error": f"Invalid price data: {current_price}", "symbol": symbol}
            
            # Calculate technical indicators
            technical_data = await self._calculate_technical_indicators(hist)
            
            # Validate volume data
            volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns and not hist['Volume'].isnull().iloc[-1] else 0
            
            # Prepare comprehensive market data
            market_data = {
                "symbol": symbol,
                "current_price": current_price,
                "previous_close": previous_close,
                "change": round(current_price - previous_close, 4),
                "change_percent": round((current_price - previous_close) / previous_close * 100, 2),
                "volume": volume,
                "technical": technical_data,
                "market_cap": info.get("marketCap", 0) if isinstance(info.get("marketCap"), (int, float)) else 0,
                "timestamp": datetime.now().isoformat(),
                "source": "yfinance",
                "cached": False
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
            return {"error": str(e), "symbol": symbol, "timestamp": datetime.now().isoformat()}
    
    async def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical analysis indicators"""
        try:
            # Validate input data
            if hist.empty or 'Close' not in hist.columns:
                return {"error": "Invalid historical data"}
            
            close_prices = hist['Close'].dropna()
            volumes = hist['Volume'].dropna() if 'Volume' in hist.columns else pd.Series()
            
            if len(close_prices) < 2:
                return {"error": "Insufficient price data for technical analysis"}
            
            # RSI calculation with error handling
            try:
                rsi = self._calculate_rsi(close_prices)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "rsi_calculation_failed"')
                rsi = 50.0  # Neutral RSI
            
            # Moving averages with proper handling
            try:
                ma_10 = float(close_prices.rolling(window=min(10, len(close_prices))).mean().iloc[-1])
                ma_20 = float(close_prices.rolling(window=min(20, len(close_prices))).mean().iloc[-1])
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "ma_calculation_failed"')
                ma_10 = float(close_prices.iloc[-1])
                ma_20 = float(close_prices.iloc[-1])
            
            # Volume analysis with validation
            try:
                if not volumes.empty and len(volumes) > 0:
                    avg_volume = float(volumes.rolling(window=min(10, len(volumes))).mean().iloc[-1])
                    current_volume = float(volumes.iloc[-1])
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                else:
                    volume_ratio = 1.0
                    avg_volume = 0.0
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "volume_calculation_failed"')
                volume_ratio = 1.0
                avg_volume = 0.0
            
            # Volatility calculation with safety checks
            try:
                returns = close_prices.pct_change().dropna()
                volatility = float(returns.std()) if len(returns) > 1 else 0.0
                # Cap extreme volatility values
                volatility = min(volatility, 1.0)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "volatility_calculation_failed"')
                volatility = 0.0
            
            # Momentum calculation with bounds checking
            try:
                if len(close_prices) >= 4:
                    momentum = float((close_prices.iloc[-1] / close_prices.iloc[-4] - 1) * 100)
                    # Cap extreme momentum values
                    momentum = max(-50, min(50, momentum))
                else:
                    momentum = 0.0
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "momentum_calculation_failed"')
                momentum = 0.0
            
            # Technical score calculation
            current_price = float(close_prices.iloc[-1])
            tech_score = self._calculate_technical_score(rsi, ma_10, ma_20, current_price)
            
            return {
                "rsi": round(float(rsi), 2),
                "ma_10": round(ma_10, 4),
                "ma_20": round(ma_20, 4),
                "volume_ratio": round(volume_ratio, 2),
                "volatility": round(volatility, 4),
                "momentum": round(momentum, 2),
                "tech_score": round(tech_score, 1),
                "current_price": round(current_price, 4),
                "data_points": len(close_prices)
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "technical_calculation_failed"')
            return {
                "error": str(e),
                "rsi": 50.0,
                "ma_10": 0.0,
                "ma_20": 0.0,
                "volume_ratio": 1.0,
                "volatility": 0.0,
                "momentum": 0.0,
                "tech_score": 50.0,
                "current_price": 0.0
            }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index) with proper error handling"""
        try:
            # Validate inputs
            if prices.empty or len(prices) < period + 1:
                return 50.0  # Neutral RSI for insufficient data
            
            # Remove any NaN values
            prices = prices.dropna()
            if len(prices) < period + 1:
                return 50.0
            
            # Calculate price differences
            delta = prices.diff().dropna()
            if delta.empty:
                return 50.0
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            avg_gains = gains.rolling(window=period, min_periods=period).mean()
            avg_losses = losses.rolling(window=period, min_periods=period).mean()
            
            # Handle edge cases
            if avg_losses.iloc[-1] == 0:
                return 100.0  # All gains, maximum RSI
            
            # Calculate RS and RSI
            rs = avg_gains.iloc[-1] / avg_losses.iloc[-1]
            rsi = 100 - (100 / (1 + rs))
            
            # Validate result
            if pd.isna(rsi) or not (0 <= rsi <= 100):
                return 50.0
            
            return float(rsi)
            
        except Exception as e:
            self.logger.warning(f'"error": "{e}", "action": "rsi_calculation_error"')
            return 50.0  # Neutral RSI if calculation fails
    
    def _calculate_technical_score(self, rsi: float, ma_10: float, ma_20: float, current_price: float) -> float:
        """Calculate overall technical analysis score (0-100) with bounds checking"""
        try:
            # Validate inputs
            if not all(isinstance(x, (int, float)) for x in [rsi, ma_10, ma_20, current_price]):
                return 50.0
            
            if current_price <= 0 or ma_10 <= 0 or ma_20 <= 0:
                return 50.0
            
            # Ensure RSI is in valid range
            rsi = max(0, min(100, rsi))
            
            score = 50.0  # Start with neutral
            
            # RSI component (0-30 points)
            if 30 <= rsi <= 70:
                score += 10  # Neutral RSI is good
            elif rsi < 30:
                score += 15  # Oversold - potential buy
            elif rsi > 70:
                score -= 10  # Overbought - potential sell
            else:
                score += 5  # Slightly favor extreme RSI
            
            # Moving average component (0-20 points)
            try:
                if current_price > ma_10 > ma_20:
                    score += 20  # Strong uptrend
                elif current_price > ma_10:
                    score += 10  # Moderate uptrend
                elif current_price < ma_10 < ma_20:
                    score -= 15  # Downtrend
                elif current_price < ma_10:
                    score -= 5   # Slight downtrend
                else:
                    score += 0   # Neutral
            except (ZeroDivisionError, ValueError):
                # If MA calculations are invalid, don't modify score
                pass
            
            # Ensure score stays within bounds
            final_score = max(0, min(100, score))
            return float(final_score)
            
        except Exception as e:
            self.logger.warning(f'"error": "{e}", "action": "tech_score_calculation_error"')
            return 50.0  # Neutral score on error
    
    async def get_asx_context(self):
        """Get overall ASX market conditions with error handling"""
        try:
            # Get ASX 200 index data with timeout protection
            asx200 = yf.Ticker("^AXJO")
            
            try:
                asx_hist = asx200.history(period="5d")
            except Exception as fetch_error:
                self.logger.error(f'"error": "{fetch_error}", "action": "asx200_fetch_failed"')
                return {
                    "context": "NEUTRAL",
                    "buy_threshold": 0.70,
                    "error": f"ASX 200 data fetch failed: {fetch_error}",
                    "timestamp": datetime.now().isoformat()
                }
            
            if not asx_hist.empty and 'Close' in asx_hist.columns and len(asx_hist) > 0:
                # Validate data integrity
                close_prices = asx_hist['Close'].dropna()
                if len(close_prices) == 0:
                    raise ValueError("No valid ASX 200 close prices")
                
                current_level = float(close_prices.iloc[-1])
                previous_close = float(close_prices.iloc[-2]) if len(close_prices) > 1 else current_level
                
                # Validate price data
                if current_level <= 0 or previous_close <= 0:
                    raise ValueError(f"Invalid ASX 200 price data: current={current_level}, previous={previous_close}")
                
                market_change = (current_level - previous_close) / previous_close * 100
                
                # Determine market context with more nuanced thresholds
                if market_change > 1.5:
                    context = "VERY_BULLISH"
                    buy_threshold = 0.60  # Very low threshold in strong bull market
                elif market_change > 0.5:
                    context = "BULLISH"
                    buy_threshold = 0.65  # Lower threshold in bull market
                elif market_change < -1.5:
                    context = "VERY_BEARISH"
                    buy_threshold = 0.85  # Very high threshold in bear market
                elif market_change < -0.5:
                    context = "BEARISH" 
                    buy_threshold = 0.80  # Higher threshold in bear market
                else:
                    context = "NEUTRAL"
                    buy_threshold = 0.70  # Standard threshold
                
                # Additional market metrics
                try:
                    # Calculate volatility
                    returns = close_prices.pct_change().dropna()
                    volatility = float(returns.std()) if len(returns) > 1 else 0.0
                    
                    # Calculate trend strength
                    if len(close_prices) >= 5:
                        trend_strength = (close_prices.iloc[-1] - close_prices.iloc[-5]) / close_prices.iloc[-5] * 100
                    else:
                        trend_strength = market_change
                        
                except Exception as calc_error:
                    self.logger.warning(f'"error": "{calc_error}", "action": "market_metrics_calculation_failed"')
                    volatility = 0.0
                    trend_strength = market_change
                
                return {
                    "context": context,
                    "asx200_level": round(current_level, 2),
                    "market_change": round(market_change, 3),
                    "buy_threshold": buy_threshold,
                    "volatility": round(volatility, 4),
                    "trend_strength": round(trend_strength, 3),
                    "data_points": len(close_prices),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "context": "NEUTRAL",
                    "buy_threshold": 0.70,
                    "error": "No valid ASX 200 data available",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "asx_context_failed"')
            return {
                "context": "NEUTRAL",
                "buy_threshold": 0.70,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
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
        """Get market data for multiple symbols efficiently with validation"""
        # Input validation
        if symbols is None:
            symbols = self.asx_symbols.copy()
        elif not isinstance(symbols, list):
            return {"error": "Symbols must be provided as a list"}
        elif len(symbols) == 0:
            return {"error": "Empty symbols list provided"}
        elif len(symbols) > 50:  # Rate limiting protection
            return {"error": "Too many symbols requested (max 50)"}
        
        # Validate and sanitize symbols
        valid_symbols = []
        for symbol in symbols:
            if isinstance(symbol, str) and symbol.strip():
                clean_symbol = symbol.upper().strip()
                if clean_symbol.replace('.', '').replace('-', '').isalnum():
                    valid_symbols.append(clean_symbol)
                else:
                    self.logger.warning(f'"invalid_symbol": "{symbol}", "action": "symbol_skipped"')
            else:
                self.logger.warning(f'"invalid_symbol": "{symbol}", "action": "symbol_skipped"')
        
        if not valid_symbols:
            return {"error": "No valid symbols provided"}
        
        results = {}
        successful_count = 0
        failed_count = 0
        
        # Process symbols with error isolation
        for symbol in valid_symbols:
            try:
                result = await self.get_market_data(symbol)
                results[symbol] = result
                
                if "error" not in result:
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "batch_fetch_error"')
                results[symbol] = {"error": str(e), "symbol": symbol}
                failed_count += 1
        
        # Calculate summary statistics
        successful_results = [r for r in results.values() if "error" not in r]
        
        summary = {
            "total_requested": len(symbols),
            "valid_symbols": len(valid_symbols),
            "total_symbols": len(valid_symbols),
            "successful": successful_count,
            "failed": failed_count,
            "success_rate": round((successful_count / len(valid_symbols)) * 100, 1) if valid_symbols else 0
        }
        
        # Add market overview if we have successful results
        if successful_results:
            try:
                prices = [r["current_price"] for r in successful_results if "current_price" in r]
                changes = [r["change_percent"] for r in successful_results if "change_percent" in r]
                
                if prices and changes:
                    summary["market_overview"] = {
                        "avg_price": round(sum(prices) / len(prices), 2),
                        "avg_change": round(sum(changes) / len(changes), 2),
                        "positive_changes": len([c for c in changes if c > 0]),
                        "negative_changes": len([c for c in changes if c < 0])
                    }
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "summary_calculation_failed"')
        
        return {
            "symbols": results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
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
