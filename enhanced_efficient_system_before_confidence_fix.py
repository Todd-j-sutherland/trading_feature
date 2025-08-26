#!/usr/bin/env python3
"""
Enhanced Efficient Prediction System with Technical Analysis
Memory-optimized version that includes technical indicators
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
    """Lightweight technical analysis"""
    
    def get_prices(self, symbol: str, days: int = 30):
        """Get historical prices"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            return hist["Close"].tolist() if not hist.empty else []
        except:
            return []
    
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
        """Get technical analysis"""
        prices = self.get_prices(symbol)
        
        if not prices:
            return {
                "rsi": 50.0,
                "tech_score": 50.0,
                "ma5": 0,
                "ma20": 0,
                "current_price": 0,
                "feature_vector": "50,50,0,0,0,0,0,0,0"
            }
        
        current = prices[-1]
        rsi = self.calculate_rsi(prices)
        
        # Moving averages
        ma5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else current
        ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current
        
        # Technical score
        score = 50
        if ma5 > ma20 * 1.01:
            score += 15
        if 60 < rsi < 80:
            score += 10
        elif rsi < 30:
            score += 5
        
        score = max(0, min(100, score))
        
        # Feature vector (9 components)
        momentum = ((current - prices[-3]) / prices[-3] * 100) if len(prices) >= 3 else 0
        volatility = sum(abs((prices[i] - prices[i-1]) / prices[i-1]) for i in range(-5, 0)) / 5 * 100 if len(prices) >= 5 else 1
        
        feature_vector = f"{rsi:.1f},{score:.1f},{ma5:.2f},{ma20:.2f},{current:.2f},{momentum:.2f},{volatility:.2f},{65.0},{45.0}"
        
        return {
            "rsi": rsi,
            "tech_score": score,
            "ma5": ma5,
            "ma20": ma20,
            "current_price": current,
            "feature_vector": feature_vector
        }

class EnhancedEfficientPredictionSystem:
    """Enhanced prediction system with technical analysis"""
    
    def __init__(self):
        self.symbols = ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "MQG.AX"]
        self.db_path = "predictions.db"
        self.technical = TechnicalAnalyzer()
        
    def is_market_hours(self):
        """Check if ASX is open"""
        try:
            import pytz
            aest = pytz.timezone("Australia/Sydney")
            now_aest = datetime.now(aest)
            
            if now_aest.weekday() >= 5:
                return False
            
            hour = now_aest.hour
            return 10 <= hour < 16
            
        except ImportError:
            from datetime import timezone, timedelta
            aest_offset = timedelta(hours=11)
            now_aest = datetime.now(timezone.utc) + aest_offset
            
            if now_aest.weekday() >= 5:
                return False
                
            hour = now_aest.hour
            return 10 <= hour < 16
    
    def log_message(self, message: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        try:
            with open("efficient_prediction_log.txt", "a") as f:
                f.write(log_entry + "\n")
        except:
            pass
    
    def make_prediction(self, symbol: str):
        """Make prediction with technical analysis"""
        try:
            # Get technical analysis
            tech_data = self.technical.analyze(symbol)
            
            # Prediction logic
            rsi = tech_data["rsi"]
            tech_score = tech_data["tech_score"]
            current_price = tech_data["current_price"]
            
            # Decision logic
            confidence = 0.4
            action = "HOLD"
            
            if tech_score > 65 and rsi > 50:
                action = "BUY"
                confidence = 0.6 + (tech_score - 65) / 100
            elif tech_score < 40:
                action = "HOLD"
                confidence = 0.5
            elif 30 < rsi < 70 and tech_score > 55:
                action = "BUY"
                confidence = 0.5 + (tech_score - 55) / 200
            
            confidence = min(confidence, 0.8)

            # Calculate missing fields
            predicted_direction = 1 if action == "BUY" else (-1 if action == "SELL" else 0)
            
            # Calculate predicted magnitude based on technical strength
            magnitude = 0.0
            if action == "BUY":
                magnitude = (tech_score - 50) / 100 * 0.05  # Up to 5% expected change
            elif action == "SELL":
                magnitude = (50 - tech_score) / 100 * 0.05  # Up to 5% expected change
            
            # Determine optimal action (enhanced recommendation)
            optimal_action = action
            if tech_score > 75 and confidence > 0.7:
                optimal_action = "STRONG_" + action
            elif tech_score < 40 and confidence > 0.6:
                optimal_action = "STRONG_HOLD"
            
            return {
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "price": current_price,
                "predicted_direction": predicted_direction,
                "predicted_magnitude": magnitude,
                "optimal_action": optimal_action,
                "feature_vector": tech_data["feature_vector"],
                "tech_data": tech_data
            }
            
        except Exception as e:
            self.log_message(f"Error predicting {symbol}: {e}")
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0.4,
                "price": 0.0,
                "feature_vector": "50,50,0,0,0,0,0,0,0",
                "tech_data": {}
            }
    
    def save_prediction(self, prediction):
        """Save to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            prediction_id = prediction["symbol"] + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            
            cursor.execute("""
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp, predicted_action,
                    action_confidence, predicted_direction, predicted_magnitude,
                    feature_vector, model_version, entry_price, optimal_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id,
                prediction["symbol"],
                datetime.now().isoformat(),
                prediction["action"],
                prediction["confidence"],
                prediction["predicted_direction"],
                prediction["predicted_magnitude"],
                prediction["feature_vector"],
                "enhanced_efficient_v1.0",
                prediction["price"],
                prediction["optimal_action"]
            ))
            
            conn.commit()
            conn.close()
            
            tech_data = prediction.get("tech_data", {})
            rsi = tech_data.get("rsi", 0)
            tech_score = tech_data.get("tech_score", 0)
            
            self.log_message(f"✅ {prediction["symbol"]}: {prediction["action"]} (conf: {prediction["confidence"]:.3f}, RSI: {rsi:.1f}, Tech: {tech_score:.1f})")
            
        except Exception as e:
            self.log_message(f"Error saving {prediction["symbol"]}: {e}")
    
    def run_predictions(self):
        """Main prediction cycle"""
        if not self.is_market_hours():
            aest_time = datetime.now().strftime("%H:%M AEST")
            self.log_message(f"⏰ Outside market hours (current: {aest_time[:2]}:xx AEST)")
            self.log_message("🕐 Skipping prediction cycle - outside market hours")
            return
        
        self.log_message("🚀 Starting enhanced prediction cycle with technical analysis")
        
        predictions_made = 0
        
        for symbol in self.symbols:
            try:
                prediction = self.make_prediction(symbol)
                self.save_prediction(prediction)
                predictions_made += 1
                
                # Force garbage collection
                gc.collect()
                
            except Exception as e:
                self.log_message(f"Error processing {symbol}: {e}")
        
        self.log_message(f"✅ Enhanced predictions completed: {predictions_made}/{len(self.symbols)} symbols")
        self.log_message("💾 Technical analysis included - memory optimized")

def main():
    """Main function"""
    try:
        system = EnhancedEfficientPredictionSystem()
        system.run_predictions()
    except Exception as e:
        print(f"System error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
