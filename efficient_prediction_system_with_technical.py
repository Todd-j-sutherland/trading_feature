#!/usr/bin/env python3
"""
Enhanced Efficient Prediction System with Technical Analysis
Memory-optimized prediction system that includes technical indicators
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings("ignore")

class EfficientTechnicalAnalysis:
    """Lightweight technical analysis for predictions"""
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI efficiently"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas[-period:]]
        losses = [-delta if delta < 0 else 0 for delta in deltas[-period:]]
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calculate_moving_averages(self, prices: List[float]) -> Dict[str, float]:
        """Calculate multiple moving averages"""
        if len(prices) < 20:
            current_price = prices[-1] if prices else 0
            return {
                "ma_5": current_price,
                "ma_10": current_price, 
                "ma_20": current_price
            }
        
        return {
            "ma_5": sum(prices[-5:]) / 5 if len(prices) >= 5 else prices[-1],
            "ma_10": sum(prices[-10:]) / 10 if len(prices) >= 10 else prices[-1],
            "ma_20": sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices[-1] if prices else 0
            return {
                "bb_upper": current_price * 1.02,
                "bb_middle": current_price,
                "bb_lower": current_price * 0.98,
                "bb_position": 0.5
            }
        
        recent_prices = prices[-period:]
        mean = sum(recent_prices) / period
        variance = sum((p - mean) ** 2 for p in recent_prices) / period
        std_dev = variance ** 0.5
        
        upper = mean + (2 * std_dev)
        lower = mean - (2 * std_dev)
        current = prices[-1]
        
        # Position within bands (0 = lower band, 1 = upper band)
        if upper != lower:
            position = (current - lower) / (upper - lower)
        else:
            position = 0.5
            
        return {
            "bb_upper": upper,
            "bb_middle": mean,
            "bb_lower": lower,
            "bb_position": max(0, min(1, position))
        }
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Simple MACD calculation"""
        if len(prices) < 26:
            return {"macd": 0, "macd_signal": 0, "macd_histogram": 0}
        
        # Simple EMA approximation
        ema_12 = sum(prices[-12:]) / 12
        ema_26 = sum(prices[-26:]) / 26
        macd = ema_12 - ema_26
        
        # Signal line (simple approximation)
        signal = macd * 0.8  # Simplified signal line
        histogram = macd - signal
        
        return {
            "macd": macd,
            "macd_signal": signal,
            "macd_histogram": histogram
        }
    
    def analyze_symbol(self, symbol: str, prices: List[float]) -> Dict[str, float]:
        """Complete technical analysis for a symbol"""
        if not prices or len(prices) < 5:
            return self.get_default_analysis()
        
        # Calculate all indicators
        rsi = self.calculate_rsi(prices)
        ma_values = self.calculate_moving_averages(prices)
        bb_values = self.calculate_bollinger_bands(prices)
        macd_values = self.calculate_macd(prices)
        
        # Calculate trend strength
        current_price = prices[-1]
        ma_20 = ma_values["ma_20"]
        trend_strength = ((current_price - ma_20) / ma_20) * 100 if ma_20 > 0 else 0
        
        # Calculate volatility
        if len(prices) >= 5:
            recent_changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(-4, 0)]
            volatility = (sum(abs(change) for change in recent_changes) / len(recent_changes)) * 100
        else:
            volatility = 1.0
        
        return {
            "rsi": rsi,
            "ma_5": ma_values["ma_5"],
            "ma_10": ma_values["ma_10"], 
            "ma_20": ma_values["ma_20"],
            "bb_upper": bb_values["bb_upper"],
            "bb_middle": bb_values["bb_middle"],
            "bb_lower": bb_values["bb_lower"],
            "bb_position": bb_values["bb_position"],
            "macd": macd_values["macd"],
            "macd_signal": macd_values["macd_signal"],
            "macd_histogram": macd_values["macd_histogram"],
            "trend_strength": trend_strength,
            "volatility": volatility,
            "technical_score": self.calculate_technical_score(rsi, ma_values, bb_values, trend_strength)
        }
    
    def calculate_technical_score(self, rsi: float, ma_values: Dict, bb_values: Dict, trend_strength: float) -> float:
        """Calculate overall technical score (0-100)"""
        score = 50  # Start neutral
        
        # RSI component (30% weight)
        if rsi > 70:
            score += 15  # Overbought - positive for momentum
        elif rsi < 30:
            score -= 15  # Oversold - negative
        elif 40 <= rsi <= 60:
            score += 5   # Neutral zone - slightly positive
        
        # Moving average trend (40% weight)
        ma_5, ma_10, ma_20 = ma_values["ma_5"], ma_values["ma_10"], ma_values["ma_20"]
        if ma_5 > ma_10 > ma_20:
            score += 20  # Strong uptrend
        elif ma_5 > ma_20:
            score += 10  # Mild uptrend
        elif ma_5 < ma_10 < ma_20:
            score -= 20  # Strong downtrend
        elif ma_5 < ma_20:
            score -= 10  # Mild downtrend
        
        # Bollinger position (20% weight)
        bb_pos = bb_values["bb_position"]
        if bb_pos > 0.8:
            score += 10  # Near upper band
        elif bb_pos < 0.2:
            score -= 10  # Near lower band
        
        # Trend strength (10% weight)
        if trend_strength > 2:
            score += 5
        elif trend_strength < -2:
            score -= 5
        
        return max(0, min(100, score))
    
    def get_default_analysis(self) -> Dict[str, float]:
        """Default analysis when insufficient data"""
        return {
            "rsi": 50.0, "ma_5": 0, "ma_10": 0, "ma_20": 0,
            "bb_upper": 0, "bb_middle": 0, "bb_lower": 0, "bb_position": 0.5,
            "macd": 0, "macd_signal": 0, "macd_histogram": 0,
            "trend_strength": 0, "volatility": 1.0, "technical_score": 50.0
        }

class EfficientPredictionSystemWithTechnical:
    """Enhanced prediction system with technical analysis"""
    
    def __init__(self):
        self.symbols = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "MQG.AX"]
        self.db_path = "predictions.db"
        self.technical_analyzer = EfficientTechnicalAnalysis()
        
    def is_market_hours(self) -> bool:
        """Check if ASX is open (10:00 AM - 4:00 PM AEST, Mon-Fri)"""
        try:
            import pytz
            aest = pytz.timezone(Australia/Sydney)
            now_aest = datetime.now(aest)
            
            # Check if weekday (Monday=0, Sunday=6)
            if now_aest.weekday() >= 5:  # Saturday=5, Sunday=6
                return False
            
            hour = now_aest.hour
            return 10 <= hour < 16
            
        except ImportError:
            # Fallback without pytz
            from datetime import timezone, timedelta
            aest_offset = timedelta(hours=11)  # AEST = UTC+11 (simplified)
            now_aest = datetime.now(timezone.utc) + aest_offset
            
            if now_aest.weekday() >= 5:
                return False
                
            hour = now_aest.hour
            return 10 <= hour < 16
    
    def log_message(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        try:
            with open("efficient_prediction_log.txt", "a") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def get_historical_prices(self, symbol: str, days: int = 30) -> List[float]:
        """Get historical prices for technical analysis"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                self.log_message(f"⚠️ No historical data for {symbol}")
                return []
            
            prices = hist[Close].tolist()
            return [float(p) for p in prices if pd.notna(p)]
            
        except Exception as e:
            self.log_message(f"⚠️ Error getting historical data for {symbol}: {e}")
            return []
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get(currentPrice) or info.get(regularMarketPrice, 0)
            return float(current_price) if current_price else 0.0
        except Exception as e:
            self.log_message(f"⚠️ Error getting current price for {symbol}: {e}")
            return 0.0
    
    def make_prediction_with_technical(self, symbol: str) -> Dict:
        """Make prediction including technical analysis"""
        try:
            # Get historical prices for technical analysis
            historical_prices = self.get_historical_prices(symbol)
            current_price = self.get_current_price(symbol)
            
            if not historical_prices:
                historical_prices = [current_price] if current_price > 0 else [100.0]
            
            # Add current price to historical data
            if current_price > 0:
                historical_prices.append(current_price)
            
            # Perform technical analysis
            technical_data = self.technical_analyzer.analyze_symbol(symbol, historical_prices)
            
            # Make prediction based on technical analysis
            prediction = self.generate_prediction(symbol, current_price, technical_data)
            
            return prediction
            
        except Exception as e:
            self.log_message(f"⚠️ Error in prediction for {symbol}: {e}")
            return self.get_default_prediction(symbol)
    
    def generate_prediction(self, symbol: str, current_price: float, technical_data: Dict) -> Dict:
        """Generate prediction based on technical analysis"""
        
        # Extract key technical indicators
        rsi = technical_data.get("rsi", 50)
        technical_score = technical_data.get("technical_score", 50)
        trend_strength = technical_data.get("trend_strength", 0)
        bb_position = technical_data.get("bb_position", 0.5)
        ma_5 = technical_data.get("ma_5", current_price)
        ma_20 = technical_data.get("ma_20", current_price)
        
        # Decision logic
        confidence = 0.4  # Base confidence
        action = "HOLD"   # Default action
        
        # RSI signals
        if rsi > 60 and rsi < 80:  # Moderate bullish
            confidence += 0.1
            action = "BUY"
        elif rsi > 80:  # Overbought
            confidence += 0.05
            action = "HOLD"  # Wait for correction
        elif rsi < 40 and rsi > 20:  # Moderate bearish
            confidence += 0.05
            action = "HOLD"  # Wait for rebound
        elif rsi < 20:  # Oversold
            confidence += 0.1
            action = "BUY"  # Potential bounce
        
        # Moving average trend
        if ma_5 > ma_20 * 1.005:  # 0.5% above MA20
            confidence += 0.1
            if action != "BUY":
                action = "BUY"
        elif ma_5 < ma_20 * 0.995:  # 0.5% below MA20
            confidence += 0.05
            action = "HOLD"
        
        # Technical score influence
        if technical_score > 65:
            confidence += 0.1
            action = "BUY"
        elif technical_score < 35:
            confidence += 0.05
            action = "HOLD"
        
        # Bollinger bands
        if bb_position > 0.8:  # Near upper band
            confidence += 0.05
            if action == "BUY":
                action = "HOLD"  # Take profits
        elif bb_position < 0.2:  # Near lower band
            confidence += 0.1
            action = "BUY"  # Potential bounce
        
        # Trend strength
        if abs(trend_strength) > 2:
            confidence += 0.05
        
        # Cap confidence
        confidence = min(confidence, 0.8)
        
        # Create feature vector
        feature_vector = [
            technical_data.get("rsi", 50),
            technical_data.get("ma_5", current_price),
            technical_data.get("ma_10", current_price),
            technical_data.get("ma_20", current_price),
            technical_data.get("bb_position", 0.5),
            technical_data.get("macd", 0),
            technical_data.get("technical_score", 50),
            technical_data.get("trend_strength", 0),
            technical_data.get("volatility", 1.0)
        ]
        
        return {
            "symbol": symbol,
            "predicted_action": action,
            "action_confidence": confidence,
            "entry_price": current_price,
            "technical_data": technical_data,
            "feature_vector": feature_vector
        }
    
    def get_default_prediction(self, symbol: str) -> Dict:
        """Default prediction when errors occur"""
        return {
            "symbol": symbol,
            "predicted_action": "HOLD",
            "action_confidence": 0.4,
            "entry_price": 0.0,
            "technical_data": self.technical_analyzer.get_default_analysis(),
            "feature_vector": [50, 0, 0, 0, 0.5, 0, 50, 0, 1.0]
        }
    
    def save_prediction(self, prediction: Dict):
        """Save prediction to database with technical data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create feature vector string
            feature_vector_str = ",".join(map(str, prediction["feature_vector"]))
            
            cursor.execute("""
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp, predicted_action,
                    action_confidence, entry_price, feature_vector, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{prediction[symbol]}_{datetime.now().strftime(%Y%m%d_%H%M%S)}",
                prediction["symbol"],
                datetime.now().isoformat(),
                prediction["predicted_action"],
                prediction["action_confidence"],
                prediction["entry_price"],
                feature_vector_str,
                "efficient_with_technical_v1.0"
            ))
            
            conn.commit()
            conn.close()
            
            self.log_message(f"✅ Saved prediction for {prediction[symbol]}: {prediction[predicted_action]} (confidence: {prediction[action_confidence]:.3f})")
            
        except Exception as e:
            self.log_message(f"⚠️ Error saving prediction for {prediction[symbol]}: {e}")
    
    def run_predictions(self):
        """Run predictions for all symbols"""
        if not self.is_market_hours():
            aest_time = datetime.now().strftime("%H:%M AEST")
            self.log_message(f"⏰ Outside market hours (current: {aest_time[:2]}:xx AEST)")
            self.log_message("🕐 Skipping prediction cycle - outside market hours")
            return
        
        self.log_message("🚀 Starting enhanced prediction cycle with technical analysis")
        
        predictions_made = 0
        
        for symbol in self.symbols:
            try:
                prediction = self.make_prediction_with_technical(symbol)
                self.save_prediction(prediction)
                predictions_made += 1
                
                # Log technical insights
                tech_data = prediction["technical_data"]
                self.log_message(f"📊 {symbol} Technical: RSI={tech_data.get(rsi, 0):.1f}, Score={tech_data.get(technical_score, 0):.1f}, Trend={tech_data.get(trend_strength, 0):.1f}%")
                
            except Exception as e:
                self.log_message(f"⚠️ Error processing {symbol}: {e}")
            
            # Clear memory after each symbol
            gc.collect()
        
        self.log_message(f"✅ Completed predictions for {predictions_made}/{len(self.symbols)} symbols")
        self.log_message(f"💾 Memory efficient cycle completed - technical analysis included")

def main():
    """Main function"""
    try:
        system = EfficientPredictionSystemWithTechnical()
        system.run_predictions()
    except Exception as e:
        print(f"❌ System error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
