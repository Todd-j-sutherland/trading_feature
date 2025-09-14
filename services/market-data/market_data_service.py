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
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Import settings configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from app.config.settings import Settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    Settings = None

class MarketDataService(BaseService):
    """Market data collection and distribution service"""
    
    def __init__(self, default_region: str = "asx"):
        super().__init__("market-data")
        
        # Multi-region support
        self.config_manager = None
        self.current_region = default_region
        self.available_regions = ["asx", "usa"]
        
        # Initialize config manager
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app", "config", "regions"))
            from config_manager import ConfigManager
            self.config_manager = ConfigManager()
            self.logger.info(f"ConfigManager initialized, using region: {self.current_region}")
        except ImportError as e:
            self.logger.warning(f"ConfigManager not available: {e}")
            self.config_manager = None
        
        # Initialize config manager
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app", "config", "regions"))
            from config_manager import ConfigManager
            self.config_manager = ConfigManager()
            self.logger.info(f"ConfigManager initialized, using region: {self.current_region}")
        except ImportError as e:
            self.logger.warning(f"ConfigManager not available: {e}")
            self.config_manager = None
        
        # Load regional configuration
        self._load_regional_config()
        
        # Load legacy configuration as fallback
        self._load_legacy_config()
        
        # Initialize market data components
        self.data_cache = {}
        self.api_call_count = 0
        self.api_errors = 0
        self.last_market_status_check = None
        self.market_status = "unknown"
        
        # Register enhanced API methods
        self.register_handler("get_market_data", self.get_market_data)
        self.register_handler("get_asx_context", self.get_asx_context) 
        self.register_handler("get_technical_indicators", self.get_technical_indicators)
        self.register_handler("refresh_cache", self.refresh_cache)
        self.register_handler("get_multiple_symbols", self.get_multiple_symbols)
        self.register_handler("get_market_hours", self.get_market_hours)
        self.register_handler("get_market_status", self.get_market_status)
        self.register_handler("get_indices_data", self.get_indices_data)
        
        # Multi-region specific handlers
        self.register_handler("switch_region", self.switch_region)
        self.register_handler("get_current_region", self.get_current_region)
        self.register_handler("get_available_regions", self.get_available_regions)
        self.register_handler("get_regional_symbols", self.get_regional_symbols)
    
    def _load_regional_config(self):
        """Load configuration from ConfigManager for current region"""
        if not self.config_manager:
            return
            
        try:
            # Get regional configuration
            config = self.config_manager.get_config(self.current_region)
            
            # Extract market data specific settings
            market_config = config.get("market_config", {})
            symbols_config = config.get("symbols", {})
            
            # Market hours
            trading_hours = market_config.get("trading_hours", {})
            regular_session = trading_hours.get("regular_session", {})
            self.market_hours = {
                "open": regular_session.get("open", "10:00"),
                "close": regular_session.get("close", "16:00"),
                "timezone": trading_hours.get("timezone", "Australia/Sydney")
            }
            
            # Symbols
            self.asx_symbols = symbols_config.get("primary", ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"])
            self.extended_symbols = symbols_config.get("financial_sector", [])
            
            # Technical indicators from base config
            base_config = config.get("base_config", {})
            self.technical_config = base_config.get("technical_indicators", {
                'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
                'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
                'SMA': {'periods': [20, 50, 200]}
            })
            
            # Data sources
            self.primary_source = 'yfinance'
            self.backup_source = 'alpha_vantage'
            self.update_frequency = 15
            self.cache_ttl = 300  # 5 minutes
            
            self.logger.info(f"Loaded regional configuration for {self.current_region}")
            
        except Exception as e:
            self.logger.error(f"Failed to load regional config: {e}")
            self._set_fallback_config()
    
    def _load_legacy_config(self):
        """Load legacy configuration from settings.py as fallback"""
        if SETTINGS_AVAILABLE:
            # Cache settings from settings.py
            cache_config = Settings.CACHE_SETTINGS
            if not hasattr(self, 'cache_ttl'):  # Only set if not already set by regional config
                self.cache_ttl = cache_config.get('duration_minutes', 15) * 60  # Convert to seconds
            
            # Data sources configuration
            data_sources = Settings.DATA_SOURCES
            if not hasattr(self, 'primary_source'):
                self.primary_source = data_sources.get('market_data', {}).get('primary', 'yfinance')
                self.backup_source = data_sources.get('market_data', {}).get('backup', 'alpha_vantage')
                self.update_frequency = data_sources.get('market_data', {}).get('update_frequency_minutes', 15)
            
            # ASX symbols from settings (fallback if regional config failed)
            if not hasattr(self, 'asx_symbols') or not self.asx_symbols:
                self.asx_symbols = Settings.BANK_SYMBOLS.copy()
                self.extended_symbols = Settings.EXTENDED_SYMBOLS.copy() if hasattr(Settings, 'EXTENDED_SYMBOLS') else []
            
            self.market_indices = Settings.MARKET_INDICES if hasattr(Settings, 'MARKET_INDICES') else {}
            
            # Market hours from settings (fallback)
            if not hasattr(self, 'market_hours') or not self.market_hours:
                self.market_hours = {
                    "open": Settings.MARKET_OPEN.strftime("%H:%M"),
                    "close": Settings.MARKET_CLOSE.strftime("%H:%M"),
                    "pre_market": Settings.PRE_MARKET.strftime("%H:%M"),
                    "post_market": Settings.POST_MARKET.strftime("%H:%M"),
                    "timezone": "Australia/Sydney"
                }
            
            # Technical indicators configuration (fallback)
            if not hasattr(self, 'technical_config') or not self.technical_config:
                self.technical_config = Settings.TECHNICAL_INDICATORS
            
            # API configuration
            api_config = Settings.API_CONFIG
            self.alpha_vantage_key = api_config.get('alpha_vantage', {}).get('key', '')
            self.alpha_vantage_enabled = api_config.get('alpha_vantage', {}).get('enabled', False)
            
            self.logger.info("Loaded legacy market data configuration from settings.py")
        else:
            self._set_fallback_config()
    
    def _set_fallback_config(self):
        """Set fallback configuration when no other config is available"""
        self.cache_ttl = 300  # 5 minutes
        self.primary_source = 'yfinance'
        self.backup_source = 'alpha_vantage'
        self.update_frequency = 15
        self.asx_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        self.extended_symbols = []
        self.market_indices = {}
        self.market_hours = {
            "open": "10:00",
            "close": "16:00",
            "timezone": "Australia/Sydney"
        }
        self.technical_config = {
            'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
            'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
            'SMA': {'periods': [20, 50, 200]}
        }
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY', '')
        self.alpha_vantage_enabled = bool(self.alpha_vantage_key)
        self.logger.warning("Using fallback configuration - no settings available")
    
    # Multi-region support methods
    async def switch_region(self, region: str):
        """Switch to a different region configuration"""
        if region not in self.available_regions:
            return {"error": f"Region '{region}' not available. Available regions: {self.available_regions}"}
        
        if not self.config_manager:
            return {"error": "ConfigManager not available - cannot switch regions"}
        
        try:
            old_region = self.current_region
            self.current_region = region
            
            # Clear cache when switching regions
            self.data_cache.clear()
            
            # Reload configuration for new region
            self._load_regional_config()
            
            self.logger.info(f"Switched from {old_region} to {region}")
            return {
                "success": True,
                "previous_region": old_region,
                "current_region": region,
                "symbols_count": len(self.asx_symbols + self.extended_symbols)
            }
        except Exception as e:
            # Rollback on error
            self.current_region = old_region if 'old_region' in locals() else "asx"
            self.logger.error(f"Failed to switch to region {region}: {e}")
            return {"error": f"Failed to switch region: {e}"}
    
    async def get_current_region(self):
        """Get current active region"""
        return {
            "current_region": self.current_region,
            "symbols": self.asx_symbols + self.extended_symbols,
            "market_hours": self.market_hours,
            "config_manager_available": self.config_manager is not None
        }
    
    async def get_available_regions(self):
        """Get list of available regions"""
        return {
            "available_regions": self.available_regions,
            "current_region": self.current_region,
            "config_manager_available": self.config_manager is not None
        }
    
    async def get_regional_symbols(self, region: str = None):
        """Get symbols for specified region (or current region)"""
        if region and region != self.current_region:
            if not self.config_manager:
                return {"error": "ConfigManager not available"}
            
            try:
                config = self.config_manager.get_config(region)
                symbols_config = config.get("symbols", {})
                return {
                    "region": region,
                    "primary_symbols": symbols_config.get("primary", []),
                    "financial_sector": symbols_config.get("financial_sector", []),
                    "trading_groups": symbols_config.get("trading_groups", {})
                }
            except Exception as e:
                return {"error": f"Failed to get symbols for region {region}: {e}"}
        else:
            return {
                "region": self.current_region,
                "primary_symbols": self.asx_symbols,
                "extended_symbols": self.extended_symbols,
                "total_symbols": len(self.asx_symbols + self.extended_symbols)
            }

    async def get_market_data(self, symbol: str, region: str = None):
        """Get comprehensive market data for a symbol, optionally switching regions"""
        # Handle region switching if requested
        original_region = None
        if region and region != self.current_region:
            if region not in self.available_regions:
                return {"error": f"Region '{region}' not available"}
            
            original_region = self.current_region
            switch_result = await self.switch_region(region)
            if "error" in switch_result:
                return switch_result
        
        try:
            # Input validation
            if not symbol or not isinstance(symbol, str):
                return {"error": "Invalid symbol parameter"}
            
            # Sanitize symbol
            symbol = symbol.upper().strip()
            if not symbol.replace('.', '').replace('-', '').isalnum():
                return {"error": "Invalid symbol format"}
            
            # Check cache first (include region in cache key)
            cache_key = f"market_data:{symbol}:{self.current_region}"
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
                "change_percent": market_data["change_percent"],
                "region": self.current_region
            })
            
            self.logger.info(f'"symbol": "{symbol}", "price": {current_price}, "region": "{self.current_region}", "action": "data_fetched"')
            
            # Add region info to response
            market_data["region"] = self.current_region
            
            return market_data
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "region": "{self.current_region}", "action": "data_fetch_failed"')
            return {"error": str(e), "symbol": symbol, "region": self.current_region, "timestamp": datetime.now().isoformat()}
        finally:
            # Restore original region if it was temporarily changed
            if original_region and original_region != self.current_region:
                await self.switch_region(original_region)
    
    async def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical analysis indicators using settings.py configuration"""
        try:
            # Validate input data
            if hist.empty or 'Close' not in hist.columns:
                return {"error": "Invalid historical data"}
            
            close_prices = hist['Close'].dropna()
            volumes = hist['Volume'].dropna() if 'Volume' in hist.columns else pd.Series()
            high_prices = hist['High'].dropna() if 'High' in hist.columns else close_prices
            low_prices = hist['Low'].dropna() if 'Low' in hist.columns else close_prices
            
            if len(close_prices) < 2:
                return {"error": "Insufficient price data for technical analysis"}
            
            # RSI calculation with settings configuration
            rsi_config = self.technical_config.get('RSI', {'period': 14, 'overbought': 70, 'oversold': 30})
            try:
                rsi = self._calculate_rsi(close_prices, period=rsi_config['period'])
                rsi_signal = self._get_rsi_signal(rsi, rsi_config)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "rsi_calculation_failed"')
                rsi = 50.0  # Neutral RSI
                rsi_signal = "NEUTRAL"
            
            # Moving averages with settings configuration
            sma_config = self.technical_config.get('SMA', {'periods': [20, 50, 200]})
            try:
                sma_data = {}
                for period in sma_config['periods']:
                    if len(close_prices) >= period:
                        sma_data[f'sma_{period}'] = float(close_prices.rolling(window=period).mean().iloc[-1])
                    else:
                        sma_data[f'sma_{period}'] = float(close_prices.mean())
                
                # Calculate SMA signals
                sma_signal = self._get_sma_signal(float(close_prices.iloc[-1]), sma_data)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "sma_calculation_failed"')
                sma_data = {'sma_20': float(close_prices.iloc[-1])}
                sma_signal = "NEUTRAL"
            
            # MACD calculation with settings configuration
            macd_config = self.technical_config.get('MACD', {'fast': 12, 'slow': 26, 'signal': 9})
            try:
                macd_data = self._calculate_macd(close_prices, macd_config)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "macd_calculation_failed"')
                macd_data = {"macd": 0.0, "signal": 0.0, "histogram": 0.0, "macd_signal": "NEUTRAL"}
            
            # Bollinger Bands with settings configuration
            bb_config = self.technical_config.get('BB', {'period': 20, 'std': 2})
            try:
                bb_data = self._calculate_bollinger_bands(close_prices, bb_config)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "bb_calculation_failed"')
                bb_data = {"bb_upper": 0.0, "bb_middle": 0.0, "bb_lower": 0.0, "bb_signal": "NEUTRAL"}
            
            # Volume analysis with enhanced validation
            try:
                if not volumes.empty and len(volumes) > 0:
                    volume_config = self.technical_config.get('VOLUME', {'ma_period': 20})
                    vol_period = min(volume_config['ma_period'], len(volumes))
                    avg_volume = float(volumes.rolling(window=vol_period).mean().iloc[-1])
                    current_volume = float(volumes.iloc[-1])
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                    volume_signal = self._get_volume_signal(volume_ratio)
                else:
                    volume_ratio = 1.0
                    avg_volume = 0.0
                    volume_signal = "NEUTRAL"
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "volume_calculation_failed"')
                volume_ratio = 1.0
                avg_volume = 0.0
                volume_signal = "NEUTRAL"
            
            # ATR calculation with settings configuration
            atr_config = self.technical_config.get('ATR', {'period': 14})
            try:
                atr = self._calculate_atr(high_prices, low_prices, close_prices, atr_config['period'])
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "atr_calculation_failed"')
                atr = 0.0
            
            # Enhanced volatility calculation
            try:
                returns = close_prices.pct_change().dropna()
                volatility = float(returns.std()) if len(returns) > 1 else 0.0
                # Calculate volatility percentile
                volatility_window = min(50, len(returns))
                if volatility_window > 10:
                    vol_percentile = (returns.rolling(window=volatility_window).std().iloc[-1] > 
                                    returns.rolling(window=volatility_window).std().quantile(0.8))
                    volatility_signal = "HIGH" if vol_percentile else "NORMAL"
                else:
                    volatility_signal = "NORMAL"
                # Cap extreme volatility values
                volatility = min(volatility, 1.0)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "volatility_calculation_failed"')
                volatility = 0.0
                volatility_signal = "NORMAL"
            
            # Enhanced momentum calculation
            try:
                momentum_periods = [4, 10, 20]
                momentum_data = {}
                for period in momentum_periods:
                    if len(close_prices) >= period:
                        mom = float((close_prices.iloc[-1] / close_prices.iloc[-period] - 1) * 100)
                        momentum_data[f'momentum_{period}d'] = max(-50, min(50, mom))
                    else:
                        momentum_data[f'momentum_{period}d'] = 0.0
                
                # Overall momentum signal
                momentum_signal = self._get_momentum_signal(momentum_data)
            except Exception as e:
                self.logger.warning(f'"error": "{e}", "action": "momentum_calculation_failed"')
                momentum_data = {'momentum_4d': 0.0, 'momentum_10d': 0.0, 'momentum_20d': 0.0}
                momentum_signal = "NEUTRAL"
            
            # Comprehensive technical score
            current_price = float(close_prices.iloc[-1])
            tech_score = self._calculate_enhanced_technical_score(
                rsi, sma_data, macd_data, bb_data, volume_ratio, momentum_data, current_price
            )
            
            # Overall technical signal
            overall_signal = self._determine_overall_signal([
                rsi_signal, sma_signal, macd_data.get('macd_signal', 'NEUTRAL'),
                bb_data.get('bb_signal', 'NEUTRAL'), volume_signal, momentum_signal
            ])
            
            return {
                "rsi": round(float(rsi), 2),
                "rsi_signal": rsi_signal,
                **sma_data,
                "sma_signal": sma_signal,
                **macd_data,
                **bb_data,
                "volume_ratio": round(volume_ratio, 2),
                "volume_signal": volume_signal,
                "atr": round(atr, 4),
                "volatility": round(volatility, 4),
                "volatility_signal": volatility_signal,
                **momentum_data,
                "momentum_signal": momentum_signal,
                "tech_score": round(tech_score, 1),
                "overall_signal": overall_signal,
                "current_price": round(current_price, 4),
                "data_points": len(close_prices),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "technical_calculation_failed"')
            return {
                "error": str(e),
                "rsi": 50.0,
                "tech_score": 50.0,
                "overall_signal": "ERROR"
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
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI using settings configuration"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI for insufficient data
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _get_rsi_signal(self, rsi: float, config: Dict) -> str:
        """Get RSI trading signal based on configuration"""
        if rsi >= config.get('overbought', 70):
            return "OVERBOUGHT"
        elif rsi <= config.get('oversold', 30):
            return "OVERSOLD"
        elif rsi > 60:
            return "BULLISH"
        elif rsi < 40:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _get_sma_signal(self, current_price: float, sma_data: Dict) -> str:
        """Get SMA trading signal"""
        sma_20 = sma_data.get('sma_20', current_price)
        sma_50 = sma_data.get('sma_50', current_price)
        
        if current_price > sma_20 > sma_50:
            return "STRONG_BULLISH"
        elif current_price > sma_20:
            return "BULLISH"
        elif current_price < sma_20 < sma_50:
            return "STRONG_BEARISH"
        elif current_price < sma_20:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _calculate_macd(self, prices: pd.Series, config: Dict) -> Dict[str, Any]:
        """Calculate MACD using settings configuration"""
        try:
            fast = config.get('fast', 12)
            slow = config.get('slow', 26)
            signal_period = config.get('signal', 9)
            
            if len(prices) < slow + signal_period:
                return {"macd": 0.0, "signal": 0.0, "histogram": 0.0, "macd_signal": "NEUTRAL"}
            
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period).mean()
            histogram = macd_line - signal_line
            
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            current_histogram = float(histogram.iloc[-1])
            
            # Determine MACD signal
            if current_macd > current_signal and current_histogram > 0:
                macd_signal = "BULLISH"
            elif current_macd < current_signal and current_histogram < 0:
                macd_signal = "BEARISH"
            else:
                macd_signal = "NEUTRAL"
            
            return {
                "macd": round(current_macd, 4),
                "signal": round(current_signal, 4),
                "histogram": round(current_histogram, 4),
                "macd_signal": macd_signal
            }
        except Exception as e:
            self.logger.warning(f"MACD calculation error: {e}")
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0, "macd_signal": "NEUTRAL"}
    
    def _calculate_bollinger_bands(self, prices: pd.Series, config: Dict) -> Dict[str, Any]:
        """Calculate Bollinger Bands using settings configuration"""
        try:
            period = config.get('period', 20)
            std_dev = config.get('std', 2)
            
            if len(prices) < period:
                current_price = float(prices.iloc[-1])
                return {
                    "bb_upper": current_price,
                    "bb_middle": current_price,
                    "bb_lower": current_price,
                    "bb_signal": "NEUTRAL"
                }
            
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            current_price = float(prices.iloc[-1])
            current_upper = float(upper_band.iloc[-1])
            current_middle = float(sma.iloc[-1])
            current_lower = float(lower_band.iloc[-1])
            
            # Determine BB signal
            if current_price >= current_upper:
                bb_signal = "OVERBOUGHT"
            elif current_price <= current_lower:
                bb_signal = "OVERSOLD"
            elif current_price > current_middle:
                bb_signal = "BULLISH"
            elif current_price < current_middle:
                bb_signal = "BEARISH"
            else:
                bb_signal = "NEUTRAL"
            
            return {
                "bb_upper": round(current_upper, 4),
                "bb_middle": round(current_middle, 4),
                "bb_lower": round(current_lower, 4),
                "bb_signal": bb_signal
            }
        except Exception as e:
            self.logger.warning(f"Bollinger Bands calculation error: {e}")
            current_price = float(prices.iloc[-1])
            return {
                "bb_upper": current_price,
                "bb_middle": current_price,
                "bb_lower": current_price,
                "bb_signal": "NEUTRAL"
            }
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(high) < period or len(low) < period or len(close) < period:
                return 0.0
            
            high_low = high - low
            high_close = abs(high - close.shift())
            low_close = abs(low - close.shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        except Exception:
            return 0.0
    
    def _get_volume_signal(self, volume_ratio: float) -> str:
        """Get volume trading signal"""
        if volume_ratio >= 2.0:
            return "VERY_HIGH"
        elif volume_ratio >= 1.5:
            return "HIGH"
        elif volume_ratio <= 0.5:
            return "LOW"
        elif volume_ratio <= 0.3:
            return "VERY_LOW"
        else:
            return "NORMAL"
    
    def _get_momentum_signal(self, momentum_data: Dict) -> str:
        """Get momentum trading signal"""
        short_momentum = momentum_data.get('momentum_4d', 0)
        medium_momentum = momentum_data.get('momentum_10d', 0)
        
        if short_momentum > 3 and medium_momentum > 2:
            return "STRONG_BULLISH"
        elif short_momentum > 1:
            return "BULLISH"
        elif short_momentum < -3 and medium_momentum < -2:
            return "STRONG_BEARISH"
        elif short_momentum < -1:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _calculate_enhanced_technical_score(self, rsi, sma_data, macd_data, bb_data, volume_ratio, momentum_data, current_price) -> float:
        """Calculate enhanced technical score using all indicators"""
        score = 50.0  # Base neutral score
        
        # RSI component (20% weight)
        if rsi > 70:
            score -= 10  # Overbought
        elif rsi > 60:
            score += 5   # Bullish
        elif rsi < 30:
            score += 10  # Oversold (bullish contrarian)
        elif rsi < 40:
            score -= 5   # Bearish
        
        # SMA component (25% weight)
        sma_20 = sma_data.get('sma_20', current_price)
        sma_50 = sma_data.get('sma_50', current_price)
        if current_price > sma_20 > sma_50:
            score += 12  # Strong bullish trend
        elif current_price > sma_20:
            score += 6   # Bullish
        elif current_price < sma_20 < sma_50:
            score -= 12  # Strong bearish trend
        elif current_price < sma_20:
            score -= 6   # Bearish
        
        # MACD component (20% weight)
        macd_signal = macd_data.get('macd_signal', 'NEUTRAL')
        if macd_signal == 'BULLISH':
            score += 8
        elif macd_signal == 'BEARISH':
            score -= 8
        
        # Volume component (15% weight)
        if volume_ratio > 1.5:
            score += 5  # High volume confirms trend
        elif volume_ratio < 0.7:
            score -= 3  # Low volume weakens signal
        
        # Momentum component (20% weight)
        short_momentum = momentum_data.get('momentum_4d', 0)
        if short_momentum > 2:
            score += 8
        elif short_momentum < -2:
            score -= 8
        
        return max(0, min(100, score))
    
    def _determine_overall_signal(self, signals: List[str]) -> str:
        """Determine overall trading signal from multiple indicators"""
        bullish_signals = sum(1 for s in signals if 'BULLISH' in s or s == 'OVERSOLD')
        bearish_signals = sum(1 for s in signals if 'BEARISH' in s or s == 'OVERBOUGHT')
        
        if bullish_signals >= bearish_signals + 2:
            return "STRONG_BUY"
        elif bullish_signals > bearish_signals:
            return "BUY"
        elif bearish_signals >= bullish_signals + 2:
            return "STRONG_SELL"
        elif bearish_signals > bullish_signals:
            return "SELL"
        else:
            return "HOLD"
    
    async def get_market_hours(self):
        """Get configured market hours"""
        return {
            "market_hours": self.market_hours,
            "current_time": datetime.now().strftime("%H:%M"),
            "timezone": self.market_hours["timezone"],
            "market_status": await self._check_market_status()
        }
    
    async def get_market_status(self):
        """Get current market status"""
        status = await self._check_market_status()
        return {
            "status": status,
            "current_time": datetime.now().strftime("%H:%M"),
            "market_hours": self.market_hours,
            "next_open": self._get_next_market_open(),
            "next_close": self._get_next_market_close()
        }
    
    async def _check_market_status(self) -> str:
        """Check if market is currently open"""
        try:
            now = datetime.now().time()
            open_time = datetime.strptime(self.market_hours["open"], "%H:%M").time()
            close_time = datetime.strptime(self.market_hours["close"], "%H:%M").time()
            
            if open_time <= now <= close_time:
                return "OPEN"
            elif now < open_time:
                return "PRE_MARKET"
            else:
                return "CLOSED"
        except Exception:
            return "UNKNOWN"
    
    def _get_next_market_open(self) -> str:
        """Get next market open time"""
        return self.market_hours["open"]
    
    def _get_next_market_close(self) -> str:
        """Get next market close time"""
        return self.market_hours["close"]
    
    async def get_indices_data(self):
        """Get market indices data"""
        if not self.market_indices:
            return {"error": "No market indices configured"}
        
        indices_data = {}
        for index_name, symbol in self.market_indices.items():
            try:
                index_data = await self.get_market_data(symbol)
                indices_data[index_name] = {
                    "symbol": symbol,
                    "level": index_data.get("current_price", 0),
                    "change": index_data.get("change", 0),
                    "change_percent": index_data.get("change_percent", 0),
                    "timestamp": index_data.get("timestamp")
                }
            except Exception as e:
                self.logger.error(f"Failed to fetch {index_name} data: {e}")
                indices_data[index_name] = {"error": str(e)}
        
        return {
            "indices": indices_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self):
        """Enhanced health check with market data service metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        market_health = {
            **base_health,
            "cache_size": len(self.data_cache),
            "cache_ttl_seconds": self.cache_ttl,
            "primary_source": self.primary_source,
            "backup_source": self.backup_source,
            "alpha_vantage_enabled": self.alpha_vantage_enabled,
            "supported_symbols": len(self.asx_symbols),
            "extended_symbols": len(self.extended_symbols),
            "market_indices": len(self.market_indices),
            "api_call_count": getattr(self, 'api_call_count', 0),
            "api_errors": getattr(self, 'api_errors', 0),
            "market_status": await self._check_market_status(),
            "settings_integration": SETTINGS_AVAILABLE,
            "market_hours": self.market_hours
        }
        
        # Test data source connectivity
        try:
            test_data = await self.get_market_data("CBA.AX")
            market_health["data_source_connectivity"] = "ok" if "error" not in test_data else "failed"
        except Exception as e:
            market_health["data_source_connectivity"] = f"error: {str(e)}"
        
        return market_health

    async def clear_cache(self):
        """Clear all cached market data"""
        cache_size = len(self.data_cache)
        self.data_cache.clear()
        
        self.logger.info(f"Cleared market data cache - {cache_size} entries removed")
        return {
            "status": "cache_cleared",
            "entries_removed": cache_size,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_supported_symbols(self):
        """Get list of supported symbols"""
        return {
            "asx_symbols": self.asx_symbols,
            "extended_symbols": self.extended_symbols,
            "market_indices": list(self.market_indices.keys()),
            "total_symbols": len(self.asx_symbols) + len(self.extended_symbols),
            "settings_source": SETTINGS_AVAILABLE
        }
    
    async def validate_symbol(self, symbol: str):
        """Validate if symbol is supported"""
        all_symbols = self.asx_symbols + self.extended_symbols + list(self.market_indices.values())
        
        is_valid = symbol in all_symbols
        category = None
        
        if symbol in self.asx_symbols:
            category = "asx_primary"
        elif symbol in self.extended_symbols:
            category = "asx_extended"
        elif symbol in self.market_indices.values():
            category = "market_index"
        
        return {
            "symbol": symbol,
            "valid": is_valid,
            "category": category,
            "supported_symbols_count": len(all_symbols)
        }

async def main(default_region: str = "asx"):
    """Main function to start the multi-region market data service"""
    service = MarketDataService(default_region=default_region)
    
    # Setup event subscriptions for market data updates
    event_handler = service.subscribe_to_events(["market_status_change"], handle_market_event)
    if event_handler:
        asyncio.create_task(event_handler())
    
    service.logger.info(f"Starting Market Data Service with region: {default_region}")
    await service.start_server()

async def handle_market_event(event_type: str, event_data: dict):
    """Handle market-related events"""
    if event_type == "market_status_change":
        # Could trigger cache refresh or other market-related actions
        pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Market Data Service")
    parser.add_argument("--region", default="asx", choices=["asx", "usa"], 
                      help="Default region for market data service")
    args = parser.parse_args()
    
    asyncio.run(main(args.region))
