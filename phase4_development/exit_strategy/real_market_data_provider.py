#!/usr/bin/env python3
"""
Real Market Data Exit Strategy Tester
Uses yfinance for actual ASX market data and historical scenarios
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealMarketDataProvider:
    """
    Provides real market data using yfinance with pre-built testing scenarios
    """
    
    def __init__(self):
        self.asx_banks = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        
        # Historical market scenarios for testing
        self.market_scenarios = {
            'covid_crash': {
                'name': 'COVID-19 Market Crash',
                'start': '2020-02-20',
                'end': '2020-04-15',
                'description': 'Major market crash - perfect for stop-loss testing',
                'expected_behavior': 'Rapid decline, high volatility'
            },
            'banking_rally': {
                'name': 'Banking Sector Rally',
                'start': '2020-11-01',
                'end': '2021-02-28',
                'description': 'Strong banking sector recovery - profit target testing',
                'expected_behavior': 'Sustained uptrend with momentum'
            },
            'rate_hike_impact': {
                'name': 'Interest Rate Rise Impact',
                'start': '2022-05-01',
                'end': '2022-12-31',
                'description': 'Rate hike volatility - sentiment testing',
                'expected_behavior': 'Mixed signals, high uncertainty'
            },
            'earnings_season': {
                'name': 'Q1 2024 Earnings Season',
                'start': '2024-02-01',
                'end': '2024-02-29',
                'description': 'Earnings volatility - technical breakdown testing',
                'expected_behavior': 'Sharp moves on earnings announcements'
            },
            'recent_stability': {
                'name': 'Recent Market Stability',
                'start': '2024-06-01',
                'end': '2024-08-31',
                'description': 'Stable period - time-based exit testing',
                'expected_behavior': 'Low volatility, sideways movement'
            },
            'election_uncertainty': {
                'name': 'Federal Election Period',
                'start': '2022-03-01',
                'end': '2022-06-30',
                'description': 'Political uncertainty - sentiment reversal testing',
                'expected_behavior': 'Increased volatility around key dates'
            }
        }
    
    def get_real_market_data(self, symbol: str, scenario: str = None, 
                           start_date: str = None, end_date: str = None,
                           period: str = '1y') -> pd.DataFrame:
        """
        Fetch real market data from Yahoo Finance
        
        Args:
            symbol: ASX stock symbol (e.g., 'CBA.AX')
            scenario: Pre-defined scenario name
            start_date: Custom start date (YYYY-MM-DD)
            end_date: Custom end date (YYYY-MM-DD)
            period: Default period if no dates specified
        
        Returns:
            DataFrame with OHLCV data and technical indicators
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Determine date range
            if scenario and scenario in self.market_scenarios:
                start = self.market_scenarios[scenario]['start']
                end = self.market_scenarios[scenario]['end']
                logger.info(f"📊 Using scenario '{scenario}': {start} to {end}")
            elif start_date and end_date:
                start, end = start_date, end_date
            else:
                # Use period
                end = datetime.now().strftime('%Y-%m-%d')
                start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Fetch data
            logger.info(f"🔍 Fetching real market data for {symbol} from {start} to {end}")
            data = ticker.history(start=start, end=end, interval='1d')
            
            if data.empty:
                logger.error(f"❌ No data found for {symbol}")
                return pd.DataFrame()
            
            # Add technical indicators
            data = self._add_technical_indicators(data)
            
            # Add market context
            if scenario:
                data['scenario'] = scenario
                data['scenario_description'] = self.market_scenarios[scenario]['description']
            
            logger.info(f"✅ Retrieved {len(data)} days of real market data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the data"""
        try:
            # Try to import pandas_ta for advanced indicators
            try:
                import pandas_ta as ta
                data.ta.rsi(length=14, append=True)
                data.ta.macd(fast=12, slow=26, signal=9, append=True)
                data.ta.bbands(length=20, std=2, append=True)
                data.ta.atr(length=14, append=True)
                logger.info("✅ Added advanced technical indicators using pandas_ta")
            except ImportError:
                # Fallback to basic indicators
                logger.warning("⚠️ pandas_ta not installed, using basic indicators")
                data = self._add_basic_indicators(data)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error adding technical indicators: {e}")
            return data
    
    def _add_basic_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators without pandas_ta"""
        # Simple Moving Averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # RSI calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI_14'] = 100 - (100 / (1 + rs))
        
        # Volatility
        data['volatility'] = data['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
        
        # Volume trend
        data['volume_sma'] = data['Volume'].rolling(window=20).mean()
        data['volume_trend'] = (data['Volume'] / data['volume_sma'] - 1) * 100
        
        return data
    
    def get_scenario_library(self) -> Dict:
        """Get all pre-built testing scenarios"""
        return self.market_scenarios
    
    def create_realistic_test_case(self, symbol: str, scenario: str, 
                                 entry_date: str = None) -> Dict:
        """
        Create a realistic test case based on actual market data
        
        Args:
            symbol: ASX stock symbol
            scenario: Scenario name from market_scenarios
            entry_date: Specific entry date (optional)
        
        Returns:
            Dictionary with realistic test case data
        """
        data = self.get_real_market_data(symbol, scenario)
        
        if data.empty:
            return {}
        
        # Select entry point
        if entry_date:
            try:
                entry_idx = data.index.get_loc(pd.to_datetime(entry_date).date())
            except KeyError:
                entry_idx = len(data) // 4  # Use 25% into the period
        else:
            entry_idx = len(data) // 4  # Default to 25% into scenario
        
        entry_price = data.iloc[entry_idx]['Close']
        entry_date_actual = data.index[entry_idx]
        
        # Calculate realistic metrics from actual data
        price_changes = data['Close'].pct_change().dropna()
        volatility = price_changes.std() * np.sqrt(252)  # Annualized
        max_drawdown = ((data['Close'] / data['Close'].cummax()) - 1).min()
        max_gain = ((data['Close'] / data['Close'].cummin()) - 1).max()
        
        # Determine realistic position based on scenario
        scenario_info = self.market_scenarios[scenario]
        
        test_case = {
            'symbol': symbol,
            'scenario': scenario,
            'scenario_description': scenario_info['description'],
            'entry_date': entry_date_actual.strftime('%Y-%m-%d'),
            'entry_price': round(entry_price, 2),
            'current_price': round(data.iloc[-1]['Close'], 2),
            'actual_return_pct': round(((data.iloc[-1]['Close'] / entry_price) - 1) * 100, 2),
            'volatility': round(volatility * 100, 2),
            'max_drawdown_pct': round(max_drawdown * 100, 2),
            'max_gain_pct': round(max_gain * 100, 2),
            'days_held': len(data) - entry_idx,
            'position_type': 'BUY',  # Default
            'confidence': 85.0,  # Default
            'technical_data': {
                'rsi': round(data.iloc[-1].get('RSI_14', 50), 1),
                'volume_trend': round(data.iloc[-1].get('volume_trend', 0), 2),
                'price_trend': 'bullish' if data.iloc[-1]['Close'] > data.iloc[-5]['Close'] else 'bearish'
            },
            'market_data': data,
            'realistic_expectations': {
                'expected_exit': self._determine_expected_exit(scenario_info, data),
                'risk_level': self._assess_risk_level(volatility, scenario)
            }
        }
        
        return test_case
    
    def _determine_expected_exit(self, scenario_info: Dict, data: pd.DataFrame) -> str:
        """Determine expected exit based on scenario characteristics"""
        scenario_name = scenario_info['name'].lower()
        
        if 'crash' in scenario_name:
            return 'STOP_LOSS'
        elif 'rally' in scenario_name:
            return 'PROFIT_TARGET'
        elif 'volatility' in scenario_name or 'uncertainty' in scenario_name:
            return 'SENTIMENT_REVERSAL'
        elif 'stability' in scenario_name:
            return 'TIME_LIMIT'
        else:
            return 'TECHNICAL_BREAKDOWN'
    
    def _assess_risk_level(self, volatility: float, scenario: str) -> str:
        """Assess risk level based on volatility and scenario"""
        if volatility > 0.4 or 'crash' in scenario:
            return 'HIGH'
        elif volatility > 0.25 or 'uncertainty' in scenario:
            return 'MEDIUM'
        else:
            return 'LOW'

def main():
    """Demo the real market data provider"""
    provider = RealMarketDataProvider()
    
    print("🚀 Real Market Data Exit Strategy Tester")
    print("=" * 50)
    
    # Show available scenarios
    print("\n📊 Available Market Scenarios:")
    for scenario, info in provider.get_scenario_library().items():
        print(f"   {scenario}: {info['name']} ({info['start']} to {info['end']})")
    
    print("\n🧪 Creating Realistic Test Cases...")
    
    # Create test cases for different scenarios
    test_scenarios = ['covid_crash', 'banking_rally', 'rate_hike_impact']
    
    for scenario in test_scenarios:
        print(f"\n📈 Scenario: {scenario.upper()}")
        print("-" * 40)
        
        test_case = provider.create_realistic_test_case('CBA.AX', scenario)
        
        if test_case:
            print(f"Symbol: {test_case['symbol']}")
            print(f"Description: {test_case['scenario_description']}")
            print(f"Entry: ${test_case['entry_price']} on {test_case['entry_date']}")
            print(f"Current: ${test_case['current_price']}")
            print(f"Return: {test_case['actual_return_pct']:+.1f}%")
            print(f"Volatility: {test_case['volatility']:.1f}%")
            print(f"Max Drawdown: {test_case['max_drawdown_pct']:.1f}%")
            print(f"Expected Exit: {test_case['realistic_expectations']['expected_exit']}")
            print(f"Risk Level: {test_case['realistic_expectations']['risk_level']}")
        else:
            print(f"❌ Could not create test case for {scenario}")

if __name__ == "__main__":
    main()
