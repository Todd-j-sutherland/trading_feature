"""
Alpha Vantage Real-Time Price Fetcher for ASX
Provides real-time price data to replace yfinance delays
"""

import requests
import json
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
import os

class AlphaVantageError(Exception):
    """Custom exception for Alpha Vantage API errors"""
    pass

class AlphaVantagePriceFetcher:
    """Real-time price fetcher using Alpha Vantage API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.cache = {}
        self.cache_timeout = 60  # Cache prices for 1 minute
        
        if not self.api_key:
            raise AlphaVantageError("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
    
    def _make_request(self, params: Dict) -> Dict:
        """Make API request to Alpha Vantage"""
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise AlphaVantageError(f"API Error: {data['Error Message']}")
            
            if 'Note' in data:
                raise AlphaVantageError(f"API Limit: {data['Note']}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise AlphaVantageError(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise AlphaVantageError(f"Invalid JSON response: {e}")
    
    def get_real_time_price(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time price for ASX symbol
        Returns dict with price, timestamp, and metadata
        """
        # Check cache first
        cache_key = f"realtime_{symbol}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_timeout):
                return cached_data
        
        try:
            # Alpha Vantage real-time quote
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol
            }
            
            data = self._make_request(params)
            
            # Parse response
            if 'Global Quote' in data:
                quote = data['Global Quote']
                
                if quote and '05. price' in quote:
                    price_data = {
                        'symbol': symbol,
                        'price': float(quote['05. price']),
                        'change': float(quote['09. change']),
                        'change_percent': quote['10. change percent'].strip('%'),
                        'volume': int(quote['06. volume']) if quote['06. volume'] != '0' else 0,
                        'latest_trading_day': quote['07. latest trading day'],
                        'previous_close': float(quote['08. previous close']),
                        'timestamp': datetime.now(),
                        'source': 'alpha_vantage_realtime'
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = (price_data, datetime.now())
                    
                    return price_data
            
            return None
            
        except Exception as e:
            print(f"‚ùå Alpha Vantage real-time error for {symbol}: {e}")
            return None
    
    def get_intraday_price(self, symbol: str, interval: str = '1min') -> Optional[Dict]:
        """
        Get most recent intraday price (alternative method)
        """
        cache_key = f"intraday_{symbol}_{interval}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_timeout):
                return cached_data
        
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'outputsize': 'compact'
            }
            
            data = self._make_request(params)
            
            # Parse intraday data
            time_series_key = f'Time Series ({interval})'
            if time_series_key in data:
                time_series = data[time_series_key]
                
                if time_series:
                    # Get most recent timestamp
                    latest_time = max(time_series.keys())
                    latest_data = time_series[latest_time]
                    
                    price_data = {
                        'symbol': symbol,
                        'price': float(latest_data['4. close']),
                        'open': float(latest_data['1. open']),
                        'high': float(latest_data['2. high']),
                        'low': float(latest_data['3. low']),
                        'volume': int(latest_data['5. volume']),
                        'timestamp': datetime.fromisoformat(latest_time.replace(' ', 'T')),
                        'data_timestamp': latest_time,
                        'source': 'alpha_vantage_intraday'
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = (price_data, datetime.now())
                    
                    return price_data
            
            return None
            
        except Exception as e:
            print(f"‚ùå Alpha Vantage intraday error for {symbol}: {e}")
            return None
    
    def get_current_price_robust(self, symbol: str, max_retries: int = 2) -> Optional[float]:
        """
        Get current price with fallback methods
        This is the main interface for paper trading
        """
        methods = [
            ('real_time', self.get_real_time_price),
            ('intraday', lambda s: self.get_intraday_price(s, '1min'))
        ]
        
        for attempt in range(max_retries):
            for method_name, method in methods:
                try:
                    data = method(symbol)
                    if data and data.get('price', 0) > 0:
                        price = data['price']
                        
                        # Check data freshness
                        data_time = data.get('timestamp', datetime.now())
                        if isinstance(data_time, str):
                            data_time = datetime.fromisoformat(data_time.replace(' ', 'T'))
                        
                        age_minutes = (datetime.now() - data_time).total_seconds() / 60
                        
                        if age_minutes < 60:  # Data less than 1 hour old
                            print(f"Ì≤∞ {symbol}: ${price:.2f} via {method_name} (age: {age_minutes:.1f}min)")
                            return price
                        else:
                            print(f"‚ö†Ô∏è {symbol}: Data too old ({age_minutes:.0f}min) via {method_name}")
                            
                except Exception as e:
                    print(f"‚ö†Ô∏è {symbol}: {method_name} method failed: {e}")
                    continue
            
            if attempt < max_retries - 1:
                print(f"Ì¥Ñ {symbol}: Retrying... (attempt {attempt + 2}/{max_retries})")
                time.sleep(1)
        
        return None

# Convenience function for direct use
def get_current_price_alpha_vantage(symbol: str) -> Optional[float]:
    """Simple interface for getting current price"""
    try:
        fetcher = AlphaVantagePriceFetcher()
        return fetcher.get_current_price_robust(symbol)
    except Exception as e:
        print(f"‚ùå Alpha Vantage setup error: {e}")
        return None

if __name__ == "__main__":
    # Test the fetcher
    print("Ì∑™ Testing Alpha Vantage Price Fetcher")
    print("=" * 40)
    
    test_symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX']
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}:")
        price = get_current_price_alpha_vantage(symbol)
        if price:
            print(f"‚úÖ {symbol}: ${price:.2f}")
        else:
            print(f"‚ùå {symbol}: Failed to get price")
