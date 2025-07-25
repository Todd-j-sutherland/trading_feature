#!/usr/bin/env python3
"""
Test script to verify all API endpoints are working correctly
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test an API endpoint and print results"""
    url = f"{BASE_URL}{endpoint}"
    headers = headers or {}
    headers['Origin'] = 'http://localhost:3001'  # Simulate frontend origin
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and 'data' in result:
                print(f"Success: {result.get('success', 'N/A')}")
                if isinstance(result['data'], list):
                    print(f"Data points: {len(result['data'])}")
                else:
                    print(f"Data: {type(result['data'])}")
            else:
                print(f"Response: {result}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    print("🧪 Testing ASX Trading API Endpoints")
    print("=" * 50)
    
    # Test historical data endpoints
    test_endpoint('GET', '/api/banks/CBA.AX/ohlcv?period=1D')
    test_endpoint('GET', '/api/banks/CBA.AX/ml-indicators?period=1D')
    test_endpoint('GET', '/api/banks/CBA.AX/predictions/latest')
    
    # Test live data endpoints
    test_endpoint('GET', '/api/live/price/CBA.AX')
    test_endpoint('GET', '/api/live/technical/CBA.AX')
    
    # Test ML prediction endpoint
    test_data = {
        "symbol": "CBA.AX",
        "priceData": {
            "open": 172.39,
            "high": 172.39,
            "low": 172.39,
            "close": 172.39,
            "volume": 1000
        },
        "technicalFeatures": {
            "rsi": 39.26,
            "macd": -1.68,
            "bollinger_position": 0.058,
            "volume_ratio": 0.459,
            "price_momentum": -3.09
        },
        "timestamp": int(time.time() * 1000)
    }
    test_endpoint('POST', '/api/live/ml-predict', data=test_data)
    
    print("\n" + "=" * 50)
    print("✅ API Testing Complete!")

if __name__ == "__main__":
    main()
