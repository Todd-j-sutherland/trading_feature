#!/usr/bin/env python3
"""
Enhanced Efficient Prediction System with News Sentiment and Volume Analysis
Comprehensive system including technical analysis, news sentiment, and volume metrics

This system integrates:
- Technical Analysis (40% weight)
- News Sentiment Analysis (30% weight) 
- Volume Analysis (20% weight)
- Risk Factors (10% weight)
"""

import os
import sys
import sqlite3
import yfinance as yf
import gc
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

class TechnicalAnalyzer:
    """Lightweight technical analysis with volume metrics"""
    
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
        recent_avg = sum(volumes[-5:]) / min(5, len(volumes))
        older_avg = sum(volumes[-15:-5]) / min(10, len(volumes))
        volume_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Price-Volume correlation (simplified)
        correlation = 0.0
        if len(volumes) >= 10 and len(prices) >= 10:
            recent_volumes = volumes[-10:]
            recent_prices = prices[-10:]
            price_changes = [recent_prices[i] - recent_prices[i-1] for i in range(1, len(recent_prices))]
            volume_changes = [recent_volumes[i] - recent_volumes[i-1] for i in range(1, len(recent_volumes))]
            
            if len(price_changes) == len(volume_changes):
                pos_correlation = sum(1 for i in range(len(price_changes)) 
                                    if (price_changes[i] > 0 and volume_changes[i] > 0) or 
                                       (price_changes[i] < 0 and volume_changes[i] < 0))
                correlation = (pos_correlation / len(price_changes) - 0.5) * 2
        
        # Volume quality score (0.0 to 1.0)
        volume_quality = min(1.0, avg_volume / 1000000)  # Normalize by 1M shares
        
        return {
            "avg_volume": avg_volume,
            "volume_trend": volume_trend,
            "price_volume_correlation": correlation,
            "volume_quality_score": volume_quality
        }
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def analyze(self, symbol: str):
        """Get comprehensive technical analysis with volume"""
        prices, volumes = self.get_prices_and_volume(symbol)
        
        if len(prices) < 20:
            return {
                "current_price": 0.0,
                "rsi": 50.0,
                "tech_score": 40.0,
                "feature_vector": "50.0,50.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0",
                "volume_metrics": {
                    "avg_volume": 0,
                    "volume_trend": 0.0,
                    "price_volume_correlation": 0.0,
                    "volume_quality_score": 0.0
                }
            }
        
        current_price = prices[-1]
        rsi = self.calculate_rsi(prices)
        volume_metrics = self.calculate_volume_metrics(volumes, prices)
        
        # Moving averages
        ma5 = sum(prices[-5:]) / 5
        ma20 = sum(prices[-20:]) / 20
        
        # Momentum and volatility
        momentum = (current_price - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        volatility = sum(abs(prices[i] - prices[i-1]) for i in range(-10, -1)) / (prices[-10] * 9) if len(prices) >= 10 else 0.01
        
        # Technical score with volume consideration
        tech_score = 50.0
        if rsi < 30:
            tech_score += 15
        elif rsi > 70:
            tech_score += 10
        
        if current_price > ma5 > ma20:
            tech_score += 15
        
        if momentum > 0.02:
            tech_score += 10
            
        # Volume boost to technical score
        if volume_metrics["volume_trend"] > 0.1:  # Volume increasing
            tech_score += 5
        if volume_metrics["price_volume_correlation"] > 0.3:  # Good price-volume relationship
            tech_score += 5
        
        tech_score = min(100.0, max(0.0, tech_score))
        
        feature_vector = f"{tech_score},{rsi},{ma5},{ma20},{current_price},{momentum},{volatility},{volume_metrics['volume_trend']*100},{volume_metrics['price_volume_correlation']*100}"
        
        return {
            "current_price": current_price,
            "rsi": rsi,
            "tech_score": tech_score,
            "feature_vector": feature_vector,
            "volume_metrics": volume_metrics
        }

class NewsVolumePredictor:
    """Enhanced predictor with news sentiment and volume analysis"""
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
        self.setup_news_analyzer()
    
    def setup_news_analyzer(self):
        """Initialize news sentiment analyzer"""
        try:
            from app.core.data.processors.news_processor import NewsTradingAnalyzer
            self.news_analyzer = NewsTradingAnalyzer()
            self.has_news = True
            print("✅ News sentiment analyzer initialized")
        except Exception as e:
            print(f"⚠️  News analyzer not available: {e}")
            self.news_analyzer = None
            self.has_news = False
    
    def get_news_sentiment(self, symbol):
        """Get news sentiment data for symbol"""
        if not self.has_news:
            return {
                "sentiment_score": 0.0,
                "news_confidence": 0.5,
                "news_count": 0,
                "news_quality_score": 0.0
            }
        
        try:
            result = self.news_analyzer.analyze_single_bank(symbol)
            if result and isinstance(result, dict):
                sentiment_score = result.get('overall_sentiment', 0.0)
                news_confidence = result.get('confidence', 0.5)
                news_count = result.get('news_count', 0)
                
                # Calculate news quality score based on coverage and confidence
                coverage_score = min(1.0, news_count / 20)  # 20+ articles = full score
                quality_score = (news_confidence * 0.7) + (coverage_score * 0.3)
                
                return {
                    "sentiment_score": sentiment_score,
                    "news_confidence": news_confidence,
                    "news_count": news_count,
                    "news_quality_score": quality_score
                }
        except Exception as e:
            print(f"⚠️  Error getting news sentiment for {symbol}: {e}")
        
        return {
            "sentiment_score": 0.0,
            "news_confidence": 0.5,
            "news_count": 0,
            "news_quality_score": 0.0
        }
    
    def calculate_enhanced_confidence(self, symbol, tech_data, news_data, volume_data):
        """Calculate comprehensive confidence with news sentiment and volume"""
        
        # Extract technical factors
        rsi = tech_data["rsi"]
        tech_score = tech_data["tech_score"]
        current_price = tech_data["current_price"]
        feature_parts = tech_data["feature_vector"].split(",")
        
        # ===========================================
        # ENHANCED CONFIDENCE CALCULATION
        # Based on Grade F investigation weighting
        # ===========================================
        
        # 1. TECHNICAL ANALYSIS COMPONENT (40% total weight)
        base_confidence = 0.20  # Reduced from 0.30
        
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
        
        # Base news factor (0-20 points)
        news_base = news_confidence * 0.20
        
        # Sentiment adjustment (-10 to +10 points)
        sentiment_factor = 0.0
        if news_sentiment > 0.05:  # Positive sentiment
            sentiment_factor = min(news_sentiment * 50, 0.10)
        elif news_sentiment < -0.05:  # Negative sentiment
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
        
        # FINAL CONFIDENCE CALCULATION
        final_confidence = technical_component + news_component + volume_component + risk_component
        final_confidence = max(0.15, min(final_confidence, 0.95))  # Clamp between 15% and 95%
        
        # Action determination based on enhanced confidence
        action = "HOLD"
        if final_confidence > 0.70 and tech_score > 60 and news_sentiment > -0.05:
            action = "BUY"
        elif final_confidence > 0.80 and tech_score > 70 and news_sentiment > 0.02:
            action = "STRONG_BUY"
        elif final_confidence < 0.30 or news_sentiment < -0.15:
            action = "HOLD"
        
        return {
            "confidence": final_confidence,
            "action": action,
            "components": {
                "technical": technical_component,
                "news": news_component,
                "volume": volume_component,
                "risk": risk_component
            },
            "details": {
                "tech_score": tech_score,
                "news_sentiment": news_sentiment,
                "news_confidence": news_confidence,
                "volume_trend": volume_trend,
                "volume_correlation": volume_correlation,
                "final_score_breakdown": f"Tech:{technical_component:.3f} + News:{news_component:.3f} + Vol:{volume_component:.3f} + Risk:{risk_component:.3f} = {final_confidence:.3f}"
            }
        }
    
    def make_enhanced_prediction(self, symbol):
        """Make prediction with comprehensive analysis"""
        print(f"🔍 Analyzing {symbol} with enhanced system...")
        
        # Get technical analysis
        tech_data = self.analyzer.analyze(symbol)
        
        # Get news sentiment
        news_data = self.get_news_sentiment(symbol)
        
        # Volume data is included in tech_data
        volume_data = tech_data["volume_metrics"]
        
        # Calculate enhanced confidence
        prediction = self.calculate_enhanced_confidence(symbol, tech_data, news_data, volume_data)
        
        # Calculate missing fields for database
        predicted_direction = 1 if prediction["action"] in ["BUY", "STRONG_BUY"] else (-1 if prediction["action"] == "SELL" else 0)
        magnitude = (tech_data["tech_score"] - 50) / 100 * 0.05 if predicted_direction == 1 else 0.0
        
        return {
            "symbol": symbol,
            "predicted_action": prediction["action"],
            "action_confidence": prediction["confidence"],
            "predicted_direction": predicted_direction,
            "predicted_magnitude": magnitude,
            "feature_vector": tech_data["feature_vector"],
            "model_version": "enhanced_news_volume_v1.0",
            "entry_price": tech_data["current_price"],
            "optimal_action": prediction["action"],
            "prediction_details": prediction["details"]
        }

def create_database():
    """Create predictions database if it doesn't exist"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/trading_predictions.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            prediction_timestamp DATETIME NOT NULL,
            predicted_action TEXT NOT NULL,
            action_confidence REAL NOT NULL,
            predicted_direction INTEGER,
            predicted_magnitude REAL,
            feature_vector TEXT,
            model_version TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            entry_price REAL DEFAULT 0,
            optimal_action TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def main():
    """Main execution with enhanced news and volume analysis"""
    symbols = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX"]  # Test with MQG.AX first
    
    print("🚀 Starting Enhanced News & Volume Prediction System")
    print("=" * 60)
    
    # Initialize predictor
    predictor = NewsVolumePredictor()
    
    # Create database
    create_database()
    
    # Process each symbol
    for symbol in symbols:
        try:
            prediction = predictor.make_enhanced_prediction(symbol)
            
            # Display results
            print(f"\n📊 {symbol} Enhanced Analysis:")
            print(f"   Action: {prediction['predicted_action']}")
            print(f"   Confidence: {prediction['action_confidence']:.1%}")
            print(f"   Price: ${prediction['entry_price']:.2f}")
            print(f"   Breakdown: {prediction['prediction_details']['final_score_breakdown']}")
            print(f"   News Sentiment: {prediction['prediction_details']['news_sentiment']:+.3f}")
            print(f"   Volume Trend: {prediction['prediction_details']['volume_trend']:+.1%}")
            
            # Store in database
            conn = sqlite3.connect("data/trading_predictions.db")
            cursor = conn.cursor()
            
            prediction_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp, predicted_action,
                    action_confidence, predicted_direction, predicted_magnitude,
                    feature_vector, model_version, entry_price, optimal_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id, symbol, timestamp, prediction["predicted_action"],
                prediction["action_confidence"], prediction["predicted_direction"],
                prediction["predicted_magnitude"], prediction["feature_vector"],
                prediction["model_version"], prediction["entry_price"],
                prediction["optimal_action"]
            ))
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ Stored in database")
            
        except Exception as e:
            print(f"   ❌ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
        
        # Memory cleanup
        gc.collect()
    
    print(f"\n🎯 Enhanced prediction system completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
