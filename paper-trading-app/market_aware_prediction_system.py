#!/usr/bin/env python3
"""
Market-Aware Prediction System - Core Logic
Implements the market context analysis and prediction improvements from investigation
"""

import yfinance as yf
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings
import numpy as np

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class MarketContextAnalyzer:
    """Analyzes broader market conditions for context-aware predictions"""
    
    def __init__(self):
        self.cache = None
        self.cache_time = None
        self.cache_duration = timedelta(minutes=30)
    
    def get_market_context(self) -> Dict[str, Any]:
        """Get market context with caching"""
        now = datetime.now()
        
        # Use cache if recent
        if (self.cache and self.cache_time and 
            now - self.cache_time < self.cache_duration):
            return self.cache
        
        # Refresh market context
        context = self._analyze_market_context()
        self.cache = context
        self.cache_time = now
        
        return context
    
    def _analyze_market_context(self) -> Dict[str, Any]:
        """Analyze ASX market conditions"""
        try:
            logger.info("🌐 Analyzing market context...")
            
            # Get ASX 200 data (5-day trend)
            asx200 = yf.Ticker("^AXJO")
            data = asx200.history(period="5d")
            
            if len(data) < 2:
                logger.warning("⚠️ Insufficient market data, defaulting to NEUTRAL")
                return self._default_context()
            
            # Calculate 5-day market trend
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            current_level = data['Close'].iloc[-1]
            
            # Determine market context
            if market_trend < -2:  # Market down >2%
                context = "BEARISH"
                confidence_multiplier = 0.7  # Reduce confidence by 30%
                buy_threshold = 0.80  # Higher threshold
            elif market_trend > 2:  # Market up >2%
                context = "BULLISH"
                confidence_multiplier = 1.1  # Boost confidence by 10%
                buy_threshold = 0.65  # Lower threshold
            else:  # Market flat
                context = "NEUTRAL"
                confidence_multiplier = 1.0  # No change
                buy_threshold = 0.70  # Standard threshold
            
            logger.info(f"📊 Market Context: {context} ({market_trend:+.2f}%)")
            
            return {
                "context": context,
                "trend_pct": market_trend,
                "confidence_multiplier": confidence_multiplier,
                "buy_threshold": buy_threshold,
                "current_level": current_level,
                "raw_data": data
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market context: {e}")
            return self._default_context()
    
    def _default_context(self) -> Dict[str, Any]:
        """Default market context when analysis fails"""
        return {
            "context": "NEUTRAL",
            "trend_pct": 0.0,
            "confidence_multiplier": 1.0,
            "buy_threshold": 0.70,
            "current_level": 0,
            "raw_data": None
        }
    
    def apply_market_stress_filter(self, confidence: float, market_data: Dict) -> float:
        """Apply emergency market stress filtering"""
        if market_data.get("raw_data") is None:
            return confidence
            
        try:
            data = market_data["raw_data"]
            if len(data) >= 5:
                # Calculate volatility
                returns = data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # Annualized
                
                # Apply stress filter for high volatility
                if volatility > 0.4:  # >40% annualized volatility
                    logger.warning(f"⚠️ High market volatility detected: {volatility:.1%}")
                    confidence *= 0.8  # Reduce confidence by 20%
                
                # Emergency override for extreme conditions
                if market_data["trend_pct"] < -5 and volatility > 0.5:
                    logger.warning("🚨 EMERGENCY: Extreme market stress detected")
                    confidence *= 0.5  # Severe reduction
        
        except Exception as e:
            logger.error(f"Error in stress filter: {e}")
        
        return confidence

class TechnicalAnalyzer:
    """Technical analysis for individual stocks"""
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Analyze technical indicators for a stock"""
        try:
            # Get stock data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="30d")
            
            if len(data) < 20:
                return {"error": "Insufficient data"}
            
            current_price = data['Close'].iloc[-1]
            
            # Calculate technical indicators
            tech_analysis = {
                "current_price": current_price,
                "sma_5": data['Close'].rolling(5).mean().iloc[-1],
                "sma_20": data['Close'].rolling(20).mean().iloc[-1],
                "volume_avg": data['Volume'].rolling(10).mean().iloc[-1],
                "volume_current": data['Volume'].iloc[-1],
                "volatility": data['Close'].pct_change().std(),
                "rsi": self._calculate_rsi(data['Close']),
                "price_change_5d": ((current_price / data['Close'].iloc[-6]) - 1) * 100 if len(data) >= 6 else 0
            }
            
            # Calculate technical score
            tech_score = self._calculate_technical_score(tech_analysis)
            tech_analysis["tech_score"] = tech_score
            
            return tech_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {"error": str(e)}
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def _calculate_technical_score(self, analysis: Dict) -> float:
        """Calculate overall technical score (0-100)"""
        score = 50  # Base score
        
        try:
            current = analysis["current_price"]
            sma_5 = analysis["sma_5"]
            sma_20 = analysis["sma_20"]
            rsi = analysis["rsi"]
            volume_ratio = analysis["volume_current"] / analysis["volume_avg"]
            
            # Price vs moving averages
            if current > sma_5 > sma_20:
                score += 20  # Strong uptrend
            elif current > sma_5:
                score += 10  # Moderate uptrend
            elif current < sma_5 < sma_20:
                score -= 20  # Strong downtrend
            elif current < sma_5:
                score -= 10  # Moderate downtrend
            
            # RSI analysis
            if 30 < rsi < 70:
                score += 10  # Healthy range
            elif rsi < 30:
                score += 5   # Oversold (potential bounce)
            elif rsi > 80:
                score -= 10  # Overbought
            
            # Volume confirmation
            if volume_ratio > 1.5:
                score += 10  # High volume
            elif volume_ratio > 1.2:
                score += 5   # Good volume
            elif volume_ratio < 0.8:
                score -= 5   # Low volume
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 50

class NewsAnalyzer:
    """News sentiment analysis (simplified)"""
    
    def analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze news sentiment for a symbol"""
        # For now, return simulated sentiment
        # In production, this would connect to news APIs
        
        import random
        random.seed(hash(symbol) + int(datetime.now().timestamp() // 3600))  # Hourly seed
        
        sentiment_score = random.uniform(-0.3, 0.3)  # -30% to +30%
        news_confidence = random.uniform(0.4, 0.8)   # 40% to 80%
        
        return {
            "sentiment_score": sentiment_score,
            "news_confidence": news_confidence,
            "article_count": random.randint(2, 8),
            "source": "simulated"  # Would be real news sources
        }

class MarketAwarePredictionSystem:
    """Main prediction system with market context awareness"""
    
    def __init__(self):
        self.market_analyzer = MarketContextAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.news_analyzer = NewsAnalyzer()
    
    def get_market_context(self) -> Dict[str, Any]:
        """Get current market context"""
        return self.market_analyzer.get_market_context()
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze a symbol with market context awareness"""
        try:
            # Get market context
            market_data = self.get_market_context()
            
            # Get technical analysis
            tech_data = self.technical_analyzer.analyze_stock(symbol)
            if "error" in tech_data:
                logger.error(f"Technical analysis failed for {symbol}: {tech_data['error']}")
                return None
            
            # Get news sentiment
            news_data = self.news_analyzer.analyze_sentiment(symbol)
            
            # Calculate market-aware confidence
            confidence, action, details = self._calculate_market_aware_confidence(
                tech_data, news_data, market_data
            )
            
            return {
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "current_price": tech_data["current_price"],
                "market_context": market_data["context"],
                "tech_score": tech_data["tech_score"],
                "news_sentiment": news_data["sentiment_score"],
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_market_aware_confidence(self, tech_data: Dict, news_data: Dict, market_data: Dict):
        """Calculate confidence with market context awareness"""
        
        # 1. REDUCED BASE CONFIDENCE (CRITICAL FIX)
        base_confidence = 0.10  # REDUCED from 0.20
        
        # 2. TECHNICAL COMPONENT (40% weight)
        tech_score = tech_data["tech_score"]
        if tech_score > 70:
            tech_component = 0.30
        elif tech_score > 60:
            tech_component = 0.20
        elif tech_score > 50:
            tech_component = 0.10
        else:
            tech_component = 0.05
        
        # 3. NEWS COMPONENT (30% weight) - Enhanced for market context
        news_sentiment = news_data["sentiment_score"]
        news_confidence = news_data["news_confidence"]
        
        news_base = news_confidence * 0.15  # Reduced from 0.20
        
        # Market-aware sentiment adjustment
        if market_data["context"] == "BEARISH":
            # Require stronger positive sentiment during bearish markets
            if news_sentiment > 0.15:  # Raised threshold
                sentiment_factor = min(news_sentiment * 30, 0.15)
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 60, -0.15)
            else:
                sentiment_factor = 0.0
        else:
            # Normal sentiment processing
            if news_sentiment > 0.05:
                sentiment_factor = min(news_sentiment * 50, 0.10)
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 50, -0.10)
            else:
                sentiment_factor = 0.0
        
        news_component = news_base + sentiment_factor
        news_component = max(0.0, min(news_component, 0.30))
        
        # 4. VOLUME COMPONENT (20% weight)
        volume_ratio = tech_data["volume_current"] / tech_data["volume_avg"]
        if volume_ratio > 1.5:
            volume_component = 0.15
        elif volume_ratio > 1.2:
            volume_component = 0.10
        elif volume_ratio > 1.0:
            volume_component = 0.05
        else:
            volume_component = 0.02
        
        # 5. RISK COMPONENT (10% weight)
        volatility = tech_data["volatility"]
        if volatility < 0.015:
            risk_component = 0.08
        elif volatility < 0.025:
            risk_component = 0.05
        elif volatility < 0.04:
            risk_component = 0.02
        else:
            risk_component = -0.02
        
        # PRELIMINARY CONFIDENCE
        preliminary = base_confidence + tech_component + news_component + volume_component + risk_component
        
        # 6. MARKET CONTEXT ADJUSTMENT
        market_adjusted = preliminary * market_data["confidence_multiplier"]
        
        # 7. MARKET STRESS FILTER
        final_confidence = self.market_analyzer.apply_market_stress_filter(market_adjusted, market_data)
        
        # Bounds check
        final_confidence = max(0.15, min(0.95, final_confidence))
        
        # 8. ACTION DETERMINATION WITH MARKET CONTEXT
        action = "HOLD"
        buy_threshold = market_data["buy_threshold"]
        
        if final_confidence > buy_threshold and tech_score > 60:
            if market_data["context"] == "BEARISH":
                # STRICTER requirements during bearish markets
                if news_sentiment > 0.10 and tech_score > 70:
                    action = "BUY"
            else:
                # Normal requirements
                if news_sentiment > -0.05:
                    action = "BUY"
        
        # Strong BUY signals
        if final_confidence > (buy_threshold + 0.10) and tech_score > 70:
            if market_data["context"] != "BEARISH" and news_sentiment > 0.02:
                action = "STRONG_BUY"
        
        # Safety override
        if news_sentiment < -0.15 or final_confidence < 0.30:
            action = "HOLD"
        
        details = {
            "base_confidence": base_confidence,
            "tech_component": tech_component,
            "news_component": news_component,
            "volume_component": volume_component,
            "risk_component": risk_component,
            "preliminary": preliminary,
            "market_adjusted": market_adjusted,
            "final_confidence": final_confidence,
            "buy_threshold": buy_threshold,
            "market_context": market_data["context"]
        }
        
        return final_confidence, action, details
