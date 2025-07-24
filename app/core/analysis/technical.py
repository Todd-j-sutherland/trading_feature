# src/technical_analysis.py
"""
Technical Analysis Module for ASX Trading System
Simple indicators to start with, expandable for momentum analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from app.config.settings import Settings

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """
    Simple technical analysis with basic indicators
    Can be expanded to include more complex momentum indicators
    """
    
    def __init__(self, settings: Settings):
        # Basic indicator settings - can be expanded
        self.settings = settings.TECHNICAL_INDICATORS
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Perform technical analysis on price data
        Returns analysis with momentum indicators
        """
        if data.empty or len(data) < 20:
            return self._empty_analysis(symbol)
        
        try:
            # Calculate indicators
            indicators = self._calculate_indicators(data)
            
            # Generate signals
            signals = self._generate_signals(indicators, data)
            
            # Calculate momentum
            momentum = self._calculate_momentum(data, indicators)
            
            # Determine trend
            trend = self._determine_trend(indicators, data)
            
            # Overall signal strength
            overall_signal = self._calculate_overall_signal(signals)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(data['Close'].iloc[-1]),
                'indicators': indicators,
                'signals': signals,
                'momentum': momentum,
                'trend': trend,
                'overall_signal': overall_signal,
                'signal_strength': self._calculate_signal_strength(signals),
                'recommendation': self._get_recommendation(overall_signal, momentum)
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {str(e)}")
            return self._empty_analysis(symbol)
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate basic technical indicators"""
        indicators = {}
        
        # RSI - Relative Strength Index
        indicators['rsi'] = self._calculate_rsi(data['Close'])
        
        # MACD - Moving Average Convergence Divergence
        macd, signal, histogram = self._calculate_macd(data['Close'])
        indicators['macd'] = {
            'line': macd,
            'signal': signal,
            'histogram': histogram
        }
        
        # Moving Averages
        indicators['sma'] = {}
        for period in self.settings['SMA']['periods']:
            indicators['sma'][f'sma_{period}'] = self._calculate_sma(data['Close'], period)
        
        indicators['ema'] = {}
        for period in self.settings['EMA']['periods']:
            indicators['ema'][f'ema_{period}'] = self._calculate_ema(data['Close'], period)
        
        # Volume analysis
        indicators['volume'] = self._calculate_volume_indicators(data)
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI - measures momentum"""
        if len(prices) < period:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        """Calculate MACD - trend and momentum indicator"""
        if len(prices) < 26:
            return 0.0, 0.0, 0.0
        
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        
        return (
            float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
        )
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        
        sma = prices.rolling(window=period).mean()
        return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else float(prices.iloc[-1])
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        
        ema = prices.ewm(span=period).mean()
        return float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else float(prices.iloc[-1])
    
    def _calculate_volume_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate volume-based indicators"""
        if 'Volume' not in data.columns or len(data) < 20:
            return {'current': 0, 'average': 0, 'ratio': 1}
        
        current_volume = float(data['Volume'].iloc[-1])
        avg_volume = float(data['Volume'].rolling(window=20).mean().iloc[-1])
        
        return {
            'current': current_volume,
            'average': avg_volume,
            'ratio': current_volume / avg_volume if avg_volume > 0 else 1
        }
    
    def _calculate_momentum(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """
        Calculate momentum indicators - key for momentum trading
        """
        current_price = float(data['Close'].iloc[-1])
        
        # Price momentum (rate of change)
        price_change_1d = ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100 if len(data) >= 2 else 0
        price_change_5d = ((current_price - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100 if len(data) >= 6 else 0
        price_change_20d = ((current_price - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100 if len(data) >= 21 else 0
        
        # RSI momentum
        rsi = indicators['rsi']
        rsi_momentum = 'bullish' if rsi > 50 else 'bearish' if rsi < 50 else 'neutral'
        
        # MACD momentum
        macd_histogram = indicators['macd']['histogram']
        macd_momentum = 'bullish' if macd_histogram > 0 else 'bearish' if macd_histogram < 0 else 'neutral'
        
        # Volume momentum
        volume_ratio = indicators['volume']['ratio']
        volume_momentum = 'high' if volume_ratio > 1.5 else 'normal'
        
        # Overall momentum score (-100 to 100)
        momentum_score = 0
        momentum_score += price_change_1d * 10  # Weight recent price action
        momentum_score += price_change_5d * 5   # Medium-term momentum
        momentum_score += price_change_20d * 2  # Longer-term trend
        
        # RSI contribution
        momentum_score += (rsi - 50) * 0.5
        
        # MACD contribution
        momentum_score += macd_histogram * 100
        
        # Volume boost
        if volume_ratio > 2:
            momentum_score *= 1.2
        
        # Clamp to -100 to 100
        momentum_score = max(-100, min(100, momentum_score))
        
        return {
            'score': momentum_score,
            'price_change_1d': price_change_1d,
            'price_change_5d': price_change_5d,
            'price_change_20d': price_change_20d,
            'rsi_momentum': rsi_momentum,
            'macd_momentum': macd_momentum,
            'volume_momentum': volume_momentum,
            'strength': self._classify_momentum_strength(momentum_score)
        }
    
    def _classify_momentum_strength(self, score: float) -> str:
        """Classify momentum strength"""
        if score > 50:
            return 'very_strong_bullish'
        elif score > 20:
            return 'strong_bullish'
        elif score > 5:
            return 'moderate_bullish'
        elif score > -5:
            return 'neutral'
        elif score > -20:
            return 'moderate_bearish'
        elif score > -50:
            return 'strong_bearish'
        else:
            return 'very_strong_bearish'
    
    def _generate_signals(self, indicators: Dict, data: pd.DataFrame) -> Dict:
        """Generate trading signals from indicators"""
        signals = {}
        current_price = float(data['Close'].iloc[-1])
        
        # RSI signals
        rsi = indicators['rsi']
        if rsi < 30:
            signals['rsi'] = {'signal': 'buy', 'strength': (30 - rsi) / 30}
        elif rsi > 70:
            signals['rsi'] = {'signal': 'sell', 'strength': (rsi - 70) / 30}
        else:
            signals['rsi'] = {'signal': 'neutral', 'strength': 0}
        
        # MACD signals
        macd = indicators['macd']
        if macd['histogram'] > 0 and macd['line'] > macd['signal']:
            signals['macd'] = {'signal': 'buy', 'strength': min(abs(macd['histogram']) * 100, 1)}
        elif macd['histogram'] < 0 and macd['line'] < macd['signal']:
            signals['macd'] = {'signal': 'sell', 'strength': min(abs(macd['histogram']) * 100, 1)}
        else:
            signals['macd'] = {'signal': 'neutral', 'strength': 0}
        
        # Moving Average signals
        sma_20 = indicators['sma'].get('sma_20', current_price)
        sma_50 = indicators['sma'].get('sma_50', current_price)
        
        if current_price > sma_20 > sma_50:
            signals['ma_trend'] = {'signal': 'buy', 'strength': 0.8}
        elif current_price < sma_20 < sma_50:
            signals['ma_trend'] = {'signal': 'sell', 'strength': 0.8}
        else:
            signals['ma_trend'] = {'signal': 'neutral', 'strength': 0}
        
        # Volume signals
        vol = indicators['volume']
        if vol['ratio'] > 2 and len(data) >= 2:
            price_direction = 'up' if data['Close'].iloc[-1] > data['Close'].iloc[-2] else 'down'
            if price_direction == 'up':
                signals['volume'] = {'signal': 'buy', 'strength': min(vol['ratio'] / 3, 1)}
            else:
                signals['volume'] = {'signal': 'sell', 'strength': min(vol['ratio'] / 3, 1)}
        else:
            signals['volume'] = {'signal': 'neutral', 'strength': 0}
        
        return signals
    
    def _determine_trend(self, indicators: Dict, data: pd.DataFrame) -> Dict:
        """Determine the current trend"""
        current_price = float(data['Close'].iloc[-1])
        
        # Moving average trend
        sma_20 = indicators['sma'].get('sma_20', current_price)
        sma_50 = indicators['sma'].get('sma_50', current_price)
        sma_200 = indicators['sma'].get('sma_200', current_price)
        
        if current_price > sma_20 > sma_50 > sma_200:
            trend = 'strong_bullish'
            strength = 'strong'
        elif current_price > sma_50 > sma_200:
            trend = 'bullish'
            strength = 'moderate'
        elif current_price < sma_20 < sma_50 < sma_200:
            trend = 'strong_bearish'
            strength = 'strong'
        elif current_price < sma_50 < sma_200:
            trend = 'bearish'
            strength = 'moderate'
        else:
            trend = 'sideways'
            strength = 'weak'
        
        return {
            'direction': trend,
            'strength': strength,
            'sma_alignment': current_price > sma_20 > sma_50
        }
    
    def _calculate_overall_signal(self, signals: Dict) -> float:
        """Calculate overall signal (-100 to 100)"""
        signal_values = []
        weights = {
            'rsi': 0.25,
            'macd': 0.35,
            'ma_trend': 0.25,
            'volume': 0.15
        }
        
        for indicator, signal_data in signals.items():
            if indicator in weights:
                if signal_data['signal'] == 'buy':
                    value = signal_data['strength'] * 100
                elif signal_data['signal'] == 'sell':
                    value = -signal_data['strength'] * 100
                else:
                    value = 0
                
                signal_values.append(value * weights[indicator])
        
        overall_signal = sum(signal_values)
        return max(-100, min(100, overall_signal))
    
    def _calculate_signal_strength(self, signals: Dict) -> str:
        """Determine signal strength category"""
        bullish_count = sum(1 for s in signals.values() if s['signal'] == 'buy')
        bearish_count = sum(1 for s in signals.values() if s['signal'] == 'sell')
        
        strengths = [s['strength'] for s in signals.values() if s['signal'] != 'neutral']
        avg_strength = sum(strengths) / len(strengths) if strengths else 0
        
        if bullish_count >= 3 and avg_strength > 0.6:
            return 'strong_buy'
        elif bullish_count > bearish_count:
            return 'buy'
        elif bearish_count >= 3 and avg_strength > 0.6:
            return 'strong_sell'
        elif bearish_count > bullish_count:
            return 'sell'
        else:
            return 'neutral'
    
    def _get_recommendation(self, overall_signal: float, momentum: Dict) -> str:
        """Get trading recommendation based on signal and momentum"""
        momentum_score = momentum['score']
        
        # Strong signals with momentum confirmation
        if overall_signal > 30 and momentum_score > 20:
            return 'STRONG_BUY'
        elif overall_signal > 15:
            return 'BUY'
        elif overall_signal < -30 and momentum_score < -20:
            return 'STRONG_SELL'
        elif overall_signal < -15:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _empty_analysis(self, symbol: str) -> Dict:
        """Return empty analysis structure"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': 0,
            'indicators': {},
            'signals': {},
            'momentum': {'score': 0, 'strength': 'neutral'},
            'trend': {'direction': 'unknown', 'strength': 'unknown'},
            'overall_signal': 0,
            'signal_strength': 'neutral',
            'recommendation': 'HOLD'
        }

def get_market_data(symbol: str, period: str = '3mo', interval: str = '1d') -> pd.DataFrame:
    """
    Get market data for technical analysis
    Using yfinance as a free data source
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        return data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()

# Example usage and testing
if __name__ == "__main__":
    # Test the technical analyzer
    analyzer = TechnicalAnalyzer()
    settings = Settings()
    
    # Test with first two symbols from canonical list
    test_symbols = settings.BANK_SYMBOLS[:2]
    
    for symbol in test_symbols:
        print(f"\n--- Technical Analysis for {symbol} ---")
        data = get_market_data(symbol)
        
        if not data.empty:
            analysis = analyzer.analyze(symbol, data)
            
            print(f"Current Price: ${analysis['current_price']:.2f}")
            print(f"RSI: {analysis['indicators'].get('rsi', 0):.2f}")
            print(f"Momentum Score: {analysis['momentum']['score']:.2f}")
            print(f"Momentum Strength: {analysis['momentum']['strength']}")
            print(f"Trend: {analysis['trend']['direction']}")
            print(f"Recommendation: {analysis['recommendation']}")
        else:
            print("No data available")
