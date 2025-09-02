import requests
import os
from typing import Optional
from datetime import datetime
import time

class AlphaVantagePriceFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        
        if not self.api_key:
            print('Alpha Vantage API key not found')
    
    def get_current_price_robust(self, symbol: str, max_retries: int = 2) -> Optional[float]:
        if not self.api_key:
            return None
            
        for attempt in range(max_retries):
            try:
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Error Message' in data:
                    print(f'API Error for {symbol}: {data}')
                    return None
                
                if 'Note' in data:
                    print(f'API Limit for {symbol}')
                    return None
                
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    
                    if quote and '05. price' in quote:
                        price = float(quote['05. price'])
                        latest_day = quote.get('07. latest trading day', 'unknown')
                        
                        print(f'Price {symbol}:  (Alpha Vantage - {latest_day})')
                        return price
                
                print(f'No price data for {symbol}')
                return None
                
            except Exception as e:
                print(f'Attempt {attempt + 1} failed for {symbol}: {e}')
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        print(f'All attempts failed for {symbol}')
        return None

def get_current_price_alpha_vantage(symbol: str) -> Optional[float]:
    try:
        fetcher = AlphaVantagePriceFetcher()
        return fetcher.get_current_price_robust(symbol)
    except Exception as e:
        print(f'Setup error: {e}')
        return None
