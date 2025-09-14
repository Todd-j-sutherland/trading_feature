#!/usr/bin/env python3
"""
Enhanced Market Data Service with Configuration Integration
Provides comprehensive market data with technical indicators and bank-specific analysis
"""
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

class EnhancedMarketDataService(BaseService):
    """Enhanced market data service with comprehensive configuration integration"""

    def __init__(self):
        super().__init__("enhanced-market-data")
        
        # Configuration loaded from enhanced config service
        self.config_loaded = False
        self.bank_symbols = []
        self.bank_profiles = {}
        self.technical_indicators = {}
        self.market_hours = {}
        self.risk_parameters = {}
        
        # Data cache
        self.price_cache = {}
        self.technical_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize with fallback configuration
        self._initialize_fallback_config()
        
        # Register methods
        self.register_handler("get_market_data", self.get_market_data)
        self.register_handler("get_bank_data", self.get_bank_data)
        self.register_handler("get_technical_indicators", self.get_technical_indicators)
        self.register_handler("get_market_context", self.get_market_context)
        self.register_handler("get_volume_analysis", self.get_volume_analysis)
        self.register_handler("get_price_data", self.get_price_data)
        self.register_handler("calculate_volatility", self.calculate_volatility)
        self.register_handler("get_market_status", self.get_market_status)

    async def _load_enhanced_config(self):
        """Load configuration from enhanced configuration service"""
        if self.config_loaded:
            return
            
        try:
            # Load bank symbols and profiles
            bank_profiles = await self.call_service("enhanced-config", "get_bank_profiles")
            if bank_profiles:
                self.bank_profiles = bank_profiles
                self.bank_symbols = list(bank_profiles.keys())
                
            # Load technical indicators configuration
            technical_config = await self.call_service("enhanced-config", "get_technical_indicators")
            if technical_config:
                self.technical_indicators = technical_config
                
            # Load risk parameters
            risk_config = await self.call_service("enhanced-config", "get_risk_parameters")
            if risk_config:
                self.risk_parameters = risk_config
                
            # Load general configuration for market hours
            general_config = await self.call_service("enhanced-config", "get_config")
            if general_config and 'MARKET_HOURS' in general_config:
                self.market_hours = general_config['MARKET_HOURS']
                
            self.config_loaded = True
            self.logger.info("Loaded enhanced configuration from config service")
            
        except Exception as e:
            self.logger.warning(f"Could not load from enhanced config service: {e}")
            # Keep using fallback configuration

    def _initialize_fallback_config(self):
        """Initialize fallback configuration"""
        self.bank_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
        
        self.bank_profiles = {
            "CBA.AX": {"name": "Commonwealth Bank", "sector": "Banking"},
            "ANZ.AX": {"name": "ANZ Banking Group", "sector": "Banking"},
            "NAB.AX": {"name": "National Australia Bank", "sector": "Banking"},
            "WBC.AX": {"name": "Westpac Banking Corporation", "sector": "Banking"},
            "MQG.AX": {"name": "Macquarie Group", "sector": "Financial Services"}
        }
        
        self.technical_indicators = {
            "RSI": {"period": 14, "overbought": 70, "oversold": 30},
            "MACD": {"fast": 12, "slow": 26, "signal": 9},
            "BB": {"period": 20, "std": 2}
        }
        
        self.market_hours = {
            "market_open": "10:00",
            "market_close": "16:00",
            "timezone": "Australia/Sydney"
        }
        
        self.risk_parameters = {
            "volatility_threshold": 0.03,
            "volume_threshold": 1.5,
            "price_change_threshold": 0.05
        }

    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data for a symbol"""
        # Load enhanced configuration if not already loaded
        if not self.config_loaded:
            await self._load_enhanced_config()
            
        try:
            # Get current price and basic data
            price_data = await self.get_price_data(symbol)
            
            # Get technical indicators
            technical_data = await self.get_technical_indicators(symbol)
            
            # Get volume analysis
            volume_data = await self.get_volume_analysis(symbol)
            
            # Get market context
            market_context = await self.get_market_context()
            
            # Calculate volatility
            volatility_data = await self.calculate_volatility(symbol)
            
            # Get bank-specific profile if available
            bank_profile = self.bank_profiles.get(symbol, {})
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "price": price_data,
                "technical": technical_data,
                "volume": volume_data,
                "market_context": market_context,
                "volatility": volatility_data,
                "bank_profile": bank_profile,
                "risk_assessment": self._assess_risk(symbol, price_data, technical_data, volatility_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    async def get_bank_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get market data for all bank symbols"""
        if not symbols:
            symbols = self.bank_symbols
            
        bank_data = {}
        for symbol in symbols:
            try:
                bank_data[symbol] = await self.get_market_data(symbol)
            except Exception as e:
                bank_data[symbol] = {"error": str(e)}
                
        return {
            "banks": bank_data,
            "summary": self._create_bank_summary(bank_data),
            "timestamp": datetime.now().isoformat()
        }

    async def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """Get current and historical price data"""
        try:
            # Check cache first
            cache_key = f"price_{symbol}"
            if cache_key in self.price_cache:
                cached_data, timestamp = self.price_cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)
            
            # Get current price
            current_data = ticker.info
            current_price = current_data.get('regularMarketPrice', 0) or current_data.get('currentPrice', 0)
            
            # Get historical data for analysis
            hist_data = ticker.history(period="30d")
            
            if hist_data.empty:
                raise Exception(f"No historical data available for {symbol}")
            
            # Calculate price metrics
            latest_close = hist_data['Close'].iloc[-1]
            prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else latest_close
            
            price_data = {
                "current_price": float(current_price or latest_close),
                "previous_close": float(prev_close),
                "price_change": float(latest_close - prev_close),
                "price_change_percent": float((latest_close - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "day_high": float(hist_data['High'].iloc[-1]),
                "day_low": float(hist_data['Low'].iloc[-1]),
                "volume": int(hist_data['Volume'].iloc[-1]),
                "avg_volume_30d": int(hist_data['Volume'].mean()),
                "52_week_high": float(hist_data['High'].max()),
                "52_week_low": float(hist_data['Low'].min())
            }
            
            # Cache the result
            self.price_cache[cache_key] = (price_data, datetime.now())
            
            return price_data
            
        except Exception as e:
            self.logger.error(f"Error getting price data for {symbol}: {e}")
            return {"error": str(e)}

    async def get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Calculate technical indicators for a symbol"""
        try:
            # Check cache first
            cache_key = f"technical_{symbol}"
            if cache_key in self.technical_cache:
                cached_data, timestamp = self.technical_cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            # Get historical data
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period="3mo")  # 3 months for better technical analysis
            
            if hist_data.empty or len(hist_data) < 30:
                raise Exception(f"Insufficient data for technical analysis of {symbol}")
            
            # Calculate RSI
            rsi_period = self.technical_indicators.get("RSI", {}).get("period", 14)
            rsi = self._calculate_rsi(hist_data['Close'], rsi_period)
            
            # Calculate MACD
            macd_params = self.technical_indicators.get("MACD", {"fast": 12, "slow": 26, "signal": 9})
            macd_line, macd_signal, macd_histogram = self._calculate_macd(
                hist_data['Close'], 
                macd_params["fast"], 
                macd_params["slow"], 
                macd_params["signal"]
            )
            
            # Calculate Bollinger Bands
            bb_params = self.technical_indicators.get("BB", {"period": 20, "std": 2})
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                hist_data['Close'], 
                bb_params["period"], 
                bb_params["std"]
            )
            
            # Calculate moving averages
            sma_20 = hist_data['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = hist_data['Close'].rolling(window=50).mean().iloc[-1]
            ema_20 = hist_data['Close'].ewm(span=20).mean().iloc[-1]
            
            current_price = hist_data['Close'].iloc[-1]
            
            technical_data = {
                "rsi": float(rsi),
                "rsi_signal": self._interpret_rsi(rsi),
                "macd": {
                    "line": float(macd_line),
                    "signal": float(macd_signal),
                    "histogram": float(macd_histogram),
                    "signal_interpretation": self._interpret_macd(macd_line, macd_signal, macd_histogram)
                },
                "bollinger_bands": {
                    "upper": float(bb_upper),
                    "middle": float(bb_middle),
                    "lower": float(bb_lower),
                    "position": self._interpret_bb_position(current_price, bb_upper, bb_middle, bb_lower)
                },
                "moving_averages": {
                    "sma_20": float(sma_20),
                    "sma_50": float(sma_50),
                    "ema_20": float(ema_20),
                    "trend": self._interpret_ma_trend(current_price, sma_20, sma_50)
                },
                "overall_signal": self._calculate_overall_technical_signal(rsi, macd_line, macd_signal, current_price, sma_20)
            }
            
            # Cache the result
            self.technical_cache[cache_key] = (technical_data, datetime.now())
            
            return technical_data
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return {"error": str(e)}

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        macd_histogram = macd_line - macd_signal
        
        return macd_line.iloc[-1], macd_signal.iloc[-1], macd_histogram.iloc[-1]

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: int = 2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band.iloc[-1], sma.iloc[-1], lower_band.iloc[-1]

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        overbought = self.technical_indicators.get("RSI", {}).get("overbought", 70)
        oversold = self.technical_indicators.get("RSI", {}).get("oversold", 30)
        
        if rsi >= overbought:
            return "OVERBOUGHT"
        elif rsi <= oversold:
            return "OVERSOLD"
        elif rsi > 50:
            return "BULLISH"
        else:
            return "BEARISH"

    def _interpret_macd(self, macd_line: float, macd_signal: float, histogram: float) -> str:
        """Interpret MACD signals"""
        if macd_line > macd_signal and histogram > 0:
            return "BULLISH"
        elif macd_line < macd_signal and histogram < 0:
            return "BEARISH"
        elif macd_line > macd_signal:
            return "POTENTIAL_BULLISH"
        else:
            return "POTENTIAL_BEARISH"

    def _interpret_bb_position(self, price: float, upper: float, middle: float, lower: float) -> str:
        """Interpret Bollinger Bands position"""
        if price >= upper:
            return "OVERBOUGHT"
        elif price <= lower:
            return "OVERSOLD"
        elif price > middle:
            return "UPPER_HALF"
        else:
            return "LOWER_HALF"

    def _interpret_ma_trend(self, current_price: float, sma_20: float, sma_50: float) -> str:
        """Interpret moving average trend"""
        if current_price > sma_20 > sma_50:
            return "STRONG_UPTREND"
        elif current_price > sma_20 and sma_20 < sma_50:
            return "WEAK_UPTREND"
        elif current_price < sma_20 < sma_50:
            return "STRONG_DOWNTREND"
        else:
            return "WEAK_DOWNTREND"

    def _calculate_overall_technical_signal(self, rsi: float, macd_line: float, macd_signal: float, 
                                          price: float, sma_20: float) -> str:
        """Calculate overall technical signal"""
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI signals
        if 30 < rsi < 70:
            if rsi > 50:
                bullish_signals += 1
            else:
                bearish_signals += 1
        elif rsi <= 30:
            bullish_signals += 2  # Oversold is bullish
        elif rsi >= 70:
            bearish_signals += 2  # Overbought is bearish
        
        # MACD signals
        if macd_line > macd_signal:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Price vs MA signals
        if price > sma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            return "BULLISH"
        elif bearish_signals > bullish_signals:
            return "BEARISH"
        else:
            return "NEUTRAL"

    async def get_volume_analysis(self, symbol: str) -> Dict[str, Any]:
        """Analyze volume patterns"""
        try:
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period="30d")
            
            if hist_data.empty:
                raise Exception(f"No data available for volume analysis of {symbol}")
            
            current_volume = hist_data['Volume'].iloc[-1]
            avg_volume = hist_data['Volume'].mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Volume trend analysis
            recent_volumes = hist_data['Volume'].tail(5)
            volume_trend = "INCREASING" if recent_volumes.is_monotonic_increasing else "DECREASING"
            
            volume_threshold = self.risk_parameters.get("volume_threshold", 1.5)
            
            return {
                "current_volume": int(current_volume),
                "average_volume": int(avg_volume),
                "volume_ratio": float(volume_ratio),
                "volume_trend": volume_trend,
                "unusual_volume": volume_ratio > volume_threshold,
                "volume_quality_score": min(volume_ratio / volume_threshold, 2.0) if volume_threshold > 0 else 1.0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing volume for {symbol}: {e}")
            return {"error": str(e)}

    async def get_market_context(self) -> Dict[str, Any]:
        """Get overall market context"""
        try:
            # Load enhanced configuration if not already loaded
            if not self.config_loaded:
                await self._load_enhanced_config()
            
            # Get ASX 200 index data as market context
            asx_ticker = yf.Ticker("^AXJO")
            asx_data = asx_ticker.history(period="5d")
            
            if not asx_data.empty:
                asx_current = asx_data['Close'].iloc[-1]
                asx_prev = asx_data['Close'].iloc[-2] if len(asx_data) > 1 else asx_current
                asx_change = (asx_current - asx_prev) / asx_prev * 100 if asx_prev > 0 else 0
                
                market_sentiment = "BULLISH" if asx_change > 1 else "BEARISH" if asx_change < -1 else "NEUTRAL"
            else:
                asx_change = 0
                market_sentiment = "NEUTRAL"
            
            # Determine market hours
            current_time = datetime.now()
            market_open = self.market_hours.get("market_open", "10:00")
            market_close = self.market_hours.get("market_close", "16:00")
            
            # Simple market hours check (would need timezone handling for production)
            current_hour = current_time.hour
            is_market_open = 10 <= current_hour < 16 and current_time.weekday() < 5
            
            return {
                "asx_200_change_percent": float(asx_change),
                "market_sentiment": market_sentiment,
                "is_market_open": is_market_open,
                "market_hours": {
                    "open": market_open,
                    "close": market_close
                },
                "trading_context": self._determine_trading_context(asx_change, is_market_open),
                "buy_threshold": 0.70 if market_sentiment == "BULLISH" else 0.75
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market context: {e}")
            return {
                "error": str(e),
                "market_sentiment": "NEUTRAL",
                "is_market_open": False,
                "buy_threshold": 0.75
            }

    def _determine_trading_context(self, asx_change: float, is_market_open: bool) -> str:
        """Determine overall trading context"""
        if not is_market_open:
            return "AFTER_HOURS"
        elif asx_change > 2:
            return "STRONG_BULL_MARKET"
        elif asx_change > 0.5:
            return "BULL_MARKET"
        elif asx_change < -2:
            return "STRONG_BEAR_MARKET"
        elif asx_change < -0.5:
            return "BEAR_MARKET"
        else:
            return "NEUTRAL_MARKET"

    async def calculate_volatility(self, symbol: str, period: int = 30) -> Dict[str, Any]:
        """Calculate volatility metrics"""
        try:
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period=f"{period}d")
            
            if hist_data.empty or len(hist_data) < 10:
                raise Exception(f"Insufficient data for volatility calculation of {symbol}")
            
            # Calculate daily returns
            returns = hist_data['Close'].pct_change().dropna()
            
            # Calculate volatility metrics
            volatility = returns.std()
            annualized_volatility = volatility * np.sqrt(252)  # 252 trading days per year
            
            # Calculate recent volatility (last 5 days)
            recent_volatility = returns.tail(5).std() if len(returns) >= 5 else volatility
            
            # Volatility trend
            first_half_vol = returns.head(len(returns)//2).std()
            second_half_vol = returns.tail(len(returns)//2).std()
            volatility_trend = "INCREASING" if second_half_vol > first_half_vol else "DECREASING"
            
            volatility_threshold = self.risk_parameters.get("volatility_threshold", 0.03)
            
            return {
                "daily_volatility": float(volatility),
                "annualized_volatility": float(annualized_volatility),
                "recent_volatility": float(recent_volatility),
                "volatility_trend": volatility_trend,
                "high_volatility": volatility > volatility_threshold,
                "volatility_score": min(volatility / volatility_threshold, 2.0) if volatility_threshold > 0 else 1.0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility for {symbol}: {e}")
            return {"error": str(e)}

    def _assess_risk(self, symbol: str, price_data: Dict, technical_data: Dict, volatility_data: Dict) -> Dict[str, Any]:
        """Assess overall risk for the symbol"""
        risk_score = 0.5  # Base risk score
        risk_factors = []
        
        # Price risk factors
        if "price_change_percent" in price_data:
            price_change = abs(price_data["price_change_percent"])
            price_threshold = self.risk_parameters.get("price_change_threshold", 0.05) * 100
            
            if price_change > price_threshold:
                risk_score += 0.2
                risk_factors.append(f"High price volatility: {price_change:.1f}%")
        
        # Technical risk factors
        if "rsi" in technical_data:
            rsi = technical_data["rsi"]
            if rsi > 80 or rsi < 20:
                risk_score += 0.15
                risk_factors.append(f"Extreme RSI: {rsi:.1f}")
        
        # Volatility risk factors
        if "high_volatility" in volatility_data and volatility_data["high_volatility"]:
            risk_score += 0.2
            risk_factors.append("High historical volatility")
        
        # Volume risk factors
        # This would be added when volume_data is available
        
        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score < 0.3:
            risk_level = "LOW"
        elif risk_score < 0.6:
            risk_level = "MEDIUM"
        elif risk_score < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"
        
        return {
            "risk_score": float(risk_score),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level)
        }

    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get risk-based recommendation"""
        recommendations = {
            "LOW": "Suitable for most investors",
            "MEDIUM": "Suitable for moderate risk tolerance",
            "HIGH": "Suitable only for high risk tolerance",
            "VERY_HIGH": "Extreme caution advised"
        }
        return recommendations.get(risk_level, "Unknown risk level")

    def _create_bank_summary(self, bank_data: Dict) -> Dict[str, Any]:
        """Create summary of bank sector performance"""
        valid_banks = {k: v for k, v in bank_data.items() if "error" not in v}
        
        if not valid_banks:
            return {"error": "No valid bank data available"}
        
        # Extract price changes
        price_changes = []
        for bank_info in valid_banks.values():
            if "price" in bank_info and "price_change_percent" in bank_info["price"]:
                price_changes.append(bank_info["price"]["price_change_percent"])
        
        if price_changes:
            avg_change = sum(price_changes) / len(price_changes)
            positive_banks = len([p for p in price_changes if p > 0])
        else:
            avg_change = 0
            positive_banks = 0
        
        return {
            "total_banks": len(valid_banks),
            "average_change_percent": float(avg_change),
            "banks_up": positive_banks,
            "banks_down": len(valid_banks) - positive_banks,
            "sector_sentiment": "BULLISH" if avg_change > 1 else "BEARISH" if avg_change < -1 else "NEUTRAL"
        }

    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        return {
            "market_hours": self.market_hours,
            "supported_symbols": self.bank_symbols,
            "cache_ttl_seconds": self.cache_ttl,
            "config_loaded": self.config_loaded,
            "total_symbols_tracked": len(self.bank_symbols)
        }

    async def health_check(self):
        """Enhanced health check with market data specific metrics"""
        base_health = await super().health_check()
        
        market_health = {
            **base_health,
            "config_loaded": self.config_loaded,
            "bank_symbols_count": len(self.bank_symbols),
            "price_cache_size": len(self.price_cache),
            "technical_cache_size": len(self.technical_cache),
            "market_hours_configured": bool(self.market_hours),
            "technical_indicators_configured": bool(self.technical_indicators)
        }
        
        return market_health

async def main():
    service = EnhancedMarketDataService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
