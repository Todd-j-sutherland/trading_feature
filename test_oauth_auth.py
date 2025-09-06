#!/usr/bin/env python3
"""
Fix IG Markets authentication to use OAuth tokens
Updated authentication method for IG Markets API v3
"""

import json
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_oauth_authentication():
    """Test IG Markets OAuth authentication method"""
    
    # Load config
    with open("config/ig_markets_config.json", 'r') as f:
        config = json.load(f)
    
    print("🔍 Testing IG Markets OAuth authentication...")
    
    url = f"{config['base_url']}/gateway/deal/session"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-IG-API-KEY': config['api_key'],
        'Version': '3'
    }
    
    data = {
        'identifier': config['username'],
        'password': config['password']
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            auth_data = response.json()
            print(f"✅ Authentication successful!")
            print(f"Auth Response: {json.dumps(auth_data, indent=2)}")
            
            # Extract OAuth token
            oauth_token = auth_data.get('oauthToken', {})
            access_token = oauth_token.get('access_token')
            account_id = auth_data.get('accountId')
            
            if access_token:
                print(f"\n🔍 Testing market data with OAuth token...")
                test_market_data_oauth(config, access_token, account_id)
            else:
                print(f"❌ No OAuth token found in response")
            
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")

def test_market_data_oauth(config, access_token, account_id):
    """Test market data request with OAuth token"""
    
    epic = "AU.CBA.CHESS.IP"
    url = f"{config['base_url']}/gateway/deal/markets/{epic}"
    
    headers = {
        'X-IG-API-KEY': config['api_key'],
        'Authorization': f'Bearer {access_token}',
        'IG-ACCOUNT-ID': account_id,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Version': '3'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Market Data Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('snapshot', {})
            
            print(f"✅ Market data successful!")
            print(f"Bid: {market_data.get('bid')}")
            print(f"Offer: {market_data.get('offer')}")
            print(f"Market Status: {market_data.get('marketStatus')}")
            return True
        else:
            print(f"❌ Market data failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Market data error: {e}")
        return False

if __name__ == "__main__":
    test_oauth_authentication()
