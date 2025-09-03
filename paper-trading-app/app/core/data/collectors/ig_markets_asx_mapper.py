#!/usr/bin/env python3
"""
IG Markets ASX Symbol Mapper
Maps ASX symbols to IG Markets EPICs for real-time price fetching
"""

import requests
import json
import logging
from typing import Dict, Optional, Tuple
import time

class IGMarketsASXMapper:
    def __init__(self, username: str, password: str, api_key: str, demo: bool = True):
        """Initialize IG Markets ASX mapper with authentication"""
        self.username = username
        self.password = password
        self.api_key = api_key
        self.demo = demo
        self.base_url = 'https://demo-api.ig.com/gateway/deal' if demo else 'https://api.ig.com/gateway/deal'
        
        # Authentication tokens
        self.auth_token = None
        self.cst_token = None
        self.auth_time = 0
        
        # Cache for symbol mappings
        self.symbol_cache = {}
        
        # Known ASX mappings (discovered through testing)
        self.known_mappings = {
            'WBC': 'AA.D.WBC.CASH.IP',      # Westpac Banking Corp
            'CBA': 'AA.D.CBA.CASH.IP',      # Commonwealth Bank
            'BHP': 'AA.D.BHP.CASH.IP',      # BHP Group Limited
            'NAB': 'AA.D.NAB.CASH.IP',      # National Australia Bank
            'WOW': 'AA.D.WOW.CASH.IP',      # Woolworths Group
            'TLS': 'AA.D.TLS.CASH.IP',      # Telstra Group
        }
        
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self) -> bool:
        """Authenticate with IG Markets API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-IG-API-KEY': self.api_key,
                'Version': '2'
            }
            
            data = {'identifier': self.username, 'password': self.password}
            response = requests.post(f'{self.base_url}/session', headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                self.auth_token = response.headers.get('X-SECURITY-TOKEN')
                self.cst_token = response.headers.get('CST')
                self.auth_time = time.time()
                self.logger.info("IG Markets authentication successful")
                return True
            else:
                self.logger.error(f"IG Markets authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"IG Markets authentication error: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication (within 6 hours)"""
        return (self.auth_token and self.cst_token and 
                time.time() - self.auth_time < 21600)  # 6 hours
    
    def ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication"""
        if not self.is_authenticated():
            return self.authenticate()
        return True
    
    def search_market(self, search_term: str) -> Optional[Dict]:
        """Search for a market by term"""
        if not self.ensure_authenticated():
            return None
        
        try:
            headers = {
                'Accept': 'application/json',
                'X-IG-API-KEY': self.api_key,
                'X-SECURITY-TOKEN': self.auth_token,
                'CST': self.cst_token,
                'Version': '1'
            }
            
            response = requests.get(f'{self.base_url}/markets', headers=headers,
                                  params={'searchTerm': search_term}, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                
                # Look for main equity shares (not derivatives/notes)
                for market in markets:
                    name = market.get('instrumentName', '')
                    epic = market.get('epic', '')
                    market_type = market.get('instrumentType', '')
                    
                    # Filter for main shares
                    if ('Banking Corp' in name or 'Bank' in name or 
                        'Limited' in name or 'Group' in name or 
                        'Corporation' in name) and 'Notes' not in name:
                        
                        return {
                            'name': name,
                            'epic': epic,
                            'type': market_type
                        }
                
                # If no filtered match, return first result
                if markets:
                    market = markets[0]
                    return {
                        'name': market.get('instrumentName', ''),
                        'epic': market.get('epic', ''),
                        'type': market.get('instrumentType', '')
                    }
                    
            return None
            
        except Exception as e:
            self.logger.error(f"IG Markets search error: {e}")
            return None
    
    def get_asx_epic(self, asx_symbol: str) -> Optional[str]:
        """Get IG Markets EPIC for an ASX symbol"""
        # Check cache first
        if asx_symbol in self.symbol_cache:
            return self.symbol_cache[asx_symbol]
        
        # Check known mappings
        if asx_symbol in self.known_mappings:
            epic = self.known_mappings[asx_symbol]
            self.symbol_cache[asx_symbol] = epic
            return epic
        
        # Search for the symbol
        market = self.search_market(asx_symbol)
        if market and market['epic']:
            epic = market['epic']
            self.symbol_cache[asx_symbol] = epic
            self.logger.info(f"Mapped {asx_symbol} to {epic} ({market['name']})")
            return epic
        
        # Try searching by company name patterns
        name_searches = {
            'ANZ': 'anz bank',
            'CSL': 'csl limited',
            'RIO': 'rio tinto',
            'WES': 'wesfarmers',
            'GMG': 'goodman group',
            'STO': 'santos',
            'FMG': 'fortescue',
            'COL': 'coles',
            'MQG': 'macquarie',
            'TCL': 'transurban'
        }
        
        if asx_symbol in name_searches:
            market = self.search_market(name_searches[asx_symbol])
            if market and market['epic']:
                epic = market['epic']
                self.symbol_cache[asx_symbol] = epic
                self.logger.info(f"Mapped {asx_symbol} to {epic} via name search ({market['name']})")
                return epic
        
        self.logger.warning(f"No IG Markets mapping found for ASX symbol: {asx_symbol}")
        return None
    
    def get_market_data(self, epic: str) -> Optional[Dict]:
        """Get full market data for an EPIC"""
        if not self.ensure_authenticated():
            return None
        
        try:
            headers = {
                'Accept': 'application/json',
                'X-IG-API-KEY': self.api_key,
                'X-SECURITY-TOKEN': self.auth_token,
                'CST': self.cst_token,
                'Version': '3'
            }
            
            response = requests.get(f'{self.base_url}/markets/{epic}', headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Market data request failed for {epic}: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Market data error for {epic}: {e}")
            return None
    
    def get_price(self, asx_symbol: str) -> Optional[Tuple[float, str]]:
        """
        Get current price for ASX symbol
        Returns (price, status) where status indicates market state
        """
        epic = self.get_asx_epic(asx_symbol)
        if not epic:
            return None
        
        market_data = self.get_market_data(epic)
        if not market_data:
            return None
        
        snapshot = market_data.get('snapshot', {})
        instrument = market_data.get('instrument', {})
        
        # Market status
        market_status = snapshot.get('marketStatus', 'UNKNOWN')
        
        # Try to get live prices first
        bid = snapshot.get('bid')
        offer = snapshot.get('offer')
        
        if bid is not None and offer is not None:
            # Live market prices available
            price = (bid + offer) / 2
            return price, f"LIVE ({market_status})"
        
        # If no live prices, try historical data
        high = snapshot.get('high')
        low = snapshot.get('low')
        
        if high is not None and low is not None:
            # Use midpoint of daily range
            price = (high + low) / 2
            return price, f"HISTORICAL ({market_status})"
        
        # Last resort - check for any price field
        for price_field in ['close', 'open', 'last']:
            price_value = snapshot.get(price_field)
            if price_value is not None:
                return price_value, f"LAST_{price_field.upper()} ({market_status})"
        
        return None
    
    def test_connection(self) -> bool:
        """Test the IG Markets connection"""
        try:
            if not self.authenticate():
                return False
            
            # Test with a known symbol
            price_data = self.get_price('WBC')
            if price_data:
                price, status = price_data
                self.logger.info(f"IG Markets test successful: WBC = ${price:.2f} ({status})")
                return True
            else:
                self.logger.error("IG Markets test failed: could not get WBC price")
                return False
                
        except Exception as e:
            self.logger.error(f"IG Markets test error: {e}")
            return False

# Test script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration
    mapper = IGMarketsASXMapper(
        username='sutho100',
        password='Helloworld987543$',
        api_key='ac68e6f053799a4a36c75936c088fc4d6cfcfa6e',
        demo=True
    )
    
    print("Testing IG Markets ASX Mapper...")
    
    if mapper.test_connection():
        print("✅ IG Markets connection working!")
        
        # Test multiple symbols
        test_symbols = ['WBC', 'CBA', 'BHP', 'NAB', 'WOW', 'TLS']
        
        for symbol in test_symbols:
            price_data = mapper.get_price(symbol)
            if price_data:
                price, status = price_data
                print(f"{symbol}: ${price:.2f} - {status}")
            else:
                print(f"{symbol}: No price available")
    else:
        print("❌ IG Markets connection failed")
