#!/usr/bin/env python3
"""
Test IG Markets credentials
"""
import requests
import json
import sys

def test_ig_markets_credentials():
    """Test IG Markets API credentials"""
    
    # Your credentials
    api_key = "ac68e6f053799a4a36c75936c088fc4d6cfcfa6e"
    username = "sutho100"
    password = "Helloworld987543$"
    
    # IG Markets API endpoints
    base_url = "https://demo-api.ig.com/gateway/deal"  # Demo environment
    # base_url = "https://api.ig.com/gateway/deal"  # Live environment
    
    login_url = f"{base_url}/session"
    
    print("🔑 Testing IG Markets credentials...")
    print(f"API Key: {api_key[:10]}...")
    print(f"Username: {username}")
    print(f"Using demo environment: {base_url}")
    
    # Login request headers
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json; charset=UTF-8",
        "X-IG-API-KEY": api_key,
        "Version": "2"
    }
    
    # Login request body
    login_data = {
        "identifier": username,
        "password": password
    }
    
    try:
        print("\n📡 Attempting login...")
        response = requests.post(
            login_url,
            headers=headers,
            data=json.dumps(login_data),
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ LOGIN SUCCESSFUL!")
            
            response_data = response.json()
            print(f"Account Info: {json.dumps(response_data, indent=2)}")
            
            # Extract session tokens
            cst_token = response.headers.get('CST')
            x_security_token = response.headers.get('X-SECURITY-TOKEN')
            
            if cst_token and x_security_token:
                print(f"\n🔐 Session Tokens Received:")
                print(f"CST: {cst_token[:20]}...")
                print(f"X-SECURITY-TOKEN: {x_security_token[:20]}...")
                
                # Test a simple API call - get accounts
                test_api_call(base_url, api_key, cst_token, x_security_token)
                
            return True
            
        else:
            print("❌ LOGIN FAILED!")
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            # Try to parse error response
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_api_call(base_url, api_key, cst_token, x_security_token):
    """Test a simple API call with the session tokens"""
    
    print("\n🧪 Testing API call - Get Accounts...")
    
    accounts_url = f"{base_url}/accounts"
    
    headers = {
        "Accept": "application/json; charset=UTF-8",
        "X-IG-API-KEY": api_key,
        "CST": cst_token,
        "X-SECURITY-TOKEN": x_security_token,
        "Version": "1"
    }
    
    try:
        response = requests.get(accounts_url, headers=headers, timeout=10)
        
        print(f"Accounts API Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API CALL SUCCESSFUL!")
            accounts_data = response.json()
            print(f"Accounts: {json.dumps(accounts_data, indent=2)}")
        else:
            print("❌ API CALL FAILED!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API CALL ERROR: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("IG MARKETS CREDENTIALS TEST")
    print("=" * 50)
    
    success = test_ig_markets_credentials()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CREDENTIALS WORK! IG Markets integration ready.")
    else:
        print("💥 CREDENTIALS FAILED! Check your details.")
    print("=" * 50)
