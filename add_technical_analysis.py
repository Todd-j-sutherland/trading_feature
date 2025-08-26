#!/usr/bin/env python3
"""
Add technical analysis to existing efficient prediction system
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import warnings
warnings.filterwarnings("ignore")

class TechnicalAnalysis:
    """Simple technical analysis for predictions"""
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[float]:
        """Get historical price data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return []
            
            return hist[Close].tolist()
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return []
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
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
    
    def calculate_technical_score(self, prices: List[float]) -> float:
        """Calculate overall technical score"""
        if len(prices) < 5:
            return 50.0
        
        score = 50  # Start neutral
        current = prices[-1]
        
        # Simple moving average trend
        if len(prices) >= 5:
            ma5 = sum(prices[-5:]) / 5
            if current > ma5 * 1.02:  # 2% above MA5
                score += 20
            elif current < ma5 * 0.98:  # 2% below MA5
                score -= 10
        
        # RSI component
        rsi = self.calculate_rsi(prices)
        if 60 < rsi < 80:
            score += 15
        elif 20 < rsi < 40:
            score -= 10
        elif rsi > 80:
            score -= 5  # Overbought
        elif rsi < 20:
            score += 10  # Oversold bounce potential
        
        # Price momentum
        if len(prices) >= 3:
            momentum = ((current - prices[-3]) / prices[-3]) * 100
            if momentum > 1:
                score += 10
            elif momentum < -1:
                score -= 10
        
        return max(0, min(100, score))
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """Get technical analysis for symbol"""
        prices = self.get_historical_data(symbol)
        
        if not prices:
            return {
                "rsi": 50.0,
                "technical_score": 50.0,
                "ma_5": 0,
                "ma_20": 0,
                "trend": "NEUTRAL",
                "feature_vector": "50,50,0,0,0,0,0,0,0"
            }
        
        current = prices[-1]
        rsi = self.calculate_rsi(prices)
        tech_score = self.calculate_technical_score(prices)
        
        # Moving averages
        ma5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else current
        ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current
        
        # Trend determination
        if ma5 > ma20 * 1.01 and rsi > 55:
            trend = "BULLISH"
        elif ma5 < ma20 * 0.99 and rsi < 45:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
        
        # Create feature vector
        volatility = self.calculate_volatility(prices)
        momentum = self.calculate_momentum(prices)
        
        feature_vector = f"{rsi:.1f},{tech_score:.1f},{ma5:.2f},{ma20:.2f},{current:.2f},{volatility:.2f},{momentum:.2f},{55.0},{45.0}"
        
        return {
            "rsi": rsi,
            "technical_score": tech_score,
            "ma_5": ma5,
            "ma_20": ma20,
            "trend": trend,
            "feature_vector": feature_vector,
            "current_price": current
        }
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < 5:
            return 1.0
        
        changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, min(6, len(prices)))]
        return sum(abs(c) for c in changes) / len(changes) * 100
    
    def calculate_momentum(self, prices: List[float]) -> float:
        """Calculate price momentum"""
        if len(prices) < 3:
            return 0.0
        
        return ((prices[-1] - prices[-3]) / prices[-3]) * 100

# Test the technical analysis
if __name__ == "__main__":
    ta = TechnicalAnalysis()
    for symbol in ["CBA.AX", "WBC.AX"]:
        result = ta.analyze_symbol(symbol)
        print(f"{symbol}: RSI={result[rsi]:.1f}, Score={result[technical_score]:.1f}, Trend={result[trend]}")
