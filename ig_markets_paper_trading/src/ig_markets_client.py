#!/usr/bin/env python3
"""
IG Markets API Client - OAuth authentication and market data
Self-contained client for IG Markets demo API integration
"""

import requests
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

class IGMarketsClient:
    """
    IG Markets API client with OAuth authentication and rate limiting
    """
    
    def __init__(self, config_path: str = "config/ig_markets_config.json"):
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        
        # OAuth authentication tokens
        self.access_token = None
        self.refresh_token = None
        self.account_id = None
        self.token_expires_at = None
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_limit_reset = datetime.now()
        
        # Authenticate on initialization
        self._authenticate()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load IG Markets configuration"""
        try:
            config_full_path = os.path.join(os.path.dirname(__file__), '..', config_path)
            with open(config_full_path, 'r') as f:
                config = json.load(f)
            
            # Check for environment variables
            config['api_key'] = os.getenv('IG_MARKETS_API_KEY', config.get('api_key', ''))
            config['username'] = os.getenv('IG_MARKETS_USERNAME', config.get('username', ''))
            config['password'] = os.getenv('IG_MARKETS_PASSWORD', config.get('password', ''))
            config['account_id'] = os.getenv('IG_MARKETS_ACCOUNT_ID', config.get('account_id', ''))
            
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset hourly counter
        if datetime.now() > self.request_limit_reset:
            self.request_count = 0
            self.request_limit_reset = datetime.now() + timedelta(hours=1)
        
        # Check hourly limit
        max_requests = self.config.get('max_api_calls_per_hour', 100)
        if self.request_count >= max_requests:
            wait_time = (self.request_limit_reset - datetime.now()).total_seconds()
            logger.warning(f"Rate limit reached, waiting {wait_time:.0f} seconds")
            time.sleep(wait_time)
            self.request_count = 0
            self.request_limit_reset = datetime.now() + timedelta(hours=1)
        
        # Minimum time between requests (1 second)
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _authenticate(self) -> bool:
        """Authenticate with IG Markets API using OAuth"""
        if not self.config.get("api_key") or not self.config.get("username"):
            logger.error("❌ IG Markets credentials not configured")
            return False
        
        url = f"{self.config['base_url']}/session"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-IG-API-KEY': self.config['api_key'],
            'Version': '3'
        }
        
        data = {
            'identifier': self.config['username'],
            'password': self.config['password']
        }
        
        try:
            self._rate_limit_check()
            response = self.session.post(url, headers=headers, json=data, timeout=self.config.get('timeout', 30))
            
            if response.status_code == 200:
                auth_data = response.json()
                
                # Extract OAuth tokens
                oauth_token = auth_data.get('oauthToken', {})
                self.access_token = oauth_token.get('access_token')
                self.refresh_token = oauth_token.get('refresh_token')
                self.account_id = auth_data.get('accountId')
                
                # Calculate token expiry time
                expires_in = int(oauth_token.get('expires_in', 30))
                self.token_expires_at = datetime.now() + timedelta(minutes=expires_in)
                
                # Update session headers for OAuth
                self.session.headers.update({
                    'X-IG-API-KEY': self.config['api_key'],
                    'Authorization': f'Bearer {self.access_token}',
                    'IG-ACCOUNT-ID': self.account_id,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Version': '3'
                })
                
                logger.info("✅ Successfully authenticated with IG Markets (OAuth)")
                logger.info(f"Account ID: {self.account_id}")
                logger.info(f"Token expires at: {self.token_expires_at}")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def _check_token_expiry(self) -> bool:
        """Check if token needs refresh"""
        if not self.token_expires_at:
            return False
        
        # Refresh token if it expires in next 5 minutes
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))
    
    def _refresh_access_token(self) -> bool:
        """Refresh OAuth access token"""
        if not self.refresh_token:
            logger.warning("No refresh token available, re-authenticating...")
            return self._authenticate()
        
        url = f"{self.config['base_url']}/session/refresh-token"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-IG-API-KEY': self.config['api_key'],
            'Authorization': f'Bearer {self.access_token}',
            'Version': '1'
        }
        
        data = {
            'refresh_token': self.refresh_token
        }
        
        try:
            self._rate_limit_check()
            response = self.session.post(url, headers=headers, json=data, timeout=self.config.get('timeout', 30))
            
            if response.status_code == 200:
                auth_data = response.json()
                oauth_token = auth_data.get('oauthToken', {})
                
                self.access_token = oauth_token.get('access_token')
                self.refresh_token = oauth_token.get('refresh_token')
                
                expires_in = int(oauth_token.get('expires_in', 30))
                self.token_expires_at = datetime.now() + timedelta(minutes=expires_in)
                
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                logger.info("✅ Successfully refreshed OAuth token")
                return True
            else:
                logger.warning(f"Token refresh failed: {response.status_code}, re-authenticating...")
                return self._authenticate()
                
        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}")
            return self._authenticate()
    
    def get_market_price(self, epic: str) -> Optional[Dict]:
        """Get current market price from IG Markets"""
        # Check token expiry
        if self._check_token_expiry():
            if not self._refresh_access_token():
                logger.error("Failed to refresh token")
                return None
        
        url = f"{self.config['base_url']}/markets/{epic}"
        
        try:
            self._rate_limit_check()
            response = self.session.get(url, timeout=self.config.get('timeout', 30))
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('snapshot', {})
                
                return {
                    'epic': epic,
                    'bid': market_data.get('bid'),
                    'offer': market_data.get('offer'),
                    'market_status': market_data.get('marketStatus'),
                    'timestamp': datetime.now().isoformat()
                }
            elif response.status_code == 404:
                logger.warning(f"Epic {epic} not found or not available")
                return None
            elif response.status_code == 403:
                logger.warning(f"Rate limit exceeded for {epic}, will retry later")
                return None
            else:
                logger.error(f"❌ Failed to get price for {epic}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting market price for {epic}: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        # Check token expiry
        if self._check_token_expiry():
            if not self._refresh_access_token():
                logger.error("Failed to refresh token")
                return None
        
        url = f"{self.config['base_url']}/accounts"
        
        try:
            self._rate_limit_check()
            response = self.session.get(url, timeout=self.config.get('timeout', 30))
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('accounts', [])
                
                # Find the demo account
                for account in accounts:
                    if account.get('accountId') == self.account_id:
                        return {
                            'account_id': account.get('accountId'),
                            'account_name': account.get('accountName'),
                            'balance': account.get('balance', {}).get('balance', 0),
                            'currency': account.get('currency'),
                            'account_type': account.get('accountType')
                        }
                
                logger.warning(f"Account {self.account_id} not found in account list")
                return None
            else:
                logger.error(f"❌ Failed to get account info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting account info: {e}")
            return None
    
    def map_symbol_to_epic(self, symbol: str) -> str:
        """Map ASX symbol to IG Markets EPIC"""
        mappings = self.config.get('symbol_mappings', {})
        epic = mappings.get(symbol, 'IX.D.FTSE.DAILY.IP')  # Default to FTSE
        
        if epic != symbol:  # Only log if mapping occurred
            logger.debug(f"Mapped {symbol} to {epic}")
        
        return epic
    
    def test_connection(self) -> bool:
        """Test connection to IG Markets API"""
        try:
            # Test authentication only
            if self._authenticate():
                logger.info(f"✅ Connection test successful - Account: {self.account_id}")
                return True
            else:
                logger.error("❌ Connection test failed - Authentication failed")
                return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        time_to_reset = (self.request_limit_reset - datetime.now()).total_seconds()
        return {
            'requests_made': self.request_count,
            'requests_remaining': max(0, self.config.get('max_api_calls_per_hour', 100) - self.request_count),
            'reset_time': self.request_limit_reset.isoformat(),
            'seconds_to_reset': max(0, time_to_reset)
        }
