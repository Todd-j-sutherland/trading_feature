#!/usr/bin/env python3
"""
IG Markets Real-Time Price Fetcher
Integrates with IG Markets REST API for real-time ASX data using demo account
"""

import requests
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import time
import pytz
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IGMarketsPriceFetcher:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, 
                 api_key: Optional[str] = None, demo: bool = True):
        """
        Initialize IG Markets API client
        
        Args:
            username: IG Markets username (or from IG_USERNAME env var)
            password: IG Markets password (or from IG_PASSWORD env var)
            api_key: IG Markets API key (or from IG_API_KEY env var)
            demo: Use demo account (True) or live account (False)
        """
        self.username = username or os.getenv('IG_USERNAME')
        self.password = password or os.getenv('IG_PASSWORD')
        self.api_key = api_key or os.getenv('IG_API_KEY')
        self.demo = demo
        
        # API endpoints
        if demo:
            self.base_url = 'https://demo-api.ig.com/gateway/deal'
        else:
            self.base_url = 'https://api.ig.com/gateway/deal'
            
        self.aest_tz = pytz.timezone('Australia/Sydney')
        self.session = requests.Session()
        self.auth_token = None
        self.client_session_token = None
        
        # Cache for market data
        self.price_cache = {}
        self.cache_expiry = {}
        self.cache_duration_seconds = 30  # Cache prices for 30 seconds
        
        if not all([self.username, self.password, self.api_key]):
            logger.error("IG Markets credentials not found. Set IG_USERNAME, IG_PASSWORD, IG_API_KEY environment variables")
        
    def authenticate(self) -> bool:
        """Authenticate with IG Markets API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-IG-API-KEY': self.api_key,
                'Version': '2'
            }
            
            data = {
                'identifier': self.username,
                'password': self.password
            }
            
            response = self.session.post(
                f'{self.base_url}/session',
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.auth_token = response.headers.get('X-SECURITY-TOKEN')
                self.client_session_token = response.headers.get('CST')
                
                if self.auth_token and self.client_session_token:
                    logger.info("✅ IG Markets authentication successful")
                    return True
                else:
                    logger.error("❌ IG Markets authentication failed - missing tokens")
                    return False
            else:
                logger.error(f"❌ IG Markets authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ IG Markets authentication error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authenticated request headers"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-IG-API-KEY': self.api_key,
            'X-SECURITY-TOKEN': self.auth_token,
            'CST': self.client_session_token,
            'Version': '3'
        }
    
    def search_market(self, symbol: str) -> Optional[str]:
        """Search for market EPIC (IG's internal identifier) for a given symbol"""
        try:
            if not self.auth_token:
                if not self.authenticate():
                    return None
            
            # Convert ASX symbol to IG format
            # ASX symbols might be in format like WBC.AX -> need to find IG EPIC
            search_term = symbol.replace('.AX', '').upper()
            
            headers = self.get_auth_headers()
            
            response = self.session.get(
                f'{self.base_url}/markets?searchTerm={search_term}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                
                # Look for ASX markets
                for market in markets:
                    market_name = market.get('instrumentName', '').upper()
                    epic = market.get('epic', '')
                    
                    if search_term in market_name and any(x in market_name for x in ['ASX', 'AUSTRALIA', 'SYDNEY']):
                        logger.info(f"Found IG EPIC: {epic} for {symbol} ({market_name})")
                        return epic
                
                # Fallback: return first match if any
                if markets:
                    epic = markets[0].get('epic', '')
                    market_name = markets[0].get('instrumentName', '')
                    logger.info(f"Using first match: {epic} for {symbol} ({market_name})")
                    return epic
                    
            logger.warning(f"No IG market found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Market search error for {symbol}: {e}")
            return None
    
    def get_current_price_by_epic(self, epic: str) -> Dict[str, Any]:
        """Get current price for a specific IG EPIC"""
        try:
            if not self.auth_token:
                if not self.authenticate():
                    return None
            
            headers = self.get_auth_headers()
            
            response = self.session.get(
                f'{self.base_url}/markets/{epic}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                market = data.get('instrument', {})
                snapshot = data.get('snapshot', {})
                
                if snapshot:
                    bid = snapshot.get('bid')
                    offer = snapshot.get('offer')
                    
                    if bid is not None and offer is not None:
                        # Use mid price
                        mid_price = (bid + offer) / 2
                        
                        return {
                            'price': mid_price,
                            'bid': bid,
                            'offer': offer,
                            'timestamp': datetime.now(self.aest_tz),
                            'delay_minutes': 0,  # IG provides real-time data
                            'source': 'ig_markets',
                            'epic': epic,
                            'market_name': market.get('name', ''),
                            'current_time': datetime.now(self.aest_tz)
                        }
                        
            logger.error(f"No price data for EPIC {epic}")
            return None
            
        except Exception as e:
            logger.error(f"Price fetch error for EPIC {epic}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for ASX symbol
        
        Args:
            symbol: ASX symbol (e.g., 'WBC.AX')
            
        Returns:
            Current price or None if not available
        """
        # Check cache first
        cache_key = symbol
        current_time = time.time()
        
        if (cache_key in self.price_cache and 
            cache_key in self.cache_expiry and 
            current_time < self.cache_expiry[cache_key]):
            
            cached_result = self.price_cache[cache_key]
            logger.info(f"📋 {symbol}: ${cached_result['price']:.2f} from IG Markets (cached)")
            return cached_result['price']
        
        # Find IG EPIC for this symbol
        epic = self.search_market(symbol)
        if not epic:
            return None
        
        # Get price data
        result = self.get_current_price_by_epic(epic)
        if result and result.get('price'):
            # Cache the result
            self.price_cache[cache_key] = result
            self.cache_expiry[cache_key] = current_time + self.cache_duration_seconds
            
            price = result['price']
            market_name = result.get('market_name', '')
            logger.info(f"📊 {symbol}: ${price:.2f} from IG Markets (real-time) - {market_name}")
            return price
            
        return None
    
    def get_current_price_with_details(self, symbol: str) -> Dict[str, Any]:
        """Get current price with full details"""
        epic = self.search_market(symbol)
        if not epic:
            return {
                'price': None,
                'error': f'No IG market found for {symbol}',
                'timestamp': datetime.now(self.aest_tz),
                'source': 'ig_markets'
            }
        
        result = self.get_current_price_by_epic(epic)
        if result:
            return result
        else:
            return {
                'price': None,
                'error': f'No price data for {symbol}',
                'timestamp': datetime.now(self.aest_tz),
                'source': 'ig_markets'
            }

# Backward compatibility functions
def get_current_price_ig_markets(symbol: str) -> Optional[float]:
    """Simple function for IG Markets integration"""
    fetcher = IGMarketsPriceFetcher()
    return fetcher.get_current_price(symbol)

def get_current_price_ig_markets_with_details(symbol: str) -> Dict[str, Any]:
    """Get price with IG Markets details"""
    fetcher = IGMarketsPriceFetcher()
    return fetcher.get_current_price_with_details(symbol)

if __name__ == "__main__":
    # Test the IG Markets fetcher
    print("Testing IG Markets API integration...")
    print("Make sure you have set these environment variables:")
    print("  IG_USERNAME=your_ig_username")
    print("  IG_PASSWORD=your_ig_password") 
    print("  IG_API_KEY=your_ig_api_key")
    print()
    
    fetcher = IGMarketsPriceFetcher()
    
    test_symbols = ['WBC.AX', 'CBA.AX', 'ANZ.AX']
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}:")
        result = fetcher.get_current_price_with_details(symbol)
        
        if result.get('price'):
            price = result['price']
            bid = result.get('bid', 'N/A')
            offer = result.get('offer', 'N/A')
            market_name = result.get('market_name', 'Unknown')
            print(f"  ✅ Price: ${price:.2f} (Bid: ${bid}, Offer: ${offer})")
            print(f"  📊 Market: {market_name}")
            print(f"  🕒 Real-time data from IG Markets")
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
