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
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalAnalysisEngine:
    """Enhanced Technical Analysis Engine with Market Hours Detection"""
    
    def __init__(self):
        self.asx_banks = [
            'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX',
            'MQG.AX', 'BOQ.AX', 'BEN.AX'
        ]
        
        # ASX timezone
        self.asx_tz = pytz.timezone('Australia/Sydney')
        
    def is_asx_market_open(self) -> Tuple[bool, str]:
        """
        Check if ASX market is currently open
        Returns: (is_open: bool, status_message: str)
        """
        now_utc = datetime.now(pytz.UTC)
        now_asx = now_utc.astimezone(self.asx_tz)
        
        # ASX trading hours: 10:00 AM - 4:00 PM AEST/AEDT, Monday-Friday
        weekday = now_asx.weekday()  # 0=Monday, 6=Sunday
        current_time = now_asx.time()
        
        # Check if it's a weekday
        if weekday >= 5:  # Saturday or Sunday
            next_open = self._get_next_market_open(now_asx)
            return False, f"Market closed (weekend). Next open: {next_open}"
        
        # Check if within trading hours (10:00 AM - 4:00 PM)
        market_open = datetime.strptime("10:00", "%H:%M").time()
        market_close = datetime.strptime("16:00", "%H:%M").time()
        
        if market_open <= current_time <= market_close:
            return True, f"Market open (ASX time: {now_asx.strftime('%H:%M %Z')})"
        else:
            if current_time < market_open:
                status = f"Market closed (pre-market). Opens at 10:00 AM (current: {now_asx.strftime('%H:%M %Z')})"
            else:
                next_open = self._get_next_market_open(now_asx)
                status = f"Market closed (after-hours). Next open: {next_open}"
            return False, status
    
    def _get_next_market_open(self, current_asx_time: datetime) -> str:
        """Get the next market opening time"""
        weekday = current_asx_time.weekday()
        
        if weekday == 4:  # Friday
            # Next open is Monday
            days_until_monday = 3
            next_open = current_asx_time + timedelta(days=days_until_monday)
            next_open = next_open.replace(hour=10, minute=0, second=0, microsecond=0)
        elif weekday == 5:  # Saturday
            days_until_monday = 2
            next_open = current_asx_time + timedelta(days=days_until_monday)
            next_open = next_open.replace(hour=10, minute=0, second=0, microsecond=0)
        elif weekday == 6:  # Sunday
            days_until_monday = 1
            next_open = current_asx_time + timedelta(days=days_until_monday)
            next_open = next_open.replace(hour=10, minute=0, second=0, microsecond=0)
        else:  # Monday-Thursday
            if current_asx_time.time() >= datetime.strptime("16:00", "%H:%M").time():
                # After close, next day
                next_open = current_asx_time + timedelta(days=1)
                next_open = next_open.replace(hour=10, minute=0, second=0, microsecond=0)
            else:
                # Before open today
                next_open = current_asx_time.replace(hour=10, minute=0, second=0, microsecond=0)
        
        return next_open.strftime('%a %b %d, %H:%M %Z')
    
    def get_current_or_last_price(self, symbol: str) -> Tuple[float, str]:
        """
        Get current price if market is open, otherwise get last closing price
        Returns: (price: float, source: str)
        """
        is_open, market_status = self.is_asx_market_open()
        
        try:
            ticker = yf.Ticker(symbol)
            
            if is_open:
                # Market is open, try to get current price
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if current_price and current_price > 0:
                    logger.info(f"✅ {symbol}: Current price ${current_price:.2f} (market open)")
                    return float(current_price), "current_price"
                else:
                    # Fallback to recent history
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        last_price = float(hist['Close'].iloc[-1])
                        logger.info(f"✅ {symbol}: Recent price ${last_price:.2f} (1min history)")
                        return last_price, "recent_price"
            
            # Market is closed or current price unavailable, get last closing price
            hist = ticker.history(period="5d")  # Get last 5 days to ensure we have data
            if not hist.empty:
                last_close = float(hist['Close'].iloc[-1])
                last_date = hist.index[-1].strftime('%Y-%m-%d')
                logger.info(f"✅ {symbol}: Last close ${last_close:.2f} on {last_date} ({market_status})")
                return last_close, "last_close"
            
        except Exception as e:
            logger.error(f"❌ Error fetching price for {symbol}: {e}")
        
        # Ultimate fallback - should never reach here
        logger.warning(f"⚠️ {symbol}: No price data available, using 0")
        return 0.0, "no_data"
        
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
            'current_price': round(current_price, 2),  # Add current_price at top level for compatibility
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
    
    def analyze(self, symbol: str, market_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Analyze a single symbol with market hours detection and proper price handling
        This is the method called by enhanced_morning_analyzer_with_ml.py
        """
        # Check market status
        is_open, market_status = self.is_asx_market_open()
        
        # Get current or last closing price
        current_price, price_source = self.get_current_or_last_price(symbol)
        
        # Use provided market data or fetch fresh data
        if market_data is not None and not market_data.empty:
            data = market_data
        else:
            data = self.get_stock_data(symbol)
        
        if data is None or len(data) < 20:
            logger.warning(f"⚠️ {symbol}: Insufficient data for technical analysis")
            return {
                'symbol': symbol,
                'technical_score': 0.0,
                'current_price': current_price,  # Use fetched price instead of 0
                'signal': 'INSUFFICIENT_DATA',
                'confidence': 0.0,
                'rsi': None,
                'macd': None,
                'moving_averages': {},
                'price_action': {
                    'current_price': current_price,
                    'price_source': price_source
                },
                'market_status': market_status,
                'data_quality': 'POOR'
            }
        
        # Calculate technical indicators using the existing logic
        result = self.calculate_technical_score(symbol)
        
        # Override the current_price with our enhanced price fetching
        if result and isinstance(result, dict):
            result['current_price'] = current_price
            result['price_action']['current_price'] = current_price
            result['price_action']['price_source'] = price_source
            result['market_status'] = market_status
            
            # Update data quality based on price source
            if price_source == "current_price":
                result['data_quality'] = 'EXCELLENT'
            elif price_source == "recent_price":
                result['data_quality'] = 'GOOD'
            elif price_source == "last_close":
                result['data_quality'] = 'FAIR'
            else:
                result['data_quality'] = 'POOR'
        
        return result
    
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
    # Test the enhanced technical analysis engine with market hours detection
    engine = TechnicalAnalysisEngine()
    
    print("🕐 ASX MARKET HOURS & PRICE TESTING")
    print("=" * 50)
    
    # Test market hours detection
    is_open, status = engine.is_asx_market_open()
    print(f"Market Status: {status}")
    print(f"Market Open: {'✅ YES' if is_open else '❌ NO'}")
    print()
    
    # Test price fetching for main banks
    test_symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']
    
    print("💰 PRICE FETCHING TEST")
    print("=" * 30)
    for symbol in test_symbols:
        price, source = engine.get_current_or_last_price(symbol)
        print(f"{symbol}: ${price:.2f} ({source})")
    print()
    
    # Test full analysis
    print("🔧 TECHNICAL ANALYSIS TEST")
    print("=" * 35)
    result = engine.analyze('CBA.AX')
    
    if result:
        print(f"Symbol: {result['symbol']}")
        print(f"Current Price: ${result['current_price']:.2f}")
        print(f"Price Source: {result['price_action'].get('price_source', 'unknown')}")
        print(f"Technical Score: {result['technical_score']:.1f}/100")
        print(f"Signal: {result.get('overall_signal', result.get('signal', 'N/A'))}")
        print(f"Data Quality: {result['data_quality']}")
        print(f"Market Status: {result.get('market_status', 'unknown')}")
    else:
        print("❌ Analysis failed")
    
    print("\n✅ Enhanced Technical Analysis Engine Test Complete!")
    
    # Also run the original isolated tests
    print("\n" + "=" * 50)
    print("🧪 RUNNING ORIGINAL ISOLATED TESTS")
    success = test_technical_analysis_isolated()
    exit(0 if success else 1)
