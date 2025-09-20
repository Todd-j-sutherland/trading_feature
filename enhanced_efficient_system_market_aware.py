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
import sys
import sqlite3
import yfinance as yf
import gc
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")
# ML prediction imports
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Try to import settings configuration
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app.config.settings import Settings
    SETTINGS_AVAILABLE = True
    print("✅ Settings configuration loaded successfully")
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️ Settings configuration not available - using fallback symbols")


class MLPredictor:
    """Machine Learning predictor for stock direction and magnitude"""
    
    def __init__(self):
        """Initialize ML models"""
        self.models_path = "/root/test/models"
        self.direction_model = None
        self.magnitude_model = None
        self.scaler = None
        self.load_models()
    
    def load_models(self):
        """Load trained ML models"""
        try:
            # Load direction model
            direction_path = os.path.join(self.models_path, "current_direction_model.pkl")
            with open(direction_path, "rb") as f:
                self.direction_model = pickle.load(f)
            
            # Load magnitude model
            magnitude_path = os.path.join(self.models_path, "current_magnitude_model.pkl")
            with open(magnitude_path, "rb") as f:
                self.magnitude_model = pickle.load(f)
            
            # Load scaler
            scaler_path = os.path.join(self.models_path, "feature_scaler.pkl")
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)
            
            print("✅ ML models loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load ML models: {e}")
            raise Exception(f"ML models required but failed to load: {e}")
    
    def extract_features(self, data):
        """Extract features for ML prediction"""
        try:
            # Calculate technical indicators
            close_prices = data["Close"].values
            volumes = data["Volume"].values
            
            # Price-based features
            returns = np.diff(close_prices) / close_prices[:-1]
            volatility = np.std(returns[-10:]) if len(returns) >= 10 else 0
            
            # Moving averages
            ma_5 = np.mean(close_prices[-5:]) if len(close_prices) >= 5 else close_prices[-1]
            ma_20 = np.mean(close_prices[-20:]) if len(close_prices) >= 20 else close_prices[-1]
            
            # Volume indicators
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
            volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
            
            # Momentum indicators
            momentum = (close_prices[-1] - close_prices[-5]) / close_prices[-5] if len(close_prices) >= 5 else 0
            
            # RSI approximation
            gains = np.maximum(returns, 0)
            losses = -np.minimum(returns, 0)
            avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
            avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            features = [
                volatility, ma_5, ma_20, volume_ratio,
                momentum, rsi, len(close_prices)
            ]
            
            return np.array(features).reshape(1, -1)
        except Exception as e:
            print(f"❌ Feature extraction failed: {e}")
            return None
    
    def predict(self, data):
        """Make ML predictions"""
        try:
            if self.direction_model is None or self.magnitude_model is None or self.scaler is None:
                raise Exception("ML models not loaded")
            
            # Extract features
            features = self.extract_features(data)
            if features is None:
                raise Exception("Feature extraction failed")
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict direction (0=down, 1=up)
            direction_prob = self.direction_model.predict_proba(features_scaled)[0]
            direction_confidence = max(direction_prob)
            predicted_direction = self.direction_model.predict(features_scaled)[0]
            
            # Predict magnitude
            magnitude = abs(self.magnitude_model.predict(features_scaled)[0])
            
            # ML confidence based on direction confidence and magnitude
            ml_confidence = min(direction_confidence * (1 + magnitude * 0.5), 1.0)
            
            return {
                "direction": "UP" if predicted_direction == 1 else "DOWN",
                "direction_confidence": direction_confidence,
                "magnitude": magnitude,
                "ml_confidence": ml_confidence,
                "features_used": features.shape[1]
            }
        except Exception as e:
            print(f"❌ ML prediction failed: {e}")
            raise Exception(f"ML prediction failed: {e}")

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
                    "buy_threshold": 0.70
                }
            
            # Calculate 5-day market trend
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            
            # Determine market context
            if market_trend < -2:  # Market down >2%
                context = "BEARISH"
                confidence_multiplier = 0.7  # Reduce confidence by 30%
                buy_threshold = 0.80  # Higher threshold
            elif market_trend > 2:  # Market up >2%
                context = "BULLISH"
                confidence_multiplier = 1.1  # Boost confidence by 10%
                buy_threshold = 0.65  # Lower threshold
            else:
                context = "NEUTRAL"
                confidence_multiplier = 1.0
                buy_threshold = 0.70
            
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
                "buy_threshold": 0.70,
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
        
        # Volume trend (comparing recent vs older) - FIXED to return 0.0-1.0
        recent_avg = sum(volumes[-5:]) / 5
        older_avg = sum(volumes[-20:-10]) / 10
        
        # Calculate percentage change first
        volume_change_pct = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Normalize to 0.0-1.0 range for volume_trend
        # Map -100% to +100% change to 0.0 to 1.0 scale
        # -50% or worse = 0.0, +50% or better = 1.0, 0% = 0.5
        if volume_change_pct <= -0.5:
            volume_trend = 0.0  # Very low volume
        elif volume_change_pct >= 0.5:
            volume_trend = 1.0  # Very high volume  
        else:
            # Linear mapping: -0.5 to +0.5 becomes 0.0 to 1.0
            volume_trend = (volume_change_pct + 0.5) / 1.0
        
        # Store both the original percentage and normalized value

        
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
        "volume_change_pct": volume_change_pct,  # Store original percentage
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
        self.ml_predictor = MLPredictor()
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
                    # Extract from nested content structure (yfinance API change)
                    content = article.get('content', {})
                    title = content.get('title', '') if isinstance(content, dict) else ''
                    summary = content.get('summary', '') if isinstance(content, dict) else ''
                    
                    # Fallback for old API structure
                    if not title and not summary:
                        title = article.get('title', '')
                        summary = article.get('summary', '')
                    
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
    
    def calculate_enhanced_confidence(self, symbol, tech_data, news_data, volume_data, market_data, ml_data):
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
        
        # ENHANCED: Sentiment adjustment with market context
        sentiment_factor = 0.0
        if market_data["context"] == "BEARISH":
            # Require stronger positive sentiment during bearish markets
            if news_sentiment > 0.15:  # Raised from 0.05
                sentiment_factor = min(news_sentiment * 30, 0.15)  # Reduced multiplier
            elif news_sentiment < -0.05:
                sentiment_factor = max(news_sentiment * 60, -0.15)  # Stronger penalty
        else:
            # Normal sentiment processing
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
        
        # Volume trend factor (0-10 points)
        volume_trend_factor = 0.0
        if volume_trend > 0.2:  # Strong volume increase
            volume_trend_factor = 0.10
        elif volume_trend > 0.05:  # Moderate volume increase
            volume_trend_factor = 0.05
        elif volume_trend < -0.2:  # Volume declining (risk)
            volume_trend_factor = -0.05
        
        # Price-volume correlation (0-10 points)
        correlation_factor = max(0.0, volume_correlation * 0.10)
        
        volume_component = volume_quality * 0.10 + volume_trend_factor + correlation_factor
        volume_component = max(0.0, min(volume_component, 0.20))  # Clamp to 0-20%
        
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

        # 5. MACHINE LEARNING COMPONENT (20% total weight)
        ml_direction = ml_data["direction"]
        ml_confidence = ml_data["ml_confidence"]
        ml_magnitude = ml_data["magnitude"]
        
        # Base ML contribution (0-15 points)
        ml_base = ml_confidence * 0.15
        
        # Direction agreement bonus (0-3 points)
        direction_bonus = 0.0
        if tech_score > 50:  # Bullish technical
            if ml_direction == "UP":
                direction_bonus = 0.03
        elif tech_score < 50:  # Bearish technical
            if ml_direction == "DOWN":
                direction_bonus = 0.03
        
        # Magnitude factor (0-2 points)
        magnitude_factor = min(ml_magnitude * 0.02, 0.02)
        
        ml_component = ml_base + direction_bonus + magnitude_factor
        ml_component = max(0.0, min(ml_component, 0.20))  # Clamp to 0-20%
        
        # PRELIMINARY CONFIDENCE CALCULATION
        preliminary_confidence = technical_component + news_component + volume_component + risk_component + ml_component
        
        # 5. MARKET CONTEXT ADJUSTMENT (NEW!)
        market_adjusted_confidence = preliminary_confidence * market_data["confidence_multiplier"]
        
        # 6. APPLY EMERGENCY MARKET STRESS FILTER
        final_confidence = self.market_analyzer.market_stress_filter(market_adjusted_confidence, market_data)
        
        # Ensure bounds
        final_confidence = max(0.15, min(final_confidence, 0.95))
        
        # ENHANCED ACTION DETERMINATION WITH MARKET CONTEXT
        action = "HOLD"
        buy_threshold = market_data["buy_threshold"]
        
        # Standard BUY logic with market-aware thresholds
        if final_confidence > buy_threshold and tech_score > 60:
            if market_data["context"] == "BEARISH":
                # STRICTER requirements during bearish markets
                if news_sentiment > 0.10 and tech_score > 70:  # Much higher bar
                    action = "BUY"
            else:
                # Normal requirements
                if news_sentiment > -0.05:
                    action = "BUY"
        
        # Strong BUY signals
        if final_confidence > (buy_threshold + 0.10) and tech_score > 70:
            if market_data["context"] != "BEARISH" and news_sentiment > 0.02:
                action = "STRONG_BUY"
        
        # Safety override for very negative sentiment or poor technicals
        if news_sentiment < -0.15 or final_confidence < 0.30:
            action = "HOLD"
        
        return {
            "confidence": final_confidence,
            "action": action,
            "market_context": market_data["context"],
            "components": {
                "technical": technical_component,
                "news": news_component,
                "volume": volume_component,
                "risk": risk_component,
                "ml": ml_component,
                "market_adjustment": market_data["confidence_multiplier"],
                "preliminary": preliminary_confidence
            },
            "details": {
                "tech_score": tech_score,
                "news_sentiment": news_sentiment,
                "news_confidence": news_confidence,
                "volume_trend": volume_trend,
                "volume_change_pct": volume_data.get("volume_change_pct", 0.0),  # From volume_data
                "volume_correlation": volume_correlation,
                "market_trend": market_data["trend_pct"],
                "buy_threshold_used": buy_threshold,
                "ml_direction": ml_direction,
                "ml_confidence": ml_confidence,
                "ml_magnitude": ml_magnitude,
                "final_score_breakdown": f"Tech:{technical_component:.3f} + News:{news_component:.3f} + Vol:{volume_component:.3f} + Risk:{risk_component:.3f} + ML:{ml_component:.3f} × Market:{market_data['confidence_multiplier']:.2f} = {final_confidence:.3f}"
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

        # Get ML prediction
        stock_data = yf.download(symbol, period="6mo", interval="1d")
        try:
            # Flatten multi-level columns
            if len(stock_data.columns.names) > 1:
                stock_data.columns = [col[0] if isinstance(col, tuple) else col for col in stock_data.columns]
                stock_data.columns = stock_data.columns.get_level_values(0)
            ml_data = self.ml_predictor.predict(stock_data)
            print(f"✅ ML prediction: {ml_data["direction"]} (confidence: {ml_data["ml_confidence"]:.3f})")
        except Exception as e:
            print(f"❌ ML prediction failed: {e}")
            raise Exception(f"ML prediction required but failed: {e}")
        volume_data = tech_data["volume_metrics"]
        
        # Calculate enhanced confidence with market context
        confidence_result = self.calculate_enhanced_confidence(
            symbol, tech_data, news_data, volume_data, market_data, ml_data
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
