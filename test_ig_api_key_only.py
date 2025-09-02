import requests
import json

# Test IG Markets API with just API key for market data
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

print('Testing IG Markets API with API key only...')
print(f'API Key: {api_key[:16]}...')

# Test different endpoints that might work with just API key
test_endpoints = [
    '/markets',  # General markets
    '/markets/AUDUSD',  # Specific market  
    '/markets?searchTerm=WBC',  # Search for WBC
    '/marketnavigation',  # Market navigation
]

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-IG-API-KEY': api_key,
    'Version': '3'
}

for endpoint in test_endpoints:
    print(f'\n=== Testing {endpoint} ===')
    
    try:
        response = requests.get(f'{base_url}{endpoint}', headers=headers, timeout=10)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ SUCCESS! API key only works')
            data = response.json()
            print(f'Response keys: {list(data.keys())}')
            if 'markets' in data:
                markets = data['markets'][:3]  # First 3 markets
                for market in markets:
                    name = market.get('instrumentName', 'Unknown')
                    epic = market.get('epic', 'Unknown')
                    print(f'  - {name} ({epic})')
            break
        elif response.status_code == 401:
            print('❌ 401: Authentication required')
        elif response.status_code == 403:
            print('❌ 403: Forbidden - API key might be invalid')
        else:
            print(f'❌ {response.status_code}: {response.text[:100]}...')
            
    except Exception as e:
        print(f'❌ Error: {e}')

# Test if we can get market data without authentication
print('\n=== Testing public market data ===')
try:
    # Some APIs have public endpoints
    headers_minimal = {
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key
    }
    
    response = requests.get(f'{base_url}/marketnavigation', headers=headers_minimal, timeout=10)
    print(f'Public data status: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ Public market data available!')
        data = response.json()
        print(f'Response keys: {list(data.keys())}')
    else:
        print(f'❌ No public data: {response.text[:100]}...')
        
except Exception as e:
    print(f'Public data error: {e}')
