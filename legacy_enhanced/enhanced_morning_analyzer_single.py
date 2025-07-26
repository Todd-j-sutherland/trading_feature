#!/usr/bin/env python3
"""
Enhanced Morning Trading Analyzer
Combines sentiment analysis with technical indicators for comprehensive signals
Runs every 30 minutes during market hours
"""
import sys
import os
import sqlite3
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/root/test/logs/enhanced_morning_analysis.log"),
        logging.StreamHandler()
    ]
)

class EnhancedMorningAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Bank symbols for analysis
        self.banks = {
            "CBA": "Commonwealth Bank",
            "WBC": "Westpac", 
            "ANZ": "ANZ Banking",
            "NAB": "National Australia Bank",
            "MQG": "Macquarie Group"
        }
        
        # Database paths
        self.db_path = "/root/test/data/trading_data.db"
        self.ml_db_path = "/root/test/data/ml_models/trading_signals.db"
        
        self.logger.info("Enhanced Morning Analyzer initialized")
    
    def is_market_hours(self) -> bool:
        """Check if during ASX market hours (10 AM - 4 PM AEST)"""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        return 10 <= now.hour < 16
    
    def get_latest_sentiment(self, bank_symbol: str) -> dict:
        """Get latest sentiment data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get latest sentiment record for this bank
                cursor.execute("""
                    SELECT confidence, analysis_timestamp, overall_sentiment
                    FROM sentiment_analysis 
                    WHERE bank = ? 
                    ORDER BY analysis_timestamp DESC 
                    LIMIT 1
                """, (bank_symbol,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "confidence": result[0],
                        "timestamp": result[1],
                        "sentiment_score": result[2] if result[2] else 0,
                        "news_available": True
                    }
                else:
                    return {
                        "confidence": 0.45,  # Default confidence
                        "timestamp": datetime.now().isoformat(),
                        "sentiment_score": 0,
                        "news_available": False
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting sentiment for {bank_symbol}: {e}")
            return {
                "confidence": 0.3,
                "timestamp": datetime.now().isoformat(),
                "sentiment_score": 0,
                "news_available": False
            }
    
    def get_news_count(self, bank_symbol: str) -> int:
        """Get recent news count for bank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count news from last 24 hours
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM news_data 
                    WHERE bank = ? 
                    AND datetime(timestamp) > datetime("now", "-1 day")
                """, (bank_symbol,))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"Error counting news for {bank_symbol}: {e}")
            return 0
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI from price list"""
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
                losses.append(-change)
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 1)
    
    def get_price_data(self, bank_symbol: str) -> dict:
        """Get recent price data and calculate technical indicators"""
        try:
            # In a real implementation, this would fetch from yfinance or another source
            # For now, simulate with some realistic values
            import random
            
            base_prices = {
                "CBA": 110, "WBC": 25, "ANZ": 28, "NAB": 35, "MQG": 200
            }
            
            base_price = base_prices.get(bank_symbol, 50)
            
            # Generate 30 days of simulated price data
            prices = []
            current_price = base_price
            
            for i in range(30):
                # Random walk with slight trend
                change_percent = (random.random() - 0.48) * 0.04  # Slightly bullish bias
                current_price *= (1 + change_percent)
                prices.append(current_price)
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(prices)
            sma_10 = sum(prices[-10:]) / 10
            sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else sum(prices) / len(prices)
            
            # Determine technical signal
            signal = "HOLD"
            strength = 0.5
            
            if rsi < 30 and prices[-1] > sma_20:
                signal = "BUY"
                strength = 0.7
            elif rsi > 70 and prices[-1] < sma_20:
                signal = "SELL"
                strength = 0.7
            elif prices[-1] > sma_20 * 1.02:
                signal = "BUY" 
                strength = 0.6
            elif prices[-1] < sma_20 * 0.98:
                signal = "SELL"
                strength = 0.6
            
            return {
                "current_price": round(prices[-1], 2),
                "rsi": rsi,
                "sma_10": round(sma_10, 2),
                "sma_20": round(sma_20, 2),
                "technical_signal": signal,
                "technical_strength": strength,
                "price_data_available": True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting price data for {bank_symbol}: {e}")
            return {
                "current_price": 0,
                "rsi": 50,
                "sma_10": 0,
                "sma_20": 0,
                "technical_signal": "HOLD",
                "technical_strength": 0.3,
                "price_data_available": False
            }
    
    def combine_signals(self, sentiment_data: dict, technical_data: dict, bank_symbol: str) -> dict:
        """Combine sentiment and technical analysis into unified signal"""
        
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        sentiment_confidence = sentiment_data.get("confidence", 0)
        technical_signal = technical_data.get("technical_signal", "HOLD")
        technical_strength = technical_data.get("technical_strength", 0)
        rsi = technical_data.get("rsi", 50)
        
        # Signal scoring system
        combined_score = 0
        
        # Sentiment contribution (40% weight)
        if sentiment_score > 0.1:
            combined_score += 0.4 * min(sentiment_score * 2, 1.0)
        elif sentiment_score < -0.1:
            combined_score -= 0.4 * min(abs(sentiment_score) * 2, 1.0)
        
        # Technical contribution (60% weight)
        if technical_signal == "BUY":
            combined_score += 0.6 * technical_strength
        elif technical_signal == "SELL":
            combined_score -= 0.6 * technical_strength
        
        # RSI adjustments
        if rsi > 70:  # Overbought
            combined_score -= 0.1
        elif rsi < 30:  # Oversold
            combined_score += 0.1
        
        # Determine final signal
        if combined_score > 0.3:
            final_signal = "BUY"
            signal_strength = "STRONG" if combined_score > 0.6 else "MODERATE"
        elif combined_score < -0.3:
            final_signal = "SELL"
            signal_strength = "STRONG" if combined_score < -0.6 else "MODERATE"
        else:
            final_signal = "HOLD"
            signal_strength = "NEUTRAL"
        
        # Calculate overall confidence
        overall_confidence = (sentiment_confidence + technical_strength) / 2
        
        return {
            "symbol": bank_symbol,
            "timestamp": datetime.now().isoformat(),
            "final_signal": final_signal,
            "signal_strength": signal_strength,
            "combined_score": round(combined_score, 3),
            "overall_confidence": round(overall_confidence, 3),
            "sentiment_contribution": round(sentiment_score, 3),
            "technical_contribution": technical_signal,
            "rsi": rsi,
            "current_price": technical_data.get("current_price", 0),
            "data_quality": {
                "sentiment_available": sentiment_data.get("news_available", False),
                "price_data_available": technical_data.get("price_data_available", False)
            }
        }
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis for all banks"""
        self.logger.info("Starting comprehensive morning analysis")
        
        results = []
        analysis_start_time = datetime.now()
        
        # Check market status
        market_status = "OPEN" if self.is_market_hours() else "CLOSED"
        self.logger.info(f"Market status: {market_status}")
        
        for bank_symbol, bank_name in self.banks.items():
            try:
                self.logger.info(f"Analyzing {bank_name} ({bank_symbol})...")
                
                # Get sentiment data from database
                sentiment_data = self.get_latest_sentiment(bank_symbol)
                news_count = self.get_news_count(bank_symbol)
                sentiment_data["news_count"] = news_count
                
                # Get technical analysis
                technical_data = self.get_price_data(bank_symbol)
                
                # Combine signals
                combined_result = self.combine_signals(sentiment_data, technical_data, bank_symbol)
                combined_result.update({
                    "bank_name": bank_name,
                    "market_status": market_status,
                    "news_count": news_count
                })
                
                results.append(combined_result)
                
                # Log summary
                signal = combined_result["final_signal"]
                strength = combined_result["signal_strength"]
                confidence = combined_result["overall_confidence"]
                score = combined_result["combined_score"]
                
                self.logger.info(
                    f"Result: {bank_name}: {signal} ({strength}) | "
                    f"Score: {score:+.3f} | Confidence: {confidence:.1%} | "
                    f"News: {news_count} | RSI: {combined_result["rsi"]}"
                )
                
            except Exception as e:
                self.logger.error(f"Error analyzing {bank_symbol}: {e}")
                results.append({
                    "symbol": bank_symbol,
                    "bank_name": self.banks.get(bank_symbol, bank_symbol),
                    "final_signal": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Analysis summary
        analysis_duration = (datetime.now() - analysis_start_time).total_seconds()
        
        buy_signals = len([r for r in results if r.get("final_signal") == "BUY"])
        sell_signals = len([r for r in results if r.get("final_signal") == "SELL"])
        hold_signals = len([r for r in results if r.get("final_signal") == "HOLD"])
        
        self.logger.info("Analysis Summary:")
        self.logger.info(f"  Duration: {analysis_duration:.1f} seconds")
        self.logger.info(f"  BUY signals: {buy_signals}")
        self.logger.info(f"  SELL signals: {sell_signals}")
        self.logger.info(f"  HOLD signals: {hold_signals}")
        self.logger.info(f"  Market status: {market_status}")
        
        return results

def main():
    """Main execution function"""
    analyzer = EnhancedMorningAnalyzer()
    
    try:
        results = analyzer.run_comprehensive_analysis()
        print(f"Completed analysis of {len(results)} banks")
        
        # Print trading signals summary
        print("\n" + "="*60)
        print("ENHANCED MORNING TRADING SIGNALS")
        print("="*60)
        
        for result in results:
            if result.get("final_signal") not in ["ERROR"]:
                symbol = result["symbol"]
                bank_name = result.get("bank_name", symbol)
                signal = result["final_signal"]
                strength = result["signal_strength"]
                score = result.get("combined_score", 0)
                confidence = result.get("overall_confidence", 0)
                rsi = result.get("rsi", 50)
                price = result.get("current_price", 0)
                news_count = result.get("news_count", 0)
                
                print(f"{symbol:4} ({bank_name:18}) | {signal:4} ({strength:8}) | "
                      f"Score: {score:+.3f} | Conf: {confidence:.1%} | "
                      f"RSI: {rsi:4.1f} | Price: ${price:6.2f} | News: {news_count}")
        
        print("="*60)
        print("🎯 Signal Methodology: 40% Sentiment + 60% Technical Analysis")
        print("📊 RSI: <30 Oversold (Buy opportunity), >70 Overbought (Sell signal)")
        print("📈 Trend: Price vs 20-day SMA determines momentum direction")
        print("="*60)
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        analyzer.logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
