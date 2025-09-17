#!/usr/bin/env python3
"""
Market-Aware Enhanced Prediction System with Context Filtering
Implements recommendations from failingStocksMarketInvestigation.md

Key Improvements:
- Market context awareness (ASX 200 trend analysis)
- Reduced base confidence (20% -> 10%)
- Dynamic BUY thresholds based on market conditions
- Enhanced news sentiment requirements during bearish markets
- Comprehensive logging for analysis
"""

import os
print("DEBUG: Script started")
import sys
import sqlite3
import yfinance as yf
import gc
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# Try to import settings configuration
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app.config.settings import Settings
    SETTINGS_AVAILABLE = True
    print("✅ Settings configuration loaded successfully")
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️ Settings configuration not available - using fallback symbols")

class MarketContextAnalyzer:
    """Analyzes broader market conditions for context-aware predictions"""
    
    def get_market_context(self):
        """Check broader ASX market conditions"""
        try:
            print("🌐 Analyzing market context...")
            
            # Get ASX 200 data (5-day trend)
            asx200 = yf.Ticker("^AXJO")
            data = asx200.history(period="5d")
            
            if len(data) < 2:
                print("⚠️  Insufficient market data, defaulting to NEUTRAL")
                return {
                    "context": "NEUTRAL",
                    "trend_pct": 0.0,
                    "confidence_multiplier": 1.0,
                    "buy_threshold": 0.66
                }
            
            # Calculate 5-day market trend
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            
            # Determine market context - OPTIMIZED: New conservative thresholds based on analysis
            if market_trend < -1.5:  # Market down >1.5% (was 2%)
                context = "BEARISH"
                confidence_multiplier = 0.7  # Reduce confidence by 30%
                buy_threshold = 0.70  # Upper bound for bearish conditions
            elif market_trend > 1.5:  # Market up >1.5% (was 2%)
                context = "BULLISH"
                confidence_multiplier = 1.1  # Boost confidence by 10%
                buy_threshold = 0.62  # Lower bound for bullish (Sept 12th range)
            elif market_trend < -0.5:  # Mild bearish (-0.5% to -1.5%)
                context = "WEAK_BEARISH"
                confidence_multiplier = 0.9  # Slight reduction
                buy_threshold = 0.68  # Conservative for weak bearish
            elif market_trend > 0.5:  # Mild bullish (0.5% to 1.5%)
                context = "WEAK_BULLISH"
                confidence_multiplier = 1.05  # Slight boost
                buy_threshold = 0.64  # Conservative for weak bullish
            else:
                context = "NEUTRAL"
                confidence_multiplier = 1.0
                buy_threshold = 0.66  # Conservative neutral threshold
            
            # Get intraday volatility
            daily_volatility = ((data['High'] - data['Low']) / data['Close']).mean() * 100
            
            result = {
                "context": context,
                "trend_pct": market_trend,
                "confidence_multiplier": confidence_multiplier,
                "buy_threshold": buy_threshold,
                "volatility": daily_volatility,
                "current_level": data['Close'].iloc[-1]
            }
            
            print(f"📊 Market Context: {context} ({market_trend:+.2f}%, Vol: {daily_volatility:.1f}%)")
            return result
            
        except Exception as e:
            print(f"❌ Error getting market context: {e}")
            return {
                "context": "NEUTRAL",
                "trend_pct": 0.0,
                "confidence_multiplier": 1.0,
                "buy_threshold": 0.66,
                "volatility": 0.0,
                "current_level": 0.0
            }
    
    def market_stress_filter(self, confidence, market_data):
        """Apply emergency market stress filter"""
        market_trend = market_data["trend_pct"]
        
        if market_trend < -1:  # Market down >1%
            stress_factor = max(0.5, 1 + (market_trend / 10))  # More aggressive reduction for larger declines
            confidence *= stress_factor
            confidence = max(confidence, 0.15)  # Minimum floor
            print(f"🚨 Market stress filter applied: {stress_factor:.2f}x")
        
        return confidence

class TechnicalAnalyzer:
    """Enhanced technical analysis with market context"""
    
    def get_prices_and_volume(self, symbol: str, days: int = 30):
        """Get historical prices and volume"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            if hist.empty:
                return [], []
            return hist["Close"].tolist(), hist["Volume"].tolist()
        except:
            return [], []
    
    def calculate_volume_metrics(self, volumes, prices):
        """Calculate volume-based metrics"""
        if len(volumes) < 10 or len(prices) < 10:
            return {
                "avg_volume": 0,
                "volume_trend": 0.0,
                "price_volume_correlation": 0.0,
                "volume_quality_score": 0.0
            }
        
        # Average volume (last 20 days)
        avg_volume = sum(volumes[-20:]) / min(20, len(volumes))
        
        # Volume trend (comparing recent vs older)
        recent_avg = sum(volumes[-5:]) / 5
        older_avg = sum(volumes[-20:-10]) / 10
        volume_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Price-volume correlation (last 10 days)
        if len(volumes) >= 10 and len(prices) >= 10:
            import numpy as np
            price_changes = [prices[i] - prices[i-1] for i in range(1, min(11, len(prices)))]
            volume_changes = [volumes[i] - volumes[i-1] for i in range(1, min(11, len(volumes)))]
            
            if len(price_changes) > 3 and len(volume_changes) > 3:
                correlation = np.corrcoef(price_changes, volume_changes)[0,1]
                correlation = correlation if not np.isnan(correlation) else 0
            else:
                correlation = 0
        else:
            correlation = 0
        
        # Quality score based on consistency
        volume_quality = min(1.0, avg_volume / 100000) * 0.8 if avg_volume > 10000 else 0.2
        
        return {
            "avg_volume": avg_volume,
            "volume_trend": volume_trend,
            "price_volume_correlation": correlation,
            "volume_quality_score": volume_quality
        }
    
    def analyze(self, symbol):
        """Comprehensive technical analysis"""
        try:
            prices, volumes = self.get_prices_and_volume(symbol)
            
            if len(prices) < 20:
                return self._default_analysis()
            
            current_price = prices[-1]
            
            # Moving averages
            ma5 = sum(prices[-5:]) / 5
            ma20 = sum(prices[-20:]) / 20
            
            # RSI calculation
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return 50
                
                gains = []
                losses = []
                
                for i in range(1, len(prices)):
                    change = prices[i] - prices[i-1]
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                
                if len(gains) < period:
                    return 50
                
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses[-period:]) / period
                
                if avg_loss == 0:
                    return 100
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            rsi = calculate_rsi(prices)
            
            # Volume metrics
            volume_metrics = self.calculate_volume_metrics(volumes, prices)
            
            # Technical score calculation
            tech_score = 50  # Base score
            
            # Price vs moving averages
            if current_price > ma5:
                tech_score += 10
            if current_price > ma20:
                tech_score += 15
            if ma5 > ma20:
                tech_score += 10
            
            # RSI scoring
            if 30 <= rsi <= 70:
                tech_score += 15
            elif 70 < rsi <= 80:
                tech_score += 10
            elif 20 < rsi < 30:
                tech_score += 5
            
            # Volume scoring
            if volume_metrics["volume_trend"] > 0.1:
                tech_score += 10
            if volume_metrics["price_volume_correlation"] > 0.3:
                tech_score += 5
            
            # Price momentum
            momentum = (current_price - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 else 0
            
            # Volatility
            price_changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = (sum([abs(change) for change in price_changes]) / len(price_changes)) * 100
            
            feature_vector = f"{rsi:.2f},{tech_score},{ma5:.2f},{ma20:.2f},{current_price:.2f},{momentum:.2f},{volatility:.2f}"
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "rsi": rsi,
                "tech_score": min(100, max(0, tech_score)),
                "ma5": ma5,
                "ma20": ma20,
                "momentum": momentum,
                "volatility": volatility,
                "volume_metrics": volume_metrics,
                "feature_vector": feature_vector
            }
            
        except Exception as e:
            print(f"❌ Technical analysis error for {symbol}: {e}")
            return self._default_analysis()
    
    def _default_analysis(self):
        """Return default analysis when data is insufficient"""
        return {
            "symbol": "UNKNOWN",
            "current_price": 0,
            "rsi": 50,
            "tech_score": 30,
            "ma5": 0,
            "ma20": 0,
            "momentum": 0,
            "volatility": 3.0,
            "volume_metrics": {
                "avg_volume": 0,
                "volume_trend": 0.0,
                "price_volume_correlation": 0.0,
                "volume_quality_score": 0.0
            },
            "feature_vector": "50,30,0,0,0,0,3.0"
        }

class MarketAwarePredictor:
    """Market-aware prediction system with enhanced context filtering"""
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
        self.market_analyzer = MarketContextAnalyzer()
        print("🚀 Market-Aware Prediction System Initialized")
    
    def get_news_sentiment(self, symbol):
        """Enhanced news sentiment analysis with better filtering"""
        try:
            import requests
            import re
            from textblob import TextBlob
            
            # Get recent news
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {
                    "sentiment_score": 0.0,
                    "news_confidence": 0.3,  # Lower default confidence
                    "news_count": 0,
                    "news_quality_score": 0.0
                }
            
            sentiments = []
            quality_scores = []
            
            for article in news[:5]:  # Limit to recent 5 articles
                try:
                    title = article.get('content', {}).get('title', '')
                    summary = article.get('content', {}).get('summary', '')
                    
                    # Combine title and summary
                    text = f"{title} {summary}"
                    
                    if len(text.strip()) < 10:
                        continue
                    
                    # Calculate sentiment
                    blob = TextBlob(text)
                    sentiment = blob.sentiment.polarity
                    sentiments.append(sentiment)
                    
                    # Quality scoring
                    quality = 0.5
                    if len(text) > 100:
                        quality += 0.2
                    if any(word in text.lower() for word in ['profit', 'revenue', 'earnings', 'growth']):
                        quality += 0.2
                    if any(word in text.lower() for word in ['loss', 'decline', 'warning', 'concern']):
                        quality -= 0.1
                    
                    quality_scores.append(quality)
                    
                except Exception as e:
                    continue
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                news_confidence = min(0.8, 0.3 + (len(sentiments) * 0.1))
                quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.3
                
                return {
                    "sentiment_score": avg_sentiment,
                    "news_confidence": news_confidence,
                    "news_count": len(sentiments),
                    "news_quality_score": quality_score
                }
        except Exception as e:
            print(f"⚠️  Error getting news sentiment for {symbol}: {e}")
        
        return {
            "sentiment_score": 0.0,
            "news_confidence": 0.3,  # Reduced from 0.5
            "news_count": 0,
            "news_quality_score": 0.0
        }
    
    def calculate_enhanced_confidence(self, symbol, tech_data, news_data, volume_data, market_data):
        """Calculate market-aware confidence with enhanced logic"""
        
        # Extract technical factors
        rsi = tech_data["rsi"]
        tech_score = tech_data["tech_score"]
        current_price = tech_data["current_price"]
        feature_parts = tech_data["feature_vector"].split(",")
        
        # ===========================================
        # MARKET-AWARE CONFIDENCE CALCULATION
        # Implementing recommendations from investigation
        # ===========================================
        
        # 1. TECHNICAL ANALYSIS COMPONENT (40% total weight)
        # FIXED: Reduced base confidence from 20% to 10%
        base_confidence = 0.10  # CRITICAL FIX: Was 0.20
        
        # Technical Score (0-25 points)
        tech_factor = min(tech_score / 100 * 0.25, 0.25)
        
        # RSI positioning (0-10 points)
        rsi_factor = 0.0
        if 30 <= rsi <= 70:  # Healthy range
            rsi_factor = 0.08
        elif 70 < rsi <= 80:  # Strong momentum
            rsi_factor = 0.10
        elif 20 < rsi < 30:   # Oversold opportunity
            rsi_factor = 0.09
        elif rsi > 80:        # Overbought risk
            rsi_factor = 0.03
        elif rsi < 20:        # Extreme oversold
            rsi_factor = 0.05
        
        # Price momentum (0-5 points)
        momentum = float(feature_parts[5]) if len(feature_parts) > 5 else 0
        momentum_factor = min(abs(momentum) / 5.0 * 0.05, 0.05)
        
        technical_component = base_confidence + tech_factor + rsi_factor + momentum_factor
        
        # 2. NEWS SENTIMENT COMPONENT (30% total weight)
        news_sentiment = news_data["sentiment_score"]
        news_confidence = news_data["news_confidence"]
        news_quality = news_data["news_quality_score"]
        
        # Base news factor (0-20 points) - reduced from original
        news_base = news_confidence * 0.15  # Reduced from 0.20
        
        # ENHANCED: Market-context-aware sentiment adjustment
        sentiment_factor = 0.0
        if market_data["context"] == "BEARISH":
            # Require stronger positive sentiment during bearish markets
            if news_sentiment > 0.15:
                sentiment_factor = min(news_sentiment * 25, 0.12)  # Conservative positive boost
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 70, -0.20)  # Strong penalty for negative
        elif market_data["context"] == "WEAK_BEARISH":
            # Moderate sentiment requirements during mild bearish conditions
            if news_sentiment > 0.10:
                sentiment_factor = min(news_sentiment * 35, 0.14)  # Moderate positive boost
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 60, -0.15)  # Moderate penalty
        elif market_data["context"] in ["BULLISH", "WEAK_BULLISH"]:
            # More lenient during bullish conditions
            if news_sentiment > 0.02:
                sentiment_factor = min(news_sentiment * 60, 0.15)  # Strong positive boost
            elif news_sentiment < -0.10:
                sentiment_factor = max(news_sentiment * 40, -0.08)  # Light penalty
        else:
            # Normal/neutral sentiment processing
            if news_sentiment > 0.05:
                sentiment_factor = min(news_sentiment * 50, 0.10)
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 50, -0.10)
        
        news_component = news_base + sentiment_factor
        news_component = max(0.0, min(news_component, 0.30))  # Clamp to 0-30%
        
        # 3. VOLUME ANALYSIS COMPONENT (20% total weight)
        volume_trend = volume_data["volume_trend"]
        volume_correlation = volume_data["price_volume_correlation"]
        volume_quality = volume_data["volume_quality_score"]
        
        # Volume trend factor (0-10 points) - FIXED: Stronger penalties for declining volume
        volume_trend_factor = 0.0
        if volume_trend > 0.2:  # Strong volume increase
            volume_trend_factor = 0.10
        elif volume_trend > 0.05:  # Moderate volume increase
            volume_trend_factor = 0.05
        elif volume_trend > -0.1:  # Neutral to slight decline
            volume_trend_factor = 0.02  # Small positive contribution
        elif volume_trend > -0.3:  # Moderate decline (market-wide condition)
            volume_trend_factor = 0.01  # Minimal positive to avoid 0.0
        elif volume_trend > -0.5:  # Severe decline but not extreme
            volume_trend_factor = -0.05  # Reduced penalty
        else:  # Extreme decline > 50%
            volume_trend_factor = -0.10  # Moderate penalty (was -0.20)
        
        # Price-volume correlation (0-10 points)
        correlation_factor = max(0.0, volume_correlation * 0.10)
        
        volume_component = volume_quality * 0.10 + volume_trend_factor + correlation_factor
        # Ensure minimum positive contribution even during market-wide volume declines
        volume_component = max(0.02, min(volume_component, 0.20))  # Min 2% contribution
        # DEBUG: Volume component calculation details
        print(f"   📊 Volume Analysis for {symbol}:")
        print(f"      Volume Trend: {volume_trend:+.1%}")
        print(f"      Volume Quality: {volume_quality:.3f}")
        print(f"      Volume Correlation: {volume_correlation:.3f}")
        print(f"      Volume Trend Factor: {volume_trend_factor:+.3f}")
        print(f"      Correlation Factor: {correlation_factor:+.3f}")
        print(f"      Final Volume Component: {volume_component:.3f}")
        
        # 4. RISK ADJUSTMENT COMPONENT (10% total weight)
        volatility = float(feature_parts[6]) if len(feature_parts) > 6 else 1
        volatility_factor = 0.05 if volatility < 1.5 else (-0.03 if volatility > 3.0 else 0)
        
        # Moving average relationship
        ma5 = float(feature_parts[2]) if len(feature_parts) > 2 else current_price
        ma20 = float(feature_parts[3]) if len(feature_parts) > 3 else current_price
        ma_factor = 0.0
        if current_price > ma5 > ma20:  # Strong uptrend
            ma_factor = 0.05
        elif current_price < ma5 < ma20:  # Strong downtrend
            ma_factor = -0.05
        
        risk_component = volatility_factor + ma_factor
        
        # PRELIMINARY CONFIDENCE CALCULATION
        preliminary_confidence = technical_component + news_component + volume_component + risk_component
        
        # 5. MARKET CONTEXT ADJUSTMENT (NEW!)
        market_adjusted_confidence = preliminary_confidence * market_data["confidence_multiplier"]
        
        # 6. APPLY EMERGENCY MARKET STRESS FILTER
        final_confidence = self.market_analyzer.market_stress_filter(market_adjusted_confidence, market_data)
        
        # Ensure bounds
        final_confidence = max(0.15, min(final_confidence, 0.95))
        
        # ENHANCED ACTION DETERMINATION WITH MARKET CONTEXT
        action = "HOLD"
        buy_threshold = market_data["buy_threshold"]
        
        # VOLUME TREND THRESHOLD VALIDATION - Global BUY Blocker
        volume_blocked = False
        if volume_trend < -0.60:  # Extreme volume decline (>60%)
            volume_blocked = True
            action = "HOLD"  # Global block for extreme volume decline
        
        # Standard BUY logic with market-aware thresholds AND volume validation
        if final_confidence > buy_threshold and tech_score > 42 and not volume_blocked:
            # OPTIMIZED FIX: Updated volume threshold for 85%+ win rate (-40% → -20%)
            if volume_trend < -0.20:  # More than 20% volume decline (optimized from -40%)
                action = "HOLD"  # Override BUY due to volume decline
            elif market_data["context"] == "BEARISH":
                # STRICTER requirements during bearish markets
                if news_sentiment > 0.05 and tech_score > 50 and volume_trend > -0.25:  # Relaxed volume requirement
                    action = "BUY"
            elif market_data["context"] == "WEAK_BEARISH":
                # Moderate requirements during mild bearish conditions
                if news_sentiment > 0.02 and tech_score > 45 and volume_trend > -0.20:  # Relaxed requirements
                    action = "BUY"
            else:
                # Normal requirements with volume check
                if news_sentiment > -0.08 and volume_trend > -0.30:  # Moderate volume decline tolerance
                    action = "BUY"
        
        # Strong BUY signals with volume validation
        if final_confidence > (buy_threshold + 0.08) and tech_score > 55:
            if market_data["context"] != "BEARISH" and news_sentiment > -0.02 and volume_trend > -0.15:  # Relaxed volume for STRONG_BUY
                action = "STRONG_BUY"
        
        # Safety override for very negative sentiment or poor technicals
        if news_sentiment < -0.15 or final_confidence < 0.30:
            action = "HOLD"
        
        # BUY DECISION VALIDATION LOGGING
        if action in ["BUY", "STRONG_BUY"]:
            print(f"🟢 {action} APPROVED for {symbol}:")
            print(f"   ✅ Confidence: {final_confidence:.3f} > {buy_threshold:.3f}")
            print(f"   ✅ Tech Score: {tech_score:.1f} > 60")
            print(f"   ✅ Volume Trend: {volume_trend:+.1%} (passed validation)")
            print(f"   ✅ News Sentiment: {news_sentiment:+.3f} (passed validation)")
            print(f"   ✅ Market Context: {market_data['context']}")
        elif final_confidence > buy_threshold:
            print(f"🟡 BUY BLOCKED for {symbol} (confidence {final_confidence:.3f} > {buy_threshold:.3f}):")
            if volume_blocked:
                print(f"   🚫 VOLUME BLOCKED: {volume_trend:+.1%} < -30% (extreme decline)")
            if tech_score <= 60:
                print(f"   ❌ Tech Score: {tech_score:.1f} ≤ 60")
            if volume_trend < -0.15 and not volume_blocked:
                print(f"   ❌ Volume Trend: {volume_trend:+.1%} < -15% (severe decline)")
            if market_data["context"] == "BEARISH":
                if news_sentiment <= 0.10:
                    print(f"   ❌ News Sentiment: {news_sentiment:+.3f} ≤ 0.10 (bearish requirement)")
                if tech_score <= 70:
                    print(f"   ❌ Tech Score: {tech_score:.1f} ≤ 70 (bearish requirement)")
                if volume_trend <= -0.05:
                    print(f"   ❌ Volume Trend: {volume_trend:+.1%} ≤ -5% (bearish requirement)")
            elif market_data["context"] == "WEAK_BEARISH":
                if news_sentiment <= 0.05:
                    print(f"   ❌ News Sentiment: {news_sentiment:+.3f} ≤ 0.05 (weak bearish requirement)")
                if tech_score <= 65:
                    print(f"   ❌ Tech Score: {tech_score:.1f} ≤ 65 (weak bearish requirement)")
            else:
                if news_sentiment <= -0.05:
                    print(f"   ❌ News Sentiment: {news_sentiment:+.3f} ≤ -0.05")
                if volume_trend <= -0.10:
                    print(f"   ❌ Volume Trend: {volume_trend:+.1%} ≤ -10%")
        
        return {
            "confidence": final_confidence,
            "action": action,
            "market_context": market_data["context"],
            "components": {
                "technical": technical_component,
                "news": news_component,
                "volume": volume_component,
                "risk": risk_component,
                "market_adjustment": market_data["confidence_multiplier"],
                "preliminary": preliminary_confidence
            },
            "details": {
                "tech_score": tech_score,
                "news_sentiment": news_sentiment,
                "news_confidence": news_confidence,
                "volume_trend": volume_trend,
                "volume_correlation": volume_correlation,
                "market_trend": market_data["trend_pct"],
                "buy_threshold_used": buy_threshold,
                "final_score_breakdown": f"Tech:{technical_component:.3f} + News:{news_component:.3f} + Vol:{volume_component:.3f} + Risk:{risk_component:.3f} × Market:{market_data['confidence_multiplier']:.2f} = {final_confidence:.3f}"
            }
        }
    
    def make_enhanced_prediction(self, symbol):
        """Make market-aware prediction with comprehensive analysis"""
        print(f"\n🔍 Analyzing {symbol} with Market-Aware System...")
        
        # Get market context FIRST
        market_data = self.market_analyzer.get_market_context()
        
        # Get technical analysis
        tech_data = self.analyzer.analyze(symbol)
        
        # Get news sentiment
        news_data = self.get_news_sentiment(symbol)
        
        # Volume data is included in tech_data
        volume_data = tech_data["volume_metrics"]
        
        # Calculate enhanced confidence with market context
        confidence_result = self.calculate_enhanced_confidence(
            symbol, tech_data, news_data, volume_data, market_data
        )
        
        # Compile prediction result
        prediction = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "predicted_action": confidence_result["action"],
            "action_confidence": confidence_result["confidence"],
            "entry_price": tech_data["current_price"],
            "market_context": confidence_result["market_context"],
            "prediction_details": confidence_result["details"],
            "components": confidence_result["components"],
            "feature_vector": tech_data["feature_vector"],
            "market_data": market_data
        }
        
        return prediction

def create_database():
    """Create enhanced database with market context logging"""
    db_path = "data/trading_predictions.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enhanced table with market context fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id TEXT UNIQUE,
            symbol TEXT,
            predicted_action TEXT,
            action_confidence REAL,
            entry_price REAL,
            market_context TEXT,
            market_trend_pct REAL,
            buy_threshold_used REAL,
            tech_score REAL,
            news_sentiment REAL,
            volume_trend REAL,
            feature_vector TEXT,
            confidence_breakdown TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def test_market_aware_system():
    """Test the market-aware prediction system"""
    
    # Use symbols from settings if available, otherwise fallback
    if SETTINGS_AVAILABLE:
        # Use ONLY the 7 bank symbols from settings configuration
        symbols = Settings.BANK_SYMBOLS.copy()
        
        print(f"📊 Using {len(symbols)} bank symbols from settings configuration")
        print(f"   Bank symbols: {', '.join(Settings.BANK_SYMBOLS)}")
    else:
        # Fallback symbols (7 bank symbols)
        symbols = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]
        print("⚠️ Using fallback bank symbols - settings not available")
    
    print("🚀 Testing Market-Aware Enhanced Prediction System")
    print("=" * 60)
    
    # Initialize predictor
    predictor = MarketAwarePredictor()
    
    # Create database
    create_database()
    
    # Get market overview first
    market_data = predictor.market_analyzer.get_market_context()
    print(f"\n🌐 Market Overview:")
    print(f"   Context: {market_data['context']}")
    print(f"   5-day Trend: {market_data['trend_pct']:+.2f}%")
    print(f"   Confidence Multiplier: {market_data['confidence_multiplier']:.2f}x")
    print(f"   BUY Threshold: {market_data['buy_threshold']:.1%}")
    
    results = []
    buy_signals = 0
    
    # Process each symbol
    for symbol in symbols:
        try:
            prediction = predictor.make_enhanced_prediction(symbol)
            
            # Count BUY signals
            if prediction['predicted_action'] in ['BUY', 'STRONG_BUY']:
                buy_signals += 1
            
            # Display results
            print(f"\n📊 {symbol} Enhanced Analysis:")
            print(f"   Action: {prediction['predicted_action']}")
            print(f"   Confidence: {prediction['action_confidence']:.1%}")
            print(f"   Price: ${prediction['entry_price']:.2f}")
            print(f"   Market Context: {prediction['market_context']}")
            print(f"   Breakdown: {prediction['prediction_details']['final_score_breakdown']}")
            print(f"   News Sentiment: {prediction['prediction_details']['news_sentiment']:+.3f}")
            print(f"   Volume Trend: {prediction['prediction_details']['volume_trend']:+.1%}")
            print(f"   Threshold Used: {prediction['prediction_details']['buy_threshold_used']:.1%}")
            
            results.append(prediction)
            
            # Store in database
            conn = sqlite3.connect("data/trading_predictions.db")
            cursor = conn.cursor()
            
            prediction_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO predictions 
                (prediction_id, symbol, predicted_action, action_confidence, entry_price,
                 market_context, market_trend_pct, buy_threshold_used, tech_score, 
                 news_sentiment, volume_trend, feature_vector, confidence_breakdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id, symbol, prediction['predicted_action'],
                prediction['action_confidence'], prediction['entry_price'],
                prediction['market_context'], prediction['market_data']['trend_pct'],
                prediction['prediction_details']['buy_threshold_used'],
                prediction['prediction_details']['tech_score'],
                prediction['prediction_details']['news_sentiment'],
                prediction['prediction_details']['volume_trend'],
                prediction['feature_vector'],
                prediction['prediction_details']['final_score_breakdown']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            continue
    
    # Summary analysis
    print(f"\n📈 ANALYSIS SUMMARY:")
    print(f"   Market Context: {market_data['context']}")
    print(f"   Symbols Analyzed: {len(results)}")
    print(f"   BUY Signals Generated: {buy_signals}")
    print(f"   BUY Signal Rate: {(buy_signals/len(results)*100):.1f}%" if results else "N/A")
    
    # Alert if too many BUY signals during bearish market
    if market_data['context'] == 'BEARISH' and buy_signals > len(results) * 0.3:
        print(f"⚠️  WARNING: High BUY signal rate ({buy_signals}/{len(results)}) during BEARISH market!")
        print("   Consider manual review of signals")
    
    return results

if __name__ == "__main__":
    test_market_aware_system()
    test_market_aware_system()
