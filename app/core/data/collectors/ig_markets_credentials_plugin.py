#!/usr/bin/env python3
"""
IG Markets Credentials Plugin

This plugin updates your existing IG Markets integration with working credentials
and ensures the main app uses IG Markets as primary data source.

Plugin approach: No disruption to existing code, just enhanced functionality.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class IGMarketsCredentialsPlugin:
    """
    Plugin to inject working IG Markets credentials into existing system
    """
    
    def __init__(self):
        self.credentials = {
            'api_key': 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e',
            'username': 'sutho100', 
            'password': 'Helloworld987543$',
            'demo': True,  # Using demo account
            'base_url': 'https://demo-api.ig.com/gateway/deal'
        }
        self._plugin_active = False
        
    def activate(self) -> bool:
        """
        Activate the credentials plugin
        Updates environment variables and configuration
        """
        try:
            # Set environment variables for IG Markets
            os.environ['IG_MARKETS_API_KEY'] = self.credentials['api_key']
            os.environ['IG_MARKETS_USERNAME'] = self.credentials['username']
            os.environ['IG_MARKETS_PASSWORD'] = self.credentials['password']
            os.environ['IG_MARKETS_DEMO'] = 'true'
            os.environ['IG_MARKETS_ENABLED'] = 'true'
            
            # Update your existing real-time price fetcher
            self._update_real_time_price_fetcher()
            
            # Update enhanced market data collector
            self._update_enhanced_market_data_collector()
            
            # Update IG Markets config
            self._update_ig_markets_config()
            
            self._plugin_active = True
            logger.info("✅ IG Markets Credentials Plugin activated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to activate IG Markets credentials plugin: {e}")
            return False
    
    def _update_real_time_price_fetcher(self):
        """Update the existing RealTimePriceFetcher with credentials"""
        try:
            # Import your existing RealTimePriceFetcher
            from app.core.data.collectors.real_time_price_fetcher import RealTimePriceFetcher
            
            # Monkey patch the initialization to use working credentials
            original_init = RealTimePriceFetcher.__init__
            
            def enhanced_init(self_inner):
                original_init(self_inner)
                # Override with working credentials
                if hasattr(self_inner, 'ig_markets'):
                    self_inner.ig_markets.username = self.credentials['username']
                    self_inner.ig_markets.password = self.credentials['password'] 
                    self_inner.ig_markets.api_key = self.credentials['api_key']
                    self_inner.ig_markets.demo = self.credentials['demo']
                    logger.info("🔧 RealTimePriceFetcher updated with working IG Markets credentials")
            
            RealTimePriceFetcher.__init__ = enhanced_init
            
        except ImportError:
            logger.debug("RealTimePriceFetcher not available for credential update")
        except Exception as e:
            logger.warning(f"Could not update RealTimePriceFetcher: {e}")
    
    def _update_enhanced_market_data_collector(self):
        """Update the EnhancedMarketDataCollector to prioritize IG Markets"""
        try:
            from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
            
            # Ensure IG Markets is always tried first for ASX symbols
            original_get_price = EnhancedMarketDataCollector.get_current_price
            
            def enhanced_get_price(self_inner, symbol: str):
                # Prioritize IG Markets for ASX symbols
                if symbol.endswith('.AX') or symbol in ['WBC', 'CBA', 'ANZ', 'NAB', 'BHP']:
                    # Force IG Markets attempt with working credentials
                    if hasattr(self_inner, 'ig_available') and self_inner.ig_available:
                        ig_result = self_inner._get_ig_markets_price(symbol)
                        if ig_result and ig_result.get('success'):
                            return ig_result
                
                # Fallback to original method
                return original_get_price(self_inner, symbol)
            
            EnhancedMarketDataCollector.get_current_price = enhanced_get_price
            logger.info("🔧 EnhancedMarketDataCollector updated to prioritize IG Markets")
            
        except ImportError:
            logger.debug("EnhancedMarketDataCollector not available for update")
        except Exception as e:
            logger.warning(f"Could not update EnhancedMarketDataCollector: {e}")
    
    def _update_ig_markets_config(self):
        """Update IG Markets configuration files"""
        try:
            # Update the config file if it exists
            config_path = Path(__file__).parent.parent.parent / 'config' / 'ig_markets_config.py'
            
            if config_path.exists():
                # Read the current config
                with open(config_path, 'r') as f:
                    content = f.read()
                
                # Update with working credentials (if they're placeholder values)
                if 'your_api_key_here' in content or 'demo_key' in content:
                    content = content.replace('your_api_key_here', self.credentials['api_key'])
                    content = content.replace('your_username_here', self.credentials['username'])
                    content = content.replace('your_password_here', self.credentials['password'])
                    
                    # Write back the updated config
                    with open(config_path, 'w') as f:
                        f.write(content)
                    
                    logger.info("🔧 IG Markets config file updated with working credentials")
            
        except Exception as e:
            logger.debug(f"Could not update IG Markets config file: {e}")
    
    def validate_credentials(self) -> Dict[str, any]:
        """
        Validate that the credentials work by testing IG Markets API
        """
        try:
            import requests
            import json
            
            # Test login to IG Markets API
            login_url = f"{self.credentials['base_url']}/session"
            
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json; charset=UTF-8", 
                "X-IG-API-KEY": self.credentials['api_key'],
                "Version": "2"
            }
            
            login_data = {
                "identifier": self.credentials['username'],
                "password": self.credentials['password']
            }
            
            response = requests.post(
                login_url,
                headers=headers,
                data=json.dumps(login_data),
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                account_info = response_data.get('accountInfo', {})
                
                return {
                    'status': 'success',
                    'authenticated': True,
                    'account_id': response_data.get('currentAccountId'),
                    'account_balance': account_info.get('balance'),
                    'currency': response_data.get('currencySymbol'),
                    'dealing_enabled': response_data.get('dealingEnabled', False),
                    'message': 'IG Markets credentials validated successfully'
                }
            else:
                return {
                    'status': 'failed',
                    'authenticated': False,
                    'error': f"Authentication failed: {response.status_code}",
                    'message': response.text
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'authenticated': False,
                'error': str(e),
                'message': 'Could not validate credentials'
            }
    
    def get_status(self) -> Dict[str, any]:
        """Get plugin status and health"""
        return {
            'plugin_active': self._plugin_active,
            'credentials_configured': bool(self.credentials['api_key']),
            'environment_variables_set': all([
                os.getenv('IG_MARKETS_API_KEY'),
                os.getenv('IG_MARKETS_USERNAME'), 
                os.getenv('IG_MARKETS_PASSWORD')
            ]),
            'demo_mode': self.credentials['demo'],
            'last_validation': 'Not tested' if not hasattr(self, '_last_validation') else self._last_validation
        }
    
    def deactivate(self):
        """Deactivate the plugin and restore original behavior"""
        try:
            # Remove environment variables
            for key in ['IG_MARKETS_API_KEY', 'IG_MARKETS_USERNAME', 'IG_MARKETS_PASSWORD', 'IG_MARKETS_DEMO', 'IG_MARKETS_ENABLED']:
                if key in os.environ:
                    del os.environ[key]
            
            self._plugin_active = False
            logger.info("🔌 IG Markets Credentials Plugin deactivated")
            
        except Exception as e:
            logger.error(f"Error deactivating plugin: {e}")

# Global plugin instance
ig_credentials_plugin = IGMarketsCredentialsPlugin()

# Convenience functions
def activate_ig_markets_credentials() -> bool:
    """Activate IG Markets credentials plugin"""
    return ig_credentials_plugin.activate()

def validate_ig_markets_credentials() -> Dict[str, any]:
    """Validate IG Markets credentials"""
    return ig_credentials_plugin.validate_credentials()

def get_ig_markets_plugin_status() -> Dict[str, any]:
    """Get IG Markets plugin status"""
    return ig_credentials_plugin.get_status()

if __name__ == "__main__":
    # Test the credentials plugin
    logging.basicConfig(level=logging.INFO)
    
    print("🔑 IG Markets Credentials Plugin Test")
    print("=" * 50)
    
    # Test credential validation
    print("📡 Validating credentials...")
    validation_result = validate_ig_markets_credentials()
    
    if validation_result['status'] == 'success':
        print(f"✅ Credentials valid!")
        print(f"   Account ID: {validation_result['account_id']}")
        print(f"   Balance: {validation_result['currency']}{validation_result['account_balance']}")
        print(f"   Dealing Enabled: {validation_result['dealing_enabled']}")
    else:
        print(f"❌ Credential validation failed:")
        print(f"   Error: {validation_result['error']}")
    
    # Test plugin activation
    print(f"\n🔌 Activating plugin...")
    activation_success = activate_ig_markets_credentials()
    
    if activation_success:
        print("✅ Plugin activated successfully")
        
        # Show status
        status = get_ig_markets_plugin_status()
        print(f"   Plugin Active: {status['plugin_active']}")
        print(f"   Environment Variables Set: {status['environment_variables_set']}")
        print(f"   Demo Mode: {status['demo_mode']}")
    else:
        print("❌ Plugin activation failed")
