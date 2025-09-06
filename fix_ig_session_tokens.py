#!/usr/bin/env python3
"""
Fix IG Markets session token handling
Debug and fix the session token extraction and persistence
"""

import json
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ig_authentication():
    """Test and debug IG Markets authentication"""
    
    # Load config
    with open("config/ig_markets_config.json", 'r') as f:
        config = json.load(f)
    
    print("🔍 Testing IG Markets authentication and token handling...")
    
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
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            # Check for tokens in various header formats
            cst_token = response.headers.get('CST')
            security_token = response.headers.get('X-SECURITY-TOKEN')
            
            # Also check alternative header names
            cst_alt = response.headers.get('cst')
            security_alt = response.headers.get('x-security-token')
            
            print(f"\n🔍 Token Analysis:")
            print(f"CST Token (CST): {cst_token}")
            print(f"CST Token (cst): {cst_alt}")
            print(f"Security Token (X-SECURITY-TOKEN): {security_token}")
            print(f"Security Token (x-security-token): {security_alt}")
            
            # Test market data request with tokens
            if cst_token and security_token:
                print(f"\n🔍 Testing market data request with tokens...")
                test_market_data(config, cst_token, security_token)
            else:
                print(f"\n❌ No valid tokens found in response headers")
            
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")

def test_market_data(config, cst_token, security_token):
    """Test market data request with session tokens"""
    
    epic = "AU.CBA.CHESS.IP"
    url = f"{config['base_url']}/gateway/deal/markets/{epic}"
    
    headers = {
        'X-IG-API-KEY': config['api_key'],
        'CST': cst_token,
        'X-SECURITY-TOKEN': security_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Version': '3'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Market Data Status: {response.status_code}")
        print(f"Market Data Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('snapshot', {})
            
            print(f"✅ Market data successful!")
            print(f"Bid: {market_data.get('bid')}")
            print(f"Offer: {market_data.get('offer')}")
            print(f"Market Status: {market_data.get('marketStatus')}")
        else:
            print(f"❌ Market data failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Market data error: {e}")

if __name__ == "__main__":
    test_ig_authentication()
