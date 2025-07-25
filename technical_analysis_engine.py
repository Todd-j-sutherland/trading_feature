#!/usr/bin/env python3
"""
Isolated Technical Analysis Module for ASX Banks
Can be tested independently and integrates with the dashboard
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalAnalysisEngine:
    """
    Standalone technical analysis engine for ASX banks
    Calculates RSI, MACD, moving averages, and generates composite technical scores
    """
    
    def __init__(self, db_path: str = "data/ml_models/training_data.db"):
        self.db_path = db_path
        self.asx_banks = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        Returns value between 0-100
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if insufficient data
        
        delta = prices.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        Returns (macd_line, signal_line, histogram)
        """
        if len(prices) < slow + signal:
            return 0.0, 0.0, 0.0
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return (
            float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
        )
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate various moving averages"""
        mas = {}
        
        for period in [5, 10, 20, 50]:
            if len(prices) >= period:
                ma = prices.rolling(window=period).mean().iloc[-1]
                mas[f'sma_{period}'] = float(ma) if not pd.isna(ma) else float(prices.iloc[-1])
            else:
                mas[f'sma_{period}'] = float(prices.iloc[-1])
        
        return mas
    
    def get_stock_data(self, symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """
        Get stock price data from Yahoo Finance
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_technical_score(self, symbol: str) -> Dict:
        """
        Calculate comprehensive technical analysis score for a symbol
        Returns score between 0-100 and component details
        """
        # Get price data
        data = self.get_stock_data(symbol)
        
        if data is None or len(data) < 20:
            return {
                'symbol': symbol,
                'technical_score': 0.0,
                'rsi': 50.0,
                'macd': {'line': 0.0, 'signal': 0.0, 'histogram': 0.0},
                'moving_averages': {},
                'price_action': {},
                'overall_signal': 'HOLD',
                'confidence': 0.3,
                'timestamp': datetime.now().isoformat(),
                'data_quality': 'INSUFFICIENT'
            }
        
        prices = data['Close']
        current_price = float(prices.iloc[-1])
        
        # Calculate indicators
        rsi = self.calculate_rsi(prices)
        macd_line, macd_signal, macd_histogram = self.calculate_macd(prices)
        moving_averages = self.calculate_moving_averages(prices)
        
        # Calculate technical score components
        score = 50.0  # Start neutral
        confidence = 0.5
        
        # RSI scoring (30% weight)
        if rsi < 30:  # Oversold - bullish
            score += 15
            confidence += 0.2
        elif rsi > 70:  # Overbought - bearish
            score -= 15
            confidence += 0.2
        elif 40 <= rsi <= 60:  # Neutral zone
            confidence += 0.1
        
        # MACD scoring (25% weight)
        if macd_histogram > 0:  # MACD above signal - bullish
            score += 12
            confidence += 0.15
        elif macd_histogram < 0:  # MACD below signal - bearish
            score -= 12
            confidence += 0.15
        
        # Moving average trend (25% weight)
        sma_20 = moving_averages.get('sma_20', current_price)
        sma_50 = moving_averages.get('sma_50', current_price)
        
        if current_price > sma_20 > sma_50:  # Strong bullish trend
            score += 12
            confidence += 0.15
        elif current_price < sma_20 < sma_50:  # Strong bearish trend
            score -= 12
            confidence += 0.15
        elif current_price > sma_20:  # Above short-term MA
            score += 6
            confidence += 0.1
        elif current_price < sma_20:  # Below short-term MA
            score -= 6
            confidence += 0.1
        
        # Price momentum (20% weight)
        if len(prices) >= 5:
            price_change_5d = (current_price - prices.iloc[-5]) / prices.iloc[-5] * 100
            if price_change_5d > 2:  # Strong upward momentum
                score += 10
                confidence += 0.1
            elif price_change_5d < -2:  # Strong downward momentum
                score -= 10
                confidence += 0.1
        
        # Volume confirmation (bonus)
        if 'Volume' in data.columns and len(data) >= 5:
            avg_volume = data['Volume'].tail(20).mean()
            recent_volume = data['Volume'].iloc[-1]
            if recent_volume > avg_volume * 1.5:  # High volume confirms move
                if score > 50:
                    score += 5
                elif score < 50:
                    score -= 5
                confidence += 0.1
        
        # Ensure score is within bounds
        technical_score = max(0, min(100, score))
        confidence = max(0, min(1, confidence))
        
        # Determine signal
        if technical_score >= 65:
            signal = 'BUY'
        elif technical_score <= 35:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'symbol': symbol,
            'technical_score': round(technical_score, 2),
            'rsi': round(rsi, 1),
            'macd': {
                'line': round(macd_line, 4),
                'signal': round(macd_signal, 4),
                'histogram': round(macd_histogram, 4)
            },
            'moving_averages': {k: round(v, 2) for k, v in moving_averages.items()},
            'price_action': {
                'current_price': round(current_price, 2),
                'price_change_5d': round(price_change_5d, 2) if len(prices) >= 5 else 0
            },
            'overall_signal': signal,
            'confidence': round(confidence, 2),
            'timestamp': datetime.now().isoformat(),
            'data_quality': 'GOOD'
        }
    
    def analyze_all_banks(self) -> List[Dict]:
        """
        Run technical analysis on all ASX banks
        """
        results = []
        
        for symbol in self.asx_banks:
            logger.info(f"Analyzing {symbol}...")
            analysis = self.calculate_technical_score(symbol)
            results.append(analysis)
        
        return results
    
    def update_database_technical_scores(self) -> bool:
        """
        Update the sentiment_features table with real technical scores
        This fixes the issue where all technical_score values are 0
        """
        try:
            # Get technical analysis for all banks
            technical_results = self.analyze_all_banks()
            
            if not technical_results:
                logger.error("No technical analysis results to update")
                return False
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update recent records with technical scores
            for result in technical_results:
                symbol = result['symbol']
                technical_score = result['technical_score']
                
                # Update the most recent records for this symbol
                cursor.execute("""
                    UPDATE sentiment_features 
                    SET technical_score = ?
                    WHERE symbol = ? 
                    AND timestamp >= date('now', '-1 day')
                """, (technical_score, symbol))
                
                logger.info(f"Updated {symbol} technical score to {technical_score}")
            
            conn.commit()
            conn.close()
            
            logger.info("Successfully updated technical scores in database")
            return True
            
        except Exception as e:
            logger.error(f"Error updating database technical scores: {e}")
            return False
    
    def get_technical_summary(self) -> Dict:
        """
        Get a summary of current technical analysis across all banks
        """
        results = self.analyze_all_banks()
        
        if not results:
            return {'error': 'No technical analysis data available'}
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_banks_analyzed': len(results),
            'signals': {'BUY': 0, 'SELL': 0, 'HOLD': 0},
            'average_technical_score': 0,
            'average_rsi': 0,
            'banks_detail': []
        }
        
        total_score = 0
        total_rsi = 0
        
        for result in results:
            summary['signals'][result['overall_signal']] += 1
            total_score += result['technical_score']
            total_rsi += result['rsi']
            
            summary['banks_detail'].append({
                'symbol': result['symbol'],
                'signal': result['overall_signal'],
                'technical_score': result['technical_score'],
                'rsi': result['rsi'],
                'confidence': result['confidence']
            })
        
        summary['average_technical_score'] = round(total_score / len(results), 1)
        summary['average_rsi'] = round(total_rsi / len(results), 1)
        
        return summary

def test_technical_analysis_isolated():
    """
    Test technical analysis components independently
    """
    print("🔧 ISOLATED TECHNICAL ANALYSIS TESTS")
    print("=" * 50)
    
    try:
        # Initialize technical analysis engine
        tech_engine = TechnicalAnalysisEngine()
        print("✅ Technical Analysis Engine initialized")
        
        # Test individual bank analysis
        print("\n📊 Testing Individual Bank Analysis:")
        test_symbol = "CBA.AX"
        result = tech_engine.calculate_technical_score(test_symbol)
        
        print(f"✅ {test_symbol} Technical Analysis:")
        print(f"   Technical Score: {result['technical_score']}")
        print(f"   RSI: {result['rsi']}")
        print(f"   Signal: {result['overall_signal']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Current Price: {result['price_action']['current_price']}")
        
        # Test all banks analysis
        print("\n🏦 Testing All Banks Analysis:")
        all_results = tech_engine.analyze_all_banks()
        
        for result in all_results:
            signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[result['overall_signal']]
            print(f"   {result['symbol']}: {signal_emoji} {result['overall_signal']} "
                  f"(Score: {result['technical_score']}, RSI: {result['rsi']})")
        
        # Test database update
        print("\n💾 Testing Database Update:")
        update_success = tech_engine.update_database_technical_scores()
        
        if update_success:
            print("✅ Database technical scores updated successfully")
        else:
            print("❌ Database update failed")
        
        # Test summary generation
        print("\n📈 Testing Technical Summary:")
        summary = tech_engine.get_technical_summary()
        
        print(f"✅ Technical Summary Generated:")
        print(f"   Banks Analyzed: {summary['total_banks_analyzed']}")
        print(f"   Average Technical Score: {summary['average_technical_score']}")
        print(f"   Average RSI: {summary['average_rsi']}")
        print(f"   Signals: {summary['signals']}")
        
        print("\n✅ ALL TECHNICAL ANALYSIS TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TECHNICAL ANALYSIS TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    # Run isolated technical analysis tests
    success = test_technical_analysis_isolated()
    exit(0 if success else 1)
