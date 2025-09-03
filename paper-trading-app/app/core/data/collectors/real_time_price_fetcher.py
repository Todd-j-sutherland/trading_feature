#!/usr/bin/env python3
"""
Real-time Price Fetcher with Multiple Data Sources
Prioritizes IG Markets -> Alpha Vantage -> yfinance for ASX stock prices
"""

import yfinance as yf
import requests
import logging
from datetime import datetime, timedelta
import time
from typing import Optional, Tuple, Dict
from ig_markets_asx_mapper import IGMarketsASXMapper

class RealTimePriceFetcher:
    """Fetches real-time stock prices using multiple data sources with fallback hierarchy"""
    
    def __init__(self):
        """Initialize the real-time price fetcher with multiple data sources"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize IG Markets (prioritized for ASX)
        self.ig_markets = IGMarketsASXMapper(
            username='sutho100',
            password='Helloworld987543$',
            api_key='ac68e6f053799a4a36c75936c088fc4d6cfcfa6e',
            demo=True
        )
        
        # Alpha Vantage configuration
        self.alpha_vantage_key = 'demo'  # Using demo key (limited)
        
        # Cache for price data (to avoid excessive API calls)
        self.price_cache = {}
        self.cache_duration = 30  # Cache prices for 30 seconds
        
        # Track data source usage for debugging
        self.source_stats = {
            'ig_markets': 0,
            'alpha_vantage': 0,
            'yfinance': 0,
            'errors': 0
        }
    
    def get_current_price(self, symbol: str) -> Optional[Tuple[float, str, int]]:
        """
        Get the most current price available from any source
        Returns (price, source_info, delay_minutes)
        """
        # Try IG Markets first (best for ASX)
        try:
            price_data = self.ig_markets.get_price(symbol)
            
            if price_data:
                price, status = price_data
                
                # Determine delay based on market status
                if 'LIVE' in status:
                    delay_minutes = 0  # Real-time during market hours
                elif 'HISTORICAL' in status:
                    delay_minutes = 60  # Historical data (market closed)
                else:
                    delay_minutes = 120  # Unknown status
                
                source_info = f"IG Markets - {status}"
                self.source_stats['ig_markets'] += 1
                return price, source_info, delay_minutes
        except Exception as e:
            self.logger.error(f"IG Markets error for {symbol}: {e}")
        
        # Fallback to yfinance if IG Markets fails
        try:
            yf_symbol = symbol if symbol.endswith('.AX') else f"{symbol}.AX"
            stock = yf.Ticker(yf_symbol)
            info = stock.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price and current_price > 0:
                delay_minutes = 900  # yfinance is often very delayed
                source_info = "yfinance (delayed)"
                self.source_stats['yfinance'] += 1
                return current_price, source_info, delay_minutes
        except Exception as e:
            self.logger.error(f"yfinance error for {symbol}: {e}")
        
        # No data source worked
        self.source_stats['errors'] += 1
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics for debugging"""
        return self.source_stats.copy()

# Test function
def test_price_fetcher():
    """Test the price fetcher with various ASX symbols"""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = RealTimePriceFetcher()
    
    test_symbols = ['WBC', 'CBA', 'BHP', 'NAB']
    
    print("Testing Real-Time Price Fetcher...")
    print("=" * 50)
    
    for symbol in test_symbols:
        price_data = fetcher.get_current_price(symbol)
        
        if price_data:
            price, source, delay = price_data
            print(f"{symbol:4s}: ${price:7.2f} from {source} (delay: {delay} min)")
        else:
            print(f"{symbol:4s}: No price available")
    
    print(f"\nSource usage stats: {fetcher.get_stats()}")

if __name__ == "__main__":
    test_price_fetcher()
