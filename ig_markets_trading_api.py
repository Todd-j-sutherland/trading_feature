#!/usr/bin/env python3
"""
IG Markets Live Trading API Client

This module provides actual IG Markets API integration for placing real orders.
Includes proper debugging, error handling, and timeout management.
"""

import os
import sys
import requests
import json
import logging
import time
from typing import Dict, Optional, Any, List
from datetime import datetime
import signal

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

class IGMarketsAPIClient:
    """IG Markets API client for live trading"""
    
    def __init__(self):
        """Initialize IG Markets API client"""
        self.logger = logging.getLogger(__name__)
        
        # API Configuration
        self.api_key = os.getenv('IG_API_KEY', 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e')
        self.username = os.getenv('IG_USERNAME', 'sutho100')
        self.password = os.getenv('IG_PASSWORD', 'Helloworld987543$')
        self.account_id = os.getenv('IG_ACCOUNT_ID', 'Z3GAGH')
        self.demo_mode = os.getenv('IG_DEMO_MODE', 'true').lower() == 'true'
        
        # API URLs
        self.base_url = "https://demo-api.ig.com/gateway/deal" if self.demo_mode else "https://api.ig.com/gateway/deal"
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({
            'X-IG-API-KEY': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Version': '2'
        })
        
        # Authentication tokens
        self.access_token = None
        self.cst_token = None
        self.security_token = None
        
        # Set up timeout for all operations
        self.timeout = 30
        
        self.logger.info(f"IG Markets API Client initialized (demo: {self.demo_mode})")
    
    def authenticate(self) -> bool:
        """Authenticate with IG Markets API"""
        try:
            # Set signal timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            auth_url = f"{self.base_url}/session"
            auth_data = {
                "identifier": self.username,
                "password": self.password
            }
            
            self.logger.info(f"Authenticating with IG Markets API...")
            
            response = self.session.post(
                auth_url, 
                json=auth_data, 
                timeout=self.timeout
            )
            
            # Cancel timeout
            signal.alarm(0)
            
            if response.status_code == 200:
                # Extract tokens from headers
                self.cst_token = response.headers.get('CST')
                self.security_token = response.headers.get('X-SECURITY-TOKEN')
                
                # Update session headers
                self.session.headers.update({
                    'CST': self.cst_token,
                    'X-SECURITY-TOKEN': self.security_token
                })
                
                auth_response = response.json()
                self.account_id = auth_response.get('currentAccountId', self.account_id)
                
                self.logger.info(f"✅ Authentication successful - Account: {self.account_id}")
                return True
            else:
                self.logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except TimeoutException:
            self.logger.error("❌ Authentication timed out after 30 seconds")
            return False
        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            return False
        finally:
            signal.alarm(0)  # Always cancel timeout
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information and verify connection"""
        try:
            if not self.cst_token:
                if not self.authenticate():
                    return None
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            accounts_url = f"{self.base_url}/accounts"
            response = self.session.get(accounts_url, timeout=self.timeout)
            
            signal.alarm(0)
            
            if response.status_code == 200:
                accounts_data = response.json()
                self.logger.info("✅ Account information retrieved successfully")
                return accounts_data
            else:
                self.logger.error(f"❌ Failed to get account info: {response.status_code}")
                return None
                
        except TimeoutException:
            self.logger.error("❌ Account info request timed out")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting account info: {e}")
            return None
        finally:
            signal.alarm(0)
    
    def get_market_info(self, epic: str) -> Optional[Dict]:
        """Get market information for a specific epic"""
        try:
            if not self.cst_token:
                if not self.authenticate():
                    return None
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            market_url = f"{self.base_url}/markets/{epic}"
            response = self.session.get(market_url, timeout=self.timeout)
            
            signal.alarm(0)
            
            if response.status_code == 200:
                market_data = response.json()
                self.logger.info(f"✅ Market info retrieved for {epic}")
                return market_data
            else:
                self.logger.error(f"❌ Failed to get market info for {epic}: {response.status_code}")
                return None
                
        except TimeoutException:
            self.logger.error(f"❌ Market info request timed out for {epic}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting market info for {epic}: {e}")
            return None
        finally:
            signal.alarm(0)
    
    def place_order(self, epic: str, direction: str, size: int, order_type: str = "MARKET") -> Optional[Dict]:
        """Place a live order with IG Markets"""
        try:
            if not self.cst_token:
                if not self.authenticate():
                    return None
            
            # Verify market is available
            market_info = self.get_market_info(epic)
            if not market_info:
                self.logger.error(f"❌ Cannot place order - market info unavailable for {epic}")
                return None
            
            # Check if market is tradeable
            market_status = market_info.get('snapshot', {}).get('marketStatus')
            if market_status != 'TRADEABLE':
                self.logger.warning(f"⚠️ Market {epic} status: {market_status} - order may not execute")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            # Prepare order data
            order_data = {
                "epic": epic,
                "direction": direction.upper(),  # BUY or SELL
                "size": str(size),
                "orderType": order_type,
                "timeInForce": "FILL_OR_KILL",
                "guaranteedStop": False,
                "forceOpen": True,
                "currencyCode": "AUD"
            }
            
            self.logger.info(f"🎯 Placing {direction} order: {size} shares of {epic}")
            self.logger.info(f"📊 Order details: {json.dumps(order_data, indent=2)}")
            
            # Place the order
            positions_url = f"{self.base_url}/positions/otc"
            response = self.session.post(
                positions_url, 
                json=order_data, 
                timeout=self.timeout
            )
            
            signal.alarm(0)
            
            # Parse response
            response_data = response.json()
            
            if response.status_code == 200:
                deal_reference = response_data.get('dealReference')
                self.logger.info(f"✅ Order placed successfully!")
                self.logger.info(f"📄 Deal Reference: {deal_reference}")
                
                # Wait a moment and check deal confirmation
                time.sleep(2)
                deal_status = self.check_deal_status(deal_reference)
                
                return {
                    'success': True,
                    'deal_reference': deal_reference,
                    'status': deal_status,
                    'order_data': order_data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.error(f"❌ Order failed: {response.status_code}")
                self.logger.error(f"📄 Error details: {json.dumps(response_data, indent=2)}")
                return {
                    'success': False,
                    'error': response_data,
                    'status_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
                
        except TimeoutException:
            self.logger.error("❌ Order placement timed out")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            self.logger.error(f"❌ Error placing order: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            signal.alarm(0)
    
    def check_deal_status(self, deal_reference: str) -> Optional[Dict]:
        """Check the status of a placed deal"""
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            deal_url = f"{self.base_url}/confirms/{deal_reference}"
            response = self.session.get(deal_url, timeout=self.timeout)
            
            signal.alarm(0)
            
            if response.status_code == 200:
                deal_data = response.json()
                status = deal_data.get('dealStatus')
                reason = deal_data.get('reason')
                
                self.logger.info(f"📋 Deal {deal_reference} status: {status}")
                if reason:
                    self.logger.info(f"📝 Reason: {reason}")
                
                return deal_data
            else:
                self.logger.error(f"❌ Could not check deal status: {response.status_code}")
                return None
                
        except TimeoutException:
            self.logger.error("❌ Deal status check timed out")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error checking deal status: {e}")
            return None
        finally:
            signal.alarm(0)
    
    def get_positions(self) -> Optional[List[Dict]]:
        """Get current open positions"""
        try:
            if not self.cst_token:
                if not self.authenticate():
                    return None
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            positions_url = f"{self.base_url}/positions"
            response = self.session.get(positions_url, timeout=self.timeout)
            
            signal.alarm(0)
            
            if response.status_code == 200:
                positions_data = response.json()
                positions = positions_data.get('positions', [])
                self.logger.info(f"📊 Retrieved {len(positions)} open positions")
                return positions
            else:
                self.logger.error(f"❌ Failed to get positions: {response.status_code}")
                return None
                
        except TimeoutException:
            self.logger.error("❌ Get positions request timed out")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting positions: {e}")
            return None
        finally:
            signal.alarm(0)

# Symbol mapping for ASX stocks to IG epics
SYMBOL_TO_EPIC = {
    'CBA.AX': 'AU.CBA.CHESS.IP',
    'WBC.AX': 'AU.WBC.CHESS.IP', 
    'ANZ.AX': 'AU.ANZ.CHESS.IP',
    'NAB.AX': 'AU.NAB.CHESS.IP',
    'MQG.AX': 'AU.MQG.CHESS.IP',
    'SUN.AX': 'AU.SUN.CHESS.IP',
    'QBE.AX': 'AU.QBE.CHESS.IP'
}
